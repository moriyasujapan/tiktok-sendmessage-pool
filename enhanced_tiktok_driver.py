import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import requests

class EnhancedTikTokDriver:
    def __init__(self, headless=False, user_data_dir=None):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.setup_driver()
    
    def setup_driver(self):
        """高度なbot検出回避設定でChromeDriverを初期化"""
        options = Options()
        
        # 基本的なbot検出回避設定
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # より人間らしいUser-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # ウィンドウサイズとビューポートの設定
        window_sizes = [
            "--window-size=1366,768",
            "--window-size=1920,1080", 
            "--window-size=1440,900"
        ]
        options.add_argument(random.choice(window_sizes))
        
        # 言語とロケール設定
        options.add_argument("--lang=ja-JP")
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'ja-JP,ja,en-US,en'
        })
        
        # WebGL、Canvas、AudioContext対策
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # メモリとCPU使用量の最適化
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # ユーザーデータディレクトリの設定
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
        
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        
        # WebDriverの初期化
        self.driver = webdriver.Chrome(options=options)
        
        # WebDriverプロパティの隠蔽
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # さらなるbot検出回避のJavaScript実行
        self.execute_stealth_scripts()
        
        self.wait = WebDriverWait(self.driver, 30)
    
    def execute_stealth_scripts(self):
        """追加のステルス化スクリプト実行"""
        stealth_scripts = [
            # Webdriverプロパティの削除
            "delete navigator.__proto__.webdriver",
            
            # Chrome runtime の偽装
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            """,
            
            # Plugin情報の偽装
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """,
            
            # 言語設定の偽装
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en-US', 'en']
            });
            """,
            
            # Permission API の偽装
            """
            const originalQuery = window.navigator.permissions.query;
            return originalQuery(parameters).then((result) => {
                if (parameters.name === 'notifications') {
                    result.__defineGetter__('state', () => 'granted');
                }
                return result;
            });
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_script(script)
            except Exception as e:
                print(f"ステルススクリプト実行エラー: {e}")
    
    def human_like_delay(self, min_seconds=1, max_seconds=3):
        """人間らしい不規則な待機時間"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay
    
    def human_like_typing(self, element, text, typing_delay_range=(0.05, 0.15)):
        """人間らしいタイピング"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*typing_delay_range))
    
    def random_mouse_movement(self):
        """ランダムなマウス移動"""
        try:
            # ページ内のランダムな要素を取得
            elements = self.driver.find_elements(By.TAG_NAME, "div")[:10]
            if elements:
                random_element = random.choice(elements)
                actions = ActionChains(self.driver)
                actions.move_to_element(random_element).perform()
                self.human_like_delay(0.5, 1.5)
        except Exception:
            pass
    
    def simulate_human_behavior(self):
        """人間らしい行動のシミュレーション"""
        behaviors = [
            self.random_mouse_movement,
            lambda: self.driver.execute_script("window.scrollBy(0, Math.floor(Math.random() * 200));"),
            lambda: self.human_like_delay(2, 5),
            lambda: self.driver.execute_script("document.title;")  # DOM操作
        ]
        
        # ランダムに1-2個の行動を実行
        for _ in range(random.randint(1, 2)):
            random.choice(behaviors)()
    
    def safe_navigate_to_tiktok(self, max_retries=3):
        """安全なTikTokナビゲーション"""
        for attempt in range(max_retries):
            try:
                print(f"TikTokアクセス試行 {attempt + 1}/{max_retries}")
                
                # まず別のサイトにアクセス（リファラー対策）
                self.driver.get("https://www.google.com")
                self.human_like_delay(2, 4)
                
                # TikTokに移動
                self.driver.get("https://www.tiktok.com/")
                self.human_like_delay(3, 6)
                
                # ページロード確認
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # 人間らしい行動
                self.simulate_human_behavior()
                
                print("TikTokアクセス成功")
                return True
                
            except TimeoutException:
                print(f"試行 {attempt + 1} タイムアウト")
                if attempt < max_retries - 1:
                    self.human_like_delay(5, 10)
                    continue
                else:
                    return False
            except Exception as e:
                print(f"試行 {attempt + 1} エラー: {e}")
                if attempt < max_retries - 1:
                    self.human_like_delay(5, 10)
                    continue
                else:
                    return False
        
        return False
    
    def enhanced_login(self, username, password):
        """拡張ログイン機能"""
        try:
            print("ログインプロセス開始")
            
            # ログインボタンを探す
            login_selectors = [
                "button[data-e2e='top-login-button']",
                "a[data-e2e='top-login-button']",
                "//button[contains(text(), 'Log in')]",
                "//a[contains(text(), 'Log in')]"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    if selector.startswith("//"):
                        login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        login_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not login_button:
                print("ログインボタンが見つかりません")
                return False
            
            # 人間らしいクリック
            self.simulate_human_behavior()
            login_button.click()
            self.human_like_delay(2, 4)
            
            # ユーザー名入力
            username_selectors = [
                "input[name='username']",
                "input[placeholder*='Email']",
                "input[placeholder*='Phone']",
                "input[data-e2e='email-or-username']"
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not username_input:
                print("ユーザー名入力フィールドが見つかりません")
                return False
            
            # 人間らしいタイピング
            self.human_like_typing(username_input, username)
            self.human_like_delay(1, 2)
            
            # パスワード入力
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[data-e2e='password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_input:
                print("パスワード入力フィールドが見つかりません")
                return False
            
            # 人間らしいタイピング
            self.human_like_typing(password_input, password)
            self.human_like_delay(1, 3)
            
            # ログイン実行
            submit_selectors = [
                "button[data-e2e='login-button']",
                "button[type='submit']",
                "//button[contains(text(), 'Log in')]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                self.simulate_human_behavior()
                submit_button.click()
                self.human_like_delay(3, 6)
                
                # ログイン成功確認
                success_indicators = [
                    "//div[@data-e2e='nav-profile']",
                    "//button[@data-e2e='nav-profile']",
                    "[data-e2e='nav-profile']"
                ]
                
                for indicator in success_indicators:
                    try:
                        if indicator.startswith("//"):
                            self.wait.until(EC.presence_of_element_located((By.XPATH, indicator)))
                        else:
                            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, indicator)))
                        print("ログイン成功")
                        return True
                    except TimeoutException:
                        continue
                
                print("ログイン結果の確認ができませんでした")
                return False
            else:
                print("ログインボタンが見つかりません")
                return False
                
        except Exception as e:
            print(f"ログインエラー: {e}")
            return False
    
    def save_session(self, session_file="tiktok_session.json"):
        """セッション情報の保存"""
        try:
            cookies = self.driver.get_cookies()
            session_data = {
                'cookies': cookies,
                'current_url': self.driver.current_url,
                'user_agent': self.driver.execute_script("return navigator.userAgent;")
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            print(f"セッション保存完了: {session_file}")
            return True
        except Exception as e:
            print(f"セッション保存エラー: {e}")
            return False
    
    def load_session(self, session_file="tiktok_session.json"):
        """セッション情報の読み込み"""
        try:
            if not os.path.exists(session_file):
                print("セッションファイルが存在しません")
                return False
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # TikTokにアクセス
            self.driver.get("https://www.tiktok.com/")
            self.human_like_delay(2, 4)
            
            # Cookieを設定
            for cookie in session_data['cookies']:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Cookie設定エラー: {e}")
            
            # ページをリロード
            self.driver.refresh()
            self.human_like_delay(3, 5)
            
            print("セッション復元完了")
            return True
            
        except Exception as e:
            print(f"セッション読み込みエラー: {e}")
            return False
    
    def get_session_info(self):
        """現在のセッション情報取得"""
        try:
            # 重要なCookieを取得
            important_cookies = ['sessionid', 'tt-target-idc']
            session_info = {}
            
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] in important_cookies:
                    session_info[cookie['name']] = cookie['value']
            
            return session_info
        except Exception as e:
            print(f"セッション情報取得エラー: {e}")
            return {}
    
    def close(self):
        """ドライバーの終了"""
        if self.driver:
            self.driver.quit()

# 使用例
def main():
    """メイン実行関数"""
    # ユーザーデータディレクトリを指定（Cookieの永続化）
    user_data_dir = "./tiktok_profile"
    
    # ドライバー初期化
    tiktok_driver = EnhancedTikTokDriver(
        headless=False,  # 初回は手動確認のためheadless=False推奨
        user_data_dir=user_data_dir
    )
    
    try:
        # セッション復元を試行
        if not tiktok_driver.load_session():
            print("新規ログインが必要です")
            
            # TikTokアクセス
            if tiktok_driver.safe_navigate_to_tiktok():
                # ログイン実行（実際の認証情報に置き換えてください）
                username = "your_username"  # 実際のユーザー名
                password = "your_password"  # 実際のパスワード
                
                if tiktok_driver.enhanced_login(username, password):
                    # セッション保存
                    tiktok_driver.save_session()
                    
                    # セッション情報表示
                    session_info = tiktok_driver.get_session_info()
                    print("取得したセッション情報:")
                    for key, value in session_info.items():
                        print(f"{key}: {value}")
                else:
                    print("ログインに失敗しました")
            else:
                print("TikTokアクセスに失敗しました")
        else:
            print("セッション復元成功")
            # セッション情報確認
            session_info = tiktok_driver.get_session_info()
            print("現在のセッション情報:")
            for key, value in session_info.items():
                print(f"{key}: {value}")
    
    finally:
        # 10秒待機してから終了（確認用）
        time.sleep(10)
        tiktok_driver.close()

if __name__ == "__main__":
    main()
