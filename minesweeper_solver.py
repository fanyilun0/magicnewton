import random
import time
from typing import List, Tuple, Optional, Set, Dict, Any, DefaultDict
from collections import defaultdict

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
        self.additional_safe = set()  # 通过高级推理找到的安全位置
        self.additional_mines = set()  # 通过高级推理找到的地雷位置
        self.cached_safe_coords = set()  # 缓存已计算的安全坐标
        self.cached_mine_coords = set()  # 缓存已计算的地雷坐标
        self.last_analyzed_board = None  # 上次分析的棋盘状态
        self.board_hash = None  # 棋盘哈希值，用于判断棋盘是否变化
        
        # 优化 - 添加更多缓存结构
        self.neighbor_cache = {}  # 缓存坐标的邻居
        self.revealed_numbers = {}  # 缓存已揭示的数字 (x, y) -> 数字值
        self.unrevealed_map = defaultdict(set)  # 未揭示格子 -> 周围的已知数字坐标集合
        self.number_to_unrevealed = {}  # 已揭示数字 -> 其周围未揭示格子列表
    
    def update_board(self, tiles: List[List[Optional[int]]]):
        """更新棋盘状态
        
        Args:
            tiles: 二维数组，包含已揭示的数字(0-8)、未揭示(None)和标记为地雷(-1)
        """
        old_revealed_count = len(self.revealed)
        old_board_hash = self._compute_board_hash(self.board)
        
        # 完整更新棋盘状态，包括更新 None 值
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                self.board[y][x] = tiles[y][x]
                if tiles[y][x] is not None:
                    self.revealed.add((x, y))
                    if tiles[y][x] == -1:  # 标记为地雷
                        self.flagged.add((x, y))
        
        # 计算新的棋盘哈希值
        new_board_hash = self._compute_board_hash(self.board)
        
        # 如果棋盘状态有变化，清空推理缓存
        if len(self.revealed) > old_revealed_count or old_board_hash != new_board_hash:
            self.additional_safe.clear()
            self.additional_mines.clear()
            self.cached_safe_coords.clear()
            self.cached_mine_coords.clear()
            self.board_hash = new_board_hash
            
            # 重置优化用的缓存结构
            self.revealed_numbers.clear()
            self.unrevealed_map.clear()
            self.number_to_unrevealed.clear()
            
            # 预先填充缓存结构
            self._prepare_caches()
            
            # 如果有新的格子被点击，自动进行高级分析
            self._analyze_number_relations()
    
    def _prepare_caches(self):
        """预先处理并填充缓存结构，提高后续计算速度"""
        # 收集所有已知数字和未揭示格子的关系
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) in self.revealed and self.board[y][x] is not None and self.board[y][x] >= 0:
                    # 记录已揭示的数字
                    self.revealed_numbers[(x, y)] = self.board[y][x]
                    
                    # 获取该数字周围的未揭示格子
                    unrevealed_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                          if (nx, ny) not in self.revealed]
                    
                    # 建立数字和周围未揭示格子的映射
                    self.number_to_unrevealed[(x, y)] = unrevealed_neighbors
                    
                    # 建立未揭示格子和周围数字的映射
                    for nx, ny in unrevealed_neighbors:
                        self.unrevealed_map[(nx, ny)].add((x, y))
    
    def _compute_board_hash(self, board: List[List[Optional[int]]]) -> str:
        """计算棋盘的哈希值，用于判断棋盘是否变化
        
        Args:
            board: 棋盘状态
            
        Returns:
            棋盘哈希值
        """
        # 简单的哈希方法，将棋盘状态转换为字符串
        return str([(x, y, board[y][x]) for y in range(self.board_size) for x in range(self.board_size) if board[y][x] is not None])
    
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
    
    def _analyze_number_relations(self):
        """分析数字之间的关系，实现更多的推理规则"""
        # 如果缓存结构为空，先准备缓存
        if not self.revealed_numbers:
            self._prepare_caches()
            
        # 记录分析前的数量
        initial_safe_count = len(self.additional_safe)
        initial_mine_count = len(self.additional_mines)
        
        # 检查棋盘是否为初始状态（没有揭示任何单元格）
        if not self.revealed:
            return
        
        # 1. 基本规则：处理单个数字的周围格子
        for (x, y), number in self.revealed_numbers.items():
            # 获取周围的未揭示格子
            unrevealed = self.number_to_unrevealed.get((x, y), [])
            
            # 获取周围的已标记地雷
            flagged = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                       if (nx, ny) in self.flagged]
            
            # 剩余地雷数
            remaining_mines = number - len(flagged)
            
            # 如果剩余地雷数等于未揭示格子数，则所有未揭示格子都是地雷
            if remaining_mines > 0 and len(unrevealed) == remaining_mines:
                for nx, ny in unrevealed:
                    if (nx, ny) not in self.flagged:
                        self.additional_mines.add((nx, ny))
            
            # 如果剩余地雷数为0，则所有未揭示格子都是安全的
            elif remaining_mines == 0 and unrevealed:
                for nx, ny in unrevealed:
                    self.additional_safe.add((nx, ny))
        
        # 2. 扫描数字对关系
        analyzed_pairs = set()  # 已分析的数字对，避免重复分析
        
        for (x1, y1), number1 in self.revealed_numbers.items():
            # 获取第一个数字周围的未揭示格子
            first_unrevealed = set(self.number_to_unrevealed.get((x1, y1), []))
            
            # 如果没有未揭示格子，跳过
            if not first_unrevealed:
                continue
            
            # 获取第一个数字周围已标记的地雷
            first_flagged = set((nx, ny) for nx, ny in self.get_neighbors(x1, y1) 
                              if (nx, ny) in self.flagged)
            
            # 第一个数字周围的剩余地雷数
            first_remaining = number1 - len(first_flagged)
            
            # 获取可能与此数字有关系的其他数字（共享未揭示格子的数字）
            related_numbers = set()
            for nx, ny in first_unrevealed:
                for number_pos in self.unrevealed_map.get((nx, ny), set()):
                    if number_pos != (x1, y1):
                        related_numbers.add(number_pos)
            
            # 对每个相关数字进行分析
            for (x2, y2) in related_numbers:
                # 避免重复分析同一对数字
                if ((x1, y1), (x2, y2)) in analyzed_pairs or ((x2, y2), (x1, y1)) in analyzed_pairs:
                    continue
                analyzed_pairs.add(((x1, y1), (x2, y2)))
                
                number2 = self.revealed_numbers[(x2, y2)]
                
                # 获取第二个数字周围的未揭示格子
                second_unrevealed = set(self.number_to_unrevealed.get((x2, y2), []))
                
                # 获取第二个数字周围已标记的地雷
                second_flagged = set((nx, ny) for nx, ny in self.get_neighbors(x2, y2) 
                                   if (nx, ny) in self.flagged)
                
                # 第二个数字周围的剩余地雷数
                second_remaining = number2 - len(second_flagged)
                
                # 计算两个数字的未揭示单元格的差异
                only_in_first = first_unrevealed - second_unrevealed
                only_in_second = second_unrevealed - first_unrevealed
                common = first_unrevealed & second_unrevealed
                
                # 规则1: 如果第一个数字的剩余地雷数等于第二个数字的剩余地雷数,
                # 并且它们有不同的未揭示单元格，那么它们的不同部分必须包含相等数量的地雷
                if first_remaining == second_remaining and only_in_first and only_in_second:
                    # 不同部分的数量相等，且等于剩余地雷数，则公共部分都是安全的
                    if len(only_in_first) == len(only_in_second) and len(common) > 0:
                        # 共同部分必须都是安全的
                        for pos in common:
                            self.additional_safe.add(pos)
                
                # 规则2: 如果第一个数字是第二个数字的超集(拥有更多的未揭示单元格)
                if second_unrevealed.issubset(first_unrevealed) and second_unrevealed:
                    # 如果第一个数字的剩余地雷数大于第二个数字的剩余地雷数
                    if first_remaining > second_remaining:
                        # 那么第一个数字特有的未揭示格子一定包含 (first_remaining - second_remaining) 个地雷
                        diff = first_remaining - second_remaining
                        if len(only_in_first) == diff:
                            # 所有只在第一个数字中的未揭示格子都是地雷
                            for pos in only_in_first:
                                self.additional_mines.add(pos)
                        # 公共格子中不可能有地雷
                        elif len(only_in_first) > diff and second_remaining == 0:
                            for pos in common:
                                self.additional_safe.add(pos)
                
                # 规则3: 如果第二个数字是第一个数字的超集(拥有更多的未揭示单元格)
                if first_unrevealed.issubset(second_unrevealed) and first_unrevealed:
                    # 如果第二个数字的剩余地雷数大于第一个数字的剩余地雷数
                    if second_remaining > first_remaining:
                        # 那么第二个数字特有的未揭示格子一定包含 (second_remaining - first_remaining) 个地雷
                        diff = second_remaining - first_remaining
                        if len(only_in_second) == diff:
                            # 所有只在第二个数字中的未揭示格子都是地雷
                            for pos in only_in_second:
                                self.additional_mines.add(pos)
                        # 公共格子中不可能有地雷
                        elif len(only_in_second) > diff and first_remaining == 0:
                            for pos in common:
                                self.additional_safe.add(pos)
        
        # 移除可能重复的坐标
        self.additional_mines -= self.flagged
        self.additional_safe -= self.revealed
        
        # 确保安全坐标和地雷坐标不重叠
        self.additional_safe -= self.additional_mines
        
        # 更新标记
        self.flagged.update(self.additional_mines)
        
        # 如果有新的发现，继续分析
        if len(self.additional_safe) > initial_safe_count or len(self.additional_mines) > initial_mine_count:
            # 再次分析，可能会发现更多的安全格子和地雷
            self._analyze_number_relations()
    
    def get_safe_coordinates(self) -> Set[Tuple[int, int]]:
        """获取所有确定安全的坐标集合
        
        Returns:
            Set[Tuple[int, int]]: 安全坐标集合
        """
        # 如果已经有缓存的安全坐标，直接返回
        if self.cached_safe_coords:
            return self.cached_safe_coords
        
        # 如果缓存结构为空，先准备缓存
        if not self.revealed_numbers and self.revealed:
            self._prepare_caches()
        
        # 存储安全坐标
        safe_coordinates = set()
        
        # 检查棋盘是否为初始状态（没有揭示任何单元格）
        if not self.revealed:
            # 第一步始终选择中心位置
            center = self.board_size // 2
            safe_coordinates.add((center, center))
            self.cached_safe_coords = safe_coordinates
            return safe_coordinates
        
        # 添加通过高级推理找到的安全位置
        safe_coordinates.update(self.additional_safe)
        
        # 遍历所有已揭示的数字单元格
        for (x, y), number in self.revealed_numbers.items():
            # 获取周围的未揭示格子和已标记地雷格子
            unrevealed_neighbors = self.number_to_unrevealed.get((x, y), [])
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
        
        # 确保安全坐标和地雷坐标不重叠
        safe_coordinates -= self.additional_mines
        
        # 缓存计算结果
        self.cached_safe_coords = safe_coordinates
        
        return safe_coordinates

    def get_mine_coordinates(self) -> Set[Tuple[int, int]]:
        """获取所有确定是地雷的坐标集合
        
        Returns:
            Set[Tuple[int, int]]: 地雷坐标集合
        """
        # 如果已经有缓存的地雷坐标，直接返回
        if self.cached_mine_coords:
            return self.cached_mine_coords
        
        # 分析可能还未执行过
        if not self.additional_mines and self.revealed:
            self._analyze_number_relations()
        
        # 存储地雷坐标
        mine_coordinates = set(self.additional_mines)
        
        # 如果缓存结构为空，先准备缓存
        if not self.revealed_numbers and self.revealed:
            self._prepare_caches()
        
        # 遍历所有已揭示的数字单元格
        for (x, y), number in self.revealed_numbers.items():
            # 获取周围的未揭示格子和已标记地雷格子
            unrevealed_neighbors = self.number_to_unrevealed.get((x, y), [])
            flagged_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                               if (nx, ny) in self.flagged]
            
            # 如果数字减去已标记地雷数等于未揭示格子数，所有未揭示格子都是地雷
            remaining_mines = number - len(flagged_neighbors)
            if remaining_mines == len(unrevealed_neighbors) and remaining_mines > 0:
                for nx, ny in unrevealed_neighbors:
                    if (nx, ny) not in self.flagged:
                        mine_coordinates.add((nx, ny))
        
        # 确保不含已标记为地雷的格子（避免重复）
        mine_coordinates -= self.flagged
        
        # 缓存计算结果
        self.cached_mine_coords = mine_coordinates
        
        return mine_coordinates

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
        print(f"推理安全格子数: {len(self.additional_safe)}")
        print(f"推理地雷格子数: {len(self.additional_mines)}")
        print("="*30)

# 为兼容性保留DeterministicMinesweeperSolver类名
DeterministicMinesweeperSolver = MinesweeperSolver
