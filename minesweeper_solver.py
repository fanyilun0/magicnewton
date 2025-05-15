import random
import numpy as np
from typing import List, Tuple, Optional, Set, Dict

class MinesweeperSolver:
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.reset_board()
        
    def reset_board(self):
        # Initialize the board, None means unknown, number means mines around, -1 means mine
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        # Record clicked positions
        self.clicked = set()
        # Mark potential mine positions
        self.potential_mines = set()
        # Mark safe positions
        self.safe_moves = set()
        # 概率图 - 记录每个格子是地雷的概率
        self.probability_map = np.zeros((self.board_size, self.board_size))
        # 记录上一次移动的位置
        self.last_move = None
        # 记录第一次点击的位置
        self.first_move = None
        
    def update_board(self, tiles: List[List[Optional[int]]]):
        """Update internal board based on API response"""
        old_board = [[self.board[y][x] for x in range(self.board_size)] for y in range(self.board_size)]
        
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if tiles[y][x] is not None:
                    self.board[y][x] = tiles[y][x]
                    self.clicked.add((x, y))
                    
                    # 如果这是一个新揭示的0，标记周围所有格子为安全
                    if tiles[y][x] == 0 and old_board[y][x] is None:
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) not in self.clicked and self.board[ny][nx] is None:
                                self.safe_moves.add((nx, ny))
        
        # 更新后分析棋盘
        self.analyze_board()
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get adjacent positions for a given position"""
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
        """Analyze board, mark potential mines and safe positions"""
        self.safe_moves = set([m for m in self.safe_moves if m not in self.clicked])
        new_potential_mines = set()
        self.probability_map = np.zeros((self.board_size, self.board_size))
        
        # 分析每个已知数字周围的未点击格子
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] is not None and self.board[y][x] > 0:
                    # 获取周围未点击的位置
                    unclicked_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                          if (nx, ny) not in self.clicked and self.board[ny][nx] is None]
                    mines_needed = self.board[y][x]
                    
                    # 如果周围未点击的格子数量等于需要的地雷数，那么这些都是地雷
                    if len(unclicked_neighbors) == mines_needed and mines_needed > 0:
                        for nx, ny in unclicked_neighbors:
                            new_potential_mines.add((nx, ny))
                            self.probability_map[ny][nx] = 1.0  # 100%是地雷
                    
                    # 检查已标记的地雷
                    marked_mines = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                   if (nx, ny) in self.potential_mines]
                    
                    # 如果已标记的地雷数量等于需要的地雷数，其余未点击的格子都是安全的
                    if len(marked_mines) == mines_needed and mines_needed > 0:
                        for nx, ny in unclicked_neighbors:
                            if (nx, ny) not in self.potential_mines:
                                self.safe_moves.add((nx, ny))
                                self.probability_map[ny][nx] = 0.0  # 0%是地雷
                    
                    # 特殊处理边缘格子（角落）
                    neighbors_count = len(self.get_neighbors(x, y))
                    if neighbors_count < 8:  # 这是边缘或角落
                        # 如果数字为1且在角落（只有3个邻居），那么至少有2个安全的格子
                        if self.board[y][x] == 1 and neighbors_count == 3:
                            # 选择一个作为地雷，其余为安全
                            if not marked_mines and not new_potential_mines.intersection(set(unclicked_neighbors)):
                                # 如果还没有标记地雷，随机选择一个作为可能的地雷
                                if unclicked_neighbors:
                                    potential_mine = random.choice(unclicked_neighbors)
                                    nx, ny = potential_mine
                                    self.probability_map[ny][nx] = 0.9  # 90%是地雷
                                    for nnx, nny in unclicked_neighbors:
                                        if (nnx, nny) != (nx, ny):
                                            self.safe_moves.add((nnx, nny))
                                            self.probability_map[nny][nnx] = 0.0  # 0%是地雷
                        
                        # 如果数字等于相邻格子数，那么所有相邻格子都是地雷
                        if self.board[y][x] == neighbors_count:
                            for nx, ny in unclicked_neighbors:
                                new_potential_mines.add((nx, ny))
                                self.probability_map[ny][nx] = 1.0  # 100%是地雷
                        
                        # 如果数字为0，那么所有相邻格子都是安全的
                        if self.board[y][x] == 0:
                            for nx, ny in unclicked_neighbors:
                                self.safe_moves.add((nx, ny))
                                self.probability_map[ny][nx] = 0.0  # 0%是地雷
                    
                    # 为未确定的格子计算地雷概率
                    unknown_count = len(unclicked_neighbors)
                    if unknown_count > 0:
                        remaining_mines = mines_needed - len(marked_mines)
                        if remaining_mines > 0:
                            prob = remaining_mines / unknown_count
                            for nx, ny in unclicked_neighbors:
                                if (nx, ny) not in new_potential_mines and (nx, ny) not in self.safe_moves:
                                    self.probability_map[ny][nx] += prob
        
        self.potential_mines = new_potential_mines
        
        # 如果没有找到安全的移动，尝试找到0值周围的格子（它们肯定是安全的）
        if not self.safe_moves:
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if self.board[y][x] == 0:
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) not in self.clicked and self.board[ny][nx] is None:
                                self.safe_moves.add((nx, ny))
                                self.probability_map[ny][nx] = 0.0  # 0%是地雷
        
        # 高级分析：比较相邻的数字信息
        self._advanced_analysis()
    
    def _advanced_analysis(self):
        """高级分析：比较相邻数字的信息来推断安全格子和地雷"""
        # 记录分析前的安全点和地雷点数量
        initial_safe_moves = len(self.safe_moves)
        initial_potential_mines = len(self.potential_mines)
        
        # 多次迭代分析以处理复杂情况
        for iteration in range(2):  # 增加迭代次数以捕获更多模式
            # 遍历所有已知数字
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if self.board[y][x] is None or self.board[y][x] <= 0:
                        continue
                        
                    # 获取这个数字周围的未知格子
                    unknown_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                       if (nx, ny) not in self.clicked and self.board[ny][nx] is None]
                    
                    # 获取这个数字周围已标记的地雷
                    marked_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                      if (nx, ny) in self.potential_mines]
                    
                    # 如果已标记的地雷数量等于数字，周围所有未知格子都是安全的
                    if len(marked_neighbors) == self.board[y][x] and len(unknown_neighbors) > 0:
                        for nx, ny in unknown_neighbors:
                            if (nx, ny) not in self.potential_mines:
                                self.safe_moves.add((nx, ny))
                                self.probability_map[ny][nx] = 0.0
                    
                    # 对于每个相邻的已知数字，比较它们的未知邻居
                    for nx, ny in self.get_neighbors(x, y):
                        if self.board[ny][nx] is None or self.board[ny][nx] <= 0 or (nx, ny) not in self.clicked:
                            continue
                            
                        # 获取相邻数字的未知邻居
                        neighbor_unknowns = [(ax, ay) for ax, ay in self.get_neighbors(nx, ny) 
                                           if (ax, ay) not in self.clicked and self.board[ay][ax] is None]
                        
                        # 获取相邻数字周围已标记的地雷
                        neighbor_marked = [(ax, ay) for ax, ay in self.get_neighbors(nx, ny) 
                                         if (ax, ay) in self.potential_mines]
                        
                        # 计算两个集合的差异
                        only_in_first = set(unknown_neighbors) - set(neighbor_unknowns)
                        only_in_second = set(neighbor_unknowns) - set(unknown_neighbors)
                        common = set(unknown_neighbors) & set(neighbor_unknowns)
                        
                        # 计算剩余需要找到的地雷数
                        remaining_first = self.board[y][x] - len(marked_neighbors)
                        remaining_second = self.board[ny][nx] - len(neighbor_marked)
                        
                        # 检测1-2-1模式 (横向或纵向)
                        if self.board[y][x] == 1 and self.board[ny][nx] == 2:
                            # 检查是否有第三个数字形成1-2-1模式
                            for third_x, third_y in self.get_neighbors(nx, ny):
                                if (third_x, third_y) in self.clicked and self.board[third_y][third_x] == 1:
                                    # 确认1-2-1模式，检查数字是否在一条线上
                                    if self._check_aligned(x, y, nx, ny, third_x, third_y):
                                        # 标记2上方和下方的格子为地雷
                                        dx, dy = x - nx, y - ny  # 方向
                                        perp_dx, perp_dy = -dy, dx  # 垂直方向
                                        
                                        # 检查垂直方向的两个格子
                                        mine1_x, mine1_y = nx + perp_dx, ny + perp_dy
                                        mine2_x, mine2_y = nx - perp_dx, ny - perp_dy
                                        
                                        # 如果这些位置在棋盘上且未点击，标记为地雷
                                        if self._is_valid_cell(mine1_x, mine1_y):
                                            self.potential_mines.add((mine1_x, mine1_y))
                                            self.probability_map[mine1_y][mine1_x] = 1.0
                                        
                                        if self._is_valid_cell(mine2_x, mine2_y):
                                            self.potential_mines.add((mine2_x, mine2_y))
                                            self.probability_map[mine2_y][mine2_x] = 1.0
                        
                        # 检测1-1-1模式 (三角形)
                        elif self.board[y][x] == 1 and self.board[ny][nx] == 1:
                            # 检查是否有第三个数字"1"形成三角形
                            for third_x, third_y in self.get_neighbors(nx, ny):
                                if (third_x, third_y) in self.clicked and (third_x, third_y) != (x, y) and self.board[third_y][third_x] == 1:
                                    # 确认三角形模式
                                    if self._is_triangle(x, y, nx, ny, third_x, third_y):
                                        # 找到三个数字"1"的公共未知邻居，应该是地雷
                                        mine_candidates = set()
                                        for pos in self.get_neighbors(x, y):
                                            if pos in self.get_neighbors(nx, ny) and pos in self.get_neighbors(third_x, third_y):
                                                mine_candidates.add(pos)
                                        
                                        for mx, my in mine_candidates:
                                            if self._is_valid_cell(mx, my):
                                                self.potential_mines.add((mx, my))
                                                self.probability_map[my][mx] = 1.0
                        
                        # 1. 两个数字完全包含关系
                        # 如果第一个数字周围的未知格子完全包含于第二个数字周围的未知格子
                        if set(unknown_neighbors).issubset(set(neighbor_unknowns)):
                            # 并且剩余需要找到的地雷数不同
                            if remaining_first < remaining_second:
                                # 那么只在第二个集合中的格子都是地雷
                                for ax, ay in only_in_second:
                                    if self._is_valid_cell(ax, ay) and remaining_second - remaining_first == len(only_in_second):
                                        self.potential_mines.add((ax, ay))
                                        self.probability_map[ay][ax] = 1.0
                        
                        # 同理，如果第二个数字周围的未知格子完全包含于第一个数字周围的未知格子
                        elif set(neighbor_unknowns).issubset(set(unknown_neighbors)):
                            # 并且剩余需要找到的地雷数不同
                            if remaining_second < remaining_first:
                                # 那么只在第一个集合中的格子都是地雷
                                for ax, ay in only_in_first:
                                    if self._is_valid_cell(ax, ay) and remaining_first - remaining_second == len(only_in_first):
                                        self.potential_mines.add((ax, ay))
                                        self.probability_map[ay][ax] = 1.0
                        
                        # 2. 数字差分析
                        # 如果两个数字的剩余未知地雷数相等，但未知格子不完全相同
                        elif remaining_first == remaining_second and len(only_in_first) > 0 and len(only_in_second) > 0:
                            if len(only_in_first) == len(only_in_second):  # 数量相等
                                # 一个集合中的格子都是地雷，另一个集合中的格子都是安全的
                                # 但由于无法确定哪个是哪个，只能增加概率
                                prob = 0.5  # 50%概率是地雷
                                for ax, ay in only_in_first:
                                    if self._is_valid_cell(ax, ay):
                                        self.probability_map[ay][ax] = max(self.probability_map[ay][ax], prob)
                                for ax, ay in only_in_second:
                                    if self._is_valid_cell(ax, ay):
                                        self.probability_map[ay][ax] = max(self.probability_map[ay][ax], prob)
                            
                            # 如果两个集合的独有部分大小相等，且共同部分不为空
                            if len(only_in_first) == len(only_in_second) and len(common) > 0:
                                # 共同部分中的格子一定是安全的
                                for ax, ay in common:
                                    if self._is_valid_cell(ax, ay):
                                        self.safe_moves.add((ax, ay))
                                        self.probability_map[ay][ax] = 0.0
                        
                        # 如果第一个数字比第二个数字大，且第二个数字的所有未知邻居都是第一个数字的未知邻居
                        if remaining_first > remaining_second and len(only_in_second) == 0 and len(only_in_first) > 0:
                            if remaining_first - remaining_second == len(only_in_first):
                                for ax, ay in only_in_first:
                                    if self._is_valid_cell(ax, ay):
                                        self.potential_mines.add((ax, ay))
                                        self.probability_map[ay][ax] = 1.0
                            
                        # 如果第二个数字比第一个数字大，且第一个数字的所有未知邻居都是第二个数字的未知邻居
                        elif remaining_second > remaining_first and len(only_in_first) == 0 and len(only_in_second) > 0:
                            if remaining_second - remaining_first == len(only_in_second):
                                for ax, ay in only_in_second:
                                    if self._is_valid_cell(ax, ay):
                                        self.potential_mines.add((ax, ay))
                                        self.probability_map[ay][ax] = 1.0
            
            # 如果本轮迭代没有找到新的安全点或地雷点，停止迭代
            if len(self.safe_moves) == initial_safe_moves and len(self.potential_mines) == initial_potential_mines:
                break
            
            # 更新迭代前的计数
            initial_safe_moves = len(self.safe_moves)
            initial_potential_mines = len(self.potential_mines)
    
    def _is_valid_cell(self, x: int, y: int) -> bool:
        """检查坐标是否有效且未点击"""
        return (0 <= x < self.board_size and 0 <= y < self.board_size and 
                (x, y) not in self.clicked and self.board[y][x] is None)
    
    def _check_aligned(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int) -> bool:
        """检查三个点是否在一条直线上（1-2-1模式检测）"""
        # 检查三点共线
        # 方法1：斜率比较 (y3-y1)/(x3-x1) == (y2-y1)/(x2-x1)
        # 防止除以零，转换为乘法形式
        return (y3-y1)*(x2-x1) == (y2-y1)*(x3-x1)
    
    def _is_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int) -> bool:
        """检查三个点是否构成三角形（三个数字1的模式检测）"""
        # 确保三点不共线
        return not self._check_aligned(x1, y1, x2, y2, x3, y3)
    
    def get_next_move(self) -> Tuple[int, int]:
        """Get the next position to click"""
        # 如果是第一步，选择中间位置（通常地雷概率较低）
        if all(self.board[y][x] is None for y in range(self.board_size) for x in range(self.board_size)):
            # 第一步总是选择中间位置
            center = self.board_size // 2
            self.first_move = (center, center)
            self.last_move = self.first_move
            return self.first_move
        
        # 确保棋盘分析为最新
        self.analyze_board()
        
        # 1. 如果有已知安全的位置，优先选择
        if self.safe_moves:
            safe_list = list(self.safe_moves)
            
            # 优先选择靠近已点击区域的安全格子，以扩大已知区域
            for x, y in safe_list:
                # 检查是否靠近数字0（最安全的情况）
                for nx, ny in self.get_neighbors(x, y):
                    if (nx, ny) in self.clicked and self.board[ny][nx] == 0:
                        self.safe_moves.remove((x, y))
                        self.last_move = (x, y)
                        return (x, y)
            
            # 其次选择靠近已点击区域的安全格子
            for x, y in safe_list:
                for nx, ny in self.get_neighbors(x, y):
                    if (nx, ny) in self.clicked and self.board[ny][nx] is not None:
                        self.safe_moves.remove((x, y))
                        self.last_move = (x, y)
                        return (x, y)
            
            # 如果上述都不满足，选择任一安全格子
            move = safe_list[0]
            self.safe_moves.remove(move)
            self.last_move = move
            return move
        
        # 2. 如果没有确定安全的位置，使用概率策略
        candidates = []
        # 找出所有未点击且不在潜在地雷列表中的位置
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and (x, y) not in self.potential_mines:
                    # 计算安全度 (1 - 地雷概率)
                    safety = 1.0 - self.probability_map[y][x]
                    
                    # 加入候选列表，包含位置和安全度
                    candidates.append(((x, y), safety))
        
        if candidates:
            # 按安全度从高到低排序
            candidates.sort(key=lambda item: item[1], reverse=True)
            
            # 2.1 如果存在安全度极高的格子，直接选择它
            if candidates[0][1] >= 0.95:  # 安全度95%以上
                best_move = candidates[0][0]
                self.last_move = best_move
                return best_move
            
            # 2.2 找出安全度接近最高值的所有候选点
            high_safety = candidates[0][1] - 0.1  # 安全度阈值
            good_candidates = [pos for pos, safety in candidates if safety >= high_safety]
            
            # 2.3 在高安全度候选点中，优先选择靠近已知数字的点
            best_moves = []
            best_score = -1
            
            for x, y in good_candidates:
                score = 0
                has_number_neighbor = False
                # 统计周围已知数字的总量和关联信息
                for nx, ny in self.get_neighbors(x, y):
                    if (nx, ny) in self.clicked and self.board[ny][nx] is not None:
                        if self.board[ny][nx] > 0:  # 是数字
                            has_number_neighbor = True
                            score += 1  # 数字邻居增加分数
                        elif self.board[ny][nx] == 0:  # 0更安全
                            score += 2  # 0邻居分数更高
                
                if has_number_neighbor and score > best_score:
                    best_score = score
                    best_moves = [(x, y)]
                elif has_number_neighbor and score == best_score:
                    best_moves.append((x, y))
            
            # 如果有靠近已知数字的优质候选点，从中选择一个
            if best_moves:
                move = random.choice(best_moves)
                self.last_move = move
                return move
            
            # 如果没有靠近已知数字的点，从安全度高的候选点中随机选择
            if good_candidates:
                move = random.choice(good_candidates)
                self.last_move = move
                return move
        
        # 3. 如果没有安全的候选点，尝试边缘处理
        edge_tiles = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and self.board[y][x] is None and (x, y) not in self.potential_mines:
                    # 检查是否是边缘（至少有一个邻居已被点击）
                    for nx, ny in self.get_neighbors(x, y):
                        if (nx, ny) in self.clicked:
                            # 计算风险评分
                            risk = self.probability_map[y][x]
                            # 统计邻居信息
                            neighbor_count = sum(1 for nx, ny in self.get_neighbors(x, y) if (nx, ny) in self.clicked)
                            # 邻居越多，信息越丰富，风险评估越准确
                            info_factor = neighbor_count / 8.0
                            weighted_risk = risk * (1.0 - 0.3 * info_factor)  # 邻居多的格子风险稍微降低
                            edge_tiles.append(((x, y), weighted_risk))
                            break
        
        if edge_tiles:
            # 按风险从低到高排序
            edge_tiles.sort(key=lambda item: item[1])
            
            # 如果存在风险极低的格子，选择它
            if edge_tiles[0][1] < 0.2:  # 风险低于20%
                best_move = edge_tiles[0][0]
                self.last_move = best_move
                return best_move
        
        # 4. 最后的后备策略：选择角落或边缘
        corner_tiles = []  # 角落
        edge_only_tiles = []  # 边缘（非角落）
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and self.board[y][x] is None and (x, y) not in self.potential_mines:
                    neighbor_count = len(self.get_neighbors(x, y))
                    if neighbor_count == 3:  # 角落
                        corner_tiles.append((x, y))
                    elif neighbor_count < 8:  # 边缘
                        edge_only_tiles.append((x, y))
        
        # 优先选择角落
        if corner_tiles:
            move = random.choice(corner_tiles)
            self.last_move = move
            return move
        
        # 其次选择边缘
        if edge_only_tiles:
            move = random.choice(edge_only_tiles)
            self.last_move = move
            return move
        
        # 5. 最终后备：在所有未点击格子中选择风险最低的一个
        lowest_risk_move = None
        lowest_risk = float('inf')
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and self.board[y][x] is None:
                    risk = self.probability_map[y][x]
                    if risk < lowest_risk:
                        lowest_risk = risk
                        lowest_risk_move = (x, y)
        
        if lowest_risk_move:
            self.last_move = lowest_risk_move
            return lowest_risk_move
        
        # 如果以上都失败，随机选择一个未点击的位置
        available_moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked:
                    available_moves.append((x, y))
        
        if not available_moves:
            raise ValueError("没有可用的移动位置")
        
        move = random.choice(available_moves)
        self.last_move = move
        return move

    def get_safe_coordinates(self) -> List[Tuple[int, int]]:
        """返回所有确定安全的坐标点数组
        
        此方法分析当前棋盘状态，返回一个包含所有被认为100%安全的坐标点的列表。
        如果没有确定安全的点，则返回概率最低的几个点。
        
        返回:
            List[Tuple[int, int]]: 安全坐标点列表，按安全度从高到低排序
        """
        # 确保棋盘状态是最新的
        self.analyze_board()
        
        result = []
        
        # 1. 首先收集所有已知安全的位置
        if self.safe_moves:
            result.extend(list(self.safe_moves))
        
        # 2. 如果没有确定安全的位置，寻找未点击且不在潜在地雷列表中的位置
        if not result:
            candidates = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked and (x, y) not in self.potential_mines:
                        # 计算安全度评分 (概率越低越安全)
                        safety_score = 1.0 - self.probability_map[y][x]
                        candidates.append(((x, y), safety_score))
            
            # 按安全度排序并选择最安全的位置
            if candidates:
                # 对候选点按安全度从高到低排序
                sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
                # 选择安全度最高的10个点或所有点(如果不足10个)
                result.extend([pos for pos, _ in sorted_candidates[:min(10, len(sorted_candidates))]])
        
        # 3. 如果仍然没有找到安全的位置，尝试返回边缘的格子
        if not result:
            edge_tiles = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked and self.board[y][x] is None:
                        # 检查是否是边缘(至少有一个邻居已被点击)
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) in self.clicked:
                                risk = self.probability_map[y][x]
                                edge_tiles.append(((x, y), risk))
                                break
            
            if edge_tiles:
                # 按风险从低到高排序
                sorted_edges = sorted(edge_tiles, key=lambda x: x[1])
                # 选择风险最低的几个点
                result.extend([pos for pos, _ in sorted_edges[:min(5, len(sorted_edges))]])
        
        # 4. 最后的后备策略：如果仍然没有找到，优先返回角落和边缘
        if not result:
            corner_and_edges = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked and self.board[y][x] is None:
                        # 检查是否是角落或边缘(邻居数少于8)
                        neighbor_count = len(self.get_neighbors(x, y))
                        if neighbor_count < 8:
                            corner_and_edges.append((x, y))
            
            if corner_and_edges:
                # 随机选择最多5个角落或边缘点
                import random
                sample_size = min(5, len(corner_and_edges))
                result.extend(random.sample(corner_and_edges, sample_size))
            else:
                # 如果没有角落或边缘，选择任意未点击的点
                available_moves = []
                for y in range(self.board_size):
                    for x in range(self.board_size):
                        if (x, y) not in self.clicked and self.board[y][x] is None:
                            available_moves.append((x, y))
                
                if available_moves:
                    # 随机选择最多5个点
                    import random
                    sample_size = min(5, len(available_moves))
                    result.extend(random.sample(available_moves, sample_size))
        
        return result
        
    def get_safe_coordinates_with_probability(self) -> List[Tuple[Tuple[int, int], float]]:
        """返回安全坐标点及其安全概率
        
        返回:
            List[Tuple[Tuple[int, int], float]]: 安全坐标点列表及其安全概率(0-1)，按安全度从高到低排序
        """
        # 确保棋盘状态是最新的
        self.analyze_board()
        
        result = []
        
        # 收集所有可能的点及其安全概率
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and self.board[y][x] is None:
                    # 计算安全概率 (1 - 地雷概率)
                    safe_prob = 1.0 - self.probability_map[y][x]
                    
                    # 如果在安全列表中，安全概率为1.0
                    if (x, y) in self.safe_moves:
                        safe_prob = 1.0
                    
                    # 如果在地雷列表中，安全概率为0.0
                    if (x, y) in self.potential_mines:
                        safe_prob = 0.0
                    
                    result.append(((x, y), safe_prob))
        
        # 按安全概率从高到低排序
        return sorted(result, key=lambda x: x[1], reverse=True)

class DeterministicMinesweeperSolver:
    """确定性的扫雷安全坐标分析器"""
    
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.reset_board()
    
    def reset_board(self):
        """重置棋盘状态"""
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.flagged = set()  # 标记为地雷的位置
        self.revealed = set()  # 已揭示的位置
    
    def update_board(self, tiles: List[List[Optional[int]]]):
        """更新棋盘状态
        
        Args:
            tiles: 二维数组，包含已揭示的数字(0-8)、未揭示(None)和标记为地雷(-1)
        """
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if tiles[y][x] is not None:
                    self.board[y][x] = tiles[y][x]
                    self.revealed.add((x, y))
                    if tiles[y][x] == -1:  # 标记为地雷
                        self.flagged.add((x, y))
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取指定位置的8个相邻位置"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    neighbors.append((nx, ny))
        return neighbors
    
    def get_safe_coordinates(self) -> Set[Tuple[int, int]]:
        """获取所有确定安全的坐标集合
        
        Returns:
            Set[Tuple[int, int]]: 安全坐标集合
        """
        safe_coordinates = set()
        
        # 遍历所有已揭示的数字单元格
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] is None or self.board[y][x] < 0:
                    continue
                
                # 获取相邻的未揭示单元格
                unrevealed_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                      if (nx, ny) not in self.revealed]
                
                # 获取相邻的已标记地雷
                flagged_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                   if (nx, ny) in self.flagged]
                
                # 规则1: 如果数字等于已标记地雷数，其余未揭示格子都是安全的
                if len(flagged_neighbors) == self.board[y][x]:
                    for nx, ny in unrevealed_neighbors:
                        if (nx, ny) not in self.flagged:
                            safe_coordinates.add((nx, ny))
                
                # 规则2: 如果数字减去已标记地雷数等于未揭示格子数，所有未揭示格子都是地雷
                remaining_mines = self.board[y][x] - len(flagged_neighbors)
                if remaining_mines == len(unrevealed_neighbors):
                    # 这种情况下没有安全的格子
                    continue
                
                # 规则3: 如果数字为0，所有相邻未揭示格子都是安全的
                if self.board[y][x] == 0:
                    for nx, ny in unrevealed_neighbors:
                        if (nx, ny) not in self.flagged:
                            safe_coordinates.add((nx, ny))
        
        return safe_coordinates
    
    def get_mine_coordinates(self) -> Set[Tuple[int, int]]:
        """获取所有确定是地雷的坐标集合
        
        Returns:
            Set[Tuple[int, int]]: 地雷坐标集合
        """
        mine_coordinates = set()
        
        # 遍历所有已揭示的数字单元格
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] is None or self.board[y][x] < 0:
                    continue
                
                # 获取相邻的未揭示单元格
                unrevealed_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                      if (nx, ny) not in self.revealed]
                
                # 获取相邻的已标记地雷
                flagged_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                   if (nx, ny) in self.flagged]
                
                # 如果数字减去已标记地雷数等于未揭示格子数，所有未揭示格子都是地雷
                remaining_mines = self.board[y][x] - len(flagged_neighbors)
                if remaining_mines == len(unrevealed_neighbors):
                    for nx, ny in unrevealed_neighbors:
                        if (nx, ny) not in self.flagged:
                            mine_coordinates.add((nx, ny))
        
        return mine_coordinates 