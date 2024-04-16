import pygame as pg
import cairosvg
from io import BytesIO
import socket     
import threading
import os
import sys
from time import sleep


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
button_color = (0, 0, 0)

# Game Specific Variables
gameWindow = None 
cell_dim = None            # Cell Dimensions
board = None               # 2-D list for storing information of pieces
valid_moves_board = None   # 2-D list for showing valid moves with help of green centers
my_turn = True             # Variable to keep track of turn
my_color = 'white'
op_color = 'black'
port = 12345
is_joined = False          # Variable to check if other player has joined game or not
win = 0                    # Variable to check for win
fps = 30
display_info = pg.display.Info()
width, height = int(display_info.current_w*0.8), int(display_info.current_h*0.8)


# Cell dimension of board
pad_y = 12
cell_dim = (height - 2*pad_y)//8
pad_x = (width - 8*cell_dim) // 2

# Base Co-ordinates for chess board
bx, by = pad_x, pad_y

clock = pg.time.Clock()


stop_event = threading.Event()       # Stop all threads var
stop_broadcast = threading.Event()   # Event for stopping broadcasting IP after player joined

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
                # Connection established now no need to broadcast ip
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
    global cell_dim
    # Convert SVG to PNG using cairosvg
    svg_content = open(filename, 'rb').read()
    png_content = cairosvg.svg2png(file_obj=BytesIO(svg_content), parent_width = cell_dim, parent_height = cell_dim)

    # Load the PNG content into a Pygame surface
    png_surface = pg.image.load(BytesIO(png_content))

    # Resize the Pygame surface
    resized_surface = pg.transform.scale(png_surface, (cell_dim, cell_dim))

    return resized_surface

# Piece class storing information of piece
class Piece:
    global gameWindow
    def __init__(self, color, ptype, path):
        self.color = color
        self.ptype = ptype
        self.path = resource_path(path)
        self.resized_svg_surface = load_svg(self.path)
        
    def place(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (bx + y*cell_dim, by + x*cell_dim))
        
    def place_transition(self, x, y):
        gameWindow.blit(self.resized_svg_surface, (x,y))
        
# Class for King piece
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

# Class for Queen piece
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

# Class for Bishop Piece        
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
        
# Class for Knight Piece        
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
        
        
# Class for Rook Piece        
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
        
# Class for Pawn Piece        
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
    
# Pre-loading of pawn-promotion UI svgs
    
pawn_promo_queen_w = Queen('white')
pawn_promo_bishop_w = Bishop('white')
pawn_promo_knight_w = Knight('white')
pawn_promo_rook_w = Rook('white')

pawn_promo_queen_b = Queen('black')
pawn_promo_bishop_b = Bishop('black')
pawn_promo_knight_b = Knight('black')
pawn_promo_rook_b = Rook('black')


# Check if move from start to end is a valid move or not
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
    global sx, sy, ex, ey, board, my_color
    if sx == -1 or sy == -1 or ex == -1 or ey == -1:
        return
    
    # If condition to check pawn Prmotion
    if board[sx][sy].ptype == 'p' and sx == 1:
        if my_color == 'black':
            if ex == 0:
                board[sx][sy] = pawn_promo_queen_b
            elif ex == 1:
                board[sx][sy] = pawn_promo_bishop_b
            elif ex == 2:
                board[sx][sy] = pawn_promo_knight_b
            elif ex == 3:
                board[sx][sy] = pawn_promo_rook_b
        else:
            if ex == 0:
                board[sx][sy] = pawn_promo_queen_w
            elif ex == 1:
                board[sx][sy] = pawn_promo_bishop_w
            elif ex == 2:
                board[sx][sy] = pawn_promo_knight_w
            elif ex == 3:
                board[sx][sy] = pawn_promo_rook_w
        board[0][ey] = board[sx][sy]
        board[sx][sy] = ''
        return
    print(sx, sy, ex, ey)
    board[ex][ey]=board[sx][sy]
    board[sx][sy]=''
    sx, sy, ex, ey = -1, -1, -1, -1
    
