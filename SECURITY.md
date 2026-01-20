# 安全性指南 (Security Guide)

本專案已實作多項安全措施以防範常見攻擊。

## 🛡️ 已實作的安全功能

### 1. 憑證保護 (Credentials Protection)
- **措施**: 所有敏感資訊 (資料庫密碼、連線資訊) 皆移至 `.env` 環境變數檔。
- **檔案**: `.env` (不應提交至 Git), `.env.example` (範本)

### 2. 速率限制 (Rate Limiting)
- **措施**: 使用 `slowapi` 限制 API 請求頻率，防止 DoS 攻擊。
- **限制**:
  - `/data/all`: 5 次/分鐘 (高負載)
  - `/data`: 30 次/分鐘
  - 其他: 60 次/分鐘

### 3. 請求大小限制 (Request Size Cap)
- **措施**: `/data` 端點的 `limit` 參數強制上限為 10,000 筆。
- **目的**: 防止惡意請求一次撈取過多數據導致 OOM。

### 4. CORS 強化 (CORS Hardening)
- **措施**: 預設僅允許 `localhost:8000`，並可透過 `CORS_ORIGINS` 環境變數設定信任網域。
- **目的**: 防止惡意網站跨域讀取數據。

### 5. Debug 模式保護
- **措施**: 生產環境預設關閉 Debug 模式，隱藏錯誤堆疊資訊。

### 6. SQL 注入防護
- **措施**: 全面使用參數化查詢 (Parameterized Queries)，並對欄位名稱進行白名單驗證。

---

## 🚀 如何設定

1. 複製範本檔案:
   ```bash
   cp .env.example .env
   ```

2. 編輯 `.env` 設定您的密碼與參數:
   ```ini
   DB_PASSWORD=your_secure_password
   DEBUG=false
   ```

3. 重新啟動伺服器:
   ```bash
   python main.py
   ```

---

## ⚠️ 已知風險與剩餘問題

雖然已加強安全性，但作為 Demo 專案仍有以下限制：
- 無身份驗證 (Authentication)
- 未使用 HTTPS (建議搭配 Nginx 反向代理使用 SSL)
