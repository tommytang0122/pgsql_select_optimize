# PostgreSQL Data Browser

A high-performance web application for browsing 100,000 database records with virtual scrolling technology.

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?logo=javascript&logoColor=black)

## Overview

This project demonstrates how to efficiently display large datasets (100K+ rows) in a web browser using **Virtual List (Virtual Scrolling)** technology. Instead of rendering all 100,000 rows at once (which would crash the browser), we only render the rows visible in the viewport.

### Key Features

- 🚀 **Virtual Scrolling** - Only renders ~35 visible rows instead of 100,000
- ⚡ **Fast Data Loading** - Batch loading with progress indicator
- 🎨 **Modern Dark Theme** - Beautiful UI with gradient accents
- 📊 **Real-time Statistics** - Query time and row count display
- 🔄 **Smooth Scrolling** - Uses `requestAnimationFrame` for optimal performance

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
├── virtual_list_implement.md    # Virtual list documentation (Chinese)
├── README.md                    # This file
├── venv/                        # Python virtual environment
└── static/
    ├── index.html               # Frontend HTML
    ├── styles.css               # CSS with dark theme
    └── app.js                   # Virtual list implementation
```

## Prerequisites

- **Docker** - For running PostgreSQL
- **Python 3.10+** - For FastAPI backend
- **Modern Web Browser** - Chrome, Firefox, Edge, or Safari

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
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
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

### 4. Populate Database with 100K Records

```bash
python insert_data.py
```

Expected output:
```
Starting to insert 100,000 records...
Batch size: 10,000 records
--------------------------------------------------
Batch 1: Inserted 10,000 records (0.27s, 37,130 records/sec)
...
Batch 10: Inserted 100,000 records (2.46s, 40,617 records/sec)
--------------------------------------------------
✅ Complete! Total: 100,000 records
Total time: 2.46 seconds
Average speed: 40,616 records/sec
```

### 5. Start the Server

```bash
python main.py
```

### 6. Open in Browser

Navigate to: **http://localhost:8000**

Click the **"載入數據" (Load Data)** button to load and display all 100,000 records.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend HTML |
| `/data/count` | GET | Get total record count |
| `/data` | GET | Get records with pagination |
| `/data/{id}` | GET | Get single record by ID |
| `/data/search` | GET | Search records by column value |

### Query Parameters for `/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Number of records (1-10000) |
| `offset` | int | 0 | Starting offset |
| `columns` | string | null | Comma-separated column names |

**Example:**
```bash
curl "http://localhost:8000/data?limit=10&offset=0&columns=id,a,b,c"
```

## Virtual List Implementation

The virtual list dramatically improves performance by only rendering visible rows.

### Performance Comparison

| Method | DOM Nodes | Memory | Initial Render |
|--------|-----------|--------|----------------|
| Traditional | ~2,700,000 | 500MB+ | 10+ seconds |
| Virtual List | ~945 | ~10MB | < 0.1 seconds |

### How It Works

1. **Fixed Row Height** - Each row is exactly 40px
2. **Scroll Position Calculation** - Determine which rows are visible
3. **Absolute Positioning** - Position rows using `top` CSS property
4. **Buffer Zone** - Render 10 extra rows above/below for smooth scrolling
5. **RequestAnimationFrame** - Throttle scroll events for performance

For detailed implementation, see [virtual_list_implement.md](./virtual_list_implement.md).

## Database Configuration

| Setting | Value |
|---------|-------|
| Host | localhost |
| Port | 5433 |
| Database | testdb |
| User | testuser |
| Password | testpass |
| Container | postgres-docker |

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **psycopg2** - PostgreSQL database adapter
- **Uvicorn** - ASGI server

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **CSS3** - Modern styling with CSS variables
- **Virtual Scrolling** - Custom implementation

### Database
- **PostgreSQL 16** - Running in Docker container

## Performance Tips

1. **Batch Data Loading** - Load data in 10,000 record batches
2. **Virtual Scrolling** - Only render visible rows
3. **DocumentFragment** - Batch DOM insertions
4. **RequestAnimationFrame** - Smooth scroll updates
5. **Sticky Positioning** - Keep header and ID column visible

## Troubleshooting

### Cannot connect to PostgreSQL
```bash
# Check if container is running
docker ps | grep postgres-docker

# Start container if stopped
docker start postgres-docker
```

### Port 5433 already in use
```bash
# Find process using port
lsof -i :5433

# Or use a different port in docker run command
docker run ... -p 5434:5432 ...
```

### Module not found errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install fastapi uvicorn psycopg2-binary
```

## License

MIT License

## Author

Created for demonstrating high-performance data visualization with PostgreSQL and virtual scrolling technology.