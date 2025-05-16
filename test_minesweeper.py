#!/usr/bin/env python
"""
扫雷算法测试脚本

使用方法:
python test_minesweeper.py [棋盘文件路径]

示例:
python test_minesweeper.py tests/data/board1.json
"""

import json
import os
import sys
import time
from typing import List, Optional, Tuple, Set

from minesweeper_solver import MinesweeperSolver

# 配置
VERBOSE = True  # 是否显示详细信息
STEP_BY_STEP = True  # 是否逐步显示模拟游戏过程


def load_board_data(filepath: str) -> List[List[Optional[int]]]:
    """加载测试棋盘数据"""
    with open(filepath, 'r') as f:
        board_json = json.load(f)
        # 提取tiles数据
        if 'data' in board_json and '_minesweeper' in board_json['data']:
            return board_json['data']['_minesweeper']['tiles']
        return []


def print_stats(duration: float, safe_coords: Set[Tuple[int, int]], solver: MinesweeperSolver):
    """打印性能统计信息"""
    print(f"\n性能统计:")
    print(f"- 计算耗时: {duration:.6f} 秒")
    print(f"- 安全坐标数量: {len(safe_coords)}")
    print(f"- 已揭示格子数: {len(solver.revealed)}")
    print(f"- 已标记地雷数: {len(solver.flagged)}")
    print(f"- 推理安全格子数: {len(solver.additional_safe)}")
    print(f"- 推理地雷格子数: {len(solver.additional_mines)}")


def simulate_game(board_data: List[List[Optional[int]]]):
    """模拟完整的游戏过程"""
    solver = MinesweeperSolver()
    
    # 初始化棋盘状态
    solver.reset_board()
    solver.update_board(board_data)
    
    move_count = 0
    max_moves = 50
    revealed_tiles = set()  # 用于跟踪已揭示的格子
    
    # 克隆真实棋盘数据，用于模拟点击
    full_board = [row[:] for row in board_data]
    
    # 显示初始棋盘状态
    print("\n初始棋盘状态:")
    solver.render_board()
    
    # 模拟游戏
    while move_count < max_moves:
        # 获取当前安全坐标
        start_time = time.time()
        safe_coords = solver.get_safe_coordinates()
        duration = time.time() - start_time
        
        if VERBOSE:
            print_stats(duration, safe_coords, solver)
        
        if not safe_coords:
            print("没有找到安全坐标，游戏结束")
            break
        
        # 选择第一个安全坐标进行模拟点击
        x, y = next(iter(safe_coords))
        move_count += 1
        print(f"\n移动 #{move_count}:")
        print(f"选择坐标: ({x}, {y})")
        
        # 显示点击前棋盘
        if STEP_BY_STEP:
            solver.set_last_clicked((x, y))
            print("点击前棋盘状态:")
            solver.render_board((x, y))
            input("按回车键继续...")
        
        # 模拟点击
        if y < len(full_board) and x < len(full_board[0]):
            # 检查是否点击到地雷
            if full_board[y][x] == -1:
                print(f"坐标 ({x}, {y}) 是地雷！游戏失败")
                # 更新棋盘状态
                board_data[y][x] = -1
                solver.reset_board()
                solver.update_board(board_data)
                solver.set_last_clicked((x, y))
                solver.render_board((x, y))
                break
            
            # 更新点击结果 - 模拟递归揭示周围空白格子
            reveal_tiles(board_data, full_board, x, y, revealed_tiles)
            
            # 更新求解器状态
            solver.reset_board()
            solver.update_board(board_data)
            
            # 显示点击后棋盘
            print("点击后棋盘状态:")
            solver.render_board((x, y))
            
            # 检查是否已完成游戏
            unrevealed_count = sum(1 for y in range(len(board_data)) 
                                 for x in range(len(board_data[0])) 
                                 if board_data[y][x] is None)
            mine_count = sum(1 for y in range(len(board_data)) 
                           for x in range(len(board_data[0])) 
                           if full_board[y][x] == -1)
            
            if unrevealed_count <= mine_count:
                print(f"游戏完成！共使用 {move_count} 步")
                break
            
            if STEP_BY_STEP:
                input("按回车键继续...")
        else:
            print(f"坐标 ({x}, {y}) 超出棋盘范围")
            break
    
    print(f"\n游戏结束，共进行 {move_count} 步")


def reveal_tiles(board_data, full_board, x, y, revealed_tiles):
    """模拟点击，递归揭示周围空白格子"""
    if (x, y) in revealed_tiles:
        return
    
    # 标记为已揭示
    revealed_tiles.add((x, y))
    
    # 更新棋盘
    board_data[y][x] = full_board[y][x]
    
    # 如果是空白格子，递归揭示周围格子
    if full_board[y][x] == 0:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if dx == 0 and dy == 0:
                    continue
                if 0 <= nx < len(board_data[0]) and 0 <= ny < len(board_data):
                    if board_data[ny][nx] is None and (nx, ny) not in revealed_tiles:
                        reveal_tiles(board_data, full_board, nx, ny, revealed_tiles)


def main():
    if len(sys.argv) < 2:
        # 检查默认位置
        if os.path.exists("tests/data/board1.json"):
            filepath = "tests/data/board1.json"
        else:
            print("请提供棋盘文件路径")
            print("用法: python test_minesweeper.py [棋盘文件路径]")
            return
    else:
        filepath = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    # 加载棋盘数据
    print(f"正在加载棋盘数据: {filepath}")
    board_data = load_board_data(filepath)
    
    if not board_data:
        print("无法加载棋盘数据")
        return
    
    print(f"成功加载棋盘 ({len(board_data)}x{len(board_data[0])})")
    
    # 模拟完整游戏过程
    simulate_game(board_data)


if __name__ == "__main__":
    main() 