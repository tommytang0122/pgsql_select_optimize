# PostgreSQL Data Browser

A high-performance web application for browsing 100,000 database records with virtual scrolling technology.

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?logo=javascript&logoColor=black)

## Overview

This project demonstrates how to efficiently display large datasets (100K+ rows) in a web browser using **Virtual List (Virtual Scrolling)** technology.

### Key Features

- 🚀 **Virtual Scrolling** - Only renders ~35 visible rows instead of 100,000
- ⚡ **Configurable Loading** - Batch/single load with optional parallel requests
- 🔧 **Toggleable Optimizations** - Connection pool, GZip, parallel requests
- 🎨 **Modern Dark Theme** - Beautiful UI with gradient accents
- 📊 **Real-time Statistics** - Query time and performance metrics

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│    FastAPI      │────▶│   PostgreSQL    │
│   (Virtual List)│     │    Backend      │     │    Database     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     HTML/CSS/JS              Python              Docker Container
```

## Project Structure

```
pgsql_select_optimize/
├── main.py                      # FastAPI backend server
├── insert_data.py               # Script to populate database
├── static/
│   ├── index.html               # Frontend HTML
│   ├── styles.css               # CSS with dark theme
│   └── app.js                   # Virtual list + loading logic
├── optimization.md              # All optimization methods
├── progress.md                  # Loading flow documentation
├── virtual_list_implement.md    # Virtual list details
├── gzip_implement.md            # GZip compression details
├── parallel_requests_implement.md # Parallel requests details
├── SECURITY.md                  # Security guide
├── time_optimization.md         # Benchmark results
└── README.md                    # This file
```

## Current Configuration

### Backend (main.py)

| Setting | Value | Description |
|---------|-------|-------------|
| `USE_GZIP` | `False` | GZip compression (off for localhost) |
| `USE_CONNECTION_POOL` | `False` | Database connection pool |

### Frontend (static/app.js)

| Setting | Value | Description |
|---------|-------|-------------|
| `USE_BATCH_LOADING` | `true` | Batch loading mode |
| `USE_PARALLEL` | `false` | Parallel requests |
| `BATCH_SIZE` | `10000` | Records per batch (10 batches) |
| `PARALLEL_LIMIT` | `5` | Max concurrent requests |

## Quick Start

### 1. Start PostgreSQL Docker Container

```bash
docker run -d \
  --name postgres-docker \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  -p 5433:5432 \
  postgres:16
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary
```

### 3. Create Database Table

```bash
PGPASSWORD=testpass psql -h localhost -p 5433 -U testuser -d testdb -c "
CREATE TABLE IF NOT EXISTS data_100k (
    id SERIAL PRIMARY KEY,
    a INTEGER, b INTEGER, c INTEGER, d INTEGER, e INTEGER,
    f INTEGER, g INTEGER, h INTEGER, i INTEGER, j INTEGER,
    k INTEGER, l INTEGER, m INTEGER, n INTEGER, o INTEGER,
    p INTEGER, q INTEGER, r INTEGER, s INTEGER, t INTEGER,
    u INTEGER, v INTEGER, w INTEGER, x INTEGER, y INTEGER,
    z INTEGER
);"
```

### 4. Populate Database

```bash
python insert_data.py
```

### 5. Start Server

```bash
python main.py
```

### 6. Open Browser

Navigate to: **http://localhost:8000**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend HTML |
| `/data/count` | GET | Get total record count |
| `/data` | GET | Get records (paginated) |
| `/data/all` | GET | Get all records at once |
| `/data/{id}` | GET | Get single record |
| `/api/pool/status` | GET | Connection pool status |

## Documentation

| File | Description |
|------|-------------|
| [optimization.md](./optimization.md) | All optimization methods overview |
| [progress.md](./progress.md) | Data loading flow |
| [virtual_list_implement.md](./virtual_list_implement.md) | Virtual scrolling details |
| [gzip_implement.md](./gzip_implement.md) | GZip compression |
| [parallel_requests_implement.md](./parallel_requests_implement.md) | Parallel requests |
| [time_optimization.md](./time_optimization.md) | Benchmark results |

## Performance

| Records | Load Time | DOM Nodes |
|---------|-----------|-----------|
| 100,000 | ~3-4 sec | ~945 |

## License

MIT License

---

# 中文版 (Chinese Version)

# PostgreSQL 數據瀏覽器

一個使用虛擬捲動技術瀏覽 10 萬筆資料庫記錄的高效能網頁應用程式。

## 概述

本專案展示如何使用**虛擬列表 (Virtual Scrolling)** 技術在網頁瀏覽器中高效顯示大量數據 (10萬+ 筆)。

### 主要特點

- 🚀 **虛擬捲動** - 只渲染約 35 個可見行，而非 100,000 行
- ⚡ **可配置載入** - 分批/單次載入，可選並行請求
- 🔧 **可開關優化** - 連線池、GZip、並行請求
- 🎨 **現代深色主題** - 漸層色調的美觀 UI
- 📊 **即時統計** - 查詢時間和效能指標

## 架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    前端         │────▶│    FastAPI      │────▶│   PostgreSQL    │
│   (虛擬列表)    │     │    後端         │     │    資料庫       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     HTML/CSS/JS              Python              Docker 容器
```

