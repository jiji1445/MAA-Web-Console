# MAA 遠端控制面板 (Web Control Panel)

這是一個基於 **Flask** 框架開發的網頁控制介面，旨在遠端遙控電腦中的 **MAA (MaaAssistantArknights)** 執行自動化任務。本專案整合了後端邏輯控管、前端介面展示以及基本的安全性驗證。

## 🌟 核心功能
*   **一鍵啟動/停止**：透過網頁按鈕直接控制電腦端 MAA 腳本。
*   **權限驗證系統**：設有登入牆與 Session 機制，防止未經授權的操作。
*   **路徑自動化管理**：使用 Python `os` 庫動態定位專案路徑，解決環境遷移問題。
*   **安全環境變數**：密碼與金鑰儲存於 `.env`，不外流至版本控制系統。

## 🛠️ 技術棧
*   **Backend**: Python / Flask
*   **Frontend**: HTML5 / CSS3 / JavaScript
*   **Tools**: Git / GitHub / PyInstaller

## 🚀 快速開始

### 1. 準備環境
確保電腦已安裝 Python 3.x，並安裝必要套件：
```bash
\` \` \`pip install flask python-dotenv\` \` \`
### 2. 設定環境變數
在專案根目錄建立 .env 檔案，並填入以下資訊：

\` \` \`FLASK_SECRET_KEY=你的隨機密鑰
LOGIN_PASSWORD=你的自訂登入密碼\` \` \`
### 3. 執行程式
\` \` \`python app.py\` \` \`
打開瀏覽器訪問 http://127.0.0.1:8000 即可進入控制面板。

🔒 安全性說明
本專案使用 .gitignore 忽略了敏感檔案（.env, dist/）。

所有核心操作皆受到 @login_required 裝飾器保護。

🎓 開發心得 (結語)
這是我的第一個全端開發專案。從一開始解決路徑錯誤、整合前後端數據，到最後實作完整的登入/登出生命週期，我學會了如何建立一個具備安全性且能解決實際問題的軟體工具。
