import pygame as pg
import cairosvg
from io import BytesIO
import socket     
import threading
import os
import sys


pg.init()
# Initilization for Fonts in pygame
font = pg.font.Font('freesansbold.ttf', 32)

# Path for exe conversion
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Colors
background = (48, 46, 43)
white = (234, 233, 210)
black = (75, 115, 153)
green = (0, 255, 0)
blue = (0, 0, 255)
red = (255, 0, 0)
button_color = (50, 0, 255)

# Game Specific Variables
gameWindow = None
cell_dim = None
bx, by = None, None
board = None
valid_moves_board = None
opp_valid_moves = None
my_color = 'white'
op_color = 'black'
piece_selected = False
my_turn = True
port = 12345
is_joined = False
win = 0
fps = 30
clock = pg.time.Clock()

# Stop all threads var
stop_event = threading.Event()
stop_broadcast = threading.Event()

# Communication Variables
sx, sy = -1, -1
ex, ey = -1, -1

def broadcast_server_ip():
    global stop_event, stop_broadcast
    while not (stop_event.is_set() or stop_broadcast.is_set()):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.bind(('0.0.0.0', 37020))  # Broadcasting on port 37020

        while not stop_event.is_set():
            server_ip = socket.gethostbyname(socket.gethostname())
            server.sendto(server_ip.encode('utf-8'), ('<broadcast>', 37020))
            threading.Event().wait(5)  # Broadcast every 5 seconds
        
def handle_client(client_socket, address):
    global sx, sy, ex, ey, stop_event, my_turn, win
    while not stop_event.is_set():
        try:
            while not stop_event.is_set():
                if sx != -1 and ex != -1:
                    data = str(sx)+str(sy)+str(ex)+str(ey)
                    client_socket.send(data.encode('utf-8'))
                    if sx == 8:
                        stop_event.set()
                        break
                    if sx == 9:
                        stop_event.set()
                        break
                    my_turn = False
                    data = client_socket.recv(1024)
                    my_turn = True
                    updates = data.decode()
                    # Update start x,y end x,y
                    usx, usy, uex, uey = map(int, updates)
                    if usx == 8:
                        win = 1
                        stop_event.set()
                        break
                    if usx == 9:
                        win = -1
                        stop_event.set()
                        break
                    move_piece_from_opponent(usx, usy, uex, uey)
                    print(data.decode()) 
                    
        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break
        finally:
            client_socket.close()
            break
        
def run_server():
    global stop_event, is_joined, stop_broadcast
    threading.Thread(target=broadcast_server_ip).start()
    flg = False
    while not (flg or stop_event.is_set()):

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', port))
        server.listen(1)
        server.settimeout(100)

        print("Server listening on port 12345...")

        try:
            while not stop_event.is_set():
                client_socket, address = server.accept()
                print(f"Accepted connection from {address}")
                stop_broadcast.set()
                is_joined = True
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
    global sx, sy, ex, ey, stop_event, my_turn, is_joined, win
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
            while True:
                try:
                    client.connect((server_ip, port)) 
                    is_joined = True
                    break
                except:
                    pass

            while not stop_event.is_set(): 
                data = client.recv(1024)
                my_turn = True
                updates = data.decode()
                # Update start x,y end x,y
                usx, usy, uex, uey = map(int, updates)
                if usx == 8:
                    stop_event.set()
                    win = 1
                    break
                if usx == 9:
                    stop_event.set()
                    win = -1
                    break
                move_piece_from_opponent(usx, usy, uex, uey)
                
                print(data.decode()) 
                while sx == -1 or ex == -1:
                    pass
                data = str(sx)+str(sy)+str(ex)+str(ey)
                client.send(data.encode('utf-8'))
                if sx == 8:
                    stop_event.set()
                    break
                if sx == 9:
                    stop_event.set()
                    break
                my_turn = False


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
        self.path = resource_path(path)
        self.resized_svg_surface = load_svg(self.path)
        
    def place(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (bx + y*cell_dim, by + x*cell_dim))
        
    def place_transition(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (x,y))
        
        
