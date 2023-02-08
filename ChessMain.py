"""
Main driver file.
Handling user input.
"""

import pygame as p
import ChessEngine

WIDTH = HEIGHT = 720
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 60
IMAGES = {}


def loadImages():
  pieces = ['wP', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bP', 'bR', 'bN', 'bB', 'bK', 'bQ']
  for piece in pieces:
    IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


def main():
  p.init()
  screen = p.display.set_mode((WIDTH, HEIGHT))
  clock = p.time.Clock()
  screen.fill(p.Color("white"))
  gs = ChessEngine.GameState()
  loadImages()
  running = True
  while running:
    for e in p.event.get():
      if e.type == p.QUIT:
        running = False
    drawGameState(screen,gs)
    clock.tick(MAX_FPS)
    p.display.flip()     

def drawGameState(screen,gs):
    drawBoard(screen)
    drawPices(screen,gs.board)

# drawing the squares on the board.
def drawBoard(screen):
  colors = [p.Color("white"),p.Color("grey")]
  for r in range(DIMENSION):
    for c in range(DIMENSION):
      color = colors[((r+c)%2)]
      p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE,SQ_SIZE,SQ_SIZE))



def drawPices(screen,board):
  for r in range(DIMENSION):
    for c in range(DIMENSION):
      piece = board[r][c]
      if piece != "--":
        screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE,SQ_SIZE,SQ_SIZE))


if __name__ == "__main__":
  main()