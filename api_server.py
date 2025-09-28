# api_server.py - 既存のAPIサーバーを拡張
import os
import json
import time
import threading
from flask import Flask, request, jsonify
from enhanced_tiktok_driver import EnhancedTikTokDriver

app = Flask(__name__)

class TikTokConnectionPool:
    def __init__(self):
        self.connections = {}
        self.drivers = {}
        self.lock = threading.Lock()
    
    def create_connection(self, unique_id):
        """接続作成（拡張版）"""
        with self.lock:
            if unique_id in self.connections:
                return {"status": "already_connected"}
            
            try:
                # 拡張ドライバーの使用
                driver = EnhancedTikTokDriver(
                    headless=True,
                    user_data_dir=f"./profiles/{unique_id}"
                )
                
                # セッション復元または新規ログイン
                session_restored = driver.load_session(f"./sessions/{unique_id}_session.json")
                
                if not session_restored:
                    # 環境変数から認証情報取得
                    username = os.getenv('TIKTOK_USERNAME')
                    password = os.getenv('TIKTOK_PASSWORD')
                    
                    if not username or not password:
                        return {"status": "error", "message": "認証情報が設定されていません"}
                    
                    # 安全なナビゲーションとログイン
                    if driver.safe_navigate_to_tiktok():
                        if driver.enhanced_login(username, password):
                            # セッション保存
                            os.makedirs("./sessions", exist_ok=True)
                            driver.save_session(f"./sessions/{unique_id}_session.json")
                        else:
                            driver.close()
                            return {"status": "error", "message": "ログインに失敗しました"}
                    else:
                        driver.close()
                        return {"status": "error", "message": "TikTokアクセスに失敗しました"}
                
                # セッション情報取得
                session_info = driver.get_session_info()
                
                # 接続情報保存
                self.drivers[unique_id] = driver
                self.connections[unique_id] = {
                    "status": "connected",
                    "session_info": session_info,
                    "created_at": time.time()
                }
                
                return {
                    "status": "connected",
                    "session_info": session_info
                }
                
            except Exception as e:
                return {"status": "error", "message": str(e)}
    
    def send_message(self, unique_id, message):
        """メッセージ送信（拡張版）"""
        with self.lock:
            if unique_id not in self.connections:
                return {"status": "error", "message": "接続が存在しません"}
            
            try:
                driver = self.drivers[unique_id]
                
                # 人間らしい行動パターンを追加
                driver.simulate_human_behavior()
                
                # 既存のメッセージ送信ロジック
                # （元のプロジェクトのsendMessage実装をここに統合）
                
                # セッション情報の更新
                session_info = driver.get_session_info()
                self.connections[unique_id]["session_info"] = session_info
                
                return {
                    "status": "sent",
                    "message": message,
                    "session_info": session_info
                }
                
            except Exception as e:
                return {"status": "error", "message": str(e)}
    
    def disconnect(self, unique_id):
        """接続切断"""
        with self.lock:
            if unique_id in self.drivers:
                self.drivers[unique_id].close()
                del self.drivers[unique_id]
            
            if unique_id in self.connections:
                del self.connections[unique_id]
            
            return {"status": "disconnected"}

# グローバル接続プール
connection_pool = TikTokConnectionPool()

@app.route('/connect', methods=['POST'])
def connect():
    """接続エンドポイント（拡張版）"""
    data = request.json
    unique_id = data.get('uniqueId')
    
    if not unique_id:
        return jsonify({"error": "uniqueId is required"}), 400
    
    result = connection_pool.create_connection(unique_id)
    
    if result["status"] == "error":
        return jsonify(result), 500
    
    return jsonify(result)

@app.route('/send', methods=['POST'])
def send():
    """送信エンドポイント（拡張版）"""
    data = request.json
    unique_id = data.get('uniqueId')
    message = data.get('message')
    
    if not unique_id or not message:
        return jsonify({"error": "uniqueId and message are required"}), 400
    
    result = connection_pool.send_message(unique_id, message)
    
    if result["status"] == "error":
        return jsonify(result), 500
    
    return jsonify(result)

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """切断エンドポイント"""
    data = request.json
    unique_id = data.get('uniqueId')
    
    if not unique_id:
        return jsonify({"error": "uniqueId is required"}), 400
    
    result = connection_pool.disconnect(unique_id)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック（拡張版）"""
    return jsonify({
        "status": "healthy",
        "active_connections": len(connection_pool.connections),
        "timestamp": time.time()
    })

@app.route('/status', methods=['GET'])
def status():
    """ステータス確認（新機能）"""
    with connection_pool.lock:
        connections_status = {}
        for unique_id, connection in connection_pool.connections.items():
            connections_status[unique_id] = {
                "status": connection["status"],
                "created_at": connection["created_at"],
                "session_valid": bool(connection["session_info"])
            }
    
    return jsonify({
        "connections": connections_status,
        "total_connections": len(connection_pool.connections)
    })

if __name__ == '__main__':
    # 必要なディレクトリ作成
    os.makedirs("./profiles", exist_ok=True)
    os.makedirs("./sessions", exist_ok=True)
    
    app.run(host='0.0.0.0', port=3000, debug=False)

# Dockerfile
dockerfile_content = '''
FROM python:3.9-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \\
    wget \\
    curl \\
    unzip \\
    gnupg \\
    xvfb \\
    && rm -rf /var/lib/apt/lists/*

# Google Chrome のインストール
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \\
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \\
    && apt-get update \\
    && apt-get install -y google-chrome-stable \\
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver のインストール
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1) \\
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \\
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \\
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \\
    && rm /tmp/chromedriver.zip \\
    && chmod +x /usr/local/bin/chromedriver

# Pythonの依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
WORKDIR /app
COPY . .

# ディレクトリ作成
RUN mkdir -p /app/profiles /app/sessions

# 実行
EXPOSE 3000
CMD ["python", "api_server.py"]
'''

# requirements.txt
requirements_content = '''
flask==2.3.3
selenium==4.15.0
requests==2.31.0
python-dotenv==1.0.0
'''

# docker-compose.yml
docker_compose_content = '''
version: '3.8'

services:
  tiktok-api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - TIKTOK_USERNAME=${TIKTOK_USERNAME}
      - TIKTOK_PASSWORD=${TIKTOK_PASSWORD}
      - DISPLAY=:99
    volumes:
      - ./profiles:/app/profiles
      - ./sessions:/app/sessions
      - /dev/shm:/dev/shm
    command: >
      sh -c "
        Xvfb :99 -screen 0 1024x768x24 &
        python api_server.py
      "
    restart: unless-stopped
    
  # オプション: Redis for session management
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
'''

# .env.example
env_example_content = '''
# TikTok認証情報
TIKTOK_USERNAME=your_username_here
TIKTOK_PASSWORD=your_password_here

# オプション設定
HEADLESS_MODE=true
MAX_CONNECTIONS=10
SESSION_TIMEOUT=3600
'''

print("=== Docker関連ファイル ===")
print("Dockerfile:", dockerfile_content)
print("\\nrequirements.txt:", requirements_content)
print("\\ndocker-compose.yml:", docker_compose_content)
print("\\n.env.example:", env_example_content)
