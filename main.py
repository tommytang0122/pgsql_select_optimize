#!/usr/bin/env python3
"""
FastAPI 後端 - 讀取 data_100k 資料表
支援連線池開關功能
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from typing import Optional
from contextlib import contextmanager
import time

# ============================================
# GZip 壓縮設定
# ============================================
USE_GZIP = False             # 開關：True=啟用 GZip, False=停用 (本地測試建議關閉)
GZIP_MIN_SIZE = 500          # 最小壓縮大小 (bytes)

app = FastAPI(
    title="PostgreSQL Data API",
    description="API for querying data_100k table",
    version="1.0.0"
)

# 啟用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 啟用 GZip 壓縮 (根據開關)
if USE_GZIP:
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_SIZE)
    print(f"✅ GZip 壓縮已啟用 (minimum_size={GZIP_MIN_SIZE})")
else:
    print("⚠️ GZip 壓縮已停用")

# 資料庫連線設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'testdb',
    'user': 'testuser',
    'password': 'testpass'
}

# ============================================
# 連線池設定
# ============================================
USE_CONNECTION_POOL = False  # 開關：True=使用連線池, False=不使用
POOL_MIN_CONN = 2           # 最小連線數
POOL_MAX_CONN = 10          # 最大連線數

# 連線池實例 (初始為 None)
connection_pool: Optional[pool.ThreadedConnectionPool] = None


def init_connection_pool():
    """初始化連線池"""
    global connection_pool
    if USE_CONNECTION_POOL and connection_pool is None:
        connection_pool = pool.ThreadedConnectionPool(
            POOL_MIN_CONN,
            POOL_MAX_CONN,
            **DB_CONFIG
        )
        print(f"✅ 連線池已啟用 (min={POOL_MIN_CONN}, max={POOL_MAX_CONN})")


def close_connection_pool():
    """關閉連線池"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        print("🔌 連線池已關閉")


@contextmanager
def get_db_connection():
    """
    取得資料庫連線 (Context Manager)
    根據 USE_CONNECTION_POOL 設定決定使用連線池或直接連線
    """
    conn = None
    try:
        if USE_CONNECTION_POOL and connection_pool:
            # 使用連線池
            conn = connection_pool.getconn()
        else:
            # 直接建立新連線
            conn = psycopg2.connect(**DB_CONFIG)
        
        yield conn
        
    finally:
        if conn:
            if USE_CONNECTION_POOL and connection_pool:
                # 歸還連線到池
                connection_pool.putconn(conn)
            else:
                # 關閉連線
                conn.close()


# ============================================
# 啟動/關閉事件
# ============================================
@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化連線池"""
    if USE_CONNECTION_POOL:
        init_connection_pool()
    else:
        print("⚠️ 連線池已停用，使用直接連線模式")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時清理連線池"""
    close_connection_pool()


# ============================================
# API 端點
# ============================================
@app.get("/")
async def root():
    """載入前端頁面"""
    return FileResponse("static/index.html")


# 掛載靜態檔案
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
async def get_count():
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
async def get_data(
    limit: int = Query(default=100, ge=1, le=100000, description="每頁筆數"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    columns: Optional[str] = Query(default=None, description="指定欄位 (逗號分隔, 例如: a,b,c)")
):
    """
    取得資料列表 (支援分頁)
    
    - **limit**: 每頁筆數 (1-100000)
    - **offset**: 偏移量
    - **columns**: 指定要回傳的欄位 (逗號分隔)
    """
    start_time = time.time()
    
    # 處理欄位選擇
    if columns:
        valid_columns = set(['id'] + [chr(ord('a') + i) for i in range(26)])
        requested_columns = [c.strip().lower() for c in columns.split(',')]
        
        for col in requested_columns:
            if col not in valid_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"無效的欄位名稱: {col}"
                )
        
        select_columns = ', '.join(requested_columns)
    else:
        select_columns = '*'
    
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
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
async def get_all_data():
    """
    一次取得全部資料 (優化版)
    適用於需要快速載入全部數據的場景
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
async def search_data(
    column: str = Query(..., description="搜尋欄位 (a-z)"),
    min_value: Optional[int] = Query(default=None, description="最小值"),
    max_value: Optional[int] = Query(default=None, description="最大值"),
    exact_value: Optional[int] = Query(default=None, description="精確值"),
    limit: int = Query(default=100, ge=1, le=10000, description="回傳筆數上限")
):
    """搜尋資料"""
    start_time = time.time()
    
    valid_columns = set([chr(ord('a') + i) for i in range(26)])
    column = column.strip().lower()
    
    if column not in valid_columns:
        raise HTTPException(
            status_code=400,
            detail=f"無效的欄位名稱: {column}"
        )
    
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
        raise HTTPException(
            status_code=400,
            detail="請提供搜尋條件 (min_value, max_value, 或 exact_value)"
        )
    
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            where_clause = ' AND '.join(conditions)
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
async def get_data_by_id(id: int):
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
