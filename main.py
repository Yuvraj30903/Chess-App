import pygame as pg
import cairosvg
from io import BytesIO
import socket     
import threading
from time import sleep
import sys
from random import randint

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
my_turn = True

# Stop all threads var
stop_event = threading.Event()

# Communication Variables
sx, sy = -1, -1
ex, ey = -1, -1

def broadcast_server_ip():
    global stop_event
    while not stop_event.is_set():
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.bind(('0.0.0.0', 37020))  # Broadcasting on port 37020

        while not stop_event.is_set():
            server_ip = socket.gethostbyname(socket.gethostname())
            server.sendto(server_ip.encode('utf-8'), ('<broadcast>', 37020))
            threading.Event().wait(5)  # Broadcast every 5 seconds
        
def handle_client(client_socket, address):
    global sx, sy, ex, ey, stop_event
    while not stop_event.is_set():
        try:
            while not stop_event.is_set():
                if sx != -1:
                    print(sx, sy)
                    data = str(sx)+str(sy)
                    client_socket.send(data.encode('utf-8'))
                    sx, sy = -1, -1
                    data = client_socket.recv(1024)
                    print(data.decode()) 
        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break
        finally:
            client_socket.close()
            break
        
def run_server():
    global stop_event
    threading.Thread(target=broadcast_server_ip).start()
    flg = False
    while not (flg or stop_event.is_set()):

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 12345))
        server.listen(1)
        server.settimeout(10)

        print("Server listening on port 12345...")

        try:
            while not stop_event.is_set():
                client_socket, address = server.accept()
                print(f"Accepted connection from {address}")
                flg = True
                if flg:
                    break
                # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.start()
        except socket.timeout:
            print("Code expired. No player found. Quitting the game")
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            server.close()
        
def discover_servers():
    global sx, sy, ex, ey, stop_event
    flg = False
    while not (flg or stop_event.is_set()):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('0.0.0.0', 37020))

        print("Searching for nearby servers...")

        try:
            flag=True
            while flag:
                data, addr = client.recvfrom(1024)
                server_ip = data.decode('utf-8')
                print(f"Found nearby server: {server_ip}")
                flag=False
            print(server_ip)

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((server_ip, 12345)) 

            pt=0
            while not stop_event.is_set(): 
                data = client.recv(1024)
                print(data.decode()) 
                while sx == -1:
                    pass
                data = str(sx)+str(sy)
                client.send(data.encode('utf-8'))
                print(sx, sy)
                sx, sy = -1, -1


        except KeyboardInterrupt:
            print("Discovery stopped.")

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
        
    def place_transition(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (x,y))
        
        
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

# Transition Logic
def generate_equal_parts(x1, y1, x2, y2, num_parts=10):
    # Calculate step sizes for x and y coordinates
    step_x = (x2 - x1) / (num_parts - 1)
    step_y = (y2 - y1) / (num_parts - 1)

    # Generate the 10 equally spaced points
    points = [(int(x1 + i * step_x), int(y1 + i * step_y)) for i in range(num_parts)]

    return points

# Function to move piece from one cell to another
def move_piece():
    global sx, sy, ex, ey
    s_x, s_y = bx + sy*cell_dim, by + sx*cell_dim 
    e_x, e_y = bx + ey*cell_dim, by + ex*cell_dim
    # print(px,py,fx,fy)
    # print(dx,dy)
    moves=generate_equal_parts(s_x, s_y, e_x, e_y)
    for i in range(1,len(moves)): 
        board[sx][sy].place_transition(moves[i][0],moves[i][1]) 
        pg.display.update()
        pass
    board[ex][ey]=board[sx][sy]
    board[sx][sy]=''
    
def clear_valid_baord():
    global valid_moves_board
    for i in range(8):
        for j in range(8):
            valid_moves_board[i][j] = False
    
# Function for welcome screen
def welcome():
    global gameWindow, my_color, op_color, my_turn
    width, height = 1200, 728
        
    # Creating Board
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill(white)
    
    clock = pg.time.Clock()
    fps = 30
    
    game_over = False
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_c:
                    # threading.Thread(target=run_server).start()
                    main()
                    game_over = True
                elif event.key == pg.K_j:
                    my_color = 'black'
                    op_color = 'white'
                    my_turn = False
                    # threading.Thread(target=discover_servers).start()
                    main()
                    game_over = True
                    
        clock.tick(fps)
        pg.display.update()

def main():
    
    global gameWindow, cell_dim, bx, by, board, piece_selected, valid_moves_board, sx, sy, ex, ey, stop_event
    # Game window Dimensions
    width, height = 1200, 728
    
    # Cell dimension of board
    pad_y = 12
    cell_dim = (height - 2*pad_y)//8
    pad_x = (width - 8*cell_dim) // 2
    
    # Base Co-ordinates for chess board
    bx, by = pad_x, pad_y
    
    # Game specific Variables
    game_over = False
    
    # Creating Board
    gameWindow = pg.display.set_mode((width, height))
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
    
    valid_moves_board = [[False for i in range(8)] for _ in range(8)]
    
    for i in range(8):
        board[6][i] = Pawn(my_color)
    pg.display.set_caption('Chess Game')
    
    # FPS
    clock = pg.time.Clock()
    fps = 30
    
    # Game loop
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
                pg.quit()
                sys.exit(0)
            elif event.type == pg.MOUSEBUTTONDOWN:
                    
                px = (event.pos[1] - by + cell_dim - 1) // cell_dim - 1
                py = (event.pos[0] - bx + cell_dim - 1) // cell_dim - 1
                
                if not my_turn:
                    continue
                
                if not valid_coordinate(px, py):
                    continue
                
                if board[px][py] == '' and not valid_moves_board[px][py]:
                    continue
                
                if (board[px][py] == '' or board[px][py].color != my_color) and valid_moves_board[px][py]:
                    ex, ey = px, py
                    move_piece()
                    clear_valid_baord()
                
                elif board[px][py].color == my_color:
                    sx, sy = px, py    
                    valid_moves = board[px][py].valid_moves(px, py)
                    
                    clear_valid_baord()
                            
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
    welcome()