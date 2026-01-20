# 優化方案總覽 (Optimization Methods)

## 已實現的優化

### ✅ 1. 連線池 (Connection Pool)

**解決的瓶頸**: 每次請求都建立新的資料庫連線，耗費 20-50ms

**設定位置**: `main.py` 第 59 行
```python
USE_CONNECTION_POOL = False  # 目前: 關閉
```

**效果**: 減少 ~20ms/請求

---

### ✅ 2. GZip 壓縮

**解決的瓶頸**: JSON 傳輸資料量大

**設定位置**: `main.py` 第 22 行
```python
USE_GZIP = False  # 目前: 關閉 (本地測試，CPU 開銷大於網路節省)
```

**測試結果**:
- 傳輸大小減少 66%
- 但 localhost 環境下時間反而增加一倍 (壓縮 CPU 開銷)

**文件**: [gzip_implement.md](./gzip_implement.md)

---

### ✅ 3. 一次載入 / 分批載入

**設定位置**: `static/app.js` 第 12 行
```javascript
USE_BATCH_LOADING: true  // 目前: 分批載入
BATCH_SIZE: 10000        // 每批 10,000 筆 = 共 10 次請求
```

**效果**: 一次載入比分批快 ~25%，但分批可顯示進度

---

### ✅ 4. 並行請求 (Promise.all)

**解決的瓶頸**: 分批載入時順序請求

**設定位置**: `static/app.js` 第 13 行
```javascript
USE_PARALLEL: false       // 目前: 關閉 (順序請求)
PARALLEL_LIMIT: 5         // 並行數量上限
```

**效果**: 啟用時分批載入減少 50-60% 時間

**文件**: [parallel_requests_implement.md](./parallel_requests_implement.md)

---

### ✅ 5. 虛擬列表 (Virtual Scrolling)

**解決的瓶頸**: 渲染 10 萬個 DOM 節點導致瀏覽器卡頓

**原理**:
```
傳統: 100,000 行 × 27 欄 = 2,700,000 個 DOM 節點
虛擬: 35 行 × 27 欄 = 945 個 DOM 節點
```

**效果**: 記憶體減少 99%, 渲染從 10 秒降到 0.1 秒

**文件**: [virtual_list_implement.md](./virtual_list_implement.md)

---

## 尚未實現的優化

### ⏳ 6. Web Worker

**解決的瓶頸**: 數據處理阻塞 UI 主執行緒

**原理**: 將數據處理移到背景執行緒

**預期效果**: UI 保持流暢，不會卡頓

---

### ⏳ 7. 移除 ORDER BY

**現況**: `SELECT * FROM data_100k ORDER BY id`

**優化**: 如果不需要排序，可省略 ORDER BY

**預期效果**: 減少 10-20% 查詢時間

---

## 目前設定總覽

| 優化項目 | 設定 | 目前值 | 狀態 |
|---------|------|--------|------|
| GZip 壓縮 | `USE_GZIP` | `False` | ❌ 關閉 |
| 連線池 | `USE_CONNECTION_POOL` | `False` | ❌ 關閉 |
| 分批載入 | `USE_BATCH_LOADING` | `true` | ✅ 啟用 |
| 並行請求 | `USE_PARALLEL` | `false` | ❌ 關閉 |
| 虛擬列表 | - | 永遠啟用 | ✅ 啟用 |

## 速度預測

| 筆數 | 未優化 | 全部優化後 |
|------|--------|-----------|
| 10,000 | ~500ms | ~150ms |
| 100,000 | ~5s | ~1.5s |
| 1,000,000 | ~50s | ~15s |
