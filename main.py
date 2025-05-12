import random
import json
import time
import requests
import os
import sys
from typing import Dict, Any, List, Optional
from colorama import Fore, Style, init
from datetime import datetime, timezone, timedelta
from fake_useragent import UserAgent

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
]
MIN_TASK_DELAY = 7  # seconds
MAX_TASK_DELAY = 14  # seconds
MIN_LOOP_DELAY = 24 * 60 * 60  # 24 hours in seconds
MAX_LOOP_DELAY = (24 * 60 * 60) + (77 * 60)  # 24 hours + 77 minutes in seconds

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
def log_info(message: str):
    print(f"{Fore.CYAN}[INFO] {message}")

def log_success(message: str):
    print(f"{Fore.GREEN}[SUCCESS] {message}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}[WARNING] {message}")

def log_error(message: str):
    print(f"{Fore.RED}[ERROR] {message}")

def countdown_timer(seconds: int):
    for remaining in range(seconds, 0, -1):
        print(f"\r{Fore.YELLOW}⏱️ Waiting: {timedelta(seconds=remaining)}", end='')
        time.sleep(1)
    print(f"\r{Fore.GREEN}✅ Wait complete!{' ' * 20}")

def get_random_delay(min_sec: int, max_sec: int) -> int:
    return random.randint(min_sec, max_sec)

def format_separator(length: int = 70):
    return f"{Fore.CYAN}{'━' * length}"

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
            
        return {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "id-ID,id;q=0.6",
            "content-type": "application/json",
            "cookie": f"__Secure-next-auth.session-token={token}",
            "origin": "https://www.magicnewton.com",
            "referer": "https://www.magicnewton.com/portal/rewards",
            "user-agent": self.headers[token]
        }

    def make_request(self, endpoint: str, method: str = "GET", token: str = None, data: Dict = None, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        if token is None:
            token = self.get_random_token()
            
        token_display = f"{token[:5]}...{token[-5:]}"
        
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
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "Quest already completed" in e.response.text:
                log_success(f"Daily Dice Roll Already Claimed Today {token_display}")
                return {"error": "Quest already completed", "status_code": 400}
            else:
                log_error(f"Request failed: {str(e)}")
            return {"error": str(e), "status_code": e.response.status_code if hasattr(e, 'response') else None}
        except Exception as e:
            log_error(f"Request error: {str(e)}")
            return {"error": str(e)}

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

    def run_automation(self):
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                log_success(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                for token in self.api_client.session_tokens:
                    token_display = f"{token[:5]}...{token[-5:]}"
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

# TODO: 完成一次性任务
                    # Process quests
                    self.process_quests(quests_data, user_quests_data, token)

                    # Check if the daily dice roll is already completed
                    roll_completed = self.check_roll_status(user_quests_data, token)

                    if roll_completed:
                        log_success(f"Skipping dice rolls for token {token_display} - already completed today")
                    else:
                        # Perform all available rolls
                        self.perform_rolls(token, proxies)

                    # Task delay before processing next token
                    task_delay = get_random_delay(MIN_TASK_DELAY, MAX_TASK_DELAY)
                    log_info(f"Waiting {task_delay} seconds before processing next account")
                    countdown_timer(task_delay)

                # Update proxy file to remove used proxies after all accounts are processed
                # self.proxy_manager.update_proxy_file()
                
                # Calculate next run time
                loop_delay = get_random_delay(MIN_LOOP_DELAY, MAX_LOOP_DELAY)
                next_run = current_time + timedelta(seconds=loop_delay)
                log_success(f"All accounts processed. Next automatic run at: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
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
    rainbow_banner()
    
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}🚀 Starting Magic Newton Automation v1.4")
    print(f"{Fore.GREEN}{'=' * 70}\n")
    automation = MagicNewtonAutomation()
    automation.run_automation()
