# 扫雷游戏解答程序

这是一个Python实现的扫雷游戏解答程序，能够根据当前棋盘状态，智能地决定下一步应该点击的位置。

## 功能特点

- 接收10x10的扫雷棋盘数据
- 分析当前棋盘状态，计算每个格子是地雷的概率
- 根据概率和策略，决定下一步最佳的点击位置
- 支持完整的游戏流程模拟

## 文件说明

- `MineSweeper.py`: 主要的解答程序实现
- `test_minesweeper.py`: 单元测试文件
- `minesweeper_demo.py`: 演示程序，展示解答程序如何在实际游戏中工作

## 使用方法

### 基本用法

```python
from MineSweeper import MinesweeperSolver

# 初始化求解器
solver = MinesweeperSolver()

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

# 获取下一步点击的坐标
x, y = solver.solve_step(current_board)
print(f"下一步点击坐标: ({x}, {y})")
```

### 运行演示程序

```bash
python minesweeper_demo.py
```

这将启动一个完整的扫雷游戏模拟，展示解答程序如何一步步解决扫雷游戏。

### 运行测试

```bash
python -m unittest test_minesweeper.py
```

## 算法说明

该解答程序使用以下策略来决定下一步的点击位置：

1. 如果有已知安全的格子（周围有0的格子），优先点击这些格子
2. 计算每个未知格子是地雷的概率，选择概率最低的格子
3. 优先选择靠近已知数字的格子
4. 如果是第一步，选择棋盘中心位置
5. 如果以上策略都无法决定，随机选择一个未知格子

## 依赖库

- numpy: 用于数组操作和概率计算
- random: 用于随机选择格子

## 注意事项

- 棋盘使用二维数组表示，`None`表示未点击的格子，数字表示周围地雷数量
- 解答程序不保证100%成功率，因为扫雷游戏本身就包含一定的运气成分
- 在实际游戏中，可能需要根据具体游戏规则调整算法
