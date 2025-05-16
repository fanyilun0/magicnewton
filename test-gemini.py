from gemini_resolver import MinesweeperSolver
import random
from typing import List, Tuple, Optional, Set, Dict

# (为了能够独立运行，我将复制上一版本中你提供的 MinesweeperSolver 类定义)
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

# class MinesweeperSolver:
#     """
#     扫雷求解器，仅使用基础数学规则分析当前棋盘状态。
#     每次分析都是独立的，不依赖之前分析的棋盘状态演变。
#     """
    
#     def __init__(self, board_size: int = 10):
#         self.board_size = board_size
#         self.neighbor_cache: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
#         self.current_board_tiles: List[List[Optional[int]]] = []
#         self.revealed_coords: Set[Tuple[int, int]] = set()
#         self.initial_flagged_coords: Set[Tuple[int, int]] = set() 
#         self.revealed_numbers: Dict[Tuple[int, int], int] = {}
#         self.last_clicked: Optional[Tuple[int, int]] = None

#     def _get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
#         if (x, y) in self.neighbor_cache:
#             return self.neighbor_cache[(x, y)]
        
#         neighbors = []
#         for dx_offset in [-1, 0, 1]:
#             for dy_offset in [-1, 0, 1]:
#                 if dx_offset == 0 and dy_offset == 0:
#                     continue
#                 nx, ny = x + dx_offset, y + dy_offset
#                 if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
#                     neighbors.append((nx, ny))
#         self.neighbor_cache[(x, y)] = neighbors
#         return neighbors

#     def _prepare_internal_state(self, board_tiles: List[List[Optional[int]]]):
#         self.current_board_tiles = board_tiles
#         self.revealed_coords.clear()
#         self.initial_flagged_coords.clear()
#         self.revealed_numbers.clear()

#         for r in range(self.board_size):
#             for c in range(self.board_size):
#                 coord = (c, r)
#                 value = board_tiles[r][c]
#                 if value is not None:
#                     if value >= 0: 
#                         self.revealed_coords.add(coord)
#                         self.revealed_numbers[coord] = value
#                     elif value == -1: 
#                         self.initial_flagged_coords.add(coord)

#     def analyze_board(self, board_tiles: List[List[Optional[int]]]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
#         if not board_tiles or len(board_tiles) != self.board_size or len(board_tiles[0]) != self.board_size:
#             raise ValueError("Board tiles are invalid or do not match board_size.")

#         self._prepare_internal_state(board_tiles)
#         determined_safe_coords: Set[Tuple[int, int]] = set()
#         determined_mine_coords: Set[Tuple[int, int]] = set(self.initial_flagged_coords)

#         is_board_empty = not self.revealed_coords and not self.initial_flagged_coords
#         if is_board_empty:
#             all_none = True
#             for r_idx in range(self.board_size):
#                 for c_idx in range(self.board_size):
#                     if board_tiles[r_idx][c_idx] is not None:
#                         all_none = False
#                         break
#                 if not all_none:
#                     break
#             if all_none:
#                 center_x, center_y = self.board_size // 2, self.board_size // 2
#                 if 0 <= center_x < self.board_size and 0 <= center_y < self.board_size:
#                     determined_safe_coords.add((center_x, center_y))
#                 return determined_safe_coords, determined_mine_coords
        
#         while True:
#             newly_found_safe_this_pass: Set[Tuple[int, int]] = set()
#             newly_found_mines_this_pass: Set[Tuple[int, int]] = set()

#             for num_coord, number_value in self.revealed_numbers.items():
#                 all_neighbors = self._get_neighbors(num_coord[0], num_coord[1])
#                 current_flagged_neighbors_count = 0
#                 unknown_unrevealed_neighbors: List[Tuple[int, int]] = []

#                 for neighbor_coord in all_neighbors:
#                     if neighbor_coord in determined_mine_coords: 
#                         current_flagged_neighbors_count += 1
#                     elif board_tiles[neighbor_coord[1]][neighbor_coord[0]] is None and \
#                          neighbor_coord not in determined_safe_coords and \
#                          neighbor_coord not in determined_mine_coords:
#                         unknown_unrevealed_neighbors.append(neighbor_coord)
                
#                 mines_to_find_in_unknown = number_value - current_flagged_neighbors_count

#                 if mines_to_find_in_unknown > 0 and \
#                    len(unknown_unrevealed_neighbors) > 0 and \
#                    mines_to_find_in_unknown == len(unknown_unrevealed_neighbors):
#                     for unk_coord in unknown_unrevealed_neighbors:
#                         if unk_coord not in determined_mine_coords:
#                              newly_found_mines_this_pass.add(unk_coord)
                
