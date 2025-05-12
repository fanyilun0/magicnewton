import numpy as np
import random

def get_safe_moves(board):
    """
    工具函数：接收10*10的二维棋盘数据，计算并返回安全的坐标点列表
    
    参数:
    board -- 10*10的二维数组，表示当前棋盘状态
             None表示未知格子，数字表示周围地雷数量
    
    返回:
    list -- 安全坐标点列表，每个坐标点为(x, y)元组
    
    使用示例:
    ```python
    # 提供当前棋盘状态
    current_board = [
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, 1, None, None, None, None, None],
        [None, None, None, None, None, None, 1, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None]
    ]
    
    # 获取安全的坐标点列表
    safe_coordinates = get_safe_moves(current_board)
    
    # 选择第一个安全坐标点进行点击
    if safe_coordinates:
        x, y = safe_coordinates[0]
        print(f"下一步点击坐标: ({x}, {y})")
    ```
    """
    solver = MinesweeperSolver()
    return solver.get_safe_coordinates(board)

class MinesweeperSolver:
    """
    扫雷游戏解答器类，用于分析棋盘状态并提供安全的点击位置
    
    主要功能:
    1. 分析棋盘状态，计算每个格子是地雷的概率
    2. 提供下一步最佳的点击位置
    3. 返回安全的坐标点列表
    """
    
    def __init__(self):
        self.board_size = 10
        self.known_board = np.full((self.board_size, self.board_size), None)
        self.probability_map = np.zeros((self.board_size, self.board_size))
        self.visited = set()
        self.safe_moves = set()
        self.potential_mines = set()  # 可能是地雷的位置
        self.last_move = None  # 记录上一次的移动
        
    def update_board(self, new_board):
        """更新当前已知的棋盘状态"""
        old_board = self.known_board.copy()
        self.known_board = np.array(new_board)
        
        # 检查新的数字，用于更精确地分析
        for i in range(self.board_size):
            for j in range(self.board_size):
                # 如果这个位置是新揭示的数字
                if old_board[i, j] is None and isinstance(self.known_board[i, j], (int, float)):
                    # 如果是0，标记周围所有格子为安全
                    if self.known_board[i, j] == 0:
                        for ni, nj in self._get_neighbors(i, j):
                            if self.known_board[ni, nj] is None:
                                self.safe_moves.add((ni, nj))
        
        # 更新后重新计算概率
        self.calculate_probabilities()
        
    def calculate_probabilities(self):
        """计算每个格子是地雷的概率"""
        self.probability_map = np.zeros((self.board_size, self.board_size))
        self.potential_mines.clear()  # 清除旧的潜在地雷标记
        
        # 标记已知数字周围的未知格子
        for i in range(self.board_size):
            for j in range(self.board_size):
                if isinstance(self.known_board[i, j], (int, float)) and self.known_board[i, j] > 0:
                    self._analyze_cell(i, j)
        
        # 高级分析：查找确定是地雷的格子
        self._advanced_analysis()
        
    def _analyze_cell(self, i, j):
        """分析一个已知数字格子周围的情况"""
        if not isinstance(self.known_board[i, j], (int, float)) or self.known_board[i, j] <= 0:
            return
            
        # 获取周围的未知格子
        unknown_cells = []
        for ni, nj in self._get_neighbors(i, j):
            if self.known_board[ni, nj] is None:
                unknown_cells.append((ni, nj))
        
        # 如果周围有未知格子，更新它们的概率
        if unknown_cells:
            # 数字表示周围地雷数量
            mine_probability = self.known_board[i, j] / len(unknown_cells)
            for ni, nj in unknown_cells:
                self.probability_map[ni, nj] += mine_probability
                
            # 如果数字等于周围未知格子数量，所有未知格子都是地雷
            if self.known_board[i, j] == len(unknown_cells):
                for ni, nj in unknown_cells:
                    self.potential_mines.add((ni, nj))
                    
            # 如果数字为0，周围所有格子都是安全的
            elif self.known_board[i, j] == 0:
                for ni, nj in unknown_cells:
                    self.safe_moves.add((ni, nj))
    
    def _advanced_analysis(self):
        """高级分析：比较相邻数字的信息来推断安全格子和地雷"""
        # 遍历所有已知数字
        for i in range(self.board_size):
            for j in range(self.board_size):
                if not isinstance(self.known_board[i, j], (int, float)) or self.known_board[i, j] <= 0:
                    continue
                    
                # 获取这个数字周围的未知格子
                unknown_neighbors = [(ni, nj) for ni, nj in self._get_neighbors(i, j) 
                                   if self.known_board[ni, nj] is None]
                
                # 对于每个相邻的已知数字，比较它们的未知邻居
                for ni, nj in self._get_neighbors(i, j):
                    if not isinstance(self.known_board[ni, nj], (int, float)) or self.known_board[ni, nj] <= 0:
                        continue
                        
                    # 获取相邻数字的未知邻居
                    neighbor_unknowns = [(xi, xj) for xi, xj in self._get_neighbors(ni, nj) 
                                       if self.known_board[xi, xj] is None]
                    
                    # 计算两个集合的差异
                    only_in_first = set(unknown_neighbors) - set(neighbor_unknowns)
                    only_in_second = set(neighbor_unknowns) - set(unknown_neighbors)
                    
                    # 如果第一个数字比第二个数字大，且第二个数字的所有未知邻居都是第一个数字的未知邻居
                    # 那么只存在于第一个集合中的格子都是地雷
                    if (self.known_board[i, j] > self.known_board[ni, nj] and 
                        len(only_in_second) == 0 and 
                        len(only_in_first) == self.known_board[i, j] - self.known_board[ni, nj]):
                        for xi, xj in only_in_first:
                            self.potential_mines.add((xi, xj))
                            
                    # 如果第二个数字比第一个数字大，且第一个数字的所有未知邻居都是第二个数字的未知邻居
                    # 那么只存在于第二个集合中的格子都是地雷
                    elif (self.known_board[ni, nj] > self.known_board[i, j] and 
                          len(only_in_first) == 0 and 
                          len(only_in_second) == self.known_board[ni, nj] - self.known_board[i, j]):
                        for xi, xj in only_in_second:
                            self.potential_mines.add((xi, xj))
    
    def _get_neighbors(self, i, j):
        """获取一个格子周围的8个相邻格子的坐标"""
        neighbors = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < self.board_size and 0 <= nj < self.board_size:
                    neighbors.append((ni, nj))
        return neighbors
    
    def get_next_move(self):
        """决定下一步点击的位置"""
        # 首先检查是否有已知安全的移动
        if self.safe_moves:
            move = list(self.safe_moves)[0]
            self.safe_moves.remove(move)
            self.last_move = move
            return move
        
        # 如果是第一步，选择中间位置
        if np.all(self.known_board == None):
            self.last_move = (self.board_size // 2, self.board_size // 2)
            return self.last_move
        
        # 找到概率最低的未知格子
        min_prob = float('inf')
        best_move = None
        
        # 避开可能是地雷的格子
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.known_board[i, j] is None and (i, j) not in self.potential_mines:
                    # 优先选择靠近已知数字的格子
                    has_number_neighbor = False
                    for ni, nj in self._get_neighbors(i, j):
                        if isinstance(self.known_board[ni, nj], (int, float)) and self.known_board[ni, nj] >= 0:
                            has_number_neighbor = True
                            break
                    
                    # 如果有数字邻居且概率较低，优先选择
                    current_prob = self.probability_map[i, j]
                    if has_number_neighbor:
                        # 优先选择概率为0的格子
                        if current_prob == 0:
                            best_move = (i, j)
                            min_prob = 0
                            break
                        elif current_prob < min_prob:
                            min_prob = current_prob
                            best_move = (i, j)
        
        # 如果没有找到靠近数字且概率低的格子，尝试任何概率低的格子
        if best_move is None:
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if self.known_board[i, j] is None and (i, j) not in self.potential_mines:
                        current_prob = self.probability_map[i, j]
                        if current_prob < min_prob:
                            min_prob = current_prob
                            best_move = (i, j)
        
        # 如果仍然没有找到，随机选择一个未知格子（避开可能的地雷）
        if best_move is None:
            unknown_positions = [(i, j) for i in range(self.board_size) 
                              for j in range(self.board_size) 
                              if self.known_board[i, j] is None and (i, j) not in self.potential_mines]
            
            # 如果所有未知格子都可能是地雷，那么只能冒险选择一个
            if not unknown_positions:
                unknown_positions = [(i, j) for i in range(self.board_size) 
                                  for j in range(self.board_size) 
                                  if self.known_board[i, j] is None]
                
            if unknown_positions:
                # 优先选择角落和边缘，因为它们通常地雷概率较低
                corner_and_edges = []
                for i, j in unknown_positions:
                    neighbor_count = len(self._get_neighbors(i, j))
                    if neighbor_count < 8:  # 不是完全被包围的格子
                        corner_and_edges.append((i, j))
                
                if corner_and_edges:
                    best_move = random.choice(corner_and_edges)
                else:
                    best_move = random.choice(unknown_positions)
            else:
                # 如果没有未知格子，游戏结束
                return None
        
        self.last_move = best_move
        return best_move
        
    def solve_step(self, current_board):
        """解决扫雷游戏的一步"""
        self.update_board(current_board)
        next_move = self.get_next_move()
        if next_move:
            return next_move[0], next_move[1]
        return None, None
        
    def get_safe_coordinates(self, board):
        """
        计算并返回安全的坐标点列表
        
        参数:
        board -- 10*10的二维数组，表示当前棋盘状态
        
        返回:
        list -- 安全坐标点列表，每个坐标点为(x, y)元组
        """
        self.update_board(board)
        
        # 收集所有安全的移动
        safe_coordinates = []
        
        # 1. 已知安全的移动（周围有0的格子）
        if self.safe_moves:
            safe_coordinates.extend(list(self.safe_moves))
            return safe_coordinates
        
        # 2. 找到概率为0的格子
        zero_prob_moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if (self.known_board[i, j] is None and 
                    (i, j) not in self.potential_mines and 
                    (i, j) not in self.safe_moves and
                    self.probability_map[i, j] == 0):
                    zero_prob_moves.append((i, j))
        
        if zero_prob_moves:
            safe_coordinates.extend(zero_prob_moves)
            return safe_coordinates
            
        # 3. 找到靠近已知数字且概率最低的格子
        min_prob = float('inf')
        best_moves = []
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.known_board[i, j] is None and (i, j) not in self.potential_mines:
                    # 检查是否靠近已知数字
                    has_number_neighbor = False
                    for ni, nj in self._get_neighbors(i, j):
                        if isinstance(self.known_board[ni, nj], (int, float)) and self.known_board[ni, nj] >= 0:
                            has_number_neighbor = True
                            break
                    
                    if has_number_neighbor:
                        current_prob = self.probability_map[i, j]
                        if current_prob < min_prob:
                            min_prob = current_prob
                            best_moves = [(i, j)]
                        elif current_prob == min_prob:
                            best_moves.append((i, j))
        
        if best_moves:
            # 返回概率最低的格子
            safe_coordinates.append(random.choice(best_moves))
            return safe_coordinates
            
        # 4. 如果没有找到靠近数字的格子，选择任何概率最低的格子
        min_prob = float('inf')
        best_moves = []
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.known_board[i, j] is None and (i, j) not in self.potential_mines:
                    current_prob = self.probability_map[i, j]
                    if current_prob < min_prob:
                        min_prob = current_prob
                        best_moves = [(i, j)]
                    elif current_prob == min_prob:
                        best_moves.append((i, j))
        
        if best_moves:
            safe_coordinates.append(random.choice(best_moves))
            return safe_coordinates
            
        # 5. 如果所有格子都可能是地雷，选择一个未知格子（优先选择角落和边缘）
        unknown_positions = [(i, j) for i in range(self.board_size) 
                          for j in range(self.board_size) 
                          if self.known_board[i, j] is None]
        
        if unknown_positions:
            # 优先选择角落和边缘
            corner_and_edges = []
            for i, j in unknown_positions:
                neighbor_count = len(self._get_neighbors(i, j))
                if neighbor_count < 8:  # 不是完全被包围的格子
                    corner_and_edges.append((i, j))
            
            if corner_and_edges:
                safe_coordinates.append(random.choice(corner_and_edges))
            else:
                safe_coordinates.append(random.choice(unknown_positions))
        
        # 如果棋盘上没有未知格子，返回空列表
        return safe_coordinates

# 使用示例
if __name__ == "__main__":
    # 初始化求解器
    solver = MinesweeperSolver()
    
    # 示例棋盘
    example_board = [
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, 1, None, None, None, None, None],
        [None, None, None, None, None, None, 1, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None]
    ]
    
    # 获取安全坐标
    safe_coordinates = get_safe_moves(example_board)
    print(f"安全坐标点: {safe_coordinates}")
    
    # 获取下一步
    x, y = solver.solve_step(example_board)
    print(f"下一步点击坐标: ({x}, {y})") 