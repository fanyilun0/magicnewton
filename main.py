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
from minesweeper_solver import MinesweeperSolver

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
MAX_TASK_DELAY = 23  # seconds
MIN_LOOP_DELAY = int(24 * 60 * 60 / 1.5)  # 8 hours (minimum wait)
MAX_LOOP_DELAY = int((24 * 60 * 60))  # 24 hours (maximum wait)

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
    def __init__(self):
        log_info("Initializing Magic Newton Automation")
        self.proxy_manager = ProxyManager()
        self.api_client = APIClient(BASE_URL)

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
        max_attempts = 10  # Safety limit
        
        log_info(f"Starting dice rolls for token {token_display}")
        
        while roll_count < max_attempts:
            # Random delay between rolls
            if roll_count > 0:
                task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                log_info(f"Waiting {task_delay} seconds before next roll attempt...")
                countdown_timer(task_delay)
            
            # Attempt roll
            roll_count += 1
            log_info(f"Attempting dice roll #{roll_count} for token {token_display}")
            
            roll_result = self.api_client.roll_dice(token=token)
            roll_success = self.process_roll(roll_result, token)
            
            # Stop if roll failed or quest already completed
            if not roll_success or "error" in roll_result:
                if roll_count > 1:
                    log_success(f"Successfully completed {roll_count-1} dice rolls for token {token_display}")
                else:
                    log_warning(f"No dice rolls completed for token {token_display}")
                break
        
        if roll_count >= max_attempts:
            log_warning(f"Reached maximum roll attempts ({max_attempts}) for token {token_display}")
    
    def check_minesweeper_status(self, user_quests_data: Dict[str, Any], token: str) -> int:
        """Check how many minesweeper games have been completed today.
        Returns the count of completed games (0-3)."""
        
        token_display = f"{token[:5]}...{token[-5:]}"
        current_time = datetime.now(timezone.utc)
        completed_count = 0
        
        if not user_quests_data or 'data' not in user_quests_data:
            log_warning(f"No quest data available for token {token_display}")
            return 0
            
        # Filter minesweeper quests completed today
        for quest in user_quests_data['data']:
            if quest['questId'] == MINESWEEPER_QUEST_ID and quest['status'] == "COMPLETED":
                updated_at = datetime.fromisoformat(quest['updatedAt'].replace('Z', '+00:00'))
                if updated_at.date() == current_time.date():
                    completed_count += 1
        
        log_info(f"🎮 Minesweeper games completed today: {completed_count}/3 for token {token_display}")
        return completed_count
    
    def play_minesweeper_game(self, token: str, proxies: Optional[Dict[str, str]] = None, difficulty: str = "Easy") -> Optional[bool]:
        """Play a single minesweeper game for the given token.
        Returns:
            True: 游戏成功完成
            False: 游戏失败
            None: 已达到当日最大游戏次数，不应再尝试
        """
        
        token_display = f"{token[:5]}...{token[-5:]}"
        log_info(f"Starting a {difficulty} minesweeper game for token {token_display}")
        
        try:
            # Create solver instance
            solver = MinesweeperSolver()
            
            # Start the game
            start_response = self.api_client.start_minesweeper_game(token=token, difficulty=difficulty, proxies=proxies)
            
            if 'error' in start_response:
                if "Max games reached for today" in str(start_response.get("error", "")):
                    log_warning(f"Max minesweeper games already reached for today - token: {token_display}")
                    return None  # 特殊返回值，表示已达到最大游戏次数
                elif "Quest already completed" in str(start_response.get("error", "")):
                    log_warning(f"Minesweeper quest already completed for token {token_display}")
                    return False
                else:
                    log_error(f"Failed to start minesweeper game for token {token_display}: {start_response.get('error')}")
                    return False
            
            if not start_response or 'data' not in start_response:
                log_error(f"Invalid start game response for token {token_display}")
                return False
                
            user_quest_id = start_response['data']['id']
            log_success(f"Successfully started minesweeper game with quest ID: {user_quest_id}")
            
            # Update board state
            if '_minesweeper' in start_response['data'] and 'tiles' in start_response['data']['_minesweeper']:
                solver.reset_board()
                solver.update_board(start_response['data']['_minesweeper']['tiles'])
            
            # Play the game
            move_count = 0
            max_moves = 50  # Safety limit
            safe_coordinates_cache = []  # 缓存安全坐标
            
            while move_count < max_moves:
                # 如果缓存为空，获取新的安全坐标列表
                if not safe_coordinates_cache:
                    safe_coordinates_cache = solver.get_safe_coordinates()
                    log_info(f"获取了 {len(safe_coordinates_cache)} 个安全坐标")
                    
                    # 如果仍然没有安全坐标，回退到获取单个坐标
                    if not safe_coordinates_cache:
                        log_warning("没有找到安全坐标，尝试获取单个移动坐标")
                        safe_coordinates_cache = [solver.get_next_move()]
                
                # 从缓存中获取下一个安全坐标
                x, y = safe_coordinates_cache.pop(0)
                move_count += 1
                
                try:
                    log_info(f"Move #{move_count}: Clicking tile at ({x}, {y})")
                    
                    # Click the tile
                    response = self.api_client.click_minesweeper_tile(
                        token=token,
                        user_quest_id=user_quest_id,
                        x=x,
                        y=y,
                        proxies=proxies
                    )
                    
                    # Check for errors
                    if 'error' in response:
                        log_error(f"Error clicking tile: {response.get('error')}")
                        return False
                    
                    # Update board state
                    if 'data' in response and '_minesweeper' in response['data'] and 'tiles' in response['data']['_minesweeper']:
                        # 更新棋盘状态并清空缓存(因为棋盘已更新，之前的安全坐标可能不再有效)
                        solver.update_board(response['data']['_minesweeper']['tiles'])
                        safe_coordinates_cache = []  # 清空缓存
                        
                        # Check if game is over
                        game_over = response['data']['_minesweeper'].get('gameOver', False)
                        exploded = response['data']['_minesweeper'].get('exploded', False)
                        
                        if game_over:
                            if exploded:
                                log_error(f"💣 Hit a mine! Game over after {move_count} moves.")
                                return False
                            else:
                                log_success(f"🎮 Successfully completed minesweeper game in {move_count} moves!")
                                return True
                    
                    # Small delay between moves
                    time.sleep(1)
                    
                except Exception as e:
                    log_error(f"Error during move #{move_count}: {str(e)}")
                    safe_coordinates_cache = []  # 出错时清空缓存
                    return False
            
            log_warning(f"Reached maximum moves limit ({max_moves}), stopping game")
            return False
            
        except Exception as e:
            log_error(f"Exception in minesweeper game: {str(e)}")
            return False
    
    def play_minesweeper_game_advanced(self, token: str, proxies: Optional[Dict[str, str]] = None, difficulty: str = "Easy") -> Optional[bool]:
        """高级扫雷游戏实现，使用概率分析优化点击策略
        
        Args:
            token: 用户令牌
            proxies: 代理设置
            difficulty: 游戏难度
            
        Returns:
            True: 游戏成功完成
            False: 游戏失败
            None: 已达到当日最大游戏次数，不应再尝试
        """
        token_display = f"{token[:5]}...{token[-5:]}"
        log_info(f"启动高级扫雷游戏（{difficulty}难度）- 使用概率分析 - token: {token_display}")
        
        try:
            # 创建扫雷求解器实例
            solver = MinesweeperSolver()
            
            # 开始游戏
            start_response = self.api_client.start_minesweeper_game(token=token, difficulty=difficulty, proxies=proxies)
            
            if 'error' in start_response:
                if "Max games reached for today" in str(start_response.get("error", "")):
                    log_warning(f"已达到今日最大扫雷游戏次数 - token: {token_display}")
                    return None  # 特殊返回值，表示已达到最大游戏次数
                elif "Quest already completed" in str(start_response.get("error", "")):
                    log_warning(f"扫雷任务已完成，无法进行更多游戏 - token: {token_display}")
                    return False
                else:
                    log_error(f"开始扫雷游戏失败 - token: {token_display} - 错误: {start_response.get('error')}")
                    return False
            
            if not start_response or 'data' not in start_response:
                log_error(f"开始游戏响应无效 - token: {token_display}")
                return False
                
            user_quest_id = start_response['data']['id']
            log_success(f"成功启动扫雷游戏，任务ID: {user_quest_id}")
            
            # 更新初始棋盘状态
            if '_minesweeper' in start_response['data'] and 'tiles' in start_response['data']['_minesweeper']:
                solver.reset_board()
                solver.update_board(start_response['data']['_minesweeper']['tiles'])
            
            # 游戏循环
            move_count = 0
            max_moves = 50  # 最大步数限制
            
            # 记录已经尝试过的坐标，避免重复点击
            tried_coordinates = set()
            
            while move_count < max_moves:
                # 获取带概率信息的安全坐标列表
                safe_coordinates = solver.get_safe_coordinates_with_probability()
                
                # 移除已尝试过的坐标
                safe_coordinates = [(coord, prob) for coord, prob in safe_coordinates if coord not in tried_coordinates]
                
                if not safe_coordinates:
                    log_warning("没有可用的安全坐标，游戏可能已完成或无法继续")
                    # 恢复到普通获取移动方式
                    x, y = solver.get_next_move()
                    if (x, y) in tried_coordinates:
                        log_error("无法获取新的安全坐标，放弃游戏")
                        return False
                else:
                    # 选择最安全的坐标（概率最高）
                    (x, y), probability = safe_coordinates[0]
                    log_info(f"选择坐标 ({x}, {y}) - 安全概率: {probability:.2f}")
                
                # 标记为已尝试
                tried_coordinates.add((x, y))
                move_count += 1
                
                try:
                    log_info(f"移动 #{move_count}: 点击 ({x}, {y})")
                    
                    # 点击格子
                    response = self.api_client.click_minesweeper_tile(
                        token=token,
                        user_quest_id=user_quest_id,
                        x=x,
                        y=y,
                        proxies=proxies
                    )
                    
                    # 检查错误
                    if 'error' in response:
                        log_error(f"点击格子出错: {response.get('error')}")
                        return False
                    
                    # 更新棋盘状态
                    if 'data' in response and '_minesweeper' in response['data'] and 'tiles' in response['data']['_minesweeper']:
                        solver.update_board(response['data']['_minesweeper']['tiles'])
                        
                        # 检查游戏是否结束
                        game_over = response['data']['_minesweeper'].get('gameOver', False)
                        exploded = response['data']['_minesweeper'].get('exploded', False)
                        
                        if game_over:
                            if exploded:
                                log_error(f"💣 踩到地雷！游戏结束，共进行了 {move_count} 步")
                                return False
                            else:
                                log_success(f"🎮 成功完成扫雷游戏，用了 {move_count} 步！")
                                return True
                    
                    # 步骤间短暂延迟
                    time.sleep(1)
                    
                except Exception as e:
                    log_error(f"移动 #{move_count} 出错: {str(e)}")
                    return False
            
            log_warning(f"达到最大步数限制 ({max_moves})，停止游戏")
            return False
            
        except Exception as e:
            log_error(f"扫雷游戏过程中发生异常: {str(e)}")
            return False
            
    def perform_minesweeper_games(self, token: str, proxies: Optional[Dict[str, str]] = None, strategy: str = "advanced"):
        """执行扫雷游戏直到达到每日限制
        
        Args:
            token: 用户令牌
            proxies: 代理设置
            strategy: 游戏策略，可选值为"advanced"(高级),"simple"(简单),"mixed"(混合)
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
                log_success(f"All daily minesweeper games already completed for token {token_display}")
                # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                if hasattr(self, 'max_games_reached_tokens'):
                    self.max_games_reached_tokens.add(token)
                    log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                return
                
            log_info(f"Need to play {games_to_play} minesweeper games for token {token_display}")
            log_info(f"使用游戏策略: {strategy}")
            
            for i in range(games_to_play):
                log_info(f"Starting minesweeper game #{i+1} of {games_to_play}")
                
                # 根据策略选择游戏方法
                if strategy == "simple":
                    success = self.play_minesweeper_game(token=token, proxies=proxies)
                    # 如果返回None，表示已达到最大游戏次数，立即返回
                    if success is None:
                        log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                        # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                        if hasattr(self, 'max_games_reached_tokens'):
                            self.max_games_reached_tokens.add(token)
                            log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                        return
                    # 如果简单策略失败，尝试高级策略
                    elif not success:
                        log_warning("简单策略失败，尝试使用高级策略")
                        success = self.play_minesweeper_game_advanced(token=token, proxies=proxies)
                        # 再次检查是否达到最大游戏数
                        if success is None:
                            log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                            # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                            if hasattr(self, 'max_games_reached_tokens'):
                                self.max_games_reached_tokens.add(token)
                                log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                            return
                elif strategy == "mixed":
                    # 混合策略：随机选择游戏方法
                    if random.random() < 0.5:
                        log_info("随机选择简单策略")
                        success = self.play_minesweeper_game(token=token, proxies=proxies)
                        # 检查是否达到最大游戏数
                        if success is None:
                            log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                            # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                            if hasattr(self, 'max_games_reached_tokens'):
                                self.max_games_reached_tokens.add(token)
                                log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                            return
                        elif not success:
                            log_warning("简单策略失败，尝试使用高级策略")
                            success = self.play_minesweeper_game_advanced(token=token, proxies=proxies)
                            # 再次检查是否达到最大游戏数
                            if success is None:
                                log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                                # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                                if hasattr(self, 'max_games_reached_tokens'):
                                    self.max_games_reached_tokens.add(token)
                                    log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                                return
                    else:
                        log_info("随机选择高级策略")
                        success = self.play_minesweeper_game_advanced(token=token, proxies=proxies)
                        # 检查是否达到最大游戏数
                        if success is None:
                            log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                            # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                            if hasattr(self, 'max_games_reached_tokens'):
                                self.max_games_reached_tokens.add(token)
                                log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                            return
                        elif not success:
                            log_warning("高级策略失败，尝试使用简单策略")
                            success = self.play_minesweeper_game(token=token, proxies=proxies)
                            # 再次检查是否达到最大游戏数
                            if success is None:
                                log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                                # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                                if hasattr(self, 'max_games_reached_tokens'):
                                    self.max_games_reached_tokens.add(token)
                                    log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                                return
                else:  # 默认使用高级策略
                    success = self.play_minesweeper_game_advanced(token=token, proxies=proxies)
                    # 检查是否达到最大游戏数
                    if success is None:
                        log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                        # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                        if hasattr(self, 'max_games_reached_tokens'):
                            self.max_games_reached_tokens.add(token)
                            log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                        return
                    # 如果高级策略失败，尝试简单策略
                    elif not success:
                        log_warning("高级策略失败，尝试使用简单策略")
                        success = self.play_minesweeper_game(token=token, proxies=proxies)
                        # 再次检查是否达到最大游戏数
                        if success is None:
                            log_warning(f"已达到今日最大扫雷游戏次数，停止尝试 - token: {token_display}")
                            # 将token添加到已达到最大游戏次数的集合中（如果该集合存在）
                            if hasattr(self, 'max_games_reached_tokens'):
                                self.max_games_reached_tokens.add(token)
                                log_info(f"已将token添加到达到最大游戏次数的列表: {token_display}")
                            return
                
                # 检查该轮游戏是否最终成功
                if success:
                    log_success(f"游戏 #{i+1} 完成成功！")
                else:
                    log_warning(f"游戏 #{i+1} 所有策略都失败")
                
                # 游戏间添加延迟
                if i < games_to_play - 1:
                    task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                    log_info(f"Waiting {task_delay} seconds before next minesweeper game...")
                    countdown_timer(task_delay)
        except Exception as e:
            log_error(f"Error in minesweeper games process for token {token_display}: {str(e)}")
            log_warning(f"Skipping remaining minesweeper games for token {token_display}")
            return

    def is_new_day(self, last_run_date: datetime) -> bool:
        """Check if we've crossed over to a new day since the last run (in UTC).
        This helps determine when to reset daily task counts."""
        current_date = datetime.now(timezone.utc).date()
        return current_date > last_run_date.date()
        
    def run_automation(self, minesweeper_strategy: str = "advanced"):
        """运行自动化流程
        
        Args:
            minesweeper_strategy: 扫雷游戏策略，可选值为"advanced"(高级),"simple"(简单),"mixed"(混合)
        """
        # Keep track of when we last ran
        last_run_date = datetime.now(timezone.utc)
        
        # 跟踪当天已达到最大游戏次数的token
        max_games_reached_tokens = set()
        
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check if we've crossed over to a new day
                if self.is_new_day(last_run_date):
                    log_success(f"New day detected! Resetting daily task counts.")
                    last_run_date = current_time
                    # 重置APIClient中被限速的token
                    self.api_client.rate_limited_tokens.clear()
                    # 重置达到最大游戏次数的token列表
                    max_games_reached_tokens.clear()
                    log_info("已重置扫雷游戏计数")
                
                log_success(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                log_info(f"使用扫雷策略: {minesweeper_strategy}")
                
                # Shuffle tokens to randomize the order of processing
                tokens_to_process = self.api_client.session_tokens.copy()
                random.shuffle(tokens_to_process)
                log_info(f"Shuffled {len(tokens_to_process)} tokens for this run")
                
                for token in tokens_to_process:
                    token_display = f"{token[:5]}...{token[-5:]}"
                    
                    # 跳过被限速的token
                    if token in self.api_client.rate_limited_tokens:
                        limited_until = self.api_client.rate_limited_tokens[token]
                        if datetime.now() < limited_until:
                            wait_time = int((limited_until - datetime.now()).total_seconds())
                            log_warning(f"Skipping rate-limited token {token_display} (cooling down for {wait_time} more seconds)")
                            continue
                        else:
                            # 限速已过期，从跟踪中移除
                            del self.api_client.rate_limited_tokens[token]
                    
                    log_info(f"Processing token: {token_display}")

                    # Get a proxy for this request
                    proxies = self.proxy_manager.get_proxy()
                    if proxies:
                        proxy_type = list(proxies.values())[0].split("://")[0] if "://" in list(proxies.values())[0] else "http"
                        log_info(f"Using {proxy_type} proxy: {list(proxies.values())[0]}")
                    else:
                        log_warning("No proxy available - proceeding without proxy")

                    # Get user data
                    user_data = self.api_client.make_request(
                        ENDPOINTS['user'],
                        token=token,
                        proxies=proxies
                    )
                    self.display_user_info(user_data, token)

                    # Get quests data
                    quests_data = self.api_client.make_request(
                        ENDPOINTS['quests'],
                        token=token,
                        proxies=proxies
                    )

                    # Get user quests data
                    user_quests_data = self.api_client.make_request(
                        ENDPOINTS['user_quests'],
                        token=token,
                        proxies=proxies
                    )

                    # Process quests
                    self.process_quests(quests_data, user_quests_data, token)

                    # Check and complete one-time quests
                    if quests_data and 'data' in quests_data:
                        available_quests = quests_data['data']
                        user_quests = {uq['questId']: uq for uq in user_quests_data.get('data', [])} if user_quests_data and 'data' in user_quests_data else {}
                        
                        print(f"\n{format_separator()}")
                        log_info(f"Checking one-time quests for token {token_display}")
                        
                        for quest in available_quests:
                            quest_id = quest['id']
                            title = quest['title']
                            
                            # Check if this is a one-time quest by title
                            if any(one_time_title in title for one_time_title in ONE_TIME_QUEST_ID):
                                # Check if quest is already completed
                                if quest_id in user_quests and user_quests[quest_id]['status'] == "COMPLETED":
                                    log_info(f"One-time quest '{title}' already completed")
                                else:
                                    # Try to complete the quest
                                    log_info(f"Found incomplete one-time quest: {title}")
                                    self.complete_one_time_quest(quest_id, title, token, proxies)
                                    
                                    # Add random delay between quest completions
                                    task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                                    log_info(f"Waiting {task_delay} seconds before next action...")
                                    countdown_timer(task_delay)
                        
                        print(f"{format_separator()}")

                    # Check if the daily dice roll is already completed
                    roll_completed = self.check_roll_status(user_quests_data, token)

                    if roll_completed:
                        log_success(f"Skipping dice rolls for token {token_display} - already completed today")
                    else:
                        # Perform all available rolls
                        self.perform_rolls(token, proxies)
                    
                    # 添加延迟前先检查token是否已达到扫雷游戏上限
                    if token in max_games_reached_tokens:
                        log_warning(f"跳过扫雷游戏 - 该token今日已达到最大游戏次数: {token_display}")
                    else:
                        # Add delay before minesweeper games
                        task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                        log_info(f"Waiting {task_delay} seconds before minesweeper games...")
                        countdown_timer(task_delay)
                        
                        # 执行扫雷游戏
                        try:
                            self.perform_minesweeper_games(token, proxies, strategy=minesweeper_strategy)
                        except Exception as e:
                            log_error(f"执行扫雷游戏时出错: {str(e)}")
                        
                        # 检查是否遇到了Max games reached错误
                        if any("Max games reached for today" in str(e) for e in [
                            # 捕获可能的"Max games reached"错误
                            user_quests_data.get("error", "") if isinstance(user_quests_data, dict) else ""
                        ]):
                            max_games_reached_tokens.add(token)
                            log_warning(f"已将token添加到达到最大游戏次数的列表: {token_display}")

                    # Task delay before processing next token
                    task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                    log_info(f"Waiting {task_delay} seconds before processing next token")
                    countdown_timer(task_delay)

                # After processing all tokens, wait for next cycle (approximately 24 hours)
                loop_delay = get_random_delay(MIN_LOOP_DELAY, MAX_LOOP_DELAY)
                next_run = current_time + timedelta(seconds=loop_delay)
                log_success(f"All accounts processed. Next automatic run at: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                log_success(f"Waiting for approximately {loop_delay//3600} hours, {(loop_delay%3600)//60} minutes before next cycle")
                countdown_timer(loop_delay)

            except KeyboardInterrupt:
                log_warning("Keyboard interrupt detected. Stopping automation...")
                # Save headers before exiting
                self.api_client.save_headers()
                # Update proxy file to remove used proxies
                #íself.proxy_manager.update_proxy_file()
                break
            except Exception as e:
                log_error(f"Unexpected error occurred: {str(e)}")
                import traceback
                log_error(traceback.format_exc())
                log_warning("Retrying in 10 seconds...")
                time.sleep(10)

if __name__ == "__main__":
    # Display the rainbow banner
    # rainbow_banner()
    
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}🚀 Starting Magic Newton Automation v1.5")
    print(f"{Fore.GREEN}{'=' * 70}\n")
    
    # 添加策略选择提示
    # print(f"\n{Fore.CYAN}请选择扫雷游戏策略:")
    # print(f"{Fore.CYAN}1. 高级策略 (利用概率分析，智能选择)")
    # print(f"{Fore.CYAN}2. 简单策略 (简单顺序点击)")
    # print(f"{Fore.CYAN}3. 混合策略 (随机选择，失败时自动切换)")
    
    # strategy_choice = input(f"\n{Fore.YELLOW}请输入选择 (1/2/3，默认为1): {Fore.WHITE}")
    
    # minesweeper_strategy = "advanced"  # 默认选择
    # if strategy_choice == "2":
    #     minesweeper_strategy = "simple"
    # elif strategy_choice == "3":
    #     minesweeper_strategy = "mixed"
    
    automation = MagicNewtonAutomation()
    automation.run_automation(minesweeper_strategy="advanced")
