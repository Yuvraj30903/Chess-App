# Multiplayer Chess Application

A multiplayer chess application built using Pygame 

## Single Device Mode
Both Player can play in single device and after each turn Board will be rotated so player is comfortable while their turn.

## Dual Device Mode 
First both device should be connected with same wi-fi.

One player has to create game and other player has to join Game.

Player who created game will play as white.

## Chess Features and Rules

- Verification of turn by turn playing
- Highlights Selected Piece and Valid Moves cells
- King-Rook Casteling
- Pawn Promotion

## Modules Used

- **Pygame**: Used for design of GUI and Interactive Playable Enviornment
- **Cairosvg**: Create Chess token (pawn, rook, etc.) from svg
- **Socket**: For interaction between 2 devices in Dual device mode
- **Threading**: Run GUI update and socket communication simultaneously
- **OS, SYS, Time**: Helps in handeling Threding and GUI updates
- **Pyinstaller**: This is an external module which is not used in code but used for creating exe file

# Getting Started

There are 2 methods to install this application.

## Method 1

You can Download Executable file from [here](https://drive.google.com/file/d/1pixLO1P9QhY0QlVw1gt_I4BEjlln__Bp/view?usp=drive_link).

But you need to provide some permission to play game.

## Method 2


### Prerequisites

- Python 3.0 or above

### Installation

1. Clone the repository:

   `git clone https://github.com/bhavyramani/Chess-App`

   `cd Chess-App`

2. Install dependencies:

    `pip install -r requirements.txt`

3. Run the application:

    `python chess.py`