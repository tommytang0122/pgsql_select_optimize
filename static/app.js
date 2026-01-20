/**
 * PostgreSQL 數據瀏覽器 - 虛擬列表實現
 * 支援切換：一次載入 / 分批載入 / 並行載入
 */

const API_BASE = 'http://localhost:8000';

// ============================================
// 可調整設定
// ============================================
const CONFIG = {
    USE_BATCH_LOADING: true,    // true=分批載入, false=一次載入
    USE_PARALLEL: false,        // true=並行請求 (分批模式時生效)
    BATCH_SIZE: 10000,          // 每批載入筆數 (100,000 / 10,000 = 10次)
    PARALLEL_LIMIT: 5,          // 並行請求數量上限
};

// 虛擬列表配置
const ROW_HEIGHT = 40;
const BUFFER_SIZE = 10;

// DOM 元素
const loadBtn = document.getElementById('loadBtn');
const loading = document.getElementById('loading');
const loadProgress = document.getElementById('loadProgress');
const tableContainer = document.getElementById('tableContainer');
const headerRow = document.getElementById('headerRow');
const tableBody = document.getElementById('tableBody');
const totalCountEl = document.getElementById('totalCount');
const queryTimeEl = document.getElementById('queryTime');
const footer = document.getElementById('footer');

// 欄位名稱 (a-z)
const columns = Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i));

// 儲存所有數據
let allData = [];
let isLoaded = false;

// 虛擬列表狀態
let virtualList = {
    totalHeight: 0,
    visibleStart: 0,
    visibleEnd: 0
};

// 初始化表頭
function initTableHeader() {
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.toUpperCase();
        headerRow.appendChild(th);
    });
}

// 格式化數字
function formatNumber(num) {
    return num.toLocaleString('zh-TW');
}

// 載入數據總數
async function loadCount() {
    try {
        const response = await fetch(`${API_BASE}/data/count`);
        const data = await response.json();
        totalCountEl.textContent = formatNumber(data.count);
        return data.count;
    } catch (error) {
        console.error('載入數據總數失敗:', error);
        totalCountEl.textContent = '錯誤';
        return 0;
    }
}

// 創建單行
function createRow(row, index) {
    const tr = document.createElement('tr');
    tr.className = 'virtual-row';
    tr.style.position = 'absolute';
    tr.style.top = `${index * ROW_HEIGHT}px`;
    tr.style.height = `${ROW_HEIGHT}px`;
    tr.style.width = '100%';
    
    const idTd = document.createElement('td');
    idTd.className = 'sticky-col';
    idTd.textContent = row.id;
    tr.appendChild(idTd);
    
    columns.forEach(col => {
        const td = document.createElement('td');
        td.textContent = row[col];
        tr.appendChild(td);
    });
    
    return tr;
}

// 計算可視範圍
function getVisibleRange() {
    const scrollTop = tableContainer.scrollTop;
    const containerHeight = tableContainer.clientHeight;
    
    const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - BUFFER_SIZE);
    const end = Math.min(
        allData.length - 1,
        Math.ceil((scrollTop + containerHeight) / ROW_HEIGHT) + BUFFER_SIZE
    );
    
    return { start, end };
}

// 渲染可視行
function renderVisibleRows() {
    if (!isLoaded || allData.length === 0) return;
    
    const { start, end } = getVisibleRange();
    
    if (start === virtualList.visibleStart && end === virtualList.visibleEnd) {
        return;
    }
    
    virtualList.visibleStart = start;
    virtualList.visibleEnd = end;
    
    tableBody.innerHTML = '';
    const fragment = document.createDocumentFragment();
    
    for (let i = start; i <= end; i++) {
        if (allData[i]) {
            fragment.appendChild(createRow(allData[i], i));
        }
    }
    
    tableBody.appendChild(fragment);
}

// 初始化虛擬列表
function initVirtualList() {
    virtualList.totalHeight = allData.length * ROW_HEIGHT;
    tableBody.style.height = `${virtualList.totalHeight}px`;
    tableBody.style.position = 'relative';
    
    tableContainer.addEventListener('scroll', onScroll);
    renderVisibleRows();
}

// 滾動事件
let scrollRAF = null;
function onScroll() {
    if (scrollRAF) cancelAnimationFrame(scrollRAF);
    scrollRAF = requestAnimationFrame(renderVisibleRows);
}

/**
 * 一次載入全部數據
 */
async function loadAllAtOnce() {
    const response = await fetch(`${API_BASE}/data/all`);
    return await response.json();
}

/**
 * 順序分批載入數據 (原始方式)
 */
async function loadInBatchesSequential(totalCount) {
    const totalBatches = Math.ceil(totalCount / CONFIG.BATCH_SIZE);
    let data = [];
    let totalQueryTime = 0;
    
    for (let batch = 0; batch < totalBatches; batch++) {
        const offset = batch * CONFIG.BATCH_SIZE;
        const response = await fetch(
            `${API_BASE}/data?limit=${CONFIG.BATCH_SIZE}&offset=${offset}`
        );
        const result = await response.json();
        
        data = data.concat(result.data);
        totalQueryTime += result.query_time_ms;
        
        const progress = Math.round(((batch + 1) / totalBatches) * 100);
        loadProgress.textContent = `${progress}%`;
    }
    
    return {
        data,
        query_time_ms: totalQueryTime,
        connection_pool: false,
        mode: 'sequential'
    };
}