## 目前設定

### 後端 (main.py)

| 設定 | 值 | 說明 |
|------|------|------|
| `USE_GZIP` | `False` | GZip 壓縮 (本地關閉) |
| `USE_CONNECTION_POOL` | `False` | 資料庫連線池 |

### 前端 (static/app.js)

| 設定 | 值 | 說明 |
|------|------|------|
| `USE_BATCH_LOADING` | `true` | 分批載入模式 |
| `USE_PARALLEL` | `false` | 並行請求 |
| `BATCH_SIZE` | `10000` | 每批筆數 (共10批) |
| `PARALLEL_LIMIT` | `5` | 最大並行數 |

## 快速開始

### 1. 啟動 PostgreSQL Docker 容器

```bash
docker run -d \
  --name postgres-docker \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  -p 5433:5432 \
  postgres:16
```

### 2. 設置 Python 環境

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary
```

### 3. 建立資料表

```bash
PGPASSWORD=testpass psql -h localhost -p 5433 -U testuser -d testdb -c "
CREATE TABLE IF NOT EXISTS data_100k (
    id SERIAL PRIMARY KEY,
    a INTEGER, b INTEGER, c INTEGER, d INTEGER, e INTEGER,
    f INTEGER, g INTEGER, h INTEGER, i INTEGER, j INTEGER,
    k INTEGER, l INTEGER, m INTEGER, n INTEGER, o INTEGER,
    p INTEGER, q INTEGER, r INTEGER, s INTEGER, t INTEGER,
    u INTEGER, v INTEGER, w INTEGER, x INTEGER, y INTEGER,
    z INTEGER
);"
```

### 4. 寫入數據

```bash
python insert_data.py
```

### 5. 啟動伺服器

```bash
python main.py
```

### 6. 開啟瀏覽器

訪問: **http://localhost:8000**

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 載入前端頁面 |
| `/data/count` | GET | 取得總筆數 |
| `/data` | GET | 取得數據 (分頁) |
| `/data/all` | GET | 一次取得全部數據 |
| `/data/{id}` | GET | 取得單筆數據 |
| `/api/pool/status` | GET | 連線池狀態 |

## 文件說明

| 檔案 | 說明 |
|------|------|
| [optimization.md](./optimization.md) | 所有優化方案總覽 |
| [progress.md](./progress.md) | 數據載入流程 |
| [virtual_list_implement.md](./virtual_list_implement.md) | 虛擬列表實作細節 |
| [gzip_implement.md](./gzip_implement.md) | GZip 壓縮實作 |
| [parallel_requests_implement.md](./parallel_requests_implement.md) | 並行請求實作 |
| [time_optimization.md](./time_optimization.md) | 效能測試結果 |

## 效能

| 筆數 | 載入時間 | DOM 節點數 |
|------|---------|-----------|
| 100,000 | ~3-4 秒 | ~945 |

## 授權

MIT License