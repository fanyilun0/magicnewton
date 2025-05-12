import numpy as np
import random
from MineSweeper import get_safe_moves

class MinesweeperGame:
    def __init__(self, size=10, num_mines=10):
        self.size = size
        self.num_mines = num_mines
        self.board = np.full((size, size), None)  # 用户看到的棋盘
        self.mines = set()  # 地雷位置
        self.game_over = False
        self.win = False
        self.clicked_cells = set()  # 记录已点击的格子
        self.first_move = True  # 标记是否是第一步
        
    def place_mines(self, first_x, first_y):
        """随机放置地雷，确保第一步点击的位置不是地雷"""
        positions = [(i, j) for i in range(self.size) for j in range(self.size)]
        
        # 移除第一步点击的位置及其周围的格子
        safe_positions = [(first_x, first_y)]
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = first_x + dx, first_y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    safe_positions.append((nx, ny))
        
        # 从可能的地雷位置中移除安全位置
        mine_candidates = [pos for pos in positions if pos not in safe_positions]
        
        # 随机选择地雷位置
        mine_positions = random.sample(mine_candidates, min(self.num_mines, len(mine_candidates)))
        self.mines = set(mine_positions)
        
    def click(self, x, y):
        """点击一个格子"""
        if self.game_over:
            return False
        
        # 如果是第一步，确保不会点到地雷
        if self.first_move:
            self.place_mines(x, y)
            self.first_move = False
            
        if (x, y) in self.mines:
            self.board[x, y] = "X"  # 标记为地雷
            self.game_over = True
            return False
            
        # 记录已点击的格子
        self.clicked_cells.add((x, y))
        
        # 计算周围地雷数
        mine_count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) in self.mines:
                    mine_count += 1
                    
        self.board[x, y] = mine_count
        
        # 检查是否胜利（除了地雷外的所有格子都被点击）
        if len(self.clicked_cells) == self.size * self.size - len(self.mines):
            self.win = True
            self.game_over = True
            
        return True
        
    def get_visible_board(self):
        """获取可见的棋盘（用于显示）"""
        visible = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                if self.board[i, j] is None:
                    row.append("□")  # 未点击
                elif self.board[i, j] == "X":
                    row.append("💣")  # 地雷
                elif self.board[i, j] == 0:
                    row.append("　")  # 周围无地雷
                else:
                    row.append(str(self.board[i, j]))  # 周围有地雷
            visible.append(row)
        return visible
        
    def print_board(self):
        """打印棋盘"""
        visible = self.get_visible_board()
        print("  " + " ".join([str(i) for i in range(self.size)]))
        for i in range(self.size):
            print(f"{i} " + " ".join(visible[i]))
            
    def get_board_for_solver(self):
        """获取用于求解器的棋盘格式"""
        solver_board = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                if self.board[i, j] == "X":
                    row.append(None)  # 地雷在求解器中仍然是未知的
                else:
                    row.append(self.board[i, j])
            solver_board.append(row)
        return solver_board

def play_game():
    """使用get_safe_moves函数玩一局扫雷游戏"""
    # 创建游戏
    game = MinesweeperGame(size=10, num_mines=10)
    moves = 0
    max_moves = 200
    
    # 打印初始棋盘
    print("初始棋盘:")
    game.print_board()
    print(f"地雷数量: {game.num_mines}")
    print("开始游戏...")
    
    while not game.game_over and moves < max_moves:
        # 获取当前棋盘状态
        current_board = game.get_board_for_solver()
        
        # 获取安全坐标
        safe_coordinates = get_safe_moves(current_board)
        
        if not safe_coordinates:
            print("无法确定安全坐标，游戏结束")
            break
            
        # 选择第一个安全坐标
        x, y = safe_coordinates[0]
        moves += 1
        
        print(f"\n步骤 {moves}: 点击 ({x}, {y})")
        
        # 点击格子
        success = game.click(x, y)
        
        # 打印当前棋盘
        game.print_board()
        
        if not success:
            print(f"游戏结束：点到地雷 ({x}, {y})")
            break
    
    # 游戏结束
    if game.win:
        print(f"\n游戏胜利！共用了{moves}步")
    elif moves >= max_moves:
        print(f"\n达到最大步数限制 ({max_moves})，游戏结束")
    else:
        print("\n游戏失败")
    
    # 显示地雷位置
    print("\n地雷位置:")
    for x, y in game.mines:
        print(f"({x}, {y})", end=" ")
    print()
    
    # 统计
    print(f"\n总格子数: {game.size * game.size}")
    print(f"地雷数量: {len(game.mines)}")
    print(f"已点击格子: {len(game.clicked_cells)}")
    print(f"总步数: {moves}")

if __name__ == "__main__":
    # 设置随机种子以便结果可重现
    seed = random.randint(1, 1000000)
    random.seed(seed)  # 使用不同的随机种子
    play_game() 