import numpy as np
import random

def get_safe_move(board):
    """
    简化版扫雷解析器，接收一个10*10的二维棋盘数据，返回一个安全的坐标点
    
    参数:
    board -- 10*10的二维数组，表示当前棋盘状态
             None表示未知格子，数字表示周围地雷数量
    
    返回:
    tuple -- 安全坐标点(x, y)，如果找不到安全点则返回None
    """
    board_size = 10
    board = np.array(board)
    potential_mines = set()
    
    # 第一步：检查是否是初始棋盘
    if np.all(board == None):
        return (board_size // 2, board_size // 2)  # 返回中心位置

    # 第三步：分析数字格子，找出可能的地雷和安全格子
    probability_map = np.zeros((board_size, board_size))
    
    for i in range(board_size):
        for j in range(board_size):
            if isinstance(board[i, j], (int, float)) and board[i, j] > 0:
                # 获取周围的未知格子
                unknown_cells = []
                for ni, nj in _get_neighbors(i, j, board_size):
                    if board[ni, nj] is None:
                        unknown_cells.append((ni, nj))
                
                # 如果周围有未知格子，更新它们的概率
                if unknown_cells:
                    # 数字表示周围地雷数量
                    mine_probability = board[i, j] / len(unknown_cells)
                    for ni, nj in unknown_cells:
                        probability_map[ni, nj] += mine_probability
                    
                    # 如果数字等于周围未知格子数量，所有未知格子都是地雷
                    if board[i, j] == len(unknown_cells):
                        for ni, nj in unknown_cells:
                            potential_mines.add((ni, nj))
    
    # 第四步：找到概率为0的格子
    for i in range(board_size):
        for j in range(board_size):
            if (board[i, j] is None and 
                (i, j) not in potential_mines and
                probability_map[i, j] == 0):
                # 找到一个靠近已知数字的概率为0的格子
                for ni, nj in _get_neighbors(i, j, board_size):
                    if isinstance(board[ni, nj], (int, float)) and board[ni, nj] >= 0:
                        return (i, j)
    
    # 第五步：找到概率最低的格子
    min_prob = float('inf')
    best_move = None
    
    for i in range(board_size):
        for j in range(board_size):
            if board[i, j] is None and (i, j) not in potential_mines:
                # 优先选择靠近已知数字的格子
                has_number_neighbor = False
                for ni, nj in _get_neighbors(i, j, board_size):
                    if isinstance(board[ni, nj], (int, float)) and board[ni, nj] >= 0:
                        has_number_neighbor = True
                        break
                
                current_prob = probability_map[i, j]
                if has_number_neighbor and current_prob < min_prob:
                    min_prob = current_prob
                    best_move = (i, j)
    
    if best_move:
        return best_move
    
    # 第六步：如果还没找到，选择任何概率最低的格子
    min_prob = float('inf')
    best_move = None
    
    for i in range(board_size):
        for j in range(board_size):
            if board[i, j] is None and (i, j) not in potential_mines:
                current_prob = probability_map[i, j]
                if current_prob < min_prob:
                    min_prob = current_prob
                    best_move = (i, j)
    
    if best_move:
        return best_move
    
    # 第七步：如果所有未知格子都可能是地雷，随机选择一个未知格子
    unknown_positions = [(i, j) for i in range(board_size) 
                      for j in range(board_size) 
                      if board[i, j] is None]
    
    if unknown_positions:
        # 优先选择角落和边缘
        corner_and_edges = []
        for i, j in unknown_positions:
            neighbor_count = len(_get_neighbors(i, j, board_size))
            if neighbor_count < 8:  # 不是完全被包围的格子
                corner_and_edges.append((i, j))
        
        if corner_and_edges:
            return random.choice(corner_and_edges)
        else:
            return random.choice(unknown_positions)
    
    # 如果没有未知格子，返回None
    return None

def _get_neighbors(i, j, board_size):
    """获取一个格子周围的8个相邻格子的坐标"""
    neighbors = []
    for di in [-1, 0, 1]:
        for dj in [-1, 0, 1]:
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < board_size and 0 <= nj < board_size:
                neighbors.append((ni, nj))
    return neighbors

# 使用示例
if __name__ == "__main__":
    # 示例棋盘
    example_board = [
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, 1, None, None, None, None, None, None, None, None],
        [None, None, None, None, 1, None, None, None, None, None],
        [None, None, 1, None, None, None, 1, None, None, None],
        [None, None, None, 2, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, 3, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None]
    ]
    
    # 获取安全坐标
    safe_move = get_safe_move(example_board)
    print(f"安全坐标点: {safe_move}") 