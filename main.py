import pygame as pg
import cairosvg
from io import BytesIO
import socket     
import threading

# Colors
background = (48, 46, 43)
white = (235, 236, 208)
black = (115, 149, 82)

# Global Variables
gameWindow = None
cell_dim = None
bx, by = None, None
board = None
my_color = None

def load_svg(filename, dim):
    # Convert SVG to PNG using cairosvg
    svg_content = open(filename, 'rb').read()
    png_content = cairosvg.svg2png(file_obj=BytesIO(svg_content), parent_width = dim, parent_height = dim)

    # Load the PNG content into a Pygame surface
    png_surface = pg.image.load(BytesIO(png_content))

    # Resize the Pygame surface
    resized_surface = pg.transform.scale(png_surface, (dim, dim))

    return resized_surface

class Piece:
    def __init__(self, color, ptype, path):
        self.color = color
        self.ptype = ptype
        self.path = path
        
    def place(self, x, y):
        resized_svg_surface = load_svg(self.path, cell_dim)
        gameWindow.blit(resized_svg_surface, (bx + y*cell_dim, by + x*cell_dim))
        
        
class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'k', f'src/k-{color}.svg')

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, 'q', f'src/q-{color}.svg')
        
class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, 'b', f'src/b-{color}.svg')
        
class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, 'n', f'src/n-{color}.svg')
        
class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'r', f'src/r-{color}.svg')
        
class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'p', f'src/p-{color}.svg')

def main():
    
    global gameWindow, cell_dim, bx, by
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
    
    # Game loop
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                print(event)
        gameWindow.fill(background)
        
        # Create Chess board
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
                
        k = King('white')
        k.place(0, 0)
        
        q = Queen('white')
        q.place(0, 1)
        
        b = Bishop('white')
        b.place(0, 2)
        
        n = Knight('white')
        n.place(0, 3)
        
        r = Rook('white')
        r.place(0, 4)
        
        p = Pawn('white')
        p.place(0, 5)
        
        
        k = King('black')
        k.place(1, 0)
        
        q = Queen('black')
        q.place(1, 1)
        
        b = Bishop('black')
        b.place(1, 2)
        
        n = Knight('black')
        n.place(1, 3)
        
        r = Rook('black')
        r.place(1, 4)
        
        p = Pawn('black')
        p.place(1, 5)
                
        
        pg.display.update()

if __name__ == '__main__':
    main()