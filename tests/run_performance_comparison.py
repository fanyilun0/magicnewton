#!/usr/bin/env python
import os
import sys
import time
import json
import pandas as pd
from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper_solver import MinesweeperSolver


def load_board_data(filepath: str) -> List[List[Optional[int]]]:
    """加载测试棋盘数据"""
    with open(filepath, 'r') as f:
        board_json = json.load(f)
        # 提取tiles数据
        if 'data' in board_json and '_minesweeper' in board_json['data']:
            return board_json['data']['_minesweeper']['tiles']
        return []


def run_performance_test(iterations=5) -> Dict[str, Any]:
    """运行性能测试，返回测试结果数据"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    board_files = [f for f in os.listdir(data_dir) if f.startswith("board") and f.endswith(".json")]
    
    results = {}
    for board_file in sorted(board_files):
        print(f"测试棋盘: {board_file}")
        filepath = os.path.join(data_dir, board_file)
        tiles = load_board_data(filepath)
        
        solver = MinesweeperSolver()
        
        # 测量各个关键方法的性能
        durations = {
            'update_board': [],
            'get_safe_coordinates': [],
            'analyze_relations': [],
            'total': []
        }
        
        for i in range(iterations):
            # 重置求解器
            solver.reset_board()
            
            # 测量 update_board 方法的性能
            start_time = time.time()
            solver.update_board(tiles)
            update_time = time.time() - start_time
            durations['update_board'].append(update_time)
            
            # 测量 _analyze_number_relations 方法的性能
            start_time = time.time()
            solver._analyze_number_relations()
            analyze_time = time.time() - start_time
            durations['analyze_relations'].append(analyze_time)
            
            # 测量 get_safe_coordinates 方法的性能
            solver.cached_safe_coords.clear()  # 清除缓存，强制重新计算
            start_time = time.time()
            safe_coords = solver.get_safe_coordinates()
            get_safe_time = time.time() - start_time
            durations['get_safe_coordinates'].append(get_safe_time)
            
            # 计算总时间
            total_time = update_time + analyze_time + get_safe_time
            durations['total'].append(total_time)
            
            # 清理缓存，准备下一次迭代
            solver.reset_board()
        
        # 计算平均值
        avg_durations = {
            method: sum(times) / len(times) for method, times in durations.items()
        }
        
        # 记录结果
        results[board_file] = {
            'avg_durations': avg_durations,
            'safe_coord_count': len(safe_coords)
        }
        
        # 输出结果
        print(f"  找到 {len(safe_coords)} 个安全坐标")
        for method, avg_time in avg_durations.items():
            print(f"  {method} 平均耗时: {avg_time:.6f} 秒")
    
    return results


def generate_report(results: Dict[str, Any], output_dir: str = 'performance_report'):
    """生成性能报告，包括图表和数据表格"""
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 提取数据
    data = []
    for board_file, result in sorted(results.items()):
        row = {
            'board_file': board_file,
            'safe_coord_count': result['safe_coord_count']
        }
        row.update({f"{method}_time": time for method, time in result['avg_durations'].items()})
        data.append(row)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存数据到CSV
    csv_path = os.path.join(output_dir, 'performance_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"性能数据已保存到: {csv_path}")
    
    # 生成图表
    plt.figure(figsize=(10, 6))
    
    # 绘制总时间柱状图
    plt.subplot(2, 1, 1)
    plt.bar(df['board_file'], df['total_time'], color='blue')
    plt.title('各棋盘总处理时间')
    plt.xlabel('棋盘文件')
    plt.ylabel('时间(秒)')
    plt.xticks(rotation=45)
    
    # 绘制各方法时间堆叠柱状图
    plt.subplot(2, 1, 2)
    methods = ['update_board_time', 'analyze_relations_time', 'get_safe_coordinates_time']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    bottom = None
    
    for i, method in enumerate(methods):
        if bottom is None:
            bottom = df[method]
            plt.bar(df['board_file'], df[method], label=method.replace('_time', ''), color=colors[i])
        else:
            plt.bar(df['board_file'], df[method], bottom=bottom, label=method.replace('_time', ''), color=colors[i])
            bottom += df[method]
    
    plt.title('各棋盘各方法处理时间')
    plt.xlabel('棋盘文件')
    plt.ylabel('时间(秒)')
    plt.legend()
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'performance_chart.png'))
    print(f"性能图表已保存到: {os.path.join(output_dir, 'performance_chart.png')}")
    
    # 打印总结报告
    print("\n性能测试总结:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    results = run_performance_test()
    generate_report(results) 