class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'k', f'src/k-{color}.svg')
        self.has_moved = False
        self.dir = [[1, 1], [1, -1], [-1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
        
    def valid_moves(self, x, y):
        global board
        moves = []
        for i in range(8):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            if valid_coordinate(cx, cy):
                if (board[cx][cy] == '' or board[cx][cy].color != board[x][y].color) and is_valid_move(x,y,cx,cy):
                    moves.append([cx, cy])
        if self.has_moved:
            return moves

        # Left Side Castling
        flg = True
        for i in range(y-1, 0, -1): 
            if (not is_valid_move(x, y, x, i)) or board[x][i] != '':
                flg = False
        if not is_valid_move(x, y, x, y):
            flg = False
        if flg and (board[x][0] != '' and board[x][0].ptype == 'r' and board[x][0].has_moved == False):
            moves.append([x, y-2])
            
        # Right Side Castling
        flg = True
        for i in range(y+1, 7): 
            if (not is_valid_move(x, y, x, i)) or board[x][i] != '':
                flg = False
        if not is_valid_move(x, y, x, y):
            flg = False
        if flg and (board[x][7] != '' and board[x][7].ptype == 'r' and board[x][7].has_moved == False):
            moves.append([x, y+2])
        return moves

class Queen(Piece):
    global board
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
                    if board[cx][cy].color != board[x][y].color and is_valid_move(x,y,cx,cy):
                        moves.append([cx, cy])
                    break
                if  is_valid_move(x,y,cx,cy):
                    moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Bishop(Piece):
    global board
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
                    if board[cx][cy].color != board[x][y].color:
                        if is_valid_move(x,y,cx,cy):
                            moves.append([cx, cy])
                    break
                if  is_valid_move(x,y,cx,cy):
                    moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Knight(Piece):
    global board
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
            if valid_coordinate(cx, cy) and (board[cx][cy] == '' or board[cx][cy].color != board[x][y].color) and is_valid_move(x,y,cx,cy):
                moves.append([cx, cy])
        return moves
        
        
class Rook(Piece):
    global board
    def __init__(self, color):
        super().__init__(color, 'r', f'src/r-{color}.svg')
        self.has_moved = False
        self.dir = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        
    def valid_moves(self, x, y):
        moves = []
        for i in range(4):
            dx, dy = self.dir[i][0], self.dir[i][1]
            cx = x + dx
            cy = y + dy
            while valid_coordinate(cx, cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color != board[x][y].color and is_valid_move(x,y,cx,cy):
                        moves.append([cx, cy])
                    break
                if  is_valid_move(x,y,cx,cy):
                    moves.append([cx, cy])
                cx += dx
                cy += dy
        return moves
        
class Pawn(Piece):
    global board
    def __init__(self, color):
        super().__init__(color, 'p', f'src/p-{color}.svg')
        
    def valid_moves(self, x, y):
        global opp_valid_moves
        moves = []
        if x == 6:
            for i in range(5, 3, -1):
                if board[i][y] == '' and is_valid_move(x,y,i,y):
                    moves.append([i, y])
                else:
                    break
        else:
            if board[x-1][y] == '' and is_valid_move(x,y,x-1,y):
                moves.append([x-1, y])

        if valid_coordinate(x-1, y-1) and board[x-1][y-1] != '' and board[x-1][y-1].color != board[x][y].color and is_valid_move(x,y,x-1,y-1):
            moves.append([x-1, y-1])
        if valid_coordinate(x-1, y+1) and board[x-1][y+1] != '' and board[x-1][y+1].color != board[x][y].color and is_valid_move(x,y,x-1,y+1):
            moves.append([x-1, y+1])
            
        return moves

def is_valid_move(sx,sy,ex,ey):
    global board,op_color,my_color
    if not( sx==ex and sy==ey):
        temp=board[ex][ey]
        board[ex][ey]=board[sx][sy]
        board[sx][sy]=''
    
    king_pos=None
    for i in range(8):
        for j in range(8):
            if board[i][j]!='' and board[i][j].color==my_color and board[i][j].ptype=='k':
                king_pos=[i,j]
    x,y=king_pos[0],king_pos[1]
    dir = [[1, 1], [1, -1], [-1, -1], [-1, 1], [0, 1], [0, -1], [1, 0], [-1, 0]]
    flg=True
    for i in range(8):
            dx, dy = dir[i][0], dir[i][1]
            cx = x + dx
            cy = y + dy
            if valid_coordinate(cx,cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color != board[x][y].color:
                        if board[cx][cy].ptype=='k':
                            flg=False
            while valid_coordinate(cx, cy):
                if board[cx][cy] != '':
                    if board[cx][cy].color != board[x][y].color:
                        if board[cx][cy].ptype=='q':
                            flg=False
                        if dx==0 or dy==0:
                            if board[cx][cy].ptype=='r':
                                flg=False
                        else :
                            if board[cx][cy].ptype=='b':
                                flg=False
                    break
                cx += dx
                cy += dy

    if valid_coordinate(x-1,y-1) and board[x-1][y-1]!='' and board[x-1][y-1].color==op_color and board[x-1][y-1].ptype=='p':
        flg=False
    if valid_coordinate(x-1,y+1) and board[x-1][y+1]!='' and board[x-1][y+1].color==op_color and board[x-1][y+1].ptype=='p':
        flg=False
    dir = [
            [1, -2], [1, 2],
            [-1, -2], [-1, 2],
            [2, 1], [2, -1],
            [-2, 1], [-2, -1]
        ]
    
    for i in range(8):
        cx, cy = x + dir[i][0], y + dir[i][1]
        if valid_coordinate(cx, cy) and (board[cx][cy] != '' and board[cx][cy].color != board[x][y].color) and board[cx][cy].ptype=='n':
                flg=False
    
    if not( sx==ex and sy==ey):
        board[sx][sy]=board[ex][ey]
        board[ex][ey]=temp
    return flg

# Function to move piece from one cell to another
def move_piece():
    global sx, sy, ex, ey, board
    if sx == -1 or sy == -1 or ex == -1 or ey == -1:
        return
    print(sx, sy, ex, ey)
    board[ex][ey]=board[sx][sy]
    board[sx][sy]=''
    sx, sy, ex, ey = -1, -1, -1, -1
    
# Function to move piece from signal of opponents
def move_piece_from_opponent(sx, sy, ex, ey):
    global board
    if board[7-sx][7-sy].ptype=='k':
        if ey-sy == 2:
            move_piece_from_opponent(7,7,ex,ey-1)
        elif sy-ey == 2:
            move_piece_from_opponent(7,0,ex,ey+1)
    sx = 7-sx
    sy = 7-sy
    ex = 7-ex
    ey = 7-ey
    board[ex][ey]=board[sx][sy]
    board[sx][sy]=''
    
def clear_valid_board():
    global valid_moves_board
    for i in range(8):
        for j in range(8):
            valid_moves_board[i][j] = False
    
# function which renders text on screen
def write(text, x, y):
    global gameWindow
    text = font.render(text, True, green, blue)
    
    textRect = text.get_rect()
    textRect.center = (x, y)
    
    gameWindow.blit(text, textRect)
    
def middle_screen_create():
    global gameWindow, is_joined, fps, clock
    width, height = 1200, 728
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill(white)
    
    
         
    write("Waiting for a player to join", width//2, height//2)
    while not is_joined:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_joined = True
                stop_event.set()
                pg.quit()
                exit()
        clock.tick(fps)
        pg.display.update()
    pg.quit()

def middle_screen_join():
    global gameWindow, is_joined, port, fps, clock
    width, height = 1200, 728
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill(white)
    
    
    write("Finding Nearby Game", width//2, height//2)
             
    while not is_joined:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_joined = True
                stop_event.set()
                pg.quit()
                exit()
        clock.tick(fps)
        pg.display.update()
    pg.quit()
    
# Function for welcome screen
def welcome():
    global gameWindow, my_color, op_color, my_turn, fps, clock,is_joined
    width, height = 1200, 728
    is_joined=False
    # Creating Board
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill(white)
    
    write("Single Device Play (Press S)", width//2, 200)
    write("Create Game - Play White (Press C)", width//2, 350)
    write("Join Game - Play Black (Press J)", width//2, 500)
    
    
    game_over = False
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    main()
                    game_over = True
                if event.key == pg.K_c:
                    threading.Thread(target=run_server).start()
                    middle_screen_create()
                    main()
                    game_over = True
                elif event.key == pg.K_j:
                    my_color = 'black'
                    op_color = 'white'
                    my_turn = False
                    threading.Thread(target=discover_servers).start()
                    middle_screen_join()
                    main()
                    game_over = True
                    
        clock.tick(fps)
        pg.display.update()
def is_checkmated():
    global board, my_color, op_color,win
    flg = True
    cnt=0
    for i in range(8):
        for j in range(8):
            if board[i][j] != '' and board[i][j].color == my_color:
                if len(board[i][j].valid_moves(i, j)):
                    flg = False
            if board[i][j] != '':cnt+=1
    king_pos=None
    for i in range(8):
        for j in range(8):
            if board[i][j]!='' and board[i][j].color==my_color and board[i][j].ptype=='k':
                king_pos=[i,j]
    x,y=king_pos[0],king_pos[1]
    if (flg and is_valid_move(x,y,x,y)) or cnt==2:
        win=-1
        flg=False
    return flg
def flip_board():
    global board
    for i in range(4):
        for j in range(8):
            t = board[i][j]
            board[i][j] = board[7-i][7-j]
            board[7-i][7-j] = t
def main():
    global gameWindow, cell_dim, bx, by, board, piece_selected, valid_moves_board, sx, sy, ex, ey, stop_event, opp_valid_moves,my_color,op_color, win, is_joined, fps, clock
    # Game window Dimensions
    width, height = 1200, 728
    win=0
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
    
    opp_valid_moves = [[False for _ in range(8)]*8]
    
    # Place pieces of opposite color
    # board[0][0] = Rook(op_color)
    # board[0][7] = Rook(op_color)
    # board[0][1] = board[0][6] = Knight(op_color)
    # board[0][2] = board[0][5] = Bishop(op_color)
    board[0][3] = Queen(op_color)
    board[0][4] = King(op_color)
    if my_color == 'black':
        board[0][4] = Queen(op_color)
        board[0][3] = King(op_color)
        
    # for i in range(8):
    #     board[1][i] = Pawn(op_color)
        
    # Place pieces of my side color
    # board[7][0] = Rook(my_color)
    # board[7][7] = Rook(my_color)
    # board[7][1] = board[7][6] = Knight(my_color)
    # board[7][2] = board[7][5] = Bishop(my_color)
    board[7][3] = Queen(my_color)
    board[7][4] = King(my_color)
    if my_color == 'black':
        board[7][4] = Queen(my_color)
        board[7][3] = King(my_color)
    
    valid_moves_board = [[False for i in range(8)] for _ in range(8)]
    
    # for i in range(8):
    #     board[6][i] = Pawn(my_color)
    pg.display.set_caption('Chess Game')
    
    # Game loop
    while not game_over:
        if is_checkmated():
            sx, sy, ex, ey = 8, 8, 8, 8
            game_over = True
            PlayAgainOrQuit()
            sys.exit()
        if win==1:
            sx, sy, ex, ey = 9, 9, 9, 9
            game_over = True
            PlayAgainOrQuit()
            sys.exit()
        if win==-1:
            game_over=True
            print("stalemate")
            PlayAgainOrQuit()
            sys.exit()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                    
                if not my_turn:
                    continue
                
                px = (event.pos[1] - by + cell_dim - 1) // cell_dim - 1
                py = (event.pos[0] - bx + cell_dim - 1) // cell_dim - 1
                
                
                if not valid_coordinate(px, py):
                    continue
                
                if board[px][py] == '' and not valid_moves_board[px][py]:
                    continue
                
                if (board[px][py] == '' or board[px][py].color != my_color) and valid_moves_board[px][py]:
                    if sx < 0:
                        continue
                    ex, ey = px, py
                    if board[sx][sy].ptype == 'k' or board[sx][sy].ptype == 'r':
                        print("Has Moved: ", sx, sy, ex, ey)
                        board[sx][sy].has_moved = True 
                    
                    if board[sx][sy].ptype=='k':
                        if ey-sy == 2: 
                            board[ex][ey-1]=board[7][7]
                            board[7][7]=''
                        elif sy-ey == 2:
                            board[ex][ey+1]=board[7][0]
                            board[7][0]=''

                    move_piece() 
                    
                    print("1: ", sx, sy, ex, ey)
                    clear_valid_board()
                    if not is_joined:
                        my_color,op_color=op_color,my_color
                        flip_board()
                
                elif board[px][py].color == my_color:
                    sx, sy = px, py    
                    valid_moves = board[px][py].valid_moves(px, py)
                    print("2: ", sx, sy, ex, ey)
                    
                    clear_valid_board()
                            
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
                    
        if sx != -1:
            pg.draw.rect(gameWindow, green, (bx + sy*cell_dim, by + sx*cell_dim, cell_dim, cell_dim), 5)
                    
        for i in range(8):
            for j in range(8):
                if valid_moves_board[i][j]:
                    pg.draw.circle(gameWindow, green, (bx + j*cell_dim + cell_dim//2, by + i*cell_dim + cell_dim//2), 10)
                    
        clock.tick(fps)
        pg.display.update()
    pg.quit()

    welcome() 
def blurSurf(surface, amt): 
    if amt < 1.0:
        raise ValueError("Arg 'amt' must be greater than 1.0, passed in value is %s"%amt)
    scale = 1.0/float(amt)
    surf_size = surface.get_size()
    scale_size = (int(surf_size[0]*scale), int(surf_size[1]*scale))
    surf = pg.transform.smoothscale(surface, scale_size)
    surf = pg.transform.smoothscale(surf, surf_size)
    return surf 
def PlayAgainOrQuit():
    global win
    width, height = 1200, 728
    
    # Game specific Variables
    game_over = False
    clock = pg.time.Clock()
    blurred_background = blurSurf(gameWindow,70)

    # Creating Board
    # gameWindow = pg.display.set_mode((width, height))
    # pg.display.set_caption('Chess Game')
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()

                play_again_button = pg.Rect(300, 300, 250, 80)
                quit_button = pg.Rect(700, 300, 250, 80)

                if play_again_button.collidepoint(mouse_pos): 
                    welcome()
                    sys.exit()
                    # Add your play again logic here
                elif quit_button.collidepoint(mouse_pos):
                    pg.quit()
                    sys.exit()

        gameWindow.blit(blurred_background,(0,0))
        # pg.draw.rect(gameWindow,white,(200,180,800,200))

        play_again_button = pg.draw.rect(gameWindow, button_color, (300, 300, 250, 80))
        quit_button = pg.draw.rect(gameWindow, button_color, (700, 300, 250, 80))
        result_button = pg.draw.rect(gameWindow, button_color, (500, 200, 250, 80))

        play_again_text = font.render("Play Again", True, white)
        quit_text = font.render("Quit", True, white)

        gameWindow.blit(play_again_text, (play_again_button.centerx - play_again_text.get_width() // 2,
                                    play_again_button.centery - play_again_text.get_height() // 2))
        gameWindow.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2,
                                quit_button.centery - quit_text.get_height() // 2))
        result_text=""
        if is_joined==False:
            if my_color=='black':
                result_text = "White won!"
            else:
                result_text = "Black won!"
            if win==-1:
                result_text = "Stalemate!"
        else :
            if win == 1: 
                result_text = "You won"
            elif win == 0:
                result_text = "You lose"
            elif win == -1:
                result_text = "Stalemate"
        result_text = font.render(result_text, True, white)
        gameWindow.blit(result_text, (result_button.centerx - result_text.get_width() // 2,
                                result_button.centery - result_text.get_height() // 2))
        
        # result_surface = font.render(result_text, True, white,button_color)
        # gameWindow.blit(result_surface, (width // 2 - result_surface.get_width() // 2, 200))


 
        clock.tick(fps)
        pg.display.update()
    pg.quit()

if __name__ == '__main__':
    welcome() 