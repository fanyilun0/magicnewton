import unittest
import os
import json
import sys
from typing import List, Optional, Set, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper_solver import MinesweeperSolver


class TestSolverCorrectness(unittest.TestCase):
    """测试扫雷算法正确性"""
    
    def setUp(self):
        """初始化测试环境"""
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.solver = MinesweeperSolver()
    
    def load_board_data(self, filename: str) -> List[List[Optional[int]]]:
        """加载测试棋盘数据"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r') as f:
            board_json = json.load(f)
            # 提取tiles数据
            if 'data' in board_json and '_minesweeper' in board_json['data']:
                return board_json['data']['_minesweeper']['tiles']
            return []
    
    def validate_safe_coordinates(self, board: List[List[Optional[int]]], safe_coords: Set[Tuple[int, int]]) -> bool:
        """验证安全坐标的有效性
        
        检查安全坐标不能是地雷(-1)，且必须在棋盘范围内。
        """
        for x, y in safe_coords:
            # 检查坐标是否在棋盘范围内
            if y >= len(board) or x >= len(board[0]):
                print(f"错误: 坐标 ({x}, {y}) 超出棋盘范围")
                return False
            
            # 检查坐标对应的值
            if board[y][x] is not None and board[y][x] == -1:
                print(f"错误: 坐标 ({x}, {y}) 是地雷")
                return False
        
        return True
    
    def test_first_move(self):
        """测试初始棋盘的第一步选择"""
        solver = MinesweeperSolver(board_size=10)
        safe_coords = solver.get_safe_coordinates()
        
        # 对于空棋盘，安全坐标应该是中心点
        self.assertEqual(len(safe_coords), 1)
        center = 10 // 2
        self.assertIn((center, center), safe_coords)
    
    def test_number_zero(self):
        """测试数字0周围的格子应该被标记为安全"""
        # 创建一个简单的测试棋盘
        board = [
            [None, None, None],
            [None, 0, None],
            [None, None, None]
        ]
        
        solver = MinesweeperSolver(board_size=3)
        solver.update_board(board)
        safe_coords = solver.get_safe_coordinates()
        
        # 数字0周围的所有格子应该被标记为安全
        expected_safe = {(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)}
        self.assertEqual(safe_coords, expected_safe)
    
    def test_number_equals_flagged(self):
        """测试数字等于已标记地雷数时的安全坐标计算"""
        # 创建一个简单的测试棋盘
        board = [
            [None, -1, None],
            [-1, 2, None],
            [None, None, None]
        ]
        
        solver = MinesweeperSolver(board_size=3)
        solver.update_board(board)
        safe_coords = solver.get_safe_coordinates()
        
        # 检查关键的安全坐标是否被正确标识
        self.assertIn((2, 0), safe_coords)
        self.assertIn((2, 1), safe_coords)
        self.assertIn((0, 2), safe_coords)
        self.assertIn((1, 2), safe_coords)
        self.assertIn((2, 2), safe_coords)
    
    def test_number_relation_common_safe(self):
        """测试数字关系推理 - 共同格子安全"""
        # 创建一个测试棋盘，其中两个数字的特有未揭示格子数量相等且等于各自的数字值，则共同的未揭示格子应安全
        board = [
            [-1, 1, None, None],
            [1, 1, None, None],
            [None, None, None, None],
            [None, None, None, None]
        ]
        
        solver = MinesweeperSolver(board_size=4)
        solver.update_board(board)
        safe_coords = solver.get_safe_coordinates()
        
        # 通过数字关系分析，(2,0)和(2,1)应该是安全的
        self.assertIn((2, 0), safe_coords)
        self.assertIn((2, 1), safe_coords)
    
    def test_all_test_boards(self):
        """测试所有测试棋盘数据的正确性"""
        board_files = [f for f in os.listdir(self.data_dir) if f.startswith("board") and f.endswith(".json")]
        
        for board_file in sorted(board_files):
            print(f"测试棋盘: {board_file}")
            tiles = self.load_board_data(board_file)
            
            # 重置求解器
            self.solver.reset_board()
            self.solver.update_board(tiles)
            
            # 获取安全坐标
            safe_coords = self.solver.get_safe_coordinates()
            print(f"  找到 {len(safe_coords)} 个安全坐标")
            
            # 验证安全坐标
            self.assertTrue(
                self.validate_safe_coordinates(tiles, safe_coords),
                f"棋盘 {board_file} 的安全坐标验证失败"
            )
            
            # 验证安全坐标和地雷坐标不重叠
            mine_coords = self.solver.get_mine_coordinates()
            print(f"  找到 {len(mine_coords)} 个地雷坐标")
            self.assertEqual(
                len(safe_coords & mine_coords), 0,
                f"棋盘 {board_file} 的安全坐标与地雷坐标有重叠"
            )


if __name__ == "__main__":
    unittest.main() 