# 1. 修正 Import (補上 session)
import os, subprocess, psutil, sys
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session # 這裡補上了 session
from dotenv import load_dotenv
# 2. 讀取環境變數
load_dotenv()

# 3. 工具函式
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 4. 統一設定路徑 (整合 BASE_DIR)
# 使用 __file__ 可以精確定位目前 py 檔的位置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "user_messages.txt")

# 5. 初始化 APP (只留這一個)
app = Flask(__name__, 
            static_folder=get_resource_path('static'),
            template_folder=get_resource_path('templates'))

# 6. 設定安全金鑰與密碼
app.secret_key = os.getenv("FLASK_SECRET_KEY")
ADMIN_PASSWORD = os.getenv("LOGIN_PASSWORD")

# 7. MAA 路徑配置 (使用上面定義好的 BASE_DIR)
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
# 【權限驗證裝飾器】
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# 【路由控制區】—— 請刪除所有重複的路由
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="密碼錯誤")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

# --- 受保護的路由 (務必加上 @login_required) ---

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/get_status")
@login_required
def get_status():
    status = "運行中" if check_maa_status() else "未啟動"
    return status

@app.route("/start_maa")
@login_required  # 這裡也要鎖起來
def start_maa():
    # ... 原有邏輯 ...
    return redirect(url_for('index'))

@app.route("/stop_maa")
@login_required
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
@login_required
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
@login_required
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
@login_required
def clear_logs():
    """ 清空日誌檔案內容 """
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] --- 日誌已清空 ---\n")
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

@app.route("/api/get-history", methods=["GET"])
@login_required
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
@login_required
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
print(f"DEBUG: 密碼已讀取 -> {ADMIN_PASSWORD}")
print(f"DEBUG: 密鑰已讀取 -> {app.secret_key}")

if __name__ == "__main__":
    # 自動偵測是否為 EXE 模式，若是則關閉 Debug
    is_exe = getattr(sys, 'frozen', False)
    
    if not os.path.exists(MAA_FULL_PATH):
        print(f"❗ 警告: 找不到 MAA 執行檔: {MAA_FULL_PATH}")
    
    # 啟動伺服器
    app.run(port=8000, debug=not is_exe)