/**
 * 並行分批載入數據 (使用 Promise.all)
 * 同時發送多個請求，大幅減少等待時間
 */
async function loadInBatchesParallel(totalCount) {
    const totalBatches = Math.ceil(totalCount / CONFIG.BATCH_SIZE);
    const batchGroups = [];
    
    // 將批次分組 (每組 PARALLEL_LIMIT 個並行請求)
    for (let i = 0; i < totalBatches; i += CONFIG.PARALLEL_LIMIT) {
        const group = [];
        for (let j = i; j < Math.min(i + CONFIG.PARALLEL_LIMIT, totalBatches); j++) {
            group.push(j);
        }
        batchGroups.push(group);
    }
    
    let allResults = [];
    let totalQueryTime = 0;
    let completedBatches = 0;
    
    // 逐組並行載入
    for (const group of batchGroups) {
        // 並行發送該組的所有請求
        const promises = group.map(batch => {
            const offset = batch * CONFIG.BATCH_SIZE;
            return fetch(`${API_BASE}/data?limit=${CONFIG.BATCH_SIZE}&offset=${offset}`)
                .then(res => res.json())
                .then(result => ({ batch, result }));
        });
        
        // 等待該組所有請求完成
        const groupResults = await Promise.all(promises);
        
        // 按順序合併結果
        groupResults
            .sort((a, b) => a.batch - b.batch)
            .forEach(({ result }) => {
                allResults = allResults.concat(result.data);
                totalQueryTime += result.query_time_ms;
            });
        
        completedBatches += group.length;
        const progress = Math.round((completedBatches / totalBatches) * 100);
        loadProgress.textContent = `${progress}% (並行)`;
    }
    
    return {
        data: allResults,
        query_time_ms: totalQueryTime,
        connection_pool: false,
        mode: 'parallel'
    };
}

/**
 * 分批載入 (根據設定選擇順序或並行)
 */
async function loadInBatches(totalCount) {
    if (CONFIG.USE_PARALLEL) {
        return await loadInBatchesParallel(totalCount);
    } else {
        return await loadInBatchesSequential(totalCount);
    }
}

/**
 * 主載入函數
 */
async function loadAllData() {
    const startTime = performance.now();
    
    // 顯示載入中
    loadBtn.disabled = true;
    loadBtn.innerHTML = '<span class="btn-icon">⏳</span> 載入中...';
    loading.classList.add('active');
    loadProgress.textContent = CONFIG.USE_BATCH_LOADING ? '0%' : '請稍候...';
    tableContainer.classList.remove('active');
    footer.classList.remove('active');
    
    // 重置
    tableBody.innerHTML = '';
    allData = [];
    isLoaded = false;
    
    try {
        let result;
        
        if (CONFIG.USE_BATCH_LOADING) {
            // 分批載入
            const totalCount = await loadCount();
            if (totalCount === 0) throw new Error('無法取得數據');
            result = await loadInBatches(totalCount);
        } else {
            // 一次載入
            result = await loadAllAtOnce();
        }
        
        allData = result.data;
        const queryTime = result.query_time_ms;
        const usePool = result.connection_pool;
        
        const endTime = performance.now();
        const totalTime = ((endTime - startTime) / 1000).toFixed(2);
        
        // 更新統計
        totalCountEl.textContent = formatNumber(allData.length);
        
        // 標記載入完成
        isLoaded = true;
        
        // 顯示表格
        loading.classList.remove('active');
        tableContainer.classList.add('active');
        footer.classList.add('active');
        
        // 初始化虛擬列表
        initVirtualList();
        
        // 確定載入模式描述
        let loadMode;
        if (!CONFIG.USE_BATCH_LOADING) {
            loadMode = '一次載入';
        } else if (CONFIG.USE_PARALLEL) {
            loadMode = `並行載入 (${CONFIG.PARALLEL_LIMIT}個並行)`;
        } else {
            loadMode = `順序載入 (${formatNumber(CONFIG.BATCH_SIZE)}筆/批)`;
        }
        
        queryTimeEl.textContent = 
            `✅ ${loadMode} 完成! 共 ${formatNumber(allData.length)} 筆 | ` +
            `後端: ${queryTime.toFixed(0)}ms | ` +
            `總耗時: ${totalTime}秒 | ` +
            `連線池: ${usePool ? '開' : '關'}`;
        
    } catch (error) {
        console.error('載入數據失敗:', error);
        loading.classList.remove('active');
        alert('載入數據失敗: ' + error.message);
    } finally {
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<span class="btn-icon">📊</span> 重新載入';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initTableHeader();
    loadCount();
    loadBtn.addEventListener('click', loadAllData);
    
    // 顯示目前設定
    console.log('=== 載入設定 ===');
    console.log(`載入模式: ${CONFIG.USE_BATCH_LOADING ? '分批載入' : '一次載入'}`);
    console.log(`並行請求: ${CONFIG.USE_PARALLEL ? '啟用' : '停用'}`);
    console.log(`並行數量: ${CONFIG.PARALLEL_LIMIT}`);
    console.log(`批次大小: ${CONFIG.BATCH_SIZE}`);
});
