import random
from typing import List, Tuple, Optional, Set

class MinesweeperSolver:
    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.reset_board()
        
    def reset_board(self):
        # Initialize the board, None means unknown, number means mines around, -1 means mine
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        # Record clicked positions
        self.clicked = set()
        # Mark potential mine positions
        self.potential_mines = set()
        # Mark safe positions
        self.safe_moves = set()
        
    def update_board(self, tiles: List[List[Optional[int]]]):
        """Update internal board based on API response"""
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if tiles[y][x] is not None:
                    self.board[y][x] = tiles[y][x]
                    self.clicked.add((x, y))
        
        # Analyze board after update
        self.analyze_board()
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get adjacent positions for a given position"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    neighbors.append((nx, ny))
        return neighbors
    
    def analyze_board(self):
        """Analyze board, mark potential mines and safe positions"""
        self.safe_moves.clear()
        new_potential_mines = set()
        
        # Analyze each known number and its surrounding unclicked cells
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] is not None and self.board[y][x] > 0:
                    # Get surrounding unclicked positions
                    unclicked_neighbors = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                          if (nx, ny) not in self.clicked and self.board[ny][nx] is None]
                    mines_needed = self.board[y][x]
                    
                    # If the number of unclicked cells equals the number of mines needed, they are all mines
                    if len(unclicked_neighbors) == mines_needed:
                        for nx, ny in unclicked_neighbors:
                            new_potential_mines.add((nx, ny))
                    
                    # Check marked mines
                    marked_mines = [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                                   if (nx, ny) in self.potential_mines]
                    
                    # If the number of marked mines equals the mines needed, other unclicked cells are safe
                    if len(marked_mines) == mines_needed:
                        for nx, ny in unclicked_neighbors:
                            if (nx, ny) not in self.potential_mines:
                                self.safe_moves.add((nx, ny))
        
        self.potential_mines = new_potential_mines
        
        # If no safe moves found, try to find cells around 0 (they are definitely safe)
        if not self.safe_moves:
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if self.board[y][x] == 0:
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) not in self.clicked and self.board[ny][nx] is None:
                                self.safe_moves.add((nx, ny))
    
    def get_next_move(self) -> Tuple[int, int]:
        """Get the next position to click"""
        # If there are known safe positions, choose one
        if self.safe_moves:
            move = self.safe_moves.pop()
            return move
        
        # If no safe positions determined, use probability strategy
        # 1. Find all unclicked positions not in potential mines list
        candidates = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked and (x, y) not in self.potential_mines:
                    candidates.append((x, y))
        
        if not candidates:
            # If no obvious safe choices, try to find edge positions with lowest probability
            edge_tiles = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked and self.board[y][x] is None:
                        # Check if it's an edge (at least one neighbor has been clicked)
                        for nx, ny in self.get_neighbors(x, y):
                            if (nx, ny) in self.clicked:
                                edge_tiles.append((x, y))
                                break
            
            if edge_tiles:
                # Calculate risk score for each edge position
                risk_scores = {}
                for x, y in edge_tiles:
                    # If position is in potential mines list, give high risk
                    if (x, y) in self.potential_mines:
                        risk_scores[(x, y)] = float('inf')
                        continue
                    
                    risk = 0
                    revealed_neighbors = 0
                    for nx, ny in self.get_neighbors(x, y):
                        if (nx, ny) in self.clicked and self.board[ny][nx] is not None:
                            if self.board[ny][nx] > 0:  # Higher number means higher risk
                                risk += self.board[ny][nx]
                            revealed_neighbors += 1
                    
                    if revealed_neighbors > 0:
                        risk_scores[(x, y)] = risk / revealed_neighbors
                    else:
                        risk_scores[(x, y)] = 0
                
                # Choose position with lowest risk
                if risk_scores:
                    return min(risk_scores.items(), key=lambda x: x[1])[0]
            
            # If above strategies don't work, randomly choose an unclicked position
            available_moves = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) not in self.clicked:
                        available_moves.append((x, y))
            
            if not available_moves:
                raise ValueError("No available moves")
            
            return random.choice(available_moves)
        
        # Prioritize positions with numbers around (more information for reasoning)
        informed_moves = []
        for x, y in candidates:
            for nx, ny in self.get_neighbors(x, y):
                if (nx, ny) in self.clicked and self.board[ny][nx] is not None and self.board[ny][nx] > 0:
                    informed_moves.append((x, y))
                    break
        
        if informed_moves:
            return random.choice(informed_moves)
        
        # If no more information, randomly choose a candidate position
        if candidates:
            return random.choice(candidates)
        
        # Last fallback strategy: randomly choose an unclicked position
        available_moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) not in self.clicked:
                    available_moves.append((x, y))
        
        if not available_moves:
            raise ValueError("No available moves")
        
        return random.choice(available_moves) 