#                 elif mines_to_find_in_unknown == 0 and len(unknown_unrevealed_neighbors) > 0:
#                     for unk_coord in unknown_unrevealed_neighbors:
#                         if unk_coord not in determined_safe_coords:
#                             newly_found_safe_this_pass.add(unk_coord)
            
#             if not newly_found_safe_this_pass and not newly_found_mines_this_pass:
#                 break

#             determined_safe_coords.update(newly_found_safe_this_pass)
#             determined_mine_coords.update(newly_found_mines_this_pass)
#             determined_safe_coords -= determined_mine_coords
        
#         determined_safe_coords -= self.revealed_coords 
#         determined_safe_coords -= self.initial_flagged_coords

#         return determined_safe_coords, determined_mine_coords

#     def set_last_clicked(self, coord: Tuple[int, int]):
#         self.last_clicked = coord

#     def render_board(self, 
#                      board_tiles_to_render: List[List[Optional[int]]], 
#                      safe_to_highlight: Set[Tuple[int, int]], 
#                      mines_to_highlight: Set[Tuple[int, int]]):
#         print("\n" + "=" * (self.board_size * 3 + 5))
#         title = f"扫雷棋盘 ({self.board_size}x{self.board_size})"
#         print(f"{title:^{self.board_size*3 + 4}}")
        
#         header = "   │ " + "  ".join(f"{i:<{1 if i<10 else 0}}" for i in range(self.board_size))
#         print(header)
#         print("───┼" + "───" * self.board_size)

#         for r_idx in range(self.board_size):
#             row_display = [f"{r_idx:<2d} │ "]
#             for c_idx in range(self.board_size):
#                 coord = (c_idx, r_idx)
#                 val = board_tiles_to_render[r_idx][c_idx]
                
#                 char_to_display = "·" 
#                 cell_style = Fore.WHITE

#                 if val is not None:
#                     if val >= 0: 
#                         char_to_display = str(val) if val > 0 else " " 
#                         if val == 0: cell_style = Fore.BLACK + Style.DIM 
#                         elif val == 1: cell_style = Fore.BLUE
#                         elif val == 2: cell_style = Fore.GREEN
#                         elif val == 3: cell_style = Fore.RED
#                         elif val == 4: cell_style = Fore.BLUE + Style.BRIGHT # Was Dark Cyan
#                         elif val == 5: cell_style = Fore.MAGENTA 
#                         elif val == 6: cell_style = Fore.CYAN 
#                         else: cell_style = Fore.BLACK + Style.BRIGHT
#                     # Removed val == -1 handling for 'F' as input board won't have it.
#                     # initial_flagged_coords will be empty.
                
#                 if val is None: 
#                     if coord in safe_to_highlight:
#                         char_to_display = "S"
#                         cell_style = Back.GREEN + Fore.BLACK + Style.BRIGHT
#                     elif coord in mines_to_highlight: 
#                         char_to_display = "M"
#                         cell_style = Back.RED + Fore.WHITE + Style.BRIGHT
                
#                 if self.last_clicked and coord == self.last_clicked:
#                     current_fg = cell_style 
#                     if COLORAMA_AVAILABLE: 
#                          row_display.append(Back.BLUE + current_fg + f" {char_to_display} " + Style.RESET_ALL)
#                     else:
#                         row_display.append(f"<{char_to_display}>") 
#                 else:
#                     if COLORAMA_AVAILABLE:
#                         row_display.append(cell_style + f" {char_to_display} " + Style.RESET_ALL)
#                     else:
#                         row_display.append(f" {char_to_display} ")
#             print("".join(row_display))
        
#         print("=" * (self.board_size * 3 + 5))
#         print(f"图例: 数字=周围雷数, ·=未揭示, 空格=已揭示0, S=推断安全格, M=推断雷格")
#         if self.last_clicked:
#             print(f"      最后点击 (蓝色背景): {self.last_clicked}")
#         print("=" * (self.board_size * 3 + 5))
# # --- End of MinesweeperSolver class definition ---


