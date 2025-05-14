from colorama import Fore, Style, init
from datetime import timedelta, datetime
import time

# Initialize colorama
init(autoreset=True)

# Log functions
def log_info(message: str):
    print(f"{Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] {message}")

def log_success(message: str):
    print(f"{Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [SUCCESS] {message}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [WARNING] {message}")

def log_error(message: str):
    print(f"{Fore.RED}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] {message}")

def countdown_timer(seconds: int):
    # For long waits (over 2 minutes), only update every minute to reduce console output
    if seconds > 120:
        # Convert to minutes first
        minutes = seconds // 60
        for remaining_min in range(minutes, 0, -1):
            remaining_seconds = remaining_min * 60
            print(f"\r{Fore.YELLOW}⏱️ Waiting: {timedelta(seconds=remaining_seconds)}", end='')
            time.sleep(60)  # Sleep for 1 minute
        
        # Handle the remaining seconds (less than a minute)
        remaining = seconds % 60
        if remaining > 0:
            for remaining_sec in range(remaining, 0, -1):
                print(f"\r{Fore.YELLOW}⏱️ Waiting: {timedelta(seconds=remaining_sec)}", end='')
                time.sleep(1)
    else:
        # For short waits, update every second as before
        for remaining in range(seconds, 0, -1):
            print(f"\r{Fore.YELLOW}⏱️ Waiting: {timedelta(seconds=remaining)}", end='')
            time.sleep(1)
    
    print(f"\r{Fore.GREEN}✅ Wait complete!{' ' * 20}")

def format_separator(length: int = 70):
    return f"{Fore.CYAN}{'━' * length}" 