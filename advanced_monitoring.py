# advanced_monitoring.py - 高度な監視と対策
import time
import random
import json
import hashlib
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import sqlite3
from threading import Lock
import requests
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import WebDriverException

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tiktok_bot_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DetectionEvent:
    """検出イベントの記録"""
    timestamp: datetime
    event_type: str  # 'captcha', 'block', 'suspicious', 'success'
    ip_address: str
    user_agent: str
    session_id: str
    details: str

class BotDetectionMonitor:
    """Bot検出の監視と対策システム"""
    
    def __init__(self, db_path="bot_detection.db"):
        self.db_path = db_path
        self.lock = Lock()
        self.setup_database()
        self.proxy_pool = ProxyManager()
        self.user_agent_pool = UserAgentPool()
        
    def setup_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detection_events (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    event_type TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    details TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_health (
                    session_id TEXT PRIMARY KEY,
                    last_success TEXT,
                    failure_count INTEGER DEFAULT 0,
                    risk_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                )
            """)

    def record_event(self, event: DetectionEvent):
        """イベントの記録"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO detection_events 
                    (timestamp, event_type, ip_address, user_agent, session_id, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.ip_address,
                    event.user_agent,
                    event.session_id,
                    event.details
                ))

    def calculate_risk_score(self, session_id: str) -> float:
        """セッションのリスクスコア計算"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT event_type, timestamp FROM detection_events 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (session_id, (datetime.now() - timedelta(hours=24)).isoformat()))
            
            events = cursor.fetchall()
            
        if not events:
            return 0.0
            
        risk_score = 0.0
        event_weights = {
            'captcha': 3.0,
            'block': 5.0,
            'suspicious': 1.5,
            'success': -0.5
        }
        
        for event_type, timestamp in events:
            # 時間による重み付け（新しいイベントほど重要）
            event_time = datetime.fromisoformat(timestamp)
            age_hours = (datetime.now() - event_time).total_seconds() / 3600
            time_weight = max(0.1, 1.0 - (age_hours / 24))
            
            risk_score += event_weights.get(event_type, 0) * time_weight
        
        return min(10.0, max(0.0, risk_score))

    def should_switch_strategy(self, session_id: str) -> bool:
        """戦略変更の必要性判定"""
        risk_score = self.calculate_risk_score(session_id)
        return risk_score > 5.0

class ProxyManager:
    """プロキシ管理システム"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.proxy_health = {}
        self.lock = Lock()
        self.load_proxy_list()
    
    def load_proxy_list(self):
        """プロキシリストの読み込み"""
        # 住宅用プロキシのリスト（例）
        proxy_configs = [
            {
                "host": "proxy1.example.com",
                "port": 8080,
                "username": "user1",
                "password": "pass1",
                "type": "residential"
            },
            {
                "host": "proxy2.example.com", 
                "port": 8080,
                "username": "user2",
                "password": "pass2",
                "type": "datacenter"
            }
        ]
        
        for config in proxy_configs:
            self.proxies.append(config)
            self.proxy_health[f"{config['host']}:{config['port']}"] = {
                "success_rate": 1.0,
                "last_used": None,
                "failures": 0
            }
    
    def get_best_proxy(self):
        """最適なプロキシを選択"""
        with self.lock:
            if not self.proxies:
                return None
            
            # 成功率でソート
            sorted_proxies = sorted(
                self.proxies,
                key=lambda p: self.proxy_health[f"{p['host']}:{p['port']}"]['success_rate'],
                reverse=True
            )
            
            # 住宅用プロキシを優先
            residential_proxies = [p for p in sorted_proxies if p['type'] == 'residential']
            
            if residential_proxies:
                return residential_proxies[0]
            else:
                return sorted_proxies[0] if sorted_proxies else None
    
    def report_proxy_result(self, proxy_config, success: bool):
        """プロキシの結果報告"""
        proxy_key = f"{proxy_config['host']}:{proxy_config['port']}"
        
        with self.lock:
            if proxy_key in self.proxy_health:
                health = self.proxy_health[proxy_key]
                
                if success:
                    health['failures'] = max(0, health['failures'] - 1)
                    health['success_rate'] = min(1.0, health['success_rate'] + 0.1)
                else:
                    health['failures'] += 1
                    health['success_rate'] = max(0.1, health['success_rate'] - 0.2)
                
                health['last_used'] = datetime.now()

