#!/usr/bin/env python3
"""
FastAPI 後端 - 讀取 data_100k 資料表
支援連線池開關功能、安全性優化 (Rate Limit, CORS, Env Vars)
"""

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from typing import Optional
from contextlib import contextmanager
import time

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================
# 配置載入
# ============================================
# Debug 模式
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# CORS 設定
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")

# GZip 壓縮設定
USE_GZIP = False             # 開關：True=啟用 GZip, False=停用 (本地測試建議關閉)
GZIP_MIN_SIZE = 500          # 最小壓縮大小 (bytes)

# 資料庫連線設定 (讀取環境變數)
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", 5433)),
    'database': os.getenv("DB_NAME", "testdb"),
    'user': os.getenv("DB_USER", "testuser"),
    'password': os.getenv("DB_PASSWORD", "testpass")
}

# 連線池設定
USE_CONNECTION_POOL = False  # 開關：True=使用連線池, False=不使用
POOL_MIN_CONN = 2           # 最小連線數
POOL_MAX_CONN = 10          # 最大連線數

# 初始化 Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="PostgreSQL Data API",
    description="API for querying data_100k table",
    version="1.0.0",
    debug=DEBUG_MODE
)

# 註冊 Rate Limit 錯誤處理
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 啟用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 啟用 GZip 壓縮
if USE_GZIP:
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_SIZE)
    print(f"✅ GZip 壓縮已啟用 (minimum_size={GZIP_MIN_SIZE})")
else:
    print("⚠️ GZip 壓縮已停用")

# 連線池實例
connection_pool: Optional[pool.ThreadedConnectionPool] = None

def init_connection_pool():
    """初始化連線池"""
    global connection_pool
    if USE_CONNECTION_POOL and connection_pool is None:
        try:
            connection_pool = pool.ThreadedConnectionPool(
                POOL_MIN_CONN,
                POOL_MAX_CONN,
                **DB_CONFIG
            )
            print(f"✅ 連線池已啟用 (min={POOL_MIN_CONN}, max={POOL_MAX_CONN})")
        except Exception as e:
            print(f"❌ 連線池初始化失敗: {e}")

