from colorama import Fore, Style, init
from datetime import timedelta
import time

# Initialize colorama
init(autoreset=True)

# Log functions
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

def format_separator(length: int = 70):
    return f"{Fore.CYAN}{'━' * length}" 