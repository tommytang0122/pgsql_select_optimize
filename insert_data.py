#!/usr/bin/env python3
"""
快速寫入 10 萬筆數據到 data_100k 資料表
使用 psycopg2 的 execute_values 進行批次寫入
"""

import psycopg2
from psycopg2.extras import execute_values
import random
import time

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", 5433)),
    'database': os.getenv("DB_NAME", "testdb"),
    'user': os.getenv("DB_USER", "testuser"),
    'password': os.getenv("DB_PASSWORD", "testpass")
}

# 設定
TOTAL_ROWS = 100_000
BATCH_SIZE = 10_000  # 每批次寫入的筆數


def generate_row():
    """產生一列隨機數據 (a-z 共 26 個欄位)"""
    return tuple(random.randint(1, 1000) for _ in range(26))


def generate_batch(size):
    """產生一批隨機數據"""
    return [generate_row() for _ in range(size)]


def insert_data():
    """使用 execute_values 批次寫入數據"""
    
    # 建立連線
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 欄位名稱 (a-z)
    columns = ', '.join([chr(ord('a') + i) for i in range(26)])
    
    # SQL 語句
    insert_sql = f"INSERT INTO data_100k ({columns}) VALUES %s"
    
    print(f"開始寫入 {TOTAL_ROWS:,} 筆數據...")
    print(f"批次大小: {BATCH_SIZE:,} 筆")
    print("-" * 50)
    
    start_time = time.time()
    total_inserted = 0
    
    try:
        for batch_num in range(TOTAL_ROWS // BATCH_SIZE):
            # 產生批次數據
            batch_data = generate_batch(BATCH_SIZE)
            
            # 批次寫入
            execute_values(cursor, insert_sql, batch_data, page_size=BATCH_SIZE)
            conn.commit()
            
            total_inserted += BATCH_SIZE
            elapsed = time.time() - start_time
            rate = total_inserted / elapsed
            
            print(f"批次 {batch_num + 1}: 已寫入 {total_inserted:,} 筆 "
                  f"({elapsed:.2f}秒, {rate:,.0f} 筆/秒)")
        
        # 處理剩餘的數據
        remaining = TOTAL_ROWS % BATCH_SIZE
        if remaining > 0:
            batch_data = generate_batch(remaining)
            execute_values(cursor, insert_sql, batch_data, page_size=remaining)
            conn.commit()
            total_inserted += remaining
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("-" * 50)
        print(f"✅ 完成! 共寫入 {total_inserted:,} 筆數據")
        print(f"總耗時: {total_time:.2f} 秒")
        print(f"平均速度: {total_inserted / total_time:,.0f} 筆/秒")
        
        # 驗證數據筆數
        cursor.execute("SELECT COUNT(*) FROM data_100k")
        count = cursor.fetchone()[0]
        print(f"資料表目前共有: {count:,} 筆數據")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 錯誤: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    insert_data()
