import requests
import json
import time
import random
from typing import Dict, Any, List, Optional, Tuple
import sys
import os
from colorama import Fore, Style, init

# 初始化colorama
init(autoreset=True)

# 配置
BASE_URL = "https://www.magicnewton.com/portal/api"
ENDPOINTS = {
    "user": "/user",
    "quests": "/quests",
    "user_quests": "/userQuests"
}
MINESWEEPER_QUEST_ID = "44ec9674-6125-4f88-9e18-8d6d6be8f156"

# 工具函数
def log_info(message: str):
    print(f"{Fore.CYAN}[信息] {message}")

def log_success(message: str):
    print(f"{Fore.GREEN}[成功] {message}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}[警告] {message}")

def log_error(message: str):
    print(f"{Fore.RED}[错误] {message}")

def format_separator(length: int = 70):
    return f"{Fore.CYAN}{'━' * length}"

# 扫雷游戏求解器
class MinesweeperSolver:
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.reset_board()
        
    def reset_board(self):
        # 初始化棋盘，None表示未知，数字表示周围地雷数，-1表示地雷
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        # 记录已经点击过的位置
        self.clicked = set()
        # 标记可能的地雷位置
        self.potential_mines = set()
        # 标记安全的位置
        self.safe_moves = set()
        
    def update_board(self, tiles: List[List[Optional[int]]]):
        """根据API返回的棋盘状态更新内部棋盘"""
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if tiles[y][x] is not None:
                    self.board[y][x] = tiles[y][x]
                    self.clicked.add((x, y))
        
        # 更新后分析棋盘
        self.analyze_board()
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取指定位置的相邻位置"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    neighbors.append((nx, ny))
        return neighbors
    
    def analyze_board(self):
        """分析棋盘，标记可能的地雷和安全位置"""
        self.safe_moves.clear()
        new_potential_mines = set()
        
        # 分析每个已知数字周围的未点击格子
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] is not None and self.board[y][x] > 0:
                    # 获取周围未点击的位置
                    unclicked_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                          if (nx, ny) not in self.clicked and self.board[ny][nx] is None]
                    mines_needed = self.board[y][x]
                    
                    # 如果周围未点击的格子数量等于需要的地雷数，那么这些都是地雷
                    if len(unclicked_neighbors) == mines_needed:
                        for nx, ny in unclicked_neighbors:
                            new_potential_mines.add((nx, ny))
                    
                    # 检查已标记的地雷
                    marked_mines = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                   if (nx, ny) in self.potential_mines]
                    
                    # 如果已标记的地雷数量等于需要的地雷数，其余未点击的格子都是安全的
                    if len(marked_mines) == mines_needed:
                        for nx, ny in unclicked_neighbors:
                            if (nx, ny) not in self.potential_mines:
                                self.safe_moves.add((nx, ny))
        
        self.potential_mines = new_potential_mines
        
        # 如果没有找到安全的移动，尝试找到0值周围的格子（它们肯定是安全的）
        if not self.safe_moves:
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if self.board[y][x] == 0:
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) not in self.clicked and self.board[ny][nx] is None:
                                self.safe_moves.add((nx, ny))
    
    def get_next_move(self) -> Tuple[int, int]:
        """获取下一步应该点击的位置"""
        # 如果有已知安全的位置，优先选择
        if self.safe_moves:
            move = self.safe_moves.pop()
            return move
        
        # 如果没有确定安全的位置，使用概率策略
        # 1. 找出所有未点击且不在潜在地雷列表中的位置
        candidates = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and (x, y) not in self.potential_mines:
                    candidates.append((x, y))
        
        if not candidates:
            # 如果没有明显安全的选择，则尝试找边缘概率最低的位置
            edge_tiles = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked and self.board[y][x] is None:
                        # 检查是否是边缘（至少有一个邻居已被点击）
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) in self.clicked:
                                edge_tiles.append((x, y))
                                break
            
            if edge_tiles:
                # 计算每个边缘位置的风险评分
                risk_scores = {}
                for x, y in edge_tiles:
                    # 如果位置在潜在地雷列表中，给予高风险
                    if (x, y) in self.potential_mines:
                        risk_scores[(x, y)] = float('inf')
                        continue
                    
                    risk = 0
                    revealed_neighbors = 0
                    for nx, ny in self.get_neighbors(x, y):
                        if (nx, ny) in self.clicked and self.board[ny][nx] is not None:
                            if self.board[ny][nx] > 0:  # 数字越大风险越高
                                risk += self.board[ny][nx]
                            revealed_neighbors += 1
                    
                    if revealed_neighbors > 0:
                        risk_scores[(x, y)] = risk / revealed_neighbors
                    else:
                        risk_scores[(x, y)] = 0
                
                # 选择风险最低的位置
                if risk_scores:
                    return min(risk_scores.items(), key=lambda x: x[1])[0]
            
            # 如果上述策略都不奏效，随机选择一个未点击的位置
            available_moves = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked:
                        available_moves.append((x, y))
            
            if not available_moves:
                raise ValueError("没有可用的移动位置")
            
            return random.choice(available_moves)
        
        # 优先选择周围已有数字的位置（更多信息可用于推理）
        informed_moves = []
        for x, y in candidates:
            for nx, ny in self.get_neighbors(x, y):
                if (nx, ny) in self.clicked and self.board[ny][nx] is not None and self.board[ny][nx] > 0:
                    informed_moves.append((x, y))
                    break
        
        if informed_moves:
            return random.choice(informed_moves)
        
        # 如果没有更多信息，随机选择一个候选位置
        if candidates:
            return random.choice(candidates)
        
        # 最后的后备策略：随机选择一个未点击的位置
        available_moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked:
                    available_moves.append((x, y))
        
        if not available_moves:
            raise ValueError("没有可用的移动位置")
        
        return random.choice(available_moves)
    
    def print_board(self):
        """打印当前棋盘状态"""
        print(f"\n{format_separator(self.board_size * 3)}")
        print("  " + " ".join(f"{i}" for i in range(self.board_size)))
        for y in range(self.board_size):
            row = f"{y} "
            for x in range(self.board_size):
                if self.board[y][x] is None:
                    row += "□ "
                elif self.board[y][x] == -1:
                    row += f"{Fore.RED}* {Style.RESET_ALL}"
                elif self.board[y][x] == 0:
                    row += "  "
                else:
                    row += f"{self.board[y][x]} "
            print(row)
        print(f"{format_separator(self.board_size * 3)}")

