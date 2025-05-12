Create MineSweeper.py
10*10
现在需要实现一个python的扫雷解答全过程， 请按步骤实现
1. 每次接受一个10*10的二维数据如：
[
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,1,null,null,null,null,null],
                [null,null,null,null,null,null,1,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null]
            ]

只需要根据这个现有的格子数据， 计算并返回安全的坐标点，
如果没有绝对的安全点责需要根据实际的情况返回， 远离已经揭露的数字格子