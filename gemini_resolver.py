import random
from typing import List, Tuple, Optional, Set, Dict, DefaultDict
from collections import defaultdict

# 添加彩色输出支持 (保持不变)
try:
    from colorama import init, Fore, Back, Style
    COLORAMA_AVAILABLE = True
    init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False
    class DummyColors:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = DummyColors()

class MinesweeperSolver:
    """
    扫雷求解器，仅使用基础数学规则分析当前棋盘状态。
    每次分析都是独立的，不依赖之前分析的棋盘状态演变。
    """
    
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        # neighbor_cache 可以保留，因为它只依赖于board_size
        self.neighbor_cache: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        
        # 以下变量将在每次 analyze_board 时根据输入棋盘重新初始化
        self.current_board_tiles: List[List[Optional[int]]] = []
        self.revealed_coords: Set[Tuple[int, int]] = set()
        self.initial_flagged_coords: Set[Tuple[int, int]] = set() # 从输入棋盘读取的初始标记
        self.revealed_numbers: Dict[Tuple[int, int], int] = {}

        self.last_clicked: Optional[Tuple[int, int]] = None # 保留用于调试渲染

    def _get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取指定位置的8个相邻位置 (内部使用，避免与方法名冲突)"""
        if (x, y) in self.neighbor_cache:
            return self.neighbor_cache[(x, y)]
        
        neighbors = []
        for dx_offset in [-1, 0, 1]:
            for dy_offset in [-1, 0, 1]:
                if dx_offset == 0 and dy_offset == 0:
                    continue
                nx, ny = x + dx_offset, y + dy_offset
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    neighbors.append((nx, ny))
        
        self.neighbor_cache[(x, y)] = neighbors
        return neighbors

    def _prepare_internal_state(self, board_tiles: List[List[Optional[int]]]):
        """
        根据输入的棋盘数据，准备本次分析所需的内部状态。
        假定 board_tiles 包含: None (未揭示), 0-8 (数字), -1 (外部程序标记的雷区，可选)。
        """
        self.current_board_tiles = board_tiles # 存储对当前棋盘的引用
        self.revealed_coords.clear()
        self.initial_flagged_coords.clear()
        self.revealed_numbers.clear()

        for r in range(self.board_size):
            for c in range(self.board_size):
                coord = (c, r)
                value = board_tiles[r][c]
                if value is not None:
                    if value >= 0: # 数字 0-8
                        self.revealed_coords.add(coord)
                        self.revealed_numbers[coord] = value
                    elif value == -1: # 假设 -1 代表外部已标记的雷
                        self.initial_flagged_coords.add(coord)
                        # 也可以选择将其视为已揭示，以避免点击
                        # self.revealed_coords.add(coord) 

    def analyze_board(self, board_tiles: List[List[Optional[int]]]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """
        分析给定的棋盘状态，仅使用基础数学规则迭代推断。
        返回: (安全坐标集合, 地雷坐标集合)
        """
        if not board_tiles or len(board_tiles) != self.board_size:
            raise ValueError("Board tiles are invalid or do not match board_size.")

        self._prepare_internal_state(board_tiles)

        # 本次分析中确定的安全格和地雷格
        # determined_mines 初始化包含外部已标记的雷
        determined_safe_coords: Set[Tuple[int, int]] = set()
        determined_mine_coords: Set[Tuple[int, int]] = set(self.initial_flagged_coords)

        # 如果棋盘完全未揭示 (所有格子都是 None)，且没有初始标记的雷
        is_board_empty = not self.revealed_coords and not self.initial_flagged_coords
        if is_board_empty:
            all_none = True
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if board_tiles[r][c] is not None:
                        all_none = False
                        break
                if not all_none:
                    break
            if all_none:
                center_x, center_y = self.board_size // 2, self.board_size // 2
                if 0 <= center_x < self.board_size and 0 <= center_y < self.board_size:
                    determined_safe_coords.add((center_x, center_y))
                return determined_safe_coords, determined_mine_coords

        # 迭代应用基础规则
        while True:
            newly_found_safe_this_pass: Set[Tuple[int, int]] = set()
            newly_found_mines_this_pass: Set[Tuple[int, int]] = set()

            for num_coord, number_value in self.revealed_numbers.items():
                # 获取所有邻居
                all_neighbors = self._get_neighbors(num_coord[0], num_coord[1])
                
                current_flagged_neighbors_count = 0
                # "未知邻居"指的是那些既未揭示，也未在本轮分析中被确定为安全或地雷的邻居
                unknown_unrevealed_neighbors: List[Tuple[int, int]] = []

                for neighbor_coord in all_neighbors:
                    if neighbor_coord in determined_mine_coords: # 已确定是雷 (包括初始标记和本轮推断的)
                        current_flagged_neighbors_count += 1
                    # 检查邻居是否真的未揭示且状态未知
                    # (即，在原始棋盘上是 None，并且当前分析中还未确定其状态)
                    elif board_tiles[neighbor_coord[1]][neighbor_coord[0]] is None and \
                         neighbor_coord not in determined_safe_coords and \
                         neighbor_coord not in determined_mine_coords:
                        unknown_unrevealed_neighbors.append(neighbor_coord)
                
                # 剩余需要在未知邻居中找到的雷数
                mines_to_find_in_unknown = number_value - current_flagged_neighbors_count

                # 规则1: 发现地雷
                # 如果剩余要找的雷数 > 0 且等于未知邻居的数量，则所有未知邻居都是雷
                if mines_to_find_in_unknown > 0 and \
                   len(unknown_unrevealed_neighbors) > 0 and \
                   mines_to_find_in_unknown == len(unknown_unrevealed_neighbors):
                    for unk_coord in unknown_unrevealed_neighbors:
                        # 只有当这个格子之前没被确定为雷时才添加
                        if unk_coord not in determined_mine_coords:
                             newly_found_mines_this_pass.add(unk_coord)
                
                # 规则2: 发现安全格
                # 如果剩余要找的雷数为0，则所有未知邻居都是安全的
                elif mines_to_find_in_unknown == 0 and len(unknown_unrevealed_neighbors) > 0:
                    for unk_coord in unknown_unrevealed_neighbors:
                        # 只有当这个格子之前没被确定为安全时才添加
                        if unk_coord not in determined_safe_coords:
                            newly_found_safe_this_pass.add(unk_coord)
            
            # 如果在本轮迭代中没有新的发现，则终止循环
            if not newly_found_safe_this_pass and not newly_found_mines_this_pass:
                break

            # 将本轮发现的格子加入到总的确定集合中，为下一轮迭代做准备
            determined_safe_coords.update(newly_found_safe_this_pass)
            determined_mine_coords.update(newly_found_mines_this_pass)

            # 清理：确保安全格和地雷格不重叠（地雷优先）
            determined_safe_coords -= determined_mine_coords
        
        # 最终清理：从安全格中移除任何初始就已揭示的格子或初始标记的雷
        # （尽管逻辑上它们不应该被加入 determined_safe_coords）
        determined_safe_coords -= self.revealed_coords 
        determined_safe_coords -= self.initial_flagged_coords # 以防万一

        return determined_safe_coords, determined_mine_coords

    def set_last_clicked(self, coord: Tuple[int, int]):
        """设置最后点击的坐标，用于调试渲染"""
        self.last_clicked = coord

    def render_board(self, 
                     board_tiles_to_render: List[List[Optional[int]]], 
                     safe_to_highlight: Set[Tuple[int, int]], 
                     mines_to_highlight: Set[Tuple[int, int]]):
        """
        增强版棋盘渲染，使用彩色标记。
        Args:
            board_tiles_to_render: 要渲染的棋盘二维数组。
            safe_to_highlight: 求解器确定的安全坐标集合。
            mines_to_highlight: 求解器确定的地雷坐标集合（不含外部初始标记的）。
        """
        print("\n" + "=" * (self.board_size * 3 + 5))
        title = f"扫雷棋盘 ({self.board_size}x{self.board_size})"
        print(f"{title:^{self.board_size*3 + 4}}")
        
        header = "   │ " + "  ".join(f"{i:<{1 if i<10 else 0}}" for i in range(self.board_size))
        print(header)
        print("───┼" + "───" * self.board_size)

        for r_idx in range(self.board_size):
            row_display = [f"{r_idx:<2d} │ "]
            for c_idx in range(self.board_size):
                coord = (c_idx, r_idx)
                val = board_tiles_to_render[r_idx][c_idx]
                
                char_to_display = "·" # Default for unrevealed (None)
                cell_style = Fore.WHITE

                if val is not None:
                    if val >= 0: # Revealed number
                        char_to_display = str(val) if val > 0 else " " # Show empty for 0
                        if val == 0: cell_style = Fore.BLACK + Style.DIM # Barely visible for 0
                        elif val == 1: cell_style = Fore.BLUE
                        elif val == 2: cell_style = Fore.GREEN
                        elif val == 3: cell_style = Fore.RED
                        elif val == 4: cell_style = Fore.CYAN # Dark blue on some terminals
                        elif val == 5: cell_style = Fore.MAGENTA # Brown/Maroon
                        elif val == 6: cell_style = Fore.CYAN + Style.BRIGHT
                        else: cell_style = Fore.BLACK + Style.BRIGHT # For 7, 8
                    elif val == -1: # Externally flagged mine
                        char_to_display = "F"
                        cell_style = Fore.YELLOW + Style.BRIGHT
                
                # Highlight solver's findings for unrevealed cells
                if val is None: # Only for cells that are truly unrevealed
                    if coord in safe_to_highlight:
                        char_to_display = "S"
                        cell_style = Back.GREEN + Fore.BLACK + Style.BRIGHT
                    elif coord in mines_to_highlight and coord not in self.initial_flagged_coords: 
                        # Highlight solver-found mines differently from pre-flagged ones
                        char_to_display = "M"
                        cell_style = Back.RED + Fore.WHITE + Style.BRIGHT
                    elif coord in self.initial_flagged_coords: # If an initial flag wasn't revealed as -1
                        char_to_display = "f" # lowercase 'f' for solver-confirmed initial flags
                        cell_style = Fore.YELLOW
                
                # Highlight last clicked cell
                if self.last_clicked and coord == self.last_clicked:
                    # Apply a background, but try to preserve foreground color if set
                    current_fg = cell_style # Preserve previous color
                    if COLORAMA_AVAILABLE: # Colorama specific way to combine
                         row_display.append(Back.BLUE + current_fg + f" {char_to_display} " + Style.RESET_ALL)
                    else:
                        row_display.append(f"<{char_to_display}>") # Simple fallback
                else:
                    if COLORAMA_AVAILABLE:
                        row_display.append(cell_style + f" {char_to_display} " + Style.RESET_ALL)
                    else:
                        row_display.append(f" {char_to_display} ")
            print("".join(row_display))
        
        print("=" * (self.board_size * 3 + 5))
        print(f"图例: 数字=周围雷数, ·=未揭示, 空格=已揭示0")
        print(f"      F=外部标记的雷, S=推断安全格, M=推断雷格")
        if self.last_clicked:
            print(f"      最后点击 (蓝色背景): {self.last_clicked}")
        print("=" * (self.board_size * 3 + 5))