# API客户端
class MinesweeperAPIClient:
    def __init__(self, token_file: str = "token.txt"):
        self.token_file = token_file
        self.session = requests.Session()
        self.token = self.load_token()
        self.user_id = None
        self.user_quest_id = None
        self.solver = MinesweeperSolver()
        
    def load_token(self) -> str:
        """从文件中加载token"""
        try:
            with open(self.token_file, 'r') as f:
                token = f.readline().strip()
                if not token:
                    raise ValueError(f"Token文件为空: {self.token_file}")
                log_success(f"成功从{self.token_file}加载token")
                return token
        except FileNotFoundError:
            raise ValueError(f"Token文件不存在: {self.token_file}")
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "cookie": f"__Secure-next-auth.session-token={self.token}",
            "origin": "https://www.magicnewton.com",
            "referer": "https://www.magicnewton.com/portal/rewards",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
    
    def make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                log_info(f"发送GET请求到 {endpoint}")
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30
                )
            else:  # POST
                log_info(f"发送POST请求到 {endpoint}")
                response = self.session.post(
                    url,
                    headers=self.get_headers(),
                    json=data,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            log_error(f"请求失败: {str(e)}")
            return {"error": str(e.response.text), "status_code": e.response.status_code if hasattr(e, 'response') else None}
        except Exception as e:
            log_error(f"请求错误: {str(e)}")
            return {"error": str(e)}
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        response = self.make_request(ENDPOINTS['user'])
        if 'data' in response and 'id' in response['data']:
            self.user_id = response['data']['id']
            log_success(f"获取到用户ID: {self.user_id}")
        else:
            log_error("获取用户ID失败")
        return response
    
    def start_game(self, difficulty: str = "Easy") -> Dict[str, Any]:
        """开始一局扫雷游戏"""
        data = {
            "questId": MINESWEEPER_QUEST_ID,
            "metadata": {
                "action": "START",
                "difficulty": difficulty
            }
        }
        response = self.make_request(ENDPOINTS['user_quests'], method="POST", data=data)
        
        if 'data' in response:
            self.user_quest_id = response['data']['id']
            log_success(f"成功开始游戏，用户任务ID: {self.user_quest_id}")
            
            # 更新棋盘状态
            if '_minesweeper' in response['data'] and 'tiles' in response['data']['_minesweeper']:
                self.solver.reset_board()
                self.solver.update_board(response['data']['_minesweeper']['tiles'])
                self.solver.print_board()
        else:
            log_error("开始游戏失败")
            
        return response
    
    def click_tile(self, x: int, y: int) -> Dict[str, Any]:
        """点击指定位置的方块"""
        if not self.user_quest_id:
            log_error("未开始游戏，无法点击方块")
            return {"error": "未开始游戏"}
            
        data = {
            "questId": MINESWEEPER_QUEST_ID,
            "metadata": {
                "action": "CLICK",
                "userQuestId": self.user_quest_id,
                "x": x,
                "y": y
            }
        }
        
        log_info(f"点击位置: ({x}, {y})")
        response = self.make_request(ENDPOINTS['user_quests'], method="POST", data=data)
        
        # 更新棋盘状态
        if 'data' in response and '_minesweeper' in response['data'] and 'tiles' in response['data']['_minesweeper']:
            self.solver.update_board(response['data']['_minesweeper']['tiles'])
            self.solver.print_board()
            
            # 检查游戏是否结束
            game_over = response['data']['_minesweeper'].get('gameOver', False)
            exploded = response['data']['_minesweeper'].get('exploded', False)
            
            if game_over:
                if exploded:
                    log_error("踩到地雷了！游戏结束")
                else:
                    log_success("恭喜！成功完成扫雷游戏")
        else:
            log_error("点击方块失败或返回数据格式不正确")
            
        return response
    
    def play_game(self, difficulty: str = "Easy", max_moves: int = 50):
        """自动玩一局扫雷游戏"""
        log_info(f"开始一局{difficulty}难度的扫雷游戏")
        
        # 获取用户信息
        self.get_user_info()
        
        # 开始游戏
        start_response = self.start_game(difficulty)
        if 'error' in start_response:
            log_error(f"开始游戏失败: {start_response['error']}")
            return
        
        # 循环点击直到游戏结束
        move_count = 0
        while move_count < max_moves:
            move_count += 1
            log_info(f"第{move_count}步")
            
            try:
                # 获取下一步移动
                x, y = self.solver.get_next_move()
                
                # 点击方块
                response = self.click_tile(x, y)
                
                # 检查游戏是否结束
                if 'data' in response and '_minesweeper' in response['data']:
                    game_over = response['data']['_minesweeper'].get('gameOver', False)
                    if game_over:
                        log_success(f"游戏结束，共进行了{move_count}步")
                        break
                
                # 等待一小段时间
                time.sleep(1)
                
            except Exception as e:
                log_error(f"游戏过程中出错: {str(e)}")
                break
        
        if move_count >= max_moves:
            log_warning(f"达到最大步数限制({max_moves})，停止游戏")

# 主函数
def main():
    print(f"\n{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}🚀 Magic Newton 扫雷游戏自动化 v1.0")
    print(f"{Fore.GREEN}{'=' * 70}\n")
    
    try:
        client = MinesweeperAPIClient()
        client.play_game(difficulty="Easy")
    except KeyboardInterrupt:
        log_warning("检测到键盘中断，停止程序...")
    except Exception as e:
        log_error(f"程序发生意外错误: {str(e)}")
        import traceback
        log_error(traceback.format_exc())

if __name__ == "__main__":
    main() 