def close_connection_pool():
    """關閉連線池"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        print("🔌 連線池已關閉")

@contextmanager
def get_db_connection():
    """取得資料庫連線 (Context Manager)"""
    conn = None
    try:
        if USE_CONNECTION_POOL and connection_pool:
            conn = connection_pool.getconn()
        else:
            conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        print(f"❌ 資料庫錯誤: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if conn:
            if USE_CONNECTION_POOL and connection_pool:
                connection_pool.putconn(conn)
            else:
                conn.close()

# 啟動/關閉事件
@app.on_event("startup")
async def startup_event():
    print(f"🛡️  CORS Origins: {CORS_ORIGINS}")
    print(f"🛡️  Debug Mode: {DEBUG_MODE}")
    if USE_CONNECTION_POOL:
        init_connection_pool()
    else:
        print("⚠️ 連線池已停用，使用直接連線模式")

@app.on_event("shutdown")
async def shutdown_event():
    close_connection_pool()

# API 端點
@app.get("/")
async def root():
    """載入前端頁面"""
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/pool/status")
async def get_pool_status():
    """取得連線池狀態"""
    return {
        "use_connection_pool": USE_CONNECTION_POOL,
        "pool_initialized": connection_pool is not None,
        "pool_min_conn": POOL_MIN_CONN if USE_CONNECTION_POOL else None,
        "pool_max_conn": POOL_MAX_CONN if USE_CONNECTION_POOL else None,
    }

@app.get("/data/count")
@limiter.limit("60/minute")
async def get_count(request: Request):
    """取得資料總數"""
    start_time = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT COUNT(*) as count FROM data_100k")
            result = cursor.fetchone()
            elapsed = time.time() - start_time
            return {
                "count": result["count"],
                "query_time_ms": round(elapsed * 1000, 2),
                "connection_pool": USE_CONNECTION_POOL
            }
        finally:
            cursor.close()

@app.get("/data")
@limiter.limit("30/minute")
async def get_data(
    request: Request,
    limit: int = Query(default=100, ge=1, le=10000, description="每頁筆數 (Max 10000)"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    columns: Optional[str] = Query(default=None, description="指定欄位 (逗號分隔)")
):
    """取得資料列表 (支援分頁)"""
    start_time = time.time()
    
    # 強制限制 limit 上限，防止大量數據請求
    limit = min(limit, 10000)
    
    if columns:
        valid_columns = set(['id'] + [chr(ord('a') + i) for i in range(26)])
        requested_columns = [c.strip().lower() for c in columns.split(',')]
        for col in requested_columns:
            if col not in valid_columns:
                raise HTTPException(status_code=400, detail=f"無效的欄位名稱: {col}")
        select_columns = ', '.join(requested_columns)
    else:
        select_columns = '*'
    
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # 使用參數化查詢，這裡的 limit 和 offset 已經由 FastAPI 驗證為 int
            query = f"SELECT {select_columns} FROM data_100k ORDER BY id LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()
            elapsed = time.time() - start_time
            return {
                "data": rows,
                "count": len(rows),
                "limit": limit,
                "offset": offset,
                "query_time_ms": round(elapsed * 1000, 2),
                "connection_pool": USE_CONNECTION_POOL
            }
        finally:
            cursor.close()

@app.get("/data/all")
@limiter.limit("5/minute")
async def get_all_data(request: Request):
    """
    一次取得全部資料 (高負載端點，嚴格限流)
    """
    start_time = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT * FROM data_100k ORDER BY id")
            rows = cursor.fetchall()
            elapsed = time.time() - start_time
            return {
                "data": rows,
                "count": len(rows),
                "query_time_ms": round(elapsed * 1000, 2),
                "connection_pool": USE_CONNECTION_POOL
            }
        finally:
            cursor.close()

@app.get("/data/search")
@limiter.limit("30/minute")
async def search_data(
    request: Request,
    column: str = Query(..., description="搜尋欄位 (a-z)"),
    min_value: Optional[int] = Query(default=None),
    max_value: Optional[int] = Query(default=None),
    exact_value: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=10000)
):
    """搜尋資料"""
    start_time = time.time()
    
    valid_columns = set([chr(ord('a') + i) for i in range(26)])
    column = column.strip().lower()
    
    if column not in valid_columns:
        raise HTTPException(status_code=400, detail=f"無效的欄位名稱: {column}")
    
    conditions = []
    params = []
    
    if exact_value is not None:
        conditions.append(f"{column} = %s")
        params.append(exact_value)
    else:
        if min_value is not None:
            conditions.append(f"{column} >= %s")
            params.append(min_value)
        if max_value is not None:
            conditions.append(f"{column} <= %s")
            params.append(max_value)
    
    if not conditions:
        raise HTTPException(status_code=400, detail="請提供搜尋條件")
    
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            where_clause = ' AND '.join(conditions)
            # 欄位名稱經過白名單驗證，是安全的
            query = f"SELECT * FROM data_100k WHERE {where_clause} ORDER BY id LIMIT %s"
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            elapsed = time.time() - start_time
            return {
                "data": rows,
                "count": len(rows),
                "search_column": column,
                "query_time_ms": round(elapsed * 1000, 2),
                "connection_pool": USE_CONNECTION_POOL
            }
        finally:
            cursor.close()

@app.get("/data/{id}")
@limiter.limit("60/minute")
async def get_data_by_id(request: Request, id: int):
    """取得單筆資料"""
    start_time = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT * FROM data_100k WHERE id = %s", (id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"找不到 id={id} 的資料")
            elapsed = time.time() - start_time
            return {
                "data": row,
                "query_time_ms": round(elapsed * 1000, 2),
                "connection_pool": USE_CONNECTION_POOL
            }
        finally:
            cursor.close()

if __name__ == "__main__":
    import uvicorn
    # 使用環境變數控制 reload
    reload = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)
