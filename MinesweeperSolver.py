import random
import time
from typing import List, Tuple, Optional, Set, Dict, Any

class MinesweeperSolver:
    """扫雷求解器，提供安全坐标分析"""
    
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.reset_board()
    
    def reset_board(self):
        """重置棋盘状态"""
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.revealed = set()  # 已揭示的位置
        self.flagged = set()  # 标记为地雷的位置
        self.neighbor_cache = {}  # 缓存坐标的邻居
        self.revealed_numbers = {}  # 缓存已揭示的数字 (x, y) -> 数字值
    
    def update_board(self, tiles: List[List[Optional[int]]]):
        """更新棋盘状态
        
        Args:
            tiles: 二维数组，包含已揭示的数字(0-8)、未揭示(None)和标记为地雷(-1)
        """
        # 完整更新棋盘状态
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                self.board[y][x] = tiles[y][x]
                if tiles[y][x] is not None:
                    self.revealed.add((x, y))
                    if tiles[y][x] == -1:  # 标记为地雷
                        self.flagged.add((x, y))
        
        # 重置缓存结构
        self.revealed_numbers.clear()
        self._prepare_caches()
    
    def _prepare_caches(self):
        """预先处理并填充缓存结构，提高后续计算速度"""
        # 收集所有已知数字
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) in self.revealed and self.board[y][x] is not None and self.board[y][x] >= 0:
                    # 记录已揭示的数字
                    self.revealed_numbers[(x, y)] = self.board[y][x]
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取指定位置的8个相邻位置"""
        # 使用缓存减少重复计算
        if (x, y) in self.neighbor_cache:
            return self.neighbor_cache[(x, y)]
        
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    neighbors.append((nx, ny))
        
        # 缓存结果
        self.neighbor_cache[(x, y)] = neighbors
        return neighbors
    
    def get_safe_coordinates(self) -> Set[Tuple[int, int]]:
        """获取所有确定安全的坐标集合
        
        Returns:
            Set[Tuple[int, int]]: 安全坐标集合
        """
        # 存储安全坐标
        safe_coordinates = set()
        
        # 检查棋盘是否为初始状态（没有揭示任何单元格）
        if not self.revealed:
            # 第一步始终选择中心位置
            center = self.board_size // 2
            safe_coordinates.add((center, center))
            return safe_coordinates
        
        # 遍历所有已揭示的数字单元格
        for (x, y), number in self.revealed_numbers.items():
            # 获取周围的未揭示格子
            unrevealed_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                 if (nx, ny) not in self.revealed]
            
            # 获取周围的已标记地雷格子
            flagged_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                               if (nx, ny) in self.flagged]
            
            # 规则1: 如果数字等于已标记地雷数，其余未揭示格子都是安全的
            if number == len(flagged_neighbors):
                for nx, ny in unrevealed_neighbors:
                    if (nx, ny) not in self.flagged:
                        safe_coordinates.add((nx, ny))
            
            # 规则2: 如果数字为0，所有相邻未揭示格子都是安全的
            elif number == 0:
                for nx, ny in unrevealed_neighbors:
                    safe_coordinates.add((nx, ny))
        
        # 确保不含已点击或已标记为地雷的格子
        safe_coordinates -= self.revealed
        safe_coordinates -= self.flagged
        
        return safe_coordinates

    def print_board_state(self):
        """打印当前棋盘状态，用于调试"""
        print("="*30)
        print("当前棋盘状态:")
        for y in range(self.board_size):
            row = []
            for x in range(self.board_size):
                if (x, y) in self.flagged:
                    row.append("F")  # 标记为地雷
                elif (x, y) not in self.revealed:
                    row.append("?")  # 未揭示
                elif self.board[y][x] == 0:
                    row.append(".")  # 已揭示，无地雷
                else:
                    row.append(str(self.board[y][x]))  # 已揭示，显示数字
            print(" ".join(row))
        print("="*30)
        print(f"已揭示格子数: {len(self.revealed)}")
        print(f"已标记地雷数: {len(self.flagged)}")
        print("="*30)

# 为兼容性保留DeterministicMinesweeperSolver类名
DeterministicMinesweeperSolver = MinesweeperSolver