class UserAgentPool:
    """User-Agent管理システム"""
    
    def __init__(self):
        self.user_agents = [
            # Windows Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebDriver/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Mac Chrome
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Linux Chrome
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        self.usage_count = {ua: 0 for ua in self.user_agents}
    
    def get_user_agent(self, strategy="least_used"):
        """User-Agentの取得"""
        if strategy == "random":
            return random.choice(self.user_agents)
        elif strategy == "least_used":
            # 最も使用頻度の低いものを選択
            min_usage = min(self.usage_count.values())
            candidates = [ua for ua, count in self.usage_count.items() if count == min_usage]
            selected = random.choice(candidates)
            self.usage_count[selected] += 1
            return selected
        else:
            return self.user_agents[0]

class AdaptiveDelayManager:
    """適応的遅延管理"""
    
    def __init__(self):
        self.base_delay = 2.0
        self.current_multiplier = 1.0
        self.success_count = 0
        self.failure_count = 0
        
    def get_delay(self) -> float:
        """現在の遅延時間を取得"""
        # 失敗が多い場合は遅延を増加
        if self.failure_count > 3:
            self.current_multiplier = min(5.0, self.current_multiplier * 1.5)
        elif self.success_count > 5:
            self.current_multiplier = max(0.5, self.current_multiplier * 0.9)
        
        base_time = self.base_delay * self.current_multiplier
        # ランダム要素を追加
        variation = random.uniform(0.5, 1.5)
        return base_time * variation
    
    def report_result(self, success: bool):
        """結果の報告"""
        if success:
            self.success_count += 1
            self.failure_count = max(0, self.failure_count - 1)
        else:
            self.failure_count += 1
            self.success_count = max(0, self.success_count - 1)

class EnhancedTikTokDriverV2:
    """さらに高度な機能を持つTikTokドライバー"""
    
    def __init__(self, session_id: str, headless=True):
        self.session_id = session_id
        self.headless = headless
        self.monitor = BotDetectionMonitor()
        self.delay_manager = AdaptiveDelayManager()
        self.current_proxy = None
        self.driver = None
        
    def setup_driver_with_proxy(self, proxy_config=None):
        """プロキシ付きドライバーの設定"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        
        # 既存の設定
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # プロキシ設定
        if proxy_config:
            proxy_auth = f"{proxy_config['username']}:{proxy_config['password']}"
            proxy_url = f"http://{proxy_auth}@{proxy_config['host']}:{proxy_config['port']}"
            options.add_argument(f"--proxy-server={proxy_url}")
            self.current_proxy = proxy_config
        
        # User-Agent設定
        user_agent = self.monitor.user_agent_pool.get_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        
        # 追加のランダム設定
        self.apply_random_browser_settings(options)
        
        if self.headless:
            options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.apply_stealth_techniques()
    
    def apply_random_browser_settings(self, options):
        """ランダムなブラウザ設定"""
        # ランダムなウィンドウサイズ
        window_sizes = [
            (1366, 768), (1920, 1080), (1440, 900),
            (1536, 864), (1280, 720), (1600, 900)
        ]
        width, height = random.choice(window_sizes)
        options.add_argument(f"--window-size={width},{height}")
        
        # ランダムな言語設定
        languages = [
            'ja-JP,ja,en-US,en',
            'en-US,en,ja-JP,ja',
            'ja,en-US,en'
        ]
        lang = random.choice(languages)
        options.add_experimental_option('prefs', {
            'intl.accept_languages': lang
        })
        
        # メモリ設定のランダム化
        memory_sizes = ['2048', '3072', '4096']
        options.add_argument(f"--max_old_space_size={random.choice(memory_sizes)}")
    
    def apply_stealth_techniques(self):
        """高度なステルス技術"""
        stealth_scripts = [
            # タイムゾーン偽装
            """
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                value: function() {
                    return {
                        timeZone: 'Asia/Tokyo',
                        locale: 'ja-JP'
                    };
                }
            });
            """,
            
            # Battery API 偽装
            """
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.85
                })
            });
            """,
            
            # Connection API 偽装
            """
            Object.defineProperty(navigator, 'connection', {
                value: {
                    effectiveType: '4g',
                    rtt: 100,
                    downlink: 10
                }
            });
            """,
            
            # Canvas fingerprint対策
            """
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                if (type === '2d') {
                    const context = getContext.call(this, type, attributes);
                    const originalFillText = context.fillText;
                    context.fillText = function(text, x, y, maxWidth) {
                        // ランダムなノイズを追加
                        const noise = Math.random() * 0.1;
                        return originalFillText.call(this, text, x + noise, y + noise, maxWidth);
                    };
                    return context;
                }
                return getContext.call(this, type, attributes);
            };
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_script(script)
            except Exception as e:
                logger.warning(f"ステルススクリプト実行失敗: {e}")
    
    def detect_bot_detection(self) -> bool:
        """Bot検出の有無をチェック"""
        indicators = [
            # Captcha関連
            "//div[contains(@class, 'captcha')]",
            "//iframe[contains(@src, 'captcha')]",
            "//*[contains(text(), 'verify') or contains(text(), '検証')]",
            
            # ブロック関連
            "//*[contains(text(), 'blocked') or contains(text(), 'ブロック')]",
            "//*[contains(text(), 'restricted') or contains(text(), '制限')]",
            "//*[contains(text(), 'unusual activity') or contains(text(), '異常な')]",
            
            # エラーページ
            "//h1[contains(text(), '403') or contains(text(), '429')]",
        ]
        
        for indicator in indicators:
            try:
                elements = self.driver.find_elements("xpath", indicator)
                if elements:
                    return True
            except Exception:
                continue
        
        return False
    
    def adaptive_action(self, action_type: str, **kwargs):
        """適応的アクション実行"""
        # 事前チェック
        if self.detect_bot_detection():
            self.handle_detection()
            return False
        
        try:
            # 適応的遅延
            delay = self.delay_manager.get_delay()
            time.sleep(delay)
            
            # アクション実行
            success = self.execute_action(action_type, **kwargs)
            
            # 結果記録
            self.delay_manager.report_result(success)
            
            if success:
                event = DetectionEvent(
                    timestamp=datetime.now(),
                    event_type='success',
                    ip_address=self.get_current_ip(),
                    user_agent=self.driver.execute_script("return navigator.userAgent;"),
                    session_id=self.session_id,
                    details=f"Action: {action_type}"
                )
                self.monitor.record_event(event)
            
            return success
            
        except Exception as e:
            logger.error(f"アクション実行エラー: {e}")
            self.delay_manager.report_result(False)
            return False
    
    def handle_detection(self):
        """検出時の対応"""
        detection_type = self.classify_detection()
        
        event = DetectionEvent(
            timestamp=datetime.now(),
            event_type=detection_type,
            ip_address=self.get_current_ip(),
            user_agent=self.driver.execute_script("return navigator.userAgent;"),
            session_id=self.session_id,
            details="Bot detection triggered"
        )
        self.monitor.record_event(event)
        
        # 対応策の実行
        if detection_type == 'captcha':
            self.handle_captcha()
        elif detection_type == 'block':
            self.handle_block()
        
        # リスクスコアチェック
        if self.monitor.should_switch_strategy(self.session_id):
            self.switch_strategy()
    
    def classify_detection(self) -> str:
        """検出タイプの分類"""
        page_text = self.driver.page_source.lower()
        
        if 'captcha' in page_text or 'verify' in page_text:
            return 'captcha'
        elif 'blocked' in page_text or '403' in page_text or '429' in page_text:
            return 'block'
        else:
            return 'suspicious'
    
    def handle_captcha(self):
        """Captcha対応"""
        logger.warning("Captcha検出 - 手動解決が必要です")
        if not self.headless:
            input("Captchaを解決してEnterを押してください...")
    
    def handle_block(self):
        """ブロック対応"""
        logger.warning("ブロック検出 - 戦略変更が必要です")
        self.switch_strategy()
    
    def switch_strategy(self):
        """戦略変更"""
        logger.info("戦略変更を実行")
        
        # 新しいプロキシに変更
        new_proxy = self.monitor.proxy_pool.get_best_proxy()
        if new_proxy and new_proxy != self.current_proxy:
            logger.info("プロキシ変更")
            self.driver.quit()
            self.setup_driver_with_proxy(new_proxy)
        
        # より長い待機時間
        self.delay_manager.current_multiplier *= 2.0
        
        # セッション一時停止
        time.sleep(random.uniform(300, 600))  # 5-10分待機
    
    def get_current_ip(self) -> str:
        """現在のIPアドレス取得"""
        try:
            response = requests.get("https://httpbin.org/ip", timeout=5)
            return response.json().get('origin', 'unknown')
        except:
            return 'unknown'
    
    def execute_action(self, action_type: str, **kwargs) -> bool:
        """具体的なアクション実行"""
        if action_type == 'navigate':
            url = kwargs.get('url')
            self.driver.get(url)
            return True
        elif action_type == 'click':
            element = kwargs.get('element')
            element.click()
            return True
        # 他のアクションタイプ...
        
        return False

# 使用例とテスト関数
def run_monitoring_test():
    """監視システムのテスト"""
    monitor = BotDetectionMonitor()
    
    # テストイベントの作成
    test_events = [
        DetectionEvent(
            timestamp=datetime.now(),
            event_type='success',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0...',
            session_id='test_session_1',
            details='Normal operation'
        ),
        DetectionEvent(
            timestamp=datetime.now(),
            event_type='captcha',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0...',
            session_id='test_session_1',
            details='Captcha appeared'
        )
    ]
    
    # イベント記録
    for event in test_events:
        monitor.record_event(event)
    
    # リスクスコア計算
    risk_score = monitor.calculate_risk_score('test_session_1')
    logger.info(f"リスクスコア: {risk_score}")
    
    # 戦略変更の必要性
    should_switch = monitor.should_switch_strategy('test_session_1')
    logger.info(f"戦略変更が必要: {should_switch}")

if __name__ == "__main__":
    run_monitoring_test()
