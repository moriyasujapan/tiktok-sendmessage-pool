# TikTok Bot Detection Bypass - 完全実装ガイド

## 概要

このガイドでは、TikTokのBot検出を回避するための包括的な解決策を段階的に実装する方法を説明します。

## 📁 プロジェクト構造

```
tiktok-sendmessage-pool/
├── enhanced_tiktok_driver.py     # 基本ドライバー
├── advanced_monitoring.py       # 高度な監視システム
├── api_server.py                # APIサーバー（拡張版）
├── requirements.txt             # Python依存関係
├── Dockerfile                   # Docker設定
├── docker-compose.yml           # Docker Compose設定
├── .env                         # 環境変数
├── profiles/                    # ブラウザプロファイル
├── sessions/                    # セッション情報
└── logs/                        # ログファイル
```

## 🚀 段階的実装手順

### Phase 1: 基本的なBot検出回避

1. **既存のSeleniumコードを置き換え**
   ```python
   # 従来のコード
   from selenium import webdriver
   driver = webdriver.Chrome()
   
   # 新しいコード
   from enhanced_tiktok_driver import EnhancedTikTokDriver
   driver = EnhancedTikTokDriver(headless=False)
   ```

2. **基本設定の適用**
   - User-Agentの最適化
   - ブラウザ指紋の改善
   - 適切な遅延時間の設定

### Phase 2: 高度な監視システムの導入

1. **監視システムの初期化**
   ```python
   from advanced_monitoring import BotDetectionMonitor
   monitor = BotDetectionMonitor()
   ```

2. **イベント記録の実装**
   ```python
   # 成功時
   monitor.record_event(DetectionEvent(
       timestamp=datetime.now(),
       event_type='success',
       ip_address=get_current_ip(),
       user_agent=driver.user_agent,
       session_id=session_id,
       details='Login successful'
   ))
   
   # 検出時
   monitor.record_event(DetectionEvent(
       timestamp=datetime.now(),
       event_type='captcha',
       ip_address=get_current_ip(),
       user_agent=driver.user_agent,
       session_id=session_id,
       details='Captcha detected'
   ))
   ```

### Phase 3: プロキシとローテーション

1. **プロキシ設定**
   ```python
   proxy_config = {
       "host": "your-proxy-host.com",
       "port": 8080,
       "username": "your_username",
       "password": "your_password",
       "type": "residential"  # 住宅用プロキシ推奨
   }
   ```

2. **プロキシローテーションの実装**
   ```python
   from advanced_monitoring import ProxyManager
   proxy_manager = ProxyManager()
   best_proxy = proxy_manager.get_best_proxy()
   ```

### Phase 4: 適応的システムの構築

1. **適応的遅延の実装**
   ```python
   from advanced_monitoring import AdaptiveDelayManager
   delay_manager = AdaptiveDelayManager()
   
   # 各アクション前に
   delay = delay_manager.get_delay()
   time.sleep(delay)
   ```

2. **リスクベースの戦略変更**
   ```python
   risk_score = monitor.calculate_risk_score(session_id)
   if risk_score > 5.0:
       switch_strategy()
   ```

## 🔧 環境設定

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成：
```env
# TikTok認証情報
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password

# プロキシ設定（オプション）
PROXY_HOST=your-proxy-host.com
PROXY_PORT=8080
PROXY_USERNAME=proxy_user
PROXY_PASSWORD=proxy_pass

# 動作設定
HEADLESS_MODE=true
MAX_CONNECTIONS=5
SESSION_TIMEOUT=3600
LOG_LEVEL=INFO
```

### 3. Docker環境での実行

```bash
# イメージビルド
docker-compose build

# サービス開始
docker-compose up -d

# ログ確認
docker-compose logs -f tiktok-api
```

## 📊 監視とメンテナンス

### 1. リアルタイム監視

```python
# ダッシュボード用のエンドポイント
@app.route('/dashboard')
def dashboard():
    with sqlite3.connect('bot_detection.db') as conn:
        # 過去24時間の統計
        stats = conn.execute("""
            SELECT event_type, COUNT(*) as count
            FROM detection_events 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY event_type
        """).fetchall()
    
    return jsonify(dict(stats))
```

### 2. アラートシステム

```python
def check_alerts():
    monitor = BotDetectionMonitor()
    
    # 高リスクセッションの検出
    high_risk_sessions = []
    for session_id in get_active_sessions():
        risk_score = monitor.calculate_risk_score(session_id)
        if risk_score > 7.0:
            high_risk_sessions.append({
                'session_id': session_id,
                'risk_score': risk_score
            })
    
    if high_risk_sessions:
        send_alert(f"高リスクセッション検出: {len(high_risk_sessions)}個")
```

### 3. 自動回復機能

```python
def auto_recovery():
    """自動回復処理"""
    monitor = BotDetectionMonitor()
    
    for session_id in get_failed_sessions():
        # セッションの再初期化
        recreate_session(session_id)
        
        # 新しいプロキシで再試行
        retry_with_new_proxy(session_id)
        
        # 成功したら正常状態に戻す
        mark_session_healthy(session_id)
```

## 🛡️ セキュリティとベストプラクティス

### 1. IPローテーション戦略

```python
class IPRotationStrategy:
    def __init__(self):
        self.residential_proxies = load_residential_proxies()
        self.datacenter_proxies = load_datacenter_proxies()
        self.current_ip_usage = {}
    
    def get_next_ip(self, session_id):
        # 住宅用プロキシを優先
        if self.residential_proxies:
            return self.select_residential_proxy()
        else:
            return self.select_datacenter_proxy()
