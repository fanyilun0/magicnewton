import random
import json
import time
import requests
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from colorama import Fore, Style, init
from datetime import datetime, timezone, timedelta
from fake_useragent import UserAgent
from log import log_info, log_success, log_warning, log_error, countdown_timer, format_separator
from gemini_resolver import MinesweeperSolver
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
# Initialize colorama
init(autoreset=True)

# Configuration
BASE_URL = "https://www.magicnewton.com/portal/api"
ENDPOINTS = {
    "user": "/user",
    "quests": "/quests",
    "user_quests": "/userQuests"
}
ROLL_QUEST_ID = "f56c760b-2186-40cb-9cbc-3af4a3dc20e2"
MINESWEEPER_QUEST_ID = "44ec9674-6125-4f88-9e18-8d6d6be8f156"
ONE_TIME_QUEST_ID = [
    "Follow X",
    "Follow Discord",
    "Follow Tiktok",
    "Follow Instagram",
    "Connect Guild",
    "Connect your Guild"
]
MIN_TASK_DELAY = 7  # seconds
MAX_TASK_DELAY = 19  # seconds
LOOP_DELAY = int(24 * 60 * 60)  # 24 hours (minimum wait)

# Rainbow Banner
def rainbow_banner():
    os.system("clear" if os.name == "posix" else "cls")
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    banner = """
  _______                          
 |     __|.--.--.---.-.-----.---.-.|
 |__     ||  |  |  _  |-- __|  _  |
 |_______||___  |___._|_____|___._|
          |_____|                   
    """
    
    banner_lines = banner.split('\n')
    
    # Print the entire banner with smooth color transition
    for line in banner_lines:
        color_line = ""
        for i, char in enumerate(line):
            color_line += colors[i % len(colors)] + char
        sys.stdout.write(color_line + "\n")
        sys.stdout.flush()
        time.sleep(0.05)

# Utility functions
def get_random_delay(min_sec: int, max_sec: int) -> int:
    return random.randint(min_sec, max_sec)

