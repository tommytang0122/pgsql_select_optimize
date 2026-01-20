# 虛擬列表 (Virtual List) 實作說明

## 概述

虛擬列表是一種優化大量數據渲染的技術。當需要顯示 10 萬筆數據時，傳統方式會創建 10 萬個 DOM 節點，這會導致：
- 瀏覽器卡頓或崩潰
- 記憶體使用過高
- 滾動不流暢

虛擬列表的解決方案是：**只渲染可視區域內的行**。

## 核心原理

```
┌─────────────────────────────────────┐
│          不可見區域 (上方)            │  ← 不渲染
├─────────────────────────────────────┤
│ ░░░░░░░░░ 緩衝區 (Buffer) ░░░░░░░░░░ │  ← 渲染 (防止滾動時閃爍)
├─────────────────────────────────────┤
│                                     │
│          可視區域 (Viewport)         │  ← 渲染
│                                     │
├─────────────────────────────────────┤
│ ░░░░░░░░░ 緩衝區 (Buffer) ░░░░░░░░░░ │  ← 渲染
├─────────────────────────────────────┤
│          不可見區域 (下方)            │  ← 不渲染
└─────────────────────────────────────┘
```

## 實作細節

### 1. 關鍵配置

```javascript
const ROW_HEIGHT = 40;      // 每行固定高度 (px)
const BUFFER_SIZE = 10;     // 緩衝區行數
```

- **ROW_HEIGHT**: 每行必須有固定高度，這樣才能精確計算滾動位置
- **BUFFER_SIZE**: 上下各多渲染 10 行，防止快速滾動時出現空白

### 2. 計算可視範圍

```javascript
function getVisibleRange() {
    const container = tableContainer;
    const scrollTop = container.scrollTop;        // 滾動距離
    const containerHeight = container.clientHeight; // 容器高度
    
    // 計算起始行 = 滾動距離 / 行高 - 緩衝區
    const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - BUFFER_SIZE);
    
    // 計算結束行 = (滾動距離 + 容器高度) / 行高 + 緩衝區
    const end = Math.min(
        allData.length - 1,
        Math.ceil((scrollTop + containerHeight) / ROW_HEIGHT) + BUFFER_SIZE
    );
    
    return { start, end };
}
```

**計算範例：**
- 假設容器高度 = 600px，行高 = 40px
- 可見行數 = 600 / 40 = 15 行
- 加上緩衝區 = 15 + 10 + 10 = 35 行
- **只需渲染 35 行，而非 100,000 行！**

### 3. 創建虛擬滾動空間

```javascript
function initVirtualList() {
    // 設置總高度 = 總行數 × 行高
    virtualList.totalHeight = allData.length * ROW_HEIGHT;
    tableBody.style.height = `${virtualList.totalHeight}px`;
    tableBody.style.position = 'relative';
}
```

- tbody 設置總高度 (100,000 × 40px = 4,000,000px)
- 這讓滾動條能正確顯示整體數據的比例
- 實際上只有可視區域的行被渲染

### 4. 使用絕對定位放置行

```javascript
function createRow(row, index) {
    const tr = document.createElement('tr');
    tr.className = 'virtual-row';
    tr.style.position = 'absolute';
    tr.style.top = `${index * ROW_HEIGHT}px`;  // 根據索引計算位置
    tr.style.height = `${ROW_HEIGHT}px`;
    // ...
    return tr;
}
```

- 每行使用 `position: absolute`
- 透過 `top` 屬性精確定位
- 這樣可以只渲染需要的行，而不影響其他行的位置

### 5. 滾動事件優化

```javascript
let scrollRAF = null;
function onScroll() {
    if (scrollRAF) {
        cancelAnimationFrame(scrollRAF);
    }
    scrollRAF = requestAnimationFrame(() => {
        renderVisibleRows();
    });
}
```

- 使用 `requestAnimationFrame` 節流
- 防止滾動時過度觸發渲染
- 確保每幀最多只渲染一次

### 6. 渲染可視行

```javascript
function renderVisibleRows() {
    const { start, end } = getVisibleRange();
    
    // 範圍沒變化就不重新渲染
    if (start === virtualList.visibleStart && end === virtualList.visibleEnd) {
        return;
    }
    
    // 更新範圍
    virtualList.visibleStart = start;
    virtualList.visibleEnd = end;
    
    // 清空並重新渲染
    tableBody.innerHTML = '';
    const fragment = document.createDocumentFragment();
    
    for (let i = start; i <= end; i++) {
        fragment.appendChild(createRow(allData[i], i));
    }
    
    tableBody.appendChild(fragment);
}
```

## CSS 關鍵樣式

```css
/* 容器需要設定 overflow: auto 產生滾動 */
.table-container {
    overflow: auto;
    position: relative;
}

/* tbody 使用 block 顯示並設定相對定位 */
tbody {
    display: block;
    position: relative;
}

/* 虛擬行使用絕對定位 */
.virtual-row {
    display: flex;
    position: absolute;
    width: 100%;
    height: 40px;  /* 固定高度 */
}

/* 固定左側欄位 */
td.sticky-col {
    position: sticky;
    left: 0;
}
```

## 性能比較

| 方式 | DOM 節點數 | 記憶體使用 | 初始渲染時間 |
|------|-----------|-----------|-------------|
| 傳統渲染 | ~2,700,000 | ~500MB+ | 10+ 秒 |
| 虛擬列表 | ~945 | ~10MB | < 0.1 秒 |

**計算：**
- 傳統：100,000 行 × 27 欄 = 2,700,000 個 TD 元素
- 虛擬：35 行 × 27 欄 = 945 個 TD 元素

## 檔案結構

```
static/
├── index.html   # HTML 結構
├── styles.css   # 虛擬列表專用樣式
└── app.js       # 虛擬列表核心邏輯
```

## 使用流程

1. 點擊「載入數據」按鈕
2. 從 API 分批載入 10 萬筆數據
3. 初始化虛擬列表 (設置總高度)
4. 只渲染可視區域的行
5. 滾動時動態更新渲染的行

## 注意事項

1. **固定行高**：虛擬列表要求每行高度固定，否則無法精確計算位置
2. **水平滾動**：ID 欄位使用 `position: sticky` 保持固定
3. **緩衝區大小**：可根據需求調整 `BUFFER_SIZE`，越大越平滑但耗費更多資源
4. **資料變更**：如果數據更新，需要重新調用 `initVirtualList()`

## 進階優化建議

1. **行重用 (Row Recycling)**：不清空 DOM，而是更新現有行的內容
2. **雙緩衝**：預先渲染下一頁數據
3. **懶載入**：滾動到底部時才載入更多數據
4. **Web Worker**：將數據處理移到背景執行
