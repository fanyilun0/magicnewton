import unittest
import os
import json
import time
import sys
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper_solver import MinesweeperSolver


class TestSolverOptimization(unittest.TestCase):
    """测试扫雷算法优化"""
    
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
    
    def test_all_boards(self):
        """测试所有棋盘数据的安全坐标计算性能"""
        board_files = [f for f in os.listdir(self.data_dir) if f.startswith("board") and f.endswith(".json")]
        
        results = {}
        for board_file in sorted(board_files):
            print(f"测试棋盘: {board_file}")
            tiles = self.load_board_data(board_file)
            
            # 重置求解器
            self.solver.reset_board()
            
            # 更新棋盘状态
            self.solver.update_board(tiles)
            
            # 计时获取安全坐标
            start_time = time.time()
            safe_coords = self.solver.get_safe_coordinates()
            end_time = time.time()
            
            # 记录结果
            duration = end_time - start_time
            results[board_file] = {
                "safe_coords": list(safe_coords),
                "duration": duration,
                "count": len(safe_coords)
            }
            
            print(f"  找到 {len(safe_coords)} 个安全坐标")
            print(f"  耗时: {duration:.6f} 秒")
            
            # 验证安全坐标不是地雷
            for coord in safe_coords:
                x, y = coord
                if x < len(tiles[0]) and y < len(tiles) and tiles[y][x] is not None:
                    self.assertNotEqual(tiles[y][x], -1, f"坐标 {coord} 不应该是地雷")
        
        # 打印结果摘要
        print("\n结果摘要:")
        for board_file, result in sorted(results.items()):
            print(f"{board_file}: 找到 {result['count']} 个安全坐标, 耗时 {result['duration']:.6f} 秒")
        
        return results
    
    def test_get_safe_coordinates_optimization(self):
        """测试安全坐标计算的性能优化效果"""
        board_files = [f for f in os.listdir(self.data_dir) if f.startswith("board") and f.endswith(".json")]
        
        for board_file in sorted(board_files):
            print(f"性能测试: {board_file}")
            tiles = self.load_board_data(board_file)
            
            # 多次执行以获得更稳定的性能测量
            iterations = 5
            durations = []
            
            for i in range(iterations):
                # 重置求解器
                self.solver.reset_board()
                self.solver.update_board(tiles)
                
                # 计时获取安全坐标
                start_time = time.time()
                safe_coords = self.solver.get_safe_coordinates()
                end_time = time.time()
                
                durations.append(end_time - start_time)
            
            # 计算平均执行时间
            avg_duration = sum(durations) / len(durations)
            print(f"  平均耗时: {avg_duration:.6f} 秒 (执行 {iterations} 次)")


if __name__ == "__main__":
    unittest.main() 