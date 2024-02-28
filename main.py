import pygame as pg
import cairosvg
from io import BytesIO
import socket     
import threading

# Colors
background = (48, 46, 43)
white = (234, 233, 210)
black = (75, 115, 153)
green = (0, 255, 0)

# Global Variables
gameWindow = None
cell_dim = None
bx, by = None, None
board = None
valid_moves_board = None
my_color = 'white'
op_color = 'black'
piece_selected = False

def valid_coordinate(x, y):
    return x >= 0 and x < 8 and y >= 0 and y < 8

def load_svg(filename):
    # Convert SVG to PNG using cairosvg
    svg_content = open(filename, 'rb').read()
    png_content = cairosvg.svg2png(file_obj=BytesIO(svg_content), parent_width = cell_dim, parent_height = cell_dim)

    # Load the PNG content into a Pygame surface
    png_surface = pg.image.load(BytesIO(png_content))

    # Resize the Pygame surface
    resized_surface = pg.transform.scale(png_surface, (cell_dim, cell_dim))

    return resized_surface

class Piece:
    def __init__(self, color, ptype, path):
        self.color = color
        self.ptype = ptype
        self.path = path
        self.resized_svg_surface = load_svg(self.path)
        
    def place(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (bx + y*cell_dim, by + x*cell_dim))
        
        
class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'k', f'src/k-{color}.svg')
        self.dir = [[1, 1], [1, -1], [-1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(8):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            if valid_coordinate(cx, cy):
                if board[cx][cy] == '' or board[cx][cy].color == op_color:
                    moves.append([cx, cy])
        return moves

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, 'q', f'src/q-{color}.svg')
        self.dir = [[1, 1], [1, -1], [-1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(8):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            while valid_coordinate(cx, cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color == op_color:
                        moves.append([cx, cy])
                    break
                moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, 'b', f'src/b-{color}.svg')
        self.dir = [[1, 1], [1, -1], [-1, -1], [-1, 1]]
    
    def valid_moves(self, x, y):
        moves = []
        for i in range(4):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            while valid_coordinate(cx, cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color == op_color:
                        moves.append([cx, cy])
                    break
                moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, 'n', f'src/n-{color}.svg')
        self.dir = [
            [1, -2], [1, 2],
            [-1, -2], [-1, 2],
            [2, 1], [2, -1],
            [-2, 1], [-2, -1]
        ]
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(8):
            cx, cy = x + self.dir[i][0], y + self.dir[i][1]
            print(cx, cy)
            if valid_coordinate(cx, cy) and (board[cx][cy] == '' or board[cx][cy].color == op_color):
                moves.append([cx, cy])
        return moves
        
        
class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'r', f'src/r-{color}.svg')
        self.dir = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(4):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            while valid_coordinate(cx, cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color == op_color:
                        moves.append([cx, cy])
                    break
                moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'p', f'src/p-{color}.svg')
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(1, 3):
            cx, cy = x-i, y
            if not valid_coordinate(cx, cy):
                break
            if board[cx][cy] != '':
                if board[cx][cy].color == op_color:
                    moves.append([cx, cy])
                break
            moves.append([cx, cy])
        return moves

def main():
    
    global gameWindow, cell_dim, bx, by, board, piece_selected, valid_moves_board
    # Game window Dimensions
    width, height = 1200, 728
    
    # Cell dimension of board
    pad_y = 12
    cell_dim = (height - 2*pad_y)//8
    pad_x = (width - 8*cell_dim) // 2
    
    # Base Co-ordinates for chess board
    bx, by = pad_x, pad_y
    
    # Creating Board
    gameWindow = pg.display.set_mode((width, height))
    pg.display.set_caption('Chess Game')
    
    # Game specific Variables
    game_over = False
    
    # FPS
    clock = pg.time.Clock()
    fps = 30
    
    # Game loop
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                px = (event.pos[1] - by + cell_dim - 1) // cell_dim - 1
                py = (event.pos[0] - bx + cell_dim - 1) // cell_dim - 1
                
                if board[px][py] == '' or board[px][py].color != my_color:
                    continue
                
                valid_moves = board[px][py].valid_moves(px, py)
                
                print(valid_moves)
                
                for i in range(8):
                    for j in range(8):
                        valid_moves_board[i][j] = False
                        
                for move in valid_moves:
                    valid_moves_board[move[0]][move[1]] = True
                
        gameWindow.fill(background)
        
        # Create Chess board background
        cell_color = black
        
        for i in range(8):
            for j in range(8):
                pg.draw.rect(gameWindow, cell_color, [bx + i*cell_dim, by + j*cell_dim, cell_dim, cell_dim])
                if cell_color == black:
                    cell_color = white
                else:
                    cell_color = black
            if cell_color == black:
                cell_color = white
            else:
                cell_color = black
        
        
        # Initalize board first time
        if board == None:
            board = [['' for i in range(8)] for j in range(8)]
            # Place pieces of opposite color
            board[0][0] = board[0][7] = Rook(op_color)
            board[0][1] = board[0][6] = Knight(op_color)
            board[0][2] = board[0][5] = Bishop(op_color)
            board[0][3] = Queen(op_color)
            board[0][4] = King(op_color)
            
            for i in range(8):
                board[1][i] = Pawn(op_color)
                
            # Place pieces of my side color
            board[7][0] = board[7][7] = Rook(my_color)
            board[7][1] = board[7][6] = Knight(my_color)
            board[7][2] = board[7][5] = Bishop(my_color)
            board[7][3] = Queen(my_color)
            board[7][4] = King(my_color)
            
            
            for i in range(8):
                board[6][i] = Pawn(my_color)
        
        if valid_moves_board == None:
            valid_moves_board = [[False for i in range(8)] for _ in range(8)]
            
        # Place pieces
        for i in range(8):
            for j in range(8):
                if board[i][j] != '':
                    board[i][j].place(i, j)
                    
        for i in range(8):
            for j in range(8):
                if valid_moves_board[i][j]:
                    pg.draw.circle(gameWindow, green, (bx + j*cell_dim + cell_dim//2, by + i*cell_dim + cell_dim//2), 10)
                    
        clock.tick(fps)
        pg.display.update()
        

if __name__ == '__main__':
    main()