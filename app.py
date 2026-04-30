from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import subprocess
import psutil
from datetime import datetime
import sys
from dotenv import load_dotenv
# ==========================================
# 【核心路徑配置】支援 EXE 打包與本地開發
# ==========================================

# --- 這裡開始是修正後的內容 ---
load_dotenv()  # 讀取 .env 檔案中的變數

# 從環境變數取得設定
app.secret_key = os.getenv("FLASK_SECRET_KEY")
ADMIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
# --- 修正結束 ---

def get_resource_path(relative_path):
    """
    取得資源絕對路徑...
    """
def get_resource_path(relatload_dotenv()ive_path):
    """ 
    取得資源絕對路徑：
    1. 打包後：指向 PyInstaller 的臨時資料夾 (_MEIPASS)
    2. 開發時：指向當前專案資料夾
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 定義基礎目錄（這確保 user_messages.txt 與 my_bg.jpg 會存在 EXE 旁邊）
BASE_DIR = os.path.abspath(".")
LOG_FILE = os.path.join(BASE_DIR, "user_messages.txt")

# 初始化 Flask：唯讀資源（HTML/內建靜態檔）使用 get_resource_path
app = Flask(__name__, 
            static_folder=get_resource_path('static'),
            template_folder=get_resource_path('templates'))

# ==========================================
# 【MAA 軟體路徑配置】
# ==========================================
# 請根據你自己的電腦路徑修改
# 獲取目前程式碼所在的資料夾路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MAA_DIR = os.path.join(BASE_DIR, "MAA-v6.3.2-win-x64")
MAA_EXE_NAME = "MAA.exe"
MAA_FULL_PATH = os.path.join(MAA_DIR, MAA_EXE_NAME)
# ==========================================
# 【系統邏輯函式】
# ==========================================

def check_maa_status():
    """ 檢查 Windows 進程清單中是否有 MAA 在執行 """
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == MAA_EXE_NAME.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

# ==========================================
# 【路由控制區】
# ==========================================

@app.route("/")
def index():
    """ 渲染主控制面板 """
    return render_template("index.html")

@app.route("/get_status")
def get_status():
    """ API：回傳當前 MAA 狀態 """
    status = "運行中" if check_maa_status() else "未啟動"
    return status

@app.route("/start_maa")
def start_maa():
    """ 啟動 MAA (傳統連結跳轉用) """
    if not check_maa_status():
        try:
            subprocess.Popen(MAA_FULL_PATH, cwd=MAA_DIR, shell=True)
        except Exception as e:
            print(f"啟動錯誤: {e}")
    return redirect(url_for('index'))

@app.route("/stop_maa")
def stop_maa():
    """ 關閉 MAA 進程 """
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == MAA_EXE_NAME.lower():
                proc.kill()
        except:
            pass
    return redirect(url_for('index'))

@app.route("/upload", methods=["POST"])
def upload():
    """ 處理背景圖上傳：確保存在 EXE 旁邊的 static 資料夾 """
    if 'file' not in request.files:
        return "No file", 400
    file = request.files['file']
    
    # 確保 EXE 旁邊有一個 static 資料夾可以存圖片
    external_static = os.path.join(BASE_DIR, 'static')
    if not os.path.exists(external_static):
        os.makedirs(external_static)
        
    save_path = os.path.join(external_static, 'my_bg.jpg')
    file.save(save_path)
    return "OK", 200

# ==========================================
# 【JSON API 區】與前端 JavaScript 溝通
# ==========================================

@app.route("/api/process-data", methods=["POST"])
def process_data():
    """ 處理指令並記錄到 TXT """
    data = request.get_json()
    user_message = data.get('message', '')
    current_time = datetime.now().strftime("%H:%M:%S")

    # 寫入日誌檔 (使用 BASE_DIR 下的 LOG_FILE)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{current_time}] {user_message}\n")
    
    success = True
    reply = ""

    # 關鍵指令判定
    if user_message == "啟動一鍵長草":
        if not check_maa_status():
            try:
                subprocess.Popen(MAA_FULL_PATH, cwd=MAA_DIR, shell=True)
                reply = "🚀 MAA 已成功啟動，開始執行長草任務！"
            except Exception as e:
                reply = f"❌ 啟動失敗：{str(e)}"
                success = False
        else:
            reply = "💡 MAA 已經在運行中，請查看黑色日誌視窗。"
    else:
        reply = f"✅ 已記錄指令：{user_message}"

    return jsonify({"reply": reply, "success": success})

@app.route("/api/clear-logs", methods=["POST"])
def clear_logs():
    """ 清空日誌檔案內容 """
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] --- 日誌已清空 ---\n")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

@app.route("/api/get-history", methods=["GET"])
def get_history():
    """ 取得最近 5 筆紀錄供小視窗顯示 """
    if not os.path.exists(LOG_FILE):
        return jsonify({"history": []})
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()[-5:]]
            lines.reverse()
            return jsonify({"history": lines})
    except:
        return jsonify({"history": ["讀取失敗"]})

@app.route("/api/get-full-logs", methods=["GET"])
def get_full_logs():
    """ 取得最後 50 行日誌供黑色視窗顯示 """
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": "尚未產生日誌..."})
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            last_logs = "".join(f.readlines()[-50:])
            return jsonify({"logs": last_logs})
    except:
        return jsonify({"logs": "無法讀取日誌"})

# ==========================================
# 【啟動點】
# ==========================================

if __name__ == "__main__":
    # 自動偵測是否為 EXE 模式，若是則關閉 Debug
    is_exe = getattr(sys, 'frozen', False)
    
    if not os.path.exists(MAA_FULL_PATH):
        print(f"❗ 警告: 找不到 MAA 執行檔: {MAA_FULL_PATH}")
    
    # 啟動伺服器
    app.run(port=8000, debug=not is_exe)