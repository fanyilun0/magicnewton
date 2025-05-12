import unittest
import numpy as np
import random
from boardresolver import get_safe_move

class TestBoardResolver(unittest.TestCase):
    def test_initial_move(self):
        """测试初始棋盘时的移动"""
        board = [[None for _ in range(10)] for _ in range(10)]
        x, y = get_safe_move(board)
        # 初始移动应该是中心位置
        self.assertEqual(x, 5)
        self.assertEqual(y, 5)
        
    def test_safe_move_detection(self):
        """测试是否能检测到安全的移动"""
        # 创建一个棋盘，其中有一个0，表示周围没有地雷
        board = [[None for _ in range(10)] for _ in range(10)]
        board[5][5] = 0
        x, y = get_safe_move(board)
        # 应该选择0周围的一个格子，因为它们是安全的
        self.assertTrue((x-5)**2 + (y-5)**2 <= 2)  # 应该是0附近的一个格子
        
    def test_number_based_decision(self):
        """测试基于数字的决策"""
        # 创建一个有数字的棋盘
        board = [[None for _ in range(10)] for _ in range(10)]
        board[3][4] = 1
        board[4][6] = 1
        x, y = get_safe_move(board)
        # 应该选择一个靠近数字的格子
        self.assertTrue(
            (abs(x-3) <= 1 and abs(y-4) <= 1) or 
            (abs(x-4) <= 1 and abs(y-6) <= 1)
        )
        
    def test_probability_calculation(self):
        """测试概率计算逻辑"""
        # 创建一个棋盘，其中有两个数字1，一个在角落（周围只有3个格子），一个在中间（周围有8个格子）
        board = [[None for _ in range(10)] for _ in range(10)]
        board[0][0] = 1  # 角落的1
        board[5][5] = 1  # 中间的1
        
        # 获取安全坐标
        x, y = get_safe_move(board)
        
        # 应该选择中间的1周围的格子，因为概率更低
        self.assertTrue(abs(x-5) <= 1 and abs(y-5) <= 1)
        
    def test_random_board_safety(self):
        """测试随机生成的棋盘和雷区，验证get_safe_move函数返回的安全坐标点"""
        # 设置随机种子以便结果可重现
        random.seed(42)
        
        # 随机生成10*10棋盘
        board_size = 10
        num_mines = 15  # 设置地雷数量
        
        # 随机放置地雷
        all_positions = [(i, j) for i in range(board_size) for j in range(board_size)]
        mine_positions = random.sample(all_positions, num_mines)
        mines = set(mine_positions)
        
        # 初始化棋盘，所有格子都是未知的
        board = [[None for _ in range(board_size)] for _ in range(board_size)]
        
        # 随机揭示一些非地雷格子
        non_mine_positions = [pos for pos in all_positions if pos not in mines]
        revealed_positions = random.sample(non_mine_positions, min(20, len(non_mine_positions)))
        
        # 更新棋盘，计算已揭示格子周围的地雷数
        for x, y in revealed_positions:
            # 计算周围地雷数
            mine_count = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < board_size and 0 <= ny < board_size and (nx, ny) in mines:
                        mine_count += 1
            board[x][y] = mine_count
        
        # 获取安全坐标
        safe_move = get_safe_move(board)
        
        # 验证返回的坐标不是地雷
        if safe_move:
            x, y = safe_move
            self.assertNotIn((x, y), mines, f"坐标 ({x}, {y}) 是地雷，但被标记为安全")

if __name__ == "__main__":
    # 设置随机种子以便结果可重现
    random.seed(42)
    unittest.main() 