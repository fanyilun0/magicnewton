# 扫雷算法优化测试

本目录包含了用于测试扫雷算法优化的测试文件和工具。

## 测试文件说明

1. `test_solver_correctness.py` - 测试算法正确性
   - 验证算法计算的安全坐标是否确实安全（不是地雷）
   - 验证算法在各种场景下的功能正确性
   - 测试包括初始棋盘、数字为0的情况、已标记地雷的情况等多种测试用例

2. `test_solver_optimization.py` - 测试算法基本性能
   - 测量算法在处理不同棋盘时的性能
   - 提供基本的性能数据输出

3. `run_performance_comparison.py` - 详细性能测试和报告生成
   - 分别测量各主要方法的执行时间
   - 生成性能报告和图表
   - 提供多次测试的平均执行时间

## 测试数据

`data/` 目录包含了用于测试的棋盘数据：
- `board1.json` - `board4.json`: 实际游戏棋盘数据

## 运行测试

1. 运行正确性测试：
```bash
python -m tests.test_solver_correctness
```

2. 运行性能测试：
```bash
python -m tests.test_solver_optimization
```

3. 生成详细性能报告：
```bash
python -m tests.run_performance_comparison
```

## 性能报告

运行 `run_performance_comparison.py` 将在 `performance_report/` 目录生成性能报告：
- `performance_data.csv` - 包含详细性能数据的CSV文件
- `performance_chart.png` - 性能可视化图表

## 优化说明

算法主要优化点包括：
1. 预先构建缓存结构，减少重复计算
2. 优化数据结构，如使用集合和映射减少查找开销
3. 缓存计算结果，避免重复计算
4. 数据预处理，减少循环次数 