# Function to move piece from message recieved by opponent
def move_piece_from_opponent(sx, sy, ex, ey):
    global board, op_color
    
    # Condition to perform opponents's Castling
    if board[7-sx][7-sy].ptype=='k':
        if ey-sy == 2:
            move_piece_from_opponent(7,7,ex,ey-1)
        elif sy-ey == 2:
            move_piece_from_opponent(7,0,ex,ey+1)
            
    # 180 degree rotation in opposite machine
    sx = 7-sx
    sy = 7-sy
    ex = 7-ex
    ey = 7-ey
    
    # Perform opponent's Pawn Promotion Move
    if board[sx][sy].ptype == 'p' and sx == 6:
        ex = 7-ex
        if op_color == 'black':
            if ex == 0:
                board[sx][sy] = pawn_promo_queen_b
            elif ex == 1:
                board[sx][sy] = pawn_promo_bishop_b
            elif ex == 2:
                board[sx][sy] = pawn_promo_knight_b
            elif ex == 3:
                board[sx][sy] = pawn_promo_rook_b
        else:
            if ex == 0:
                board[sx][sy] = pawn_promo_queen_w
            elif ex == 1:
                board[sx][sy] = pawn_promo_bishop_w
            elif ex == 2:
                board[sx][sy] = pawn_promo_knight_w
            elif ex == 3:
                board[sx][sy] = pawn_promo_rook_w
        ex = 7
    board[ex][ey]=board[sx][sy]
    board[sx][sy]=''
    
def clear_valid_board():
    global valid_moves_board
    for i in range(8):
        for j in range(8):
            valid_moves_board[i][j] = False
    
# function to render text on screen
def write(text, x, y):
    global gameWindow
    text = font.render(text, True, (255, 255, 255), (0, 0, 0))
    
    textRect = text.get_rect()
    textRect.center = (x, y)
    
    gameWindow.blit(text, textRect)
  