def generate_complete_board(board_size: int, num_mines: int) -> Tuple[List[List[int]], Set[Tuple[int, int]]]:
    """
    生成一个完整的扫雷棋盘，包含地雷和数字。
    -1 代表地雷。
    """
    if num_mines > board_size * board_size:
        raise ValueError("Number of mines cannot exceed the total number of cells.")

    # 使用一个临时的 solver 实例来获取邻居（避免在全局创建）
    temp_solver = MinesweeperSolver(board_size)
    mine_locations: Set[Tuple[int, int]] = set()

    # 随机放置地雷
    placed_mines = 0
    while placed_mines < num_mines:
        r = random.randint(0, board_size - 1)
        c = random.randint(0, board_size - 1)
        if (c, r) not in mine_locations:
            mine_locations.add((c, r))
            placed_mines += 1

    # 创建棋盘并计算数字
    solution_board = [[0 for _ in range(board_size)] for _ in range(board_size)]
    for r in range(board_size):
        for c in range(board_size):
            if (c, r) in mine_locations:
                solution_board[r][c] = -1  # -1 代表地雷 (内部表示)
                continue
            
            mine_count = 0
            for nc, nr in temp_solver._get_neighbors(c, r):
                if (nc, nr) in mine_locations:
                    mine_count += 1
            solution_board[r][c] = mine_count
    
    return solution_board, mine_locations

def create_puzzle_board(
    solution_board: List[List[int]], # 完整答案棋盘，-1是雷
    board_size: int,
    num_initial_reveals: int = 1, # 希望进行多少次独立的“初始点击”
    reveal_zeros_cascade: bool = True
) -> List[List[Optional[int]]]:
    """
    从完整答案棋盘创建一个谜题棋盘 (只包含数字和 None)。
    """
    puzzle_board: List[List[Optional[int]]] = [[None for _ in range(board_size)] for _ in range(board_size)]
    
    temp_solver = MinesweeperSolver(board_size) # 用于获取邻居
    
    # 用于模拟点击的队列和已处理集合
    cells_to_process_queue: List[Tuple[int,int]] = []
    # 记录已经被放入队列或已经被揭示的格子，避免重复处理或选择
    # 主要用于确保 num_initial_reveals 选择了不同的起始点
    already_selected_for_reveal_initiation: Set[Tuple[int,int]] = set()


    # 1. 选择初始揭示点
    initial_reveal_points_selected = 0
    attempts = 0
    max_attempts = board_size * board_size * 2 # 防止死循环

    # 优先选择数字为0的点进行初始揭示
    if reveal_zeros_cascade:
        zero_cells = []
        for r_idx in range(board_size):
            for c_idx in range(board_size):
                if solution_board[r_idx][c_idx] == 0:
                    zero_cells.append((c_idx, r_idx))
        random.shuffle(zero_cells) # 打乱一下顺序
        for zc, zr in zero_cells:
            if initial_reveal_points_selected < num_initial_reveals:
                if (zc, zr) not in already_selected_for_reveal_initiation:
                    cells_to_process_queue.append((zc, zr))
                    already_selected_for_reveal_initiation.add((zc,zr))
                    initial_reveal_points_selected +=1
            else:
                break
    
    # 如果0不够，或者不优先揭示0，则随机选择非雷点
    while initial_reveal_points_selected < num_initial_reveals and attempts < max_attempts:
        r, c = random.randint(0, board_size - 1), random.randint(0, board_size - 1)
        if solution_board[r][c] != -1 and (c,r) not in already_selected_for_reveal_initiation:
            cells_to_process_queue.append((c,r))
            already_selected_for_reveal_initiation.add((c,r))
            initial_reveal_points_selected += 1
        attempts += 1
    
    if not cells_to_process_queue and initial_reveal_points_selected == 0: # 如果一个点都没选上
        # 强制选一个非雷点
        for r_idx in range(board_size):
            for c_idx in range(board_size):
                 if solution_board[r_idx][c_idx] != -1:
                     cells_to_process_queue.append((c_idx, r_idx))
                     already_selected_for_reveal_initiation.add((c_idx,r_idx)) # 确保它也被记录
                     break
            if cells_to_process_queue:
                break
        if not cells_to_process_queue: # 还是没有（比如全雷棋盘），返回空谜题
             return puzzle_board


    # 2. 处理揭示队列（包括0的连锁反应）
    # 使用 already_selected_for_reveal_initiation 来确保不会重复处理连锁反应的起点
    # 但连锁反应自身也需要一个 processed_for_cascade 集合
    processed_in_cascade: Set[Tuple[int,int]] = set()

    while cells_to_process_queue:
        c, r = cells_to_process_queue.pop(0)
        
        if (c,r) in processed_in_cascade: # 如果在本次连锁反应中已处理过
            continue
        processed_in_cascade.add((c,r))

        cell_value = solution_board[r][c]
        puzzle_board[r][c] = cell_value # 揭示该格子

        if reveal_zeros_cascade and cell_value == 0:
            for nc, nr in temp_solver._get_neighbors(c, r):
                if (nc, nr) not in processed_in_cascade:
                    # 将0的邻居也加入队列，它们会被揭示
                    cells_to_process_queue.append((nc, nr))
                    
    return puzzle_board


