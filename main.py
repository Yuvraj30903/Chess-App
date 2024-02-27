import pygame as pg
import socket
import threading

# Colors
white = (255, 255, 255)

def main():
    # Game window Dimensions
    width, height = 900, 800
    
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
        gameWindow.fill()

if __name__ == '__main__':
    main()