# Screen for waiting of another player  
def middle_screen_create():
    global gameWindow, is_joined, fps, clock, width, height
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill((0, 0, 0))
    pg.display.set_caption('Chess Game')
    
    background_image = pg.image.load(resource_path("src/middle-bg.jpeg")).convert()
    background_image = pg.transform.scale(background_image, (height, height))
    bg_width, bg_height = background_image.get_rect().size

    # Calculate the position to center the image horizontally
    bg_x = (width - bg_width) // 2
    bg_y = 0  # Align at the top of the window

    gameWindow.blit(background_image, (bg_x, bg_y))
    pg.display.update()
         
    write("Waiting For a player to join", width//2, height//2)
    
    while not is_joined:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_joined = True
                stop_event.set()
                pg.quit()
                sys.exit(0)
        clock.tick(fps)
        pg.display.update()
        
# Screen for finding nearby games
def middle_screen_join():
    global gameWindow, is_joined, port, fps, clock, width, height
    gameWindow = pg.display.set_mode((width, height))
    gameWindow.fill((0, 0, 0))
    pg.display.set_caption('Chess Game')
    
    background_image = pg.image.load(resource_path("src/middle-bg.jpeg")).convert()
    background_image = pg.transform.scale(background_image, (height, height))
    bg_width, bg_height = background_image.get_rect().size

    # Calculate the position to center the image horizontally
    bg_x = (width - bg_width) // 2
    bg_y = 0  # Align at the top of the window

    gameWindow.blit(background_image, (bg_x, bg_y))
    pg.display.update()
    
    write("Finding Nearby Game", width//2, height//2)
             
    while not is_joined:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                is_joined = True
                stop_event.set()
                pg.quit()
                sys.exit(0)
        clock.tick(fps)
        pg.display.update()
        
# Function to draw rounded buttons
def draw_button(x, y, width, height, radius, color, text):
    global gameWindow
    rect = pg.Rect(x, y, width, height)
    pg.draw.rect(gameWindow, color, rect, border_radius=radius)
    font = pg.font.SysFont(None, 30)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    gameWindow.blit(text_surface, text_rect)
    
# Function for welcome screen
def welcome():
    global gameWindow, my_color, op_color, my_turn, fps, clock,is_joined, stop_event, stop_broadcast, width, height
    stop_event.clear()
    stop_broadcast.clear()
    is_joined=False

    gameWindow = pg.display.set_mode((width, height))
    pg.display.set_caption('Chess Game')
    gameWindow.fill((0, 0, 0))
    
    background_image = pg.image.load(resource_path("src/welcome-bg.png")).convert()
    background_image = pg.transform.scale(background_image, (width, height))
    
    bg_width, bg_height = background_image.get_rect().size

    # Calculate the position to center the image horizontally
    bg_x = (width - bg_width) // 2
    bg_y = 0  # Align at the top of the window

    gameWindow.blit(background_image, (bg_x, bg_y))
    pg.display.update()
    
    button_width = 400
    button_height = 50
    button_gap = 20
    button_start_x = (width - button_width) // 2
    button_start_y = (height - (button_height * 3 + button_gap * 2)) // 2
    button_radius = 10
    
    button_x = button_start_x
    button_y = button_start_y
    draw_button(button_x, button_y, button_width, button_height, button_radius, (0, 0, 0), "Single Device Play")
    button_y = button_start_y + (button_height + button_gap)
    draw_button(button_x, button_y, button_width, button_height, button_radius, (0, 0, 0), "Create Game - Play White")
    button_y = button_start_y + (button_height + button_gap)*2
    draw_button(button_x, button_y, button_width, button_height, button_radius, (0, 0, 0), "Join Game - Play Black")

    # Update the display
    pg.display.update()
    
    
    game_over = False
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                # Check if any button is clicked
                for i in range(3):
                    button_x = button_start_x
                    button_y = button_start_y + (button_height + button_gap) * i
                    if button_x <= mouse_pos[0] <= button_x + button_width and \
                    button_y <= mouse_pos[1] <= button_y + button_height:
                        if i == 0:
                            main()
                            game_over = True
                        elif i == 1:
                            threading.Thread(target=run_server).start()
                            middle_screen_create()
                            main()
                            game_over = True
                        else:
                            my_color = 'black'
                            op_color = 'white'
                            my_turn = False
                            threading.Thread(target=discover_servers).start()
                            middle_screen_join()
                            main()
                            game_over = True
                    
                    
        clock.tick(fps)
        pg.display.update()

# Function to check if 'my_color' player is checkmated or not
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

# Flip board by 180 in single device mode
def flip_board():
    global board
    for i in range(4):
        for j in range(8):
            t = board[i][j]
            board[i][j] = board[7-i][7-j]
            board[7-i][7-j] = t
            
# Funtion which returns type of pawn promotion choosen by player
def pawn_promotion():
    global gameWindow, stop_event, ey, board, cell_dim, bx, by, clock, fps, my_color
    
    game_over = False
    
    # Wait until player chooses a type of piece for pawn promotion
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
                pg.quit()
                sys.exit(0)
            if event.type == pg.MOUSEBUTTONDOWN:
                px = (event.pos[1] - by + cell_dim - 1) // cell_dim - 1
                py = (event.pos[0] - bx + cell_dim - 1) // cell_dim - 1
                if py == ey and 0 <= px <= 3:
                    game_over = True
        clock.tick(fps)
    return px

def main():
    global gameWindow, cell_dim, bx, by, board, valid_moves_board, sx, sy, ex, ey, stop_event, opp_valid_moves,my_color,op_color, win, is_joined, fps, clock
    # Game window Dimensions
    win=0
    
    # Game specific Variables
    game_over = False
    
    # Creating Board
    gameWindow = pg.display.set_mode((width, height))
    board = [['' for i in range(8)] for j in range(8)]
        
    # Place pieces of opposite color
    board[0][0] = Rook(op_color)
    board[0][7] = Rook(op_color)
    board[0][1] = board[0][6] = Knight(op_color)
    board[0][2] = board[0][5] = Bishop(op_color)
    board[0][3] = Queen(op_color)
    board[0][4] = King(op_color)
    if my_color == 'black':
        board[0][4] = Queen(op_color)
        board[0][3] = King(op_color)
        
    for i in range(8):
        board[1][i] = Pawn(op_color)
        
    # Place pieces of my side color
    board[7][0] = Rook(my_color)
    board[7][7] = Rook(my_color)
    board[7][1] = board[7][6] = Knight(my_color)
    board[7][2] = board[7][5] = Bishop(my_color)
    board[7][3] = Queen(my_color)
    board[7][4] = King(my_color)
    if my_color == 'black':
        board[7][4] = Queen(my_color)
        board[7][3] = King(my_color)
    
    valid_moves_board = [[False for i in range(8)] for _ in range(8)]
    
    for i in range(8):
        board[6][i] = Pawn(my_color)
    pg.display.set_caption('Chess Game')
    
    # Game loop
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
                sys.exit(0)
            elif event.type == pg.MOUSEBUTTONDOWN:
                    
                if not my_turn:
                    continue
                
                # Calulation for co-ordinates of cell from co-ordinates of pixel
                px = (event.pos[1] - by + cell_dim - 1) // cell_dim - 1
                py = (event.pos[0] - bx + cell_dim - 1) // cell_dim - 1
                
                # If pixel is outside from cell do nothinf
                if not valid_coordinate(px, py):
                    continue
                
                # Click on cell which is not valid move
                if board[px][py] == '' and not valid_moves_board[px][py]:
                    continue
                
                # Click on opponent Piece
                if (board[px][py] == '' or board[px][py].color != my_color) and valid_moves_board[px][py]:
                    if sx < 0:
                        continue
                        
                    ey = py
                    
                    # Check for Pawn Promotion
                    if board[sx][sy].ptype == 'p' and px == 0:
                        
                        # UI asking for Pawn Promotion
                        pg.draw.rect(gameWindow, (255, 255, 255), (bx + ey*cell_dim, by, cell_dim, 4*cell_dim))
                        if my_color == 'black':
                            pawn_promo_queen_b.place(0, ey)
                            pawn_promo_bishop_b.place(1, ey)
                            pawn_promo_knight_b.place(2, ey)
                            pawn_promo_rook_b.place(3, ey)
                        else:
                            pawn_promo_queen_w.place(0, ey)
                            pawn_promo_bishop_w.place(1, ey)
                            pawn_promo_knight_w.place(2, ey)
                            pawn_promo_rook_w.place(3, ey)
                        pg.draw.rect(gameWindow, green, (bx+ ey*cell_dim, by , cell_dim, 4*cell_dim), 5)
                        pg.display.flip()
                        clock.tick(fps)
                        
                        # Wait for player choice
                        px = pawn_promotion()
                        print("pawn promo", px)
                         
                    ex = px
                    
                    # If king or rook has moves then mark them moved piece and They can not do castling any longer
                    if board[sx][sy].ptype == 'k' or board[sx][sy].ptype == 'r':
                        print("Has Moved: ", sx, sy, ex, ey)
                        board[sx][sy].has_moved = True 
                        
                    # Perform Castling Moves                    
                    if board[sx][sy].ptype=='k':
                        if ey-sy == 2: 
                            board[ex][ey-1]=board[7][7]
                            board[7][7]=''
                        elif sy-ey == 2:
                            board[ex][ey+1]=board[7][0]
                            board[7][0]=''

                    sleep(0.001) # Giving enough time to thread for sending message
                    move_piece() 
                    sx, sy, ex, ey = -1, -1, -1, -1
                    
                    
                    # Once piece is moved no need to show green circles therefore clear valid board
                    clear_valid_board()
                    if not is_joined:
                        # If single device mode rotate board and swap colors
                        my_color,op_color=op_color,my_color
                        flip_board()
                        
                # If cell contains 'my_color' piece then change starting co-ordinates                
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
                    
        # Draw Green square around selected piece                    
        if sx != -1:
            pg.draw.rect(gameWindow, green, (bx + sy*cell_dim, by + sx*cell_dim, cell_dim, cell_dim), 5)
                    
        # Draw green circles
        for i in range(8):
            for j in range(8):
                if valid_moves_board[i][j]:
                    pg.draw.circle(gameWindow, green, (bx + j*cell_dim + cell_dim//2, by + i*cell_dim + cell_dim//2), 10)
                    
        # Check for checkmate
        if is_checkmated():
            sx, sy, ex, ey = 8, 8, 8, 8
            game_over = True
            PlayAgainOrQuit()
            sys.exit(0)
            
        # Check if player has won or not
        if win==1:
            sx, sy, ex, ey = 9, 9, 9, 9
            game_over = True
            PlayAgainOrQuit()
            sys.exit(0)
            
        # Check for stalemate
        if win==-1:
            game_over=True
            print("stalemate")
            PlayAgainOrQuit()
            sys.exit(0)
                        
        clock.tick(fps)
        pg.display.update()
    pg.quit()

def PlayAgainOrQuit():
    global win, clock, is_joined, gameWindow, width, height, bx, by

    # Game specific Variables
    bx = bx//2
    cell_color = black
    
    gameWindow.fill(background)
    pg.display.update()
    
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
                
    button_width = 210
    button_height = 80
    
    button_gap = int(height*0.05)
    
    button_pad_x = (width - (bx + 8*cell_dim) - button_width) // 2
    
    button_start_x = bx + 8*cell_dim + button_pad_x
    button_start_y = (height - 2*button_height - button_gap) // 2
    
    game_over = False
    while not game_over:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game_over = True
                stop_event.set()
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()

                quit_button = pg.Rect(button_start_x, button_start_y + button_height + button_gap, button_width, button_height)

                if quit_button.collidepoint(mouse_pos):
                    pg.quit()
                    sys.exit(0)

        result_button = pg.draw.rect(gameWindow, button_color, (button_start_x, button_start_y, button_width, button_height))
        quit_button = pg.draw.rect(gameWindow, button_color, (button_start_x, button_start_y + button_height + button_gap, button_width, button_height))

        quit_text = font.render("Quit", True, (255, 255, 255))

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
        result_text = font.render(result_text, True, (255, 255, 255))
        gameWindow.blit(result_text, (result_button.centerx - result_text.get_width() // 2,
                                result_button.centery - result_text.get_height() // 2))
 
        clock.tick(fps)
        pg.display.update()
    pg.quit()

if __name__ == '__main__':
    welcome() 