# Class to manage proxies
class ProxyManager:
    def __init__(self, proxy_file: str = "proxy.txt"):
        self.proxy_file = proxy_file
        self.proxies = self.load_proxies()
        self.used_proxies = set()
        
        if self.proxies:
            log_info(f"Successfully loaded {len(self.proxies)} proxies from {proxy_file}")
        else:
            log_warning(f"No proxies found in {proxy_file} - running without proxies")

    def load_proxies(self) -> List[str]:
        try:
            with open(self.proxy_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            log_warning(f"Proxy file not found: {self.proxy_file}")
            return []

    def get_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        
        # Filter out used proxies
        available_proxies = [p for p in self.proxies if p not in self.used_proxies]
        
        if not available_proxies:
            log_warning("All proxies have been used - resetting proxy list")
            self.used_proxies.clear()
            available_proxies = self.proxies
        
        proxy = random.choice(available_proxies)
        self.used_proxies.add(proxy)
        
        # Format proxy based on its type (http, socks4, socks5)
        if proxy.startswith('http'):
            return {'http': proxy, 'https': proxy}
        elif proxy.startswith('socks4'):
            return {'http': f'socks4:{proxy[7:]}', 'https': f'socks4:{proxy[7:]}'}
        elif proxy.startswith('socks5'):
            return {'http': f'socks5:{proxy[7:]}', 'https': f'socks5:{proxy[7:]}'}
        return None
    
    def update_proxy_file(self):
        """Remove used proxies from the proxy file regardless of their success/failure status"""
        try:
            if not self.used_proxies:
                log_info("No proxies were used - nothing to update")
                return
                
            # Remove used proxies from the file
            remaining_proxies = [p for p in self.proxies if p not in self.used_proxies]
            with open(self.proxy_file, 'w') as f:
                for proxy in remaining_proxies:
                    f.write(f"{proxy}\n")
            log_info(f"Updated proxy file - removed {len(self.used_proxies)} used proxies")
            
            # Update internal lists
            self.proxies = remaining_proxies
            self.used_proxies.clear()
        except Exception as e:
            log_error(f"Failed to update proxy file: {str(e)}")

# Class to manage API
class APIClient:
    def __init__(self, base_url: str, token_file: str = "token.txt", header_file: str = "header.json"):
        self.base_url = base_url
        self.token_file = token_file
        self.header_file = header_file
        self.session = requests.Session()
        self.ua = UserAgent()
        self.rate_limited_tokens = {}  # 跟踪被限速的token
        
        try:
            self.session_tokens = self.load_tokens()
            log_success(f"Successfully loaded {len(self.session_tokens)} tokens from {token_file}")
        except Exception as e:
            log_error(str(e))
            raise
            
        self.headers = self.load_headers()

    def load_tokens(self) -> List[str]:
        try:
            with open(self.token_file, 'r') as f:
                tokens = [line.strip() for line in f.readlines() if line.strip()]
                if not tokens:
                    raise Exception(f"Token file is empty: {self.token_file}")
                return tokens
        except FileNotFoundError:
            raise Exception(f"Token file not found: {self.token_file}")

    def load_headers(self) -> Dict[str, str]:
        try:
            with open(self.header_file, 'r') as f:
                headers = json.load(f)
                log_info(f"Successfully loaded headers from {self.header_file}")
                return headers
        except FileNotFoundError:
            log_info(f"Header file not found: {self.header_file} - will create new headers for each account")
            return {}

    def get_desktop_user_agent(self) -> str:
        """Generate a random desktop-only user agent"""
        # Try up to 5 times to get a desktop user agent
        for _ in range(5):
            ua = self.ua.random
            # Check if it's likely a desktop user agent (no mobile indicators)
            if 'Mobile' not in ua and 'Android' not in ua and 'iPhone' not in ua and 'iPad' not in ua:
                return ua
        
        # Fallback to a known desktop user agent pattern if all attempts failed
        return self.ua.chrome
        
    def save_headers(self) -> None:
        """Save the headers to file"""
        try:
            with open(self.header_file, 'w') as f:
                json.dump(self.headers, f, indent=2)
            log_info(f"Successfully saved {len(self.headers)} headers to {self.header_file}")
        except Exception as e:
            log_error(f"Failed to save headers: {str(e)}")

    def get_headers(self, token: str) -> Dict[str, str]:
        """Get or generate request headers for a specific token"""
        # Use the full token as the unique key to ensure each account gets its own header
        if token not in self.headers:
            self.headers[token] = self.get_desktop_user_agent()
            self.save_headers()
            log_info(f"Generated new desktop user agent for token {token[:5]}...{token[-5:]}")
            
        # 添加更多浏览器般的请求头
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "cookie": f"__Secure-next-auth.session-token={token}",
            "origin": "https://www.magicnewton.com",
            "referer": "https://www.magicnewton.com/portal/rewards",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors", 
            "sec-fetch-site": "same-origin",
            "user-agent": self.headers[token]
        }

    def make_request(self, endpoint: str, method: str = "GET", token: str = None, data: Dict = None, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        if token is None:
            token = self.get_random_token()
            
        token_display = f"{token[:5]}...{token[-5:]}"
        
        # 检查token是否被限速
        if token in self.rate_limited_tokens:
            limited_until = self.rate_limited_tokens[token]
            if datetime.now() < limited_until:
                wait_time = int((limited_until - datetime.now()).total_seconds())
                log_warning(f"Token {token_display} is rate limited. Waiting for {wait_time} seconds before retrying.")
                return {"error": f"Rate limited. Try again after {wait_time} seconds", "status_code": 429}
            else:
                # 限速时间已过，从跟踪中移除
                del self.rate_limited_tokens[token]
        
        # 在每个请求前添加一个小的随机延迟，模拟人类行为
        time.sleep(random.uniform(1.0, 3.0))
        
        retries = 0
        max_retries = 3  # 最大重试次数
        retry_delay = 60  # 初始重试延迟（秒）
        
        while retries <= max_retries:
            try:
                if method == "GET":
                    log_info(f"Sending GET request to {endpoint} with token {token_display}")
                    response = self.session.get(
                        url,
                        headers=self.get_headers(token),
                        proxies=proxies,
                        timeout=30
                    )
                else:  # POST
                    log_info(f"Sending POST request to {endpoint} with token {token_display}")
                    response = self.session.post(
                        url,
                        headers=self.get_headers(token),
                        json=data,
                        proxies=proxies,
                        timeout=30
                    )
                
                # 处理速率限制
                if response.status_code == 429:
                    retries += 1
                    # 指数退避策略
                    current_delay = retry_delay * (2 ** retries)
                    log_warning(f"Rate limited (429) for token {token_display}. Retry {retries}/{max_retries} after {current_delay}s")
                    
                    if retries > max_retries:
                        # 将此token标记为被限速，冷却30分钟
                        self.rate_limited_tokens[token] = datetime.now() + timedelta(minutes=30)
                        log_error(f"Token {token_display} has been rate limited too many times. Cooling down for 30 minutes.")
                        return {"error": str(e), "status_code": e.response.status_code}
                    
                    time.sleep(current_delay)
                    continue
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retries += 1
                    # 指数退避策略
                    current_delay = retry_delay * (2 ** retries)
                    log_warning(f"Rate limited (429) for token {token_display}. Retry {retries}/{max_retries} after {current_delay}s")
                    
                    if retries > max_retries:
                        # 将此token标记为被限速，冷却30分钟
                        self.rate_limited_tokens[token] = datetime.now() + timedelta(minutes=30)
                        log_error(f"Token {token_display} has been rate limited too many times. Cooling down for 30 minutes.")
                        return {"error": str(e), "status_code": e.response.status_code}
                    
                    time.sleep(current_delay)
                    continue
                
                elif e.response.status_code == 400 and "Quest already completed" in e.response.text:
                    log_success(f"Daily Dice Roll Already Claimed Today {token_display}")
                    return {"error": "Quest already completed", "status_code": 400}
                elif e.response.status_code == 400 and "Max games reached for today" in e.response.text:
                    log_success(f"Max games reached for today {token_display}")
                    return {"error": "Max games reached for today", "status_code": 400}
                else:
                    log_error(f"Request failed: {str(e.response.text)}")
                    return {"error": str(e), "status_code": e.response.status_code if hasattr(e, 'response') else None}
            
            except requests.exceptions.ConnectionError as e:
                log_error(f"Connection error for token {token_display}: {str(e)}")
                if retries < max_retries:
                    retries += 1
                    current_delay = retry_delay * (2 ** retries)
                    log_warning(f"Connection error. Retry {retries}/{max_retries} after {current_delay}s")
                    time.sleep(current_delay)
                    continue
                return {"error": str(e)}
            
            except Exception as e:
                log_error(f"Request error for token {token_display}: {str(e)}")
                return {"error": str(e)}
        
        return {"error": "Maximum retries exceeded"}

    def get_random_token(self) -> str:
        return random.choice(self.session_tokens)

    def roll_dice(self, token: str = None) -> Dict[str, Any]:
        data = {
            "questId": ROLL_QUEST_ID,
            "metadata": {
                #"action": "ROLL"
            }
        }
        return self.make_request("/userQuests", method="POST", token=token, data=data)
        
    def start_minesweeper_game(self, token: str = None, difficulty: str = "Easy", proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Start a minesweeper game"""
        data = {
            "questId": MINESWEEPER_QUEST_ID,
            "metadata": {
                "action": "START",
                "difficulty": difficulty
            }
        }
        
        response = self.make_request("/userQuests", method="POST", token=token, data=data, proxies=proxies)
        
        # 特别检查常见的错误情况，提供更清晰的错误信息
        if "error" in response:
            error_text = str(response.get("error", ""))
            status_code = response.get("status_code", 0)
            
            # 特别处理扫雷相关的错误
            if status_code == 400:
                if "Max games reached for today" in error_text:
                    # 确保返回标准化的错误格式
                    return {"error": "Max games reached for today", "status_code": 400}
                elif "Quest already completed" in error_text:
                    return {"error": "Quest already completed", "status_code": 400}
        
        return response
        
    def click_minesweeper_tile(self, token: str, user_quest_id: str, x: int, y: int, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Click a tile in the minesweeper game"""
        data = {
            "questId": MINESWEEPER_QUEST_ID,
            "metadata": {
                "action": "CLICK",
                "userQuestId": user_quest_id,
                "x": x,
                "y": y
            }
        }
        return self.make_request("/userQuests", method="POST", token=token, data=data, proxies=proxies)

# Main class for automation
class MagicNewtonAutomation:
    def __init__(self, max_parallel_tokens: int = 3):
        log_info("Initializing Magic Newton Automation")
        self.proxy_manager = ProxyManager()
        self.api_client = APIClient(BASE_URL)
        self.max_parallel_tokens = max_parallel_tokens
        self.thread_lock = threading.Lock()
        log_info(f"设置最大并行token数量: {max_parallel_tokens}")

    def display_user_info(self, user_data: Dict[str, Any], token: str):
        token_display = f"{token[:5]}...{token[-5:]}"
        
        if not user_data or 'data' not in user_data:
            log_error(f"Failed to fetch user data for token: {token_display}")
            return

        user = user_data['data']
        user_email = user.get('email', 'Unknown')
        display_name = user.get('auths', [{}])[0].get('displayName', 'Unknown') if user.get('auths') else 'Unknown'
        user_identifier = user_email if user_email != 'Unknown' else display_name

        print(f"\n{format_separator()}")
        log_success(f"User Profile: {user_identifier}")
        print(f"🆔 ID: {user.get('id', 'Unknown')}")
        print(f"👤 Name: {user.get('name', 'Unknown')}")
        print(f"📧 Email: {user_email}")
        print(f"🔗 Ref Code: {user.get('refCode', 'Unknown')}")
        print(f"👁️ Display Name: {display_name}")
        print(f"{format_separator()}")

    def process_roll(self, roll_response: Dict[str, Any], token: str) -> bool:
        """Process roll response and return True if roll was successful, False otherwise"""
        token_display = f"{token[:5]}...{token[-5:]}"
        
        # Check for error
        if "error" in roll_response:
            if roll_response.get("error") == "Quest already completed":
                log_warning(f"No more dice rolls available for token {token_display}")
                return False
            else:
                log_error(f"Dice roll failed for token {token_display}: {roll_response.get('error')}")
                return False
        
        # Check for valid response
        if not roll_response or 'data' not in roll_response:
            log_error(f"Invalid dice roll response for token {token_display}")
            return False

        data = roll_response['data']
        dice_rolls = data.get('_diceRolls', [])
        credits = data.get('credits', 0)

        print(f"\n{format_separator(30)}")
        log_success(f"🎲 Dice Roll Result for token {token_display}:")
        print(f"💰 Credits earned: {credits}")
        
        if len(dice_rolls) > 0:
            last_roll = dice_rolls[-1]
            print(f"🎯 Roll value: {last_roll}")
        else:
            print(f"🎯 Roll value: None")
            
        print(f"📋 Status: {data.get('status', 'Unknown')}")
        print(f"{format_separator(30)}")
        
        return True

    def process_quests(self, quests_data: Dict[str, Any], user_quests_data: Dict[str, Any], token: str):
        token_display = f"{token[:5]}...{token[-5:]}"
        
        if not quests_data or 'data' not in quests_data:
            log_error(f"Failed to fetch quests data for token: {token_display}")
            return

        available_quests = quests_data['data']
        user_quests = {uq['questId']: uq for uq in user_quests_data.get('data', [])} if user_quests_data and 'data' in user_quests_data else {}

        print(f"\n{format_separator()}")
        log_success(f"📋 Quests Status for token {token_display}:")
        
        for quest in available_quests:
            quest_id = quest['id']
            title = quest['title']
            
            if quest_id in user_quests:
                status = user_quests[quest_id]['status']
                if status == "COMPLETED":
                    status_display = f"{Fore.GREEN}✅ COMPLETED (Already claimed)"
                elif status == "PENDING":
                    status_display = f"{Fore.YELLOW}⏳ PENDING (Not yet completed)"
                else:
                    status_display = f"{Fore.YELLOW}⚠️ {status}"
            else:
                status_display = f"{Fore.YELLOW}🆕 NOT STARTED"
                
            print(f"🔸 {title}: {status_display}")
        
        print(f"{format_separator()}")

    def check_roll_status(self, user_quests_data: Dict[str, Any], token: str) -> bool:
        """Check if the daily dice roll has been completed today.
        Returns True if roll is already completed, False otherwise."""
        
        token_display = f"{token[:5]}...{token[-5:]}"
        current_time = datetime.now(timezone.utc)
        
        if not user_quests_data or 'data' not in user_quests_data:
            log_warning(f"No quest data available for token {token_display}")
            return False
            
        roll_quest = next((uq for uq in user_quests_data['data'] if uq['questId'] == ROLL_QUEST_ID), None)

        if roll_quest:
            status = roll_quest['status']
            roll_updated_at = datetime.fromisoformat(roll_quest['updatedAt'].replace('Z', '+00:00'))
            roll_date = roll_updated_at.date()
            
            if status == "COMPLETED" and roll_date == current_time.date():
                log_info(f"🎲 Daily dice roll status: {Fore.GREEN}COMPLETED ✅")
                log_info(f"Last completed: {roll_updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                return True
            else:
                log_info(f"🎲 Daily dice roll status: {Fore.YELLOW}PENDING ⏳")
                if status == "COMPLETED":
                    log_info(f"Last completed: {roll_updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')} (outdated)")
                return False
        else:
            log_info(f"🎲 Daily dice roll status: {Fore.YELLOW}NOT STARTED 🆕")
            return False

    def complete_one_time_quest(self, quest_id: str, quest_title: str, token: str, proxies: Optional[Dict[str, str]] = None) -> bool:
        """Complete a one-time quest and return True if successful, False otherwise."""
        token_display = f"{token[:5]}...{token[-5:]}"
        
        log_info(f"Attempting to complete one-time quest: {quest_title} for token {token_display}")
        
        data = {
            "questId": quest_id,
            "metadata": {}
        }
        
        result = self.api_client.make_request(
            ENDPOINTS['user_quests'],
            method="POST",
            token=token,
            data=data,
            proxies=proxies
        )
        
        if "error" in result:
            if result.get("status_code") == 400 and "Quest already completed" in result.get("error", ""):
                log_warning(f"Quest '{quest_title}' already completed for token {token_display}")
                return True
            else:
                log_error(f"Failed to complete quest '{quest_title}' for token {token_display}: {result.get('error')}")
                return False
        
        if not result or 'data' not in result:
            log_error(f"Invalid response for quest '{quest_title}' completion for token {token_display}")
            return False
            
        log_success(f"Successfully completed one-time quest: {quest_title} for token {token_display}")
        return True

    def perform_rolls(self, token: str, proxies: Optional[Dict[str, str]] = None):
        """Perform dice rolls until no more rolls are available"""
        token_display = f"{token[:5]}...{token[-5:]}"
        roll_count = 0
        max_attempts = 2  # Safety limit
        
        with self.thread_lock:
            log_info(f"开始骰子游戏 - token: {token_display}")
        
        while roll_count < max_attempts:
            # Random delay between rolls
            if roll_count > 0:
                task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                with self.thread_lock:
                    log_info(f"等待 {task_delay} 秒后进行下一次骰子尝试... - token: {token_display}")
                time.sleep(task_delay)
            
            # Attempt roll
            roll_count += 1
            with self.thread_lock:
                log_info(f"尝试第 #{roll_count} 次骰子游戏 - token: {token_display}")
            
            roll_result = self.api_client.roll_dice(token=token)
            roll_success = self.process_roll(roll_result, token)
            
            # Stop if roll failed or quest already completed
            if not roll_success or "error" in roll_result:
                if roll_count > 1:
                    with self.thread_lock:
                        log_success(f"成功完成 {roll_count-1} 次骰子游戏 - token: {token_display}")
                else:
                    with self.thread_lock:
                        log_warning(f"没有完成任何骰子游戏 - token: {token_display}")
                break
        
        if roll_count >= max_attempts:
            with self.thread_lock:
                log_warning(f"达到最大骰子尝试次数 ({max_attempts}) - token: {token_display}")

    def check_minesweeper_status(self, user_quests_data: Dict[str, Any], token: str) -> int:
        """Check how many minesweeper games have been completed today.
        Returns the count of completed games (0-3)."""
        
        token_display = f"{token[:5]}...{token[-5:]}"
        current_time = datetime.now(timezone.utc)
        completed_count = 0
        
        if not user_quests_data or 'data' not in user_quests_data:
            with self.thread_lock:
                log_warning(f"没有可用的任务数据 - token: {token_display}")
            return 0
            
        # Filter minesweeper quests completed today
        for quest in user_quests_data['data']:
            if quest['questId'] == MINESWEEPER_QUEST_ID and quest['status'] == "COMPLETED":
                updated_at = datetime.fromisoformat(quest['updatedAt'].replace('Z', '+00:00'))
                if updated_at.date() == current_time.date():
                    completed_count += 1
        
        with self.thread_lock:
            log_info(f"🎮 今日已完成扫雷游戏: {completed_count}/3 - token: {token_display}")
        return completed_count
    
    def _start_minesweeper_game(self, token: str, difficulty: str, proxies: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """启动扫雷游戏并处理初始状态
        
        Returns:
            Dict: 成功时返回包含游戏信息的字典
            None: 游戏无法启动（已达上限或其他错误）
        """
        token_display = f"{token[:5]}...{token[-5:]}"
        log_info(f"开始 {difficulty} 难度扫雷游戏 - token: {token_display}")
        
        # 开始游戏
        start_response = self.api_client.start_minesweeper_game(token=token, difficulty=difficulty, proxies=proxies)
        
        # 处理开始游戏的错误情况
        if 'error' in start_response:
            if "Max games reached for today" in str(start_response.get("error", "")):
                log_warning(f"今日已达到最大扫雷游戏次数 - token: {token_display}")
                return None
            elif "Quest already completed" in str(start_response.get("error", "")):
                log_warning(f"扫雷任务已完成 - token: {token_display}")
                return None
            else:
                log_error(f"开始扫雷游戏失败 - token: {token_display}: {start_response.get('error')}")
                return None
        
        if not start_response or 'data' not in start_response:
            log_error(f"开始游戏响应无效 - token: {token_display}")
            return None
        
        user_quest_id = start_response['data']['id']
        log_success(f"成功启动扫雷游戏，任务ID: {user_quest_id}")
        
        return start_response['data']

    def _log_game_status(self, solver, safe_coords, move_count, cached_coords_count=None):
        """记录当前游戏状态日志"""
        # 输出当前分析信息
        # log_info(f"移动 #{move_count} - 分析结果")
        
        # if not safe_coords:
        #     log_info("当前分析没有找到安全坐标")
        # else:
        #     log_info(f"当前分析得到 {len(safe_coords)} 个新的安全坐标")
            
        # if cached_coords_count is not None:
        #     log_info(f"缓存中有 {cached_coords_count} 个安全坐标")
        
        # 限制输出详情的坐标数量
        if safe_coords:
            if len(safe_coords) <= 5:
                coords_str = ", ".join([f"({x},{y})" for x, y in safe_coords])
                log_info(f"安全坐标详情: {coords_str}")
            else:
                coords_str = ", ".join([f"({x},{y})" for x, y in list(safe_coords)[:5]])
                log_info(f"安全坐标详情(部分): {coords_str}... 等共{len(safe_coords)}个")

    def play_minesweeper_game(self, token: str, proxies: Optional[Dict[str, str]] = None, difficulty: str = "Easy") -> Optional[bool]:
        """进行单局扫雷游戏，使用确定性安全坐标策略并缓存安全坐标
        
        Returns:
            True: 游戏成功完成
            False: 游戏失败
            None: 已达到当日最大游戏次数，不应再尝试
        """
        token_display = f"{token[:5]}...{token[-5:]}"
        
        try:
            # 创建扫雷求解器实例
            solver = MinesweeperSolver()
            
            # 启动游戏并获取初始数据
            game_data = self._start_minesweeper_game(token, difficulty, proxies)
            if game_data is None:
                return None  # 表示游戏无法启动（已达上限或其他错误）
                
            user_quest_id = game_data['id']
            
            move_count = 0
            max_moves = 25  # 最大步数限制
            
            # 用于缓存安全坐标的集合
            safe_coordinates_cache = set()
            
            # 初始棋盘数据
            if '_minesweeper' in game_data and 'tiles' in game_data['_minesweeper']:
                # 分析初始棋盘
                initial_tiles = game_data['_minesweeper']['tiles']
                safe_coords, mine_coords = solver.analyze_board(initial_tiles)
                
                # 将分析结果添加到缓存
                safe_coordinates_cache.update(safe_coords)
                
                # 记录已揭示和标记的格子，用于后续过滤
                revealed_coords = set()
                flagged_coords = set()
                
                # 更新已揭示和标记的格子集合
                for y in range(len(initial_tiles)):
                    for x in range(len(initial_tiles[y])):
                        if initial_tiles[y][x] is not None:
                            revealed_coords.add((x, y))
                            if initial_tiles[y][x] == -1:  # 标记为地雷
                                flagged_coords.add((x, y))
            else:
                # 如果没有初始棋盘数据，创建空集合
                revealed_coords = set()
                flagged_coords = set()
            
            # 游戏主循环
            while move_count < max_moves:
                current_board = None
                
                # 获取当前棋盘状态（仅在第一次之后的循环中需要）
                if move_count > 0 and 'data' in response and '_minesweeper' in response['data'] and 'tiles' in response['data']['_minesweeper']:
                    current_board = response['data']['_minesweeper']['tiles']
                    # 分析当前棋盘
                    new_safe_coords, new_mine_coords = solver.analyze_board(current_board)
                    
                    # 更新安全坐标缓存
                    safe_coordinates_cache.update(new_safe_coords)
                    
                    # 更新已揭示和标记的格子集合
                    new_revealed_coords = set()
                    new_flagged_coords = set()
                    
                    for y in range(len(current_board)):
                        for x in range(len(current_board[y])):
                            if current_board[y][x] is not None:
                                new_revealed_coords.add((x, y))
                                if current_board[y][x] == -1:  # 标记为地雷
                                    new_flagged_coords.add((x, y))
                    
                    # 更新集合
                    revealed_coords = new_revealed_coords
                    flagged_coords = new_flagged_coords
                elif move_count == 0 and '_minesweeper' in game_data and 'tiles' in game_data['_minesweeper']:
                    current_board = game_data['_minesweeper']['tiles']
                
                # 移除已揭示或标记为地雷的坐标
                safe_coordinates_cache = {coord for coord in safe_coordinates_cache 
                                          if coord not in revealed_coords and coord not in flagged_coords}
                
                # 记录游戏状态日志
                if current_board:
                    # 获取当前安全坐标用于显示
                    current_safe_coords, _ = solver.analyze_board(current_board)
                    self._log_game_status(solver, current_safe_coords, move_count, len(safe_coordinates_cache))
                else:
                    log_info(f"游戏状态: 缓存中有 {len(safe_coordinates_cache)} 个安全坐标")
                
                # 选择要点击的坐标
                if not safe_coordinates_cache:
                    if current_board is None:
                        # 第一步，没有棋盘数据，选择中心位置
                        x, y = solver.board_size // 2, solver.board_size // 2
                        log_info(f"没有安全坐标，选择棋盘中心: ({x}, {y})")
                    else:
                        # 没有安全坐标时随机选择一个未揭示的位置
                        all_unrevealed = []
                        for y in range(len(current_board)):
                            for x in range(len(current_board[y])):
                                if (x, y) not in revealed_coords and (x, y) not in flagged_coords:
                                    all_unrevealed.append((x, y))
                        
                        if not all_unrevealed:
                            log_info("没有可用的坐标，游戏可能已完成")
                            return True
                        
                        # 随机选择一个未揭示的坐标
                        x, y = random.choice(all_unrevealed)
                        log_info(f"没有确定安全的坐标，随机选择坐标: ({x}, {y})")
                else:
                    # 从缓存的安全坐标中选择一个
                    x, y = next(iter(safe_coordinates_cache))
                    safe_coordinates_cache.remove((x, y))  # 从缓存中移除将要点击的坐标
                    # log_info(f"选择缓存的安全坐标: ({x}, {y})")
                
                move_count += 1
                log_info(f"#{move_count}: 点击坐标 ({x}, {y})")
                
                # 设置最后点击的坐标（用于调试）
                solver.set_last_clicked((x, y))
                
                # 执行点击
                try:
                    response = self.api_client.click_minesweeper_tile(
                        token=token,
                        user_quest_id=user_quest_id,
                        x=x,
                        y=y,
                        proxies=proxies
                    )
                    
                    # 检查点击错误
                    if 'error' in response:
                        log_error(f"点击错误: {response.get('error')}")
                        return False
                    
                    # 检查游戏状态
                    if 'data' in response and '_minesweeper' in response['data']:
                        game_over = response['data']['_minesweeper'].get('gameOver', False)
                        exploded = response['data']['_minesweeper'].get('exploded', False)
                        
                        if game_over:
                            if exploded:
                                log_error(f"💣 踩到地雷! 游戏结束，共进行 {move_count} 步。")
                                return False
                            else:
                                log_success(f"🎮 成功完成扫雷游戏，用了 {move_count} 步!")
                                return True
                
                    # 步骤间短暂延迟
                    time.sleep(1)
                    
                except Exception as e:
                    log_error(f"移动 #{move_count} 出错: {str(e)}")
                    safe_coordinates_cache.clear()  # 出错时清空缓存
                    return False
            
            log_warning(f"达到最大步数限制 ({max_moves})，停止游戏")
            return False
            
        except Exception as e:
            log_error(f"扫雷游戏过程中发生异常: {str(e)}")
            return False

    def perform_minesweeper_games(self, token: str, proxies: Optional[Dict[str, str]] = None):
        """执行扫雷游戏直到达到每日限制
        
        Args:
            token: 用户令牌
            proxies: 代理设置
        """
        token_display = f"{token[:5]}...{token[-5:]}"
        
        try:
            # 获取用户任务数据，检查已完成游戏数量
            user_quests_data = self.api_client.make_request(
                ENDPOINTS['user_quests'],
                token=token,
                proxies=proxies
            )
            
            completed_games = self.check_minesweeper_status(user_quests_data, token)
            games_to_play = 3 - completed_games
            
            if games_to_play <= 0:
                with self.thread_lock:
                    log_success(f"今日扫雷游戏已全部完成 - token: {token_display}")
                # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                if hasattr(self, 'max_games_reached_tokens'):
                    self.max_games_reached_tokens.add(token)
                    with self.thread_lock:
                        log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                return
                
            with self.thread_lock:
                log_info(f"计划进行 {games_to_play} 局扫雷游戏 - token: {token_display}")
            
            for i in range(games_to_play):
                with self.thread_lock:
                    log_info(f"开始扫雷游戏 #{i+1}/{games_to_play} - token: {token_display}")
                
                # 使用改进的扫雷算法
                success = self.play_minesweeper_game(token=token, proxies=proxies)
                
                # 检查游戏结果
                if success is None:
                    # 已达到最大游戏次数，立即返回
                    with self.thread_lock:
                        log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                    if hasattr(self, 'max_games_reached_tokens'):
                        self.max_games_reached_tokens.add(token)
                        with self.thread_lock:
                            log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                    return
                elif success:
                    with self.thread_lock:
                        log_success(f"游戏 #{i+1} 完成成功！ - token: {token_display}")
                else:
                    with self.thread_lock:
                        log_warning(f"游戏 #{i+1} 失败 - token: {token_display}")
                
                # 游戏间添加延迟
                if i < games_to_play - 1:
                    task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                    with self.thread_lock:
                        log_info(f"等待 {task_delay} 秒后开始下一局扫雷游戏... - token: {token_display}")
                    time.sleep(task_delay)
        except Exception as e:
            with self.thread_lock:
                log_error(f"扫雷游戏过程中发生错误 - token: {token_display}: {str(e)}")
                log_warning(f"跳过剩余的扫雷游戏 - token: {token_display}")
            return

    def is_new_day(self, last_run_date: datetime) -> bool:
        """Check if we've crossed over to a new day since the last run (in UTC).
        This helps determine when to reset daily task counts."""
        current_date = datetime.now(timezone.utc).date()
        return current_date > last_run_date.date()

    def process_single_token(self, token: str, max_games_reached_tokens: set) -> Dict[str, Any]:
        """处理单个token的所有任务
        
        Args:
            token: 要处理的token
            max_games_reached_tokens: 已达到最大游戏次数的token集合
            
        Returns:
            Dict: 包含处理结果的字典
        """
        token_display = f"{token[:5]}...{token[-5:]}"
        result = {
            "token": token_display,
            "success": False,
            "error": None,
            "tasks_completed": []
        }
        
        try:
            # 跳过被限速的token
            if token in self.api_client.rate_limited_tokens:
                limited_until = self.api_client.rate_limited_tokens[token]
                if datetime.now() < limited_until:
                    wait_time = int((limited_until - datetime.now()).total_seconds())
                    result["error"] = f"Rate-limited (cooling down for {wait_time} more seconds)"
                    with self.thread_lock:
                        log_warning(f"跳过被限速的token {token_display} (还需冷却 {wait_time} 秒)")
                    return result
                else:
                    # 限速已过期，从跟踪中移除
                    del self.api_client.rate_limited_tokens[token]
            
            with self.thread_lock:
                log_info(f"开始处理token: {token_display}")

            # 获取代理
            proxies = self.proxy_manager.get_proxy()
            if proxies:
                proxy_type = list(proxies.values())[0].split("://")[0] if "://" in list(proxies.values())[0] else "http"
                with self.thread_lock:
                    log_info(f"使用 {proxy_type} 代理: {list(proxies.values())[0]} - token: {token_display}")
            else:
                with self.thread_lock:
                    log_warning(f"没有可用代理 - 直连处理 - token: {token_display}")

            # 获取用户数据
            user_data = self.api_client.make_request(
                ENDPOINTS['user'],
                token=token,
                proxies=proxies
            )
            
            if "error" in user_data:
                result["error"] = f"Failed to get user data: {user_data.get('error')}"
                return result
                
            with self.thread_lock:
                self.display_user_info(user_data, token)

            # 获取任务数据
            quests_data = self.api_client.make_request(
                ENDPOINTS['quests'],
                token=token,
                proxies=proxies
            )

            # 获取用户任务数据
            user_quests_data = self.api_client.make_request(
                ENDPOINTS['user_quests'],
                token=token,
                proxies=proxies
            )

            # 处理任务
            with self.thread_lock:
                self.process_quests(quests_data, user_quests_data, token)

            # 检查并完成一次性任务
            if quests_data and 'data' in quests_data:
                available_quests = quests_data['data']
                user_quests = {uq['questId']: uq for uq in user_quests_data.get('data', [])} if user_quests_data and 'data' in user_quests_data else {}
                
                with self.thread_lock:
                    print(f"\n{format_separator()}")
                    log_info(f"检查一次性任务 - token: {token_display}")
                
                for quest in available_quests:
                    quest_id = quest['id']
                    title = quest['title']
                    
                    # 检查是否为一次性任务
                    if any(one_time_title in title for one_time_title in ONE_TIME_QUEST_ID):
                        # 检查任务是否已完成
                        if quest_id in user_quests and user_quests[quest_id]['status'] == "COMPLETED":
                            with self.thread_lock:
                                log_info(f"一次性任务 '{title}' 已完成")
                        else:
                            # 尝试完成任务
                            with self.thread_lock:
                                log_info(f"发现未完成的一次性任务: {title}")
                            
                            if self.complete_one_time_quest(quest_id, title, token, proxies):
                                result["tasks_completed"].append(f"One-time quest: {title}")
                            
                            # 任务完成间添加随机延迟
                            task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                            with self.thread_lock:
                                log_info(f"等待 {task_delay} 秒后进行下一个操作... - token: {token_display}")
                            time.sleep(task_delay)
                
                with self.thread_lock:
                    print(f"{format_separator()}")

            # 检查每日骰子是否已完成
            roll_completed = self.check_roll_status(user_quests_data, token)

            if roll_completed:
                with self.thread_lock:
                    log_success(f"跳过骰子游戏 - 今日已完成 - token: {token_display}")
            else:
                # 执行所有可用的骰子游戏
                self.perform_rolls(token, proxies)
                result["tasks_completed"].append("Dice rolls")
            
            # 检查token是否已达到扫雷游戏上限
            if token in max_games_reached_tokens:
                with self.thread_lock:
                    log_warning(f"跳过扫雷游戏 - 该token今日已达到最大游戏次数: {token_display}")
            else:
                # 扫雷游戏前添加延迟
                task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                with self.thread_lock:
                    log_info(f"等待 {task_delay} 秒后开始扫雷游戏... - token: {token_display}")
                time.sleep(task_delay)
                
                # 执行扫雷游戏
                try:
                    self.perform_minesweeper_games(token, proxies)
                    result["tasks_completed"].append("Minesweeper games")
                except Exception as e:
                    with self.thread_lock:
                        log_error(f"执行扫雷游戏时出错 - token: {token_display}: {str(e)}")
                    
                    # 检查是否遇到了Max games reached错误
                    if "Max games reached for today" in str(e):
                        max_games_reached_tokens.add(token)
                        with self.thread_lock:
                            log_warning(f"已将token添加到达到最大游戏次数的列表: {token_display}")

            result["success"] = True
            with self.thread_lock:
                log_success(f"成功完成token处理: {token_display}")
                
        except Exception as e:
            result["error"] = str(e)
            with self.thread_lock:
                log_error(f"处理token时发生错误 - {token_display}: {str(e)}")
        
        return result

    def run_automation(self):
        """运行自动化流程"""
        # Keep track of when we last ran
        last_run_date = datetime.now(timezone.utc)
        
        # 跟踪当天已达到最大游戏次数的token
        max_games_reached_tokens = set()
        
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check if we've crossed over to a new day
                if self.is_new_day(last_run_date):
                    log_success(f"检测到新的一天！重置每日任务计数。")
                    last_run_date = current_time
                    # 重置APIClient中被限速的token
                    self.api_client.rate_limited_tokens.clear()
                    # 重置达到最大游戏次数的token列表
                    max_games_reached_tokens.clear()
                    log_info("已重置扫雷游戏计数")
                
                log_success(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                # Shuffle tokens to randomize the order of processing
                tokens_to_process = self.api_client.session_tokens.copy()
                random.shuffle(tokens_to_process)
                log_info(f"随机排列 {len(tokens_to_process)} 个token进行处理")
                
                # 将token分批处理，每批最多self.max_parallel_tokens个
                batch_size = self.max_parallel_tokens
                total_batches = (len(tokens_to_process) + batch_size - 1) // batch_size
                
                log_info(f"开始并行处理，每批 {batch_size} 个token，共 {total_batches} 批")
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, len(tokens_to_process))
                    current_batch = tokens_to_process[start_idx:end_idx]
                    
                    log_success(f"处理第 {batch_num + 1}/{total_batches} 批，包含 {len(current_batch)} 个token")
                    
                    # 使用ThreadPoolExecutor并行处理当前批次的token
                    with ThreadPoolExecutor(max_workers=len(current_batch)) as executor:
                        # 提交所有任务
                        future_to_token = {
                            executor.submit(self.process_single_token, token, max_games_reached_tokens): token 
                            for token in current_batch
                        }
                        
                        # 收集结果
                        batch_results = []
                        for future in as_completed(future_to_token):
                            token = future_to_token[future]
                            try:
                                result = future.result()
                                batch_results.append(result)
                            except Exception as e:
                                token_display = f"{token[:5]}...{token[-5:]}"
                                log_error(f"处理token {token_display} 时发生异常: {str(e)}")
                                batch_results.append({
                                    "token": token_display,
                                    "success": False,
                                    "error": str(e),
                                    "tasks_completed": []
                                })
                    
                    # 输出批次处理结果摘要
                    successful_tokens = [r for r in batch_results if r["success"]]
                    failed_tokens = [r for r in batch_results if not r["success"]]
                    
                    log_success(f"第 {batch_num + 1} 批处理完成:")
                    log_success(f"  ✅ 成功: {len(successful_tokens)} 个token")
                    if failed_tokens:
                        log_warning(f"  ❌ 失败: {len(failed_tokens)} 个token")
                        for failed in failed_tokens:
                            log_warning(f"    - {failed['token']}: {failed['error']}")
                    
                    # 批次间添加延迟（除了最后一批）
                    if batch_num < total_batches - 1:
                        batch_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                        log_info(f"等待 {batch_delay} 秒后处理下一批token...")
                        countdown_timer(batch_delay)

                # 所有token处理完成后，等待下一个周期（大约24小时）
                loop_delay = get_random_delay(LOOP_DELAY, LOOP_DELAY+30)
                next_run = current_time + timedelta(seconds=loop_delay)
                log_success(f"所有账户处理完成。下次自动运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                log_success(f"等待大约 {loop_delay//3600} 小时 {(loop_delay%3600)//60} 分钟后开始下一个周期")
                countdown_timer(loop_delay)

            except KeyboardInterrupt:
                log_warning("检测到键盘中断。停止自动化...")
                # Save headers before exiting
                self.api_client.save_headers()
                # Update proxy file to remove used proxies
                #self.proxy_manager.update_proxy_file()
                break
            except Exception as e:
                log_error(f"发生意外错误: {str(e)}")
                import traceback
                log_error(traceback.format_exc())
                log_warning("10秒后重试...")
                time.sleep(10)

if __name__ == "__main__":
    # Display the rainbow banner
    # rainbow_banner()
    
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}🚀 Starting Magic Newton Automation v1.6 (并行处理版本)")
    print(f"{Fore.GREEN}{'=' * 70}\n")
    
    # 可以通过环境变量或命令行参数设置并行token数量
    max_parallel_tokens = int(os.environ.get('MAX_PARALLEL_TOKENS', 3))
    log_info(f"设置最大并行token数量: {max_parallel_tokens}")
    
    automation = MagicNewtonAutomation(max_parallel_tokens=max_parallel_tokens)
    automation.run_automation()