if __name__ == '__main__':
    BOARD_SIZE = 10
    NUM_MINES = 12  # 调整雷数以获得合适的难度
    NUM_INITIAL_REVEAL_CLICKS = 2 # 初始“点击”多少个不同的地方

    solver = MinesweeperSolver(board_size=BOARD_SIZE)

    print(f"--- 测试用例 1: 随机生成棋盘 ---")
    for i in range(10):
        print(f"---------------------------------------随机棋盘{i+1}-------------------------------")
        print(f"棋盘参数: 大小={BOARD_SIZE}x{BOARD_SIZE}, 雷数={NUM_MINES}, 初始模拟点击数={NUM_INITIAL_REVEAL_CLICKS}")

        # 1. 生成完整答案板 (包含地雷和数字)
        solution_board_1, actual_mines_1 = generate_complete_board(BOARD_SIZE, NUM_MINES)

        # 2. 基于答案板生成谜题板 (只包含数字和None)
        puzzle_board_1 = create_puzzle_board(solution_board_1, BOARD_SIZE, NUM_INITIAL_REVEAL_CLICKS, reveal_zeros_cascade=True)

        print("\n[初始谜题棋盘 (提供给求解器)]")
        solver.render_board(puzzle_board_1, set(), set()) # 用空set渲染初始状态

        # 3. 求解器分析
        print("\n[求解器分析中...]")
        safe_coords_1, mine_coords_1 = solver.analyze_board(puzzle_board_1)

        # 4. 渲染结果
        print("\n[求解器分析结果渲染]")
        solver.render_board(puzzle_board_1, safe_coords_1, mine_coords_1)
        print(f"推断的安全格: {sorted(list(safe_coords_1))}")
        print(f"推断的地雷格: {sorted(list(mine_coords_1))}")
        # 可选：验证正确性 (如果需要)
        # print(f"实际地雷位置: {sorted(list(actual_mines_1))}")
        # correctly_identified_mines = mine_coords_1 == actual_mines_1 # 简单求解器可能无法找到所有雷
        # print(f"地雷推断是否完全正确: {correctly_identified_mines}")

    # print(f"\n\n--- 测试用例 2: 另一个随机棋盘 (不同参数) ---")
    # NUM_MINES_2 = 15
    # NUM_INITIAL_REVEAL_CLICKS_2 = 3
    # print(f"棋盘参数: 大小={BOARD_SIZE}x{BOARD_SIZE}, 雷数={NUM_MINES_2}, 初始模拟点击数={NUM_INITIAL_REVEAL_CLICKS_2}")

    # solution_board_2, actual_mines_2 = generate_complete_board(BOARD_SIZE, NUM_MINES_2)
    # puzzle_board_2 = create_puzzle_board(solution_board_2, BOARD_SIZE, NUM_INITIAL_REVEAL_CLICKS_2, reveal_zeros_cascade=True)

    # print("\n[初始谜题棋盘 2]")
    # solver.render_board(puzzle_board_2, set(), set())

    # print("\n[求解器分析中...]")
    # safe_coords_2, mine_coords_2 = solver.analyze_board(puzzle_board_2)

    # print("\n[求解器分析结果渲染 2]")
    # solver.render_board(puzzle_board_2, safe_coords_2, mine_coords_2)
    # print(f"推断的安全格: {sorted(list(safe_coords_2))}")
    # print(f"推断的地雷格: {sorted(list(mine_coords_2))}")


    # print(f"\n\n--- 测试用例 3: 空白棋盘 ---")
    # empty_board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # print("\n[初始空白棋盘]")
    # solver.render_board(empty_board, set(), set())
    # print("\n[求解器分析中...]")
    # safe_coords_empty, mine_coords_empty = solver.analyze_board(empty_board)
    # print("\n[求解器分析结果渲染 - 空白棋盘]")
    # solver.render_board(empty_board, safe_coords_empty, mine_coords_empty)
    # print(f"推断的安全格: {sorted(list(safe_coords_empty))}") # 应该是 {(中心点)}
    # print(f"推断的地雷格: {sorted(list(mine_coords_empty))}") # 应该是 []