"""
Main driver file.
Handling user input.
Displaying current GameStatus object.
"""
import pygame as p
import ChessEngine, ChessAI
import sys
import time
import os
import numpy as np
from multiprocessing import Process, Queue
import random

# Suppress pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initial dimensions
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def loadImages():
    """
    Initialize a global directory of images.
    This will be called exactly once in the main.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.image.load("images/" + piece + ".png")
        IMAGES[piece + "_scaled"] = p.transform.scale(IMAGES[piece], (SQUARE_SIZE, SQUARE_SIZE))


def scaleImages(square_size):
    """
    Scale all piece images to the new square size
    """
    for piece in IMAGES:
        if not piece.endswith("_scaled"):
            IMAGES[piece + "_scaled"] = p.transform.scale(IMAGES[piece], (square_size, square_size))


def drawText(screen, text, font, color, x, y, centered=True):
    """
    Draw text on the screen.
    """
    text_surface = font.render(text, True, color)
    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
    screen.blit(text_surface, text_rect)
    return text_rect


def drawButton(screen, text, font, text_color, button_color, x, y, width, height):
    """
    Draw a button with text.
    """
    button_rect = p.Rect(x - width // 2, y - height // 2, width, height)
    p.draw.rect(screen, button_color, button_rect)
    p.draw.rect(screen, p.Color("black"), button_rect, 2)
    drawText(screen, text, font, text_color, x, y)
    return button_rect


def formatTime(seconds):
    """
    Format time in seconds to MM:SS format
    """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def showMenu(screen):
    """
    Shows a game mode selection menu and returns the players (True for human, False for AI)
    """
    # Get screen dimensions
    screen_width, screen_height = screen.get_size()
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    
    # Define colors for the retro-style menu
    MENU_BG = p.Color(0, 0, 40)  # Dark blue background
    TITLE_COLOR = p.Color(0, 255, 255)  # Cyan title
    BUTTON_COLOR = p.Color(130, 0, 255)  # Purple buttons
    BUTTON_BORDER = p.Color(255, 0, 80)  # Neon pink border
    BUTTON_HOVER = p.Color(180, 0, 255)  # Lighter purple for hover
    TEXT_COLOR = p.Color(255, 255, 255)  # White text
    
    # Define button dimensions - increased button width to prevent text overflow
    button_width = 360  # Increased from 320 to 360
    button_height = 60
    button_spacing = 60  # Reduced spacing to accommodate three buttons
    
    # Create button rectangles
    pvp_button = p.Rect(screen_center_x - button_width // 2, screen_center_y - button_spacing - button_height, button_width, button_height)
    aivp_white_button = p.Rect(screen_center_x - button_width // 2, screen_center_y, button_width, button_height)
    aivp_black_button = p.Rect(screen_center_x - button_width // 2, screen_center_y + button_spacing + button_height, button_width, button_height)
    
    # Font for title and buttons
    title_font = p.font.SysFont("consolas", 60, True)
    menu_font = p.font.SysFont("consolas", 30, True)
    
    # Animation variables
    title_pulse = 0
    pulse_direction = 1
    animated_pieces = []
    
    # Create some animated chess pieces
    piece_images = [IMAGES['wp'], IMAGES['wR'], IMAGES['wN'], 
                    IMAGES['wB'], IMAGES['wK'], IMAGES['wQ'],
                    IMAGES['bp'], IMAGES['bR'], IMAGES['bN'], 
                    IMAGES['bB'], IMAGES['bK'], IMAGES['bQ']]
    
    # Function to initialize animated pieces with improved distribution
    def create_animated_pieces(width, height, count=20):
        # Create a grid to ensure better distribution
        grid_cells_x = 8
        grid_cells_y = 6
        grid_width = width / grid_cells_x
        grid_height = height / grid_cells_y
        
        pieces = []
        
        # First, distribute pieces in a grid to avoid clustering
        for i in range(min(count, grid_cells_x * grid_cells_y)):
            grid_x = i % grid_cells_x
            grid_y = i // grid_cells_x
            
            # Add randomness within each grid cell
            x = grid_x * grid_width + random.uniform(0.2, 0.8) * grid_width
            y = grid_y * grid_height + random.uniform(0.2, 0.8) * grid_height
            
            # Create more variety in movement patterns
            vx = random.uniform(-0.4, 0.4)
            vy = random.uniform(-0.4, 0.4)
            
            # Ensure minimum speed to avoid stationary pieces
            if abs(vx) < 0.05: vx = 0.05 * (1 if vx >= 0 else -1)
            if abs(vy) < 0.05: vy = 0.05 * (1 if vy >= 0 else -1)
            
            piece = {
                'img': random.choice(piece_images),
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'rot': random.randint(0, 360),
                'rot_speed': random.uniform(-0.8, 0.8),
                'scale': random.uniform(0.8, 1.2),  # Vary the size
                'alpha': random.randint(70, 120)    # Vary the transparency
            }
            pieces.append(piece)
        
        # Add any remaining pieces randomly
        for i in range(grid_cells_x * grid_cells_y, count):
            piece = {
                'img': random.choice(piece_images),
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'vx': random.uniform(-0.4, 0.4),
                'vy': random.uniform(-0.4, 0.4),
                'rot': random.randint(0, 360),
                'rot_speed': random.uniform(-0.8, 0.8),
                'scale': random.uniform(0.8, 1.2),
                'alpha': random.randint(70, 120)
            }
            # Ensure minimum speed
            if abs(piece['vx']) < 0.05: piece['vx'] = 0.05 * (1 if piece['vx'] > 0 else -1)
            if abs(piece['vy']) < 0.05: piece['vy'] = 0.05 * (1 if piece['vy'] > 0 else -1)
            pieces.append(piece)
        
        return pieces
    
    # Initialize animated pieces based on screen size
    piece_count = max(20, min(48, (screen_width * screen_height) // 15000))
    animated_pieces = create_animated_pieces(screen_width, screen_height, count=piece_count)
    
    # Main menu loop
    running = True
    selection = None
    
    clock = p.time.Clock()
    
    while running:
        # Handle events
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            
            if event.type == p.VIDEORESIZE:
                # Handle window resize
                screen = p.display.set_mode((event.w, event.h), p.RESIZABLE)
                screen_width, screen_height = screen.get_size()
                screen_center_x = screen_width // 2
                screen_center_y = screen_height // 2
                
                # Reposition buttons
                pvp_button = p.Rect(screen_center_x - button_width // 2, screen_center_y - button_spacing - button_height, button_width, button_height)
                aivp_white_button = p.Rect(screen_center_x - button_width // 2, screen_center_y, button_width, button_height)
                aivp_black_button = p.Rect(screen_center_x - button_width // 2, screen_center_y + button_spacing + button_height, button_width, button_height)
                
                # Reinitialize animated pieces for the new screen size
                piece_count = max(20, min(48, (screen_width * screen_height) // 15000))
                animated_pieces = create_animated_pieces(screen_width, screen_height, count=piece_count)
            
            if event.type == p.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = p.mouse.get_pos()
                    if pvp_button.collidepoint(mouse_pos):
                        selection = (True, True)  # Human vs Human
                        running = False
                    elif aivp_white_button.collidepoint(mouse_pos):
                        selection = (True, False)  # Human (White) vs AI (Black)
                        running = False
                    elif aivp_black_button.collidepoint(mouse_pos):
                        selection = (False, True)  # AI (White) vs Human (Black)
                        running = False
        
        # Update animations
        title_pulse += 0.05 * pulse_direction
        if title_pulse > 1.0:
            title_pulse = 1.0
            pulse_direction = -1
        elif title_pulse < 0.0:
            title_pulse = 0.0
            pulse_direction = 1
        
        # Update animated pieces
        for piece in animated_pieces:
            # Update position
            piece['x'] += piece['vx']
            piece['y'] += piece['vy']
            piece['rot'] += piece['rot_speed']
            
            # Occasionally change direction slightly for more natural movement
            if random.random() < 0.01:  # 1% chance each frame
                piece['vx'] += random.uniform(-0.1, 0.1)
                piece['vy'] += random.uniform(-0.1, 0.1)
                # Keep speed within limits
                max_speed = 0.6
                if abs(piece['vx']) > max_speed:
                    piece['vx'] = max_speed * (1 if piece['vx'] > 0 else -1)
                if abs(piece['vy']) > max_speed:
                    piece['vy'] = max_speed * (1 if piece['vy'] > 0 else -1)
            
            # Wrap around screen with fixed margin
            margin = 50
            if piece['x'] < -margin:
                piece['x'] = screen_width + margin
                # Randomize Y position when wrapping horizontally to avoid repetitive patterns
                piece['y'] = random.uniform(0, screen_height)
            elif piece['x'] > screen_width + margin:
                piece['x'] = -margin
                piece['y'] = random.uniform(0, screen_height)
            
            if piece['y'] < -margin:
                piece['y'] = screen_height + margin
                # Randomize X position when wrapping vertically
                piece['x'] = random.uniform(0, screen_width)
            elif piece['y'] > screen_height + margin:
                piece['y'] = -margin
                piece['x'] = random.uniform(0, screen_width)
        
        # Draw everything
        screen.fill(MENU_BG)
        
        # Draw animated background pieces with rotation and transparency
        for piece in animated_pieces:
            # Create a rotated and scaled copy of the piece image
            piece_img = p.transform.scale(piece['img'], 
                                         (int(piece['img'].get_width() * piece['scale']), 
                                          int(piece['img'].get_height() * piece['scale'])))
            rotated_image = p.transform.rotate(piece_img, piece['rot'])
            # Add transparency
            rotated_image.set_alpha(piece['alpha'])
            # Get the rect for the rotated image
            rect = rotated_image.get_rect(center=(piece['x'], piece['y']))
            # Draw the piece
            screen.blit(rotated_image, rect)
        
        # Draw scan lines effect (horizontal semi-transparent lines)
        for y in range(0, screen_height, 4):
            p.draw.line(screen, p.Color(0, 0, 0, 50), (0, y), (screen_width, y))
        
        # Draw title with pulsing glow effect
        glow_size = int(10 + 5 * title_pulse)
        glow_color = p.Color(0, 
                           int(150 + 105 * title_pulse), 
                           int(150 + 105 * title_pulse))
        
        # Draw multiple layers of the title for glow effect
        for i in range(glow_size, 0, -2):
            title_text = title_font.render("CHESS MASTER", True, glow_color)
            title_rect = title_text.get_rect(center=(screen_center_x, screen_center_y - 200))
            title_rect.inflate_ip(i, i)
            p.draw.rect(screen, glow_color, title_rect, 1)
        
        # Draw the main title
        title_text = title_font.render("CHESS MASTER", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(screen_center_x, screen_center_y - 200))
        screen.blit(title_text, title_rect)
        
        # Get mouse position for hover effects
        mouse_pos = p.mouse.get_pos()
        
        # Draw PVP button with hover effect
        button_color = BUTTON_HOVER if pvp_button.collidepoint(mouse_pos) else BUTTON_COLOR
        p.draw.rect(screen, button_color, pvp_button)
        p.draw.rect(screen, BUTTON_BORDER, pvp_button, 3)
        
        pvp_text = menu_font.render("PLAYER VS PLAYER", True, TEXT_COLOR)
        pvp_rect = pvp_text.get_rect(center=pvp_button.center)
        screen.blit(pvp_text, pvp_rect)
        
        # Draw Player White vs AI Black button with hover effect
        button_color = BUTTON_HOVER if aivp_white_button.collidepoint(mouse_pos) else BUTTON_COLOR
        p.draw.rect(screen, button_color, aivp_white_button)
        p.draw.rect(screen, BUTTON_BORDER, aivp_white_button, 3)
        
        aivp_white_text = menu_font.render("PLAYER (W) VS AI (B)", True, TEXT_COLOR)
        aivp_white_rect = aivp_white_text.get_rect(center=aivp_white_button.center)
        screen.blit(aivp_white_text, aivp_white_rect)
        
        # Draw Player Black vs AI White button with hover effect
        button_color = BUTTON_HOVER if aivp_black_button.collidepoint(mouse_pos) else BUTTON_COLOR
        p.draw.rect(screen, button_color, aivp_black_button)
        p.draw.rect(screen, BUTTON_BORDER, aivp_black_button, 3)
        
        aivp_black_text = menu_font.render("PLAYER (B) VS AI (W)", True, TEXT_COLOR)
        aivp_black_rect = aivp_black_text.get_rect(center=aivp_black_button.center)
        screen.blit(aivp_black_text, aivp_black_rect)
        
        # Draw version info
        version_font = p.font.SysFont("consolas", 16, True)
        version_text = version_font.render("v1.0", True, p.Color(150, 150, 150))
        version_rect = version_text.get_rect(bottomright=(screen_width - 10, screen_height - 10))
        screen.blit(version_text, version_rect)
        
        p.display.flip()
        clock.tick(60)
    
    return selection


def drawHelpOverlay(screen, alpha=200, duration=5):
    """
    Draw an overlay with game controls
    """
    screen_width, screen_height = screen.get_size()
    
    # Create semi-transparent overlay
    overlay = p.Surface((screen_width, screen_height), p.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    
    # Create help content
    help_font = p.font.SysFont("Arial", 24, True, False)
    title_font = p.font.SysFont("Arial", 32, True, True)
    
    # Title
    title = title_font.render("GAME CONTROLS", True, p.Color("white"))
    title_rect = title.get_rect(center=(screen_width//2, screen_height//2 - 100))
    
    # Help text - updated to show buttons instead of keyboard shortcuts
    controls = [
        ("Button", "Description"),
        ("Undo", "Take back last move"),
        ("Restart", "Start a new game"),
        ("Menu", "Return to menu"),
        ("ESC", "Show/hide this help")
    ]
    
    # Draw text
    overlay.blit(title, title_rect)
    
    # Draw table header in a different color
    y_pos = screen_height//2 - 40
    key_text = help_font.render(controls[0][0], True, p.Color("yellow"))
    key_rect = p.Rect(screen_width//2 - 160, y_pos, 100, 30)
    p.draw.rect(overlay, p.Color(60, 60, 120), key_rect)
    p.draw.rect(overlay, p.Color(120, 120, 180), key_rect, 2)
    key_text_rect = key_text.get_rect(center=key_rect.center)
    overlay.blit(key_text, key_text_rect)
    
    desc_text = help_font.render(controls[0][1], True, p.Color("yellow"))
    desc_rect = desc_text.get_rect(midleft=(screen_width//2 - 50, y_pos + 15))
    overlay.blit(desc_text, desc_rect)
    
    # Draw remaining controls
    for i, (key, desc) in enumerate(controls[1:], 1):
        y_pos = screen_height//2 - 40 + i * 40
        
        # Key/button box
        key_text = help_font.render(key, True, p.Color("white"))
        key_rect = p.Rect(screen_width//2 - 160, y_pos, 100, 30)
        p.draw.rect(overlay, p.Color(60, 60, 100), key_rect)
        p.draw.rect(overlay, p.Color(120, 120, 180), key_rect, 2)
        
        # Center key text in box
        key_text_rect = key_text.get_rect(center=key_rect.center)
        overlay.blit(key_text, key_text_rect)
        
        # Description text
        desc_text = help_font.render(desc, True, p.Color("white"))
        desc_rect = desc_text.get_rect(midleft=(screen_width//2 - 50, y_pos + 15))
        overlay.blit(desc_text, desc_rect)
    
    # Draw close instruction at bottom
    close_text = help_font.render("Press any key to continue", True, p.Color(200, 200, 200))
    close_rect = close_text.get_rect(center=(screen_width//2, screen_height//2 + 150))
    overlay.blit(close_text, close_rect)
    
    # Blend overlay with screen
    screen.blit(overlay, (0, 0))
    p.display.flip()
    
    # Wait for keypress or duration
    start_time = p.time.get_ticks()
    waiting = True
    while waiting:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.KEYDOWN:
                waiting = False
        
        # Check if duration has elapsed
        if (p.time.get_ticks() - start_time) > duration * 1000:
            waiting = False
        
        p.time.delay(100)  # Small delay to reduce CPU usage


def drawGameButtons(screen, game_width, game_height):
    """
    Draw game control buttons below the board
    """
    screen_width, screen_height = screen.get_size()
    button_area_height = min(60, screen_height // 10)  # Button area height below the board
    
    # Button dimensions
    button_width = min(120, game_width // 4)
    button_height = min(40, button_area_height - 10)
    button_y = game_height + button_area_height // 2
    button_spacing = min(20, game_width // 20)
    
    # Define button properties
    buttons = [
        {"text": "Restart", "x": game_width // 5},
        {"text": "Undo", "x": game_width // 2},
        {"text": "Menu", "x": game_width * 4 // 5}
    ]
    
    # Draw button area background
    button_area = p.Rect(0, game_height, screen_width, button_area_height)
    p.draw.rect(screen, p.Color(20, 20, 40), button_area)
    
    # Draw buttons
    button_rects = []
    button_font = p.font.SysFont("Arial", min(18, button_height // 2 + 6), True)
    
    for button in buttons:
        button_rect = p.Rect(
            button["x"] - button_width // 2, 
            button_y - button_height // 2,
            button_width, 
            button_height
        )
        
        # Check if mouse is hovering over button
        mouse_pos = p.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        # Draw button with hover effect
        if is_hover:
            p.draw.rect(screen, p.Color(120, 70, 180), button_rect)  # Lighter when hovered
        else:
            p.draw.rect(screen, p.Color(80, 40, 140), button_rect)
            
        p.draw.rect(screen, p.Color(180, 180, 240), button_rect, 2)  # Button border
        
        # Draw button text
        text_surf = button_font.render(button["text"], True, p.Color("white"))
        text_rect = text_surf.get_rect(center=button_rect.center)
        screen.blit(text_surf, text_rect)
        
        # Save button rect for click detection
        button_rects.append((button_rect, button["text"]))
    
    return button_rects


def main():
    """
    The main driver for our code.
    This will handle user input and updating the graphics.
    """
    p.init()
    # Set initial dimensions and make the window resizable
    global BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT, SQUARE_SIZE
    
    # Add extra height for buttons below the board
    button_area_height = 60
    
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT + button_area_height), p.RESIZABLE)
    p.display.set_caption("Chess Master")  # Set the window title
    
    # Load images before showing menu - needed for icon
    loadImages()  # do this only once before while loop
    
    # Set window icon to black rook
    p.display.set_icon(IMAGES["bR"])
    
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    
    # Show menu and get game mode selection
    player_one, player_two = showMenu(screen)
    
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # flag variable for when a move is made
    animate = False  # flag variable for when we should animate a move
    running = True
    square_selected = ()  # no square is selected initially, this will keep track of the last click of the user (tuple(row,col))
    player_clicks = []  # this will keep track of player clicks (two tuples)
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    
    # Use the game mode selection
    dragging = False
    drag_piece = None
    drag_pos = ()
    drag_start_square = None
    
    # Timer variables
    white_time = 0
    black_time = 0
    last_tick = time.time()
    timer_font = p.font.SysFont("Arial", 24, True, False)
    
    # Move log scroll variables
    move_log_scroll = 0
    max_scroll = 0

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        
        # Update timer
        current_time = time.time()
        time_delta = current_time - last_tick
        last_tick = current_time
        
        if not game_over:
            if game_state.white_to_move:
                white_time += time_delta
            else:
                black_time += time_delta
        
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.VIDEORESIZE:
                # Handle window resize event
                button_area_height = min(60, e.h // 10)
                screen = p.display.set_mode((e.w, e.h), p.RESIZABLE)
                
                # Calculate new dimensions
                if e.w - MOVE_LOG_PANEL_WIDTH >= e.h - button_area_height:
                    # Width constrained by height
                    BOARD_HEIGHT = e.h - button_area_height
                    BOARD_WIDTH = BOARD_HEIGHT
                else:
                    # Height constrained by width - panel
                    BOARD_WIDTH = e.w - MOVE_LOG_PANEL_WIDTH
                    BOARD_HEIGHT = BOARD_WIDTH
                
                MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
                SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
                
                # Rescale images
                scaleImages(SQUARE_SIZE)
                
                # Update move log font size based on new dimensions
                move_log_font = p.font.SysFont("Arial", max(12, min(18, SQUARE_SIZE // 4)), False, False)
                timer_font = p.font.SysFont("Arial", max(18, min(24, SQUARE_SIZE // 3)), True, False)
            
            # Mouse wheel for scrolling move log
            elif e.type == p.MOUSEWHEEL:
                mouse_pos = p.mouse.get_pos()
                # Check if mouse is over move log panel (not just right of board, but between timers)
                move_log_rect = p.Rect(BOARD_WIDTH, 40, screen.get_size()[0] - BOARD_WIDTH, BOARD_HEIGHT - 80)
                if move_log_rect.collidepoint(mouse_pos):
                    move_log_scroll = max(0, min(move_log_scroll - e.y * 20, max_scroll))
            
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if e.button == 1:  # Left mouse button
                    location = p.mouse.get_pos()
                    
                    # Check if clicked on a game button
                    button_clicked = False
                    for button_rect, button_text in game_buttons:
                        if button_rect.collidepoint(location):
                            button_clicked = True
                            if button_text == "Restart":
                                game_state = ChessEngine.GameState()
                                valid_moves = game_state.getValidMoves()
                                square_selected = ()
                                player_clicks = []
                                move_made = False
                                animate = False
                                game_over = False
                                dragging = False
                                drag_piece = None
                                drag_start_square = None
                                white_time = 0
                                black_time = 0
                                move_log_scroll = 0
                                if ai_thinking:
                                    move_finder_process.terminate()
                                    ai_thinking = False
                                move_undone = True
                            elif button_text == "Undo":
                                game_state.undoMove()
                                move_made = True
                                animate = False
                                game_over = False
                                if ai_thinking:
                                    move_finder_process.terminate()
                                    ai_thinking = False
                                move_undone = True
                                dragging = False
                                drag_piece = None
                                drag_start_square = None
                            elif button_text == "Menu":
                                player_one, player_two = showMenu(screen)
                                game_state = ChessEngine.GameState()
                                valid_moves = game_state.getValidMoves()
                                square_selected = ()
                                player_clicks = []
                                move_made = False
                                animate = False
                                game_over = False
                                dragging = False
                                drag_piece = None
                                drag_start_square = None
                                white_time = 0
                                black_time = 0
                                move_log_scroll = 0
                                if ai_thinking:
                                    move_finder_process.terminate()
                                    ai_thinking = False
                                move_undone = True
                            break
                    
                    if button_clicked:
                        continue
                    
                    # Check if clicked on scroll buttons in move log
                    if location[0] > BOARD_WIDTH:
                        # Get scroll button rects
                        screen_width, screen_height = screen.get_size()
                        move_log_panel_width = screen_width - BOARD_WIDTH
                        
                        # Log panel is now between the timers (40px from top and bottom)
                        move_log_rect = p.Rect(BOARD_WIDTH, 40, move_log_panel_width, BOARD_HEIGHT - 80)
                        
                        button_height = 20
                        up_button_rect = p.Rect(
                            move_log_rect.right - 20,
                            move_log_rect.top + 5,
                            15,
                            button_height
                        )
                        down_button_rect = p.Rect(
                            move_log_rect.right - 20,
                            move_log_rect.bottom - button_height - 5,
                            15,
                            button_height
                        )
                        
                        # Handle scroll button clicks
                        if up_button_rect.collidepoint(location):
                            move_log_scroll = max(0, move_log_scroll - 30)
                        elif down_button_rect.collidepoint(location):
                            move_log_scroll = min(max_scroll, move_log_scroll + 30)
                
                if not game_over and human_turn:
                    location = p.mouse.get_pos()  # (x, y) location of the mouse
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    
                    if col < 8 and row < 8:  # Check if click is on the board
                        # Check if user clicked on the same square twice or clicked on empty square
                        if square_selected == (row, col):
                            square_selected = ()  # deselect
                            player_clicks = []  # clear clicks
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)  # append for both 1st and 2nd click
                            
                            # Enable dragging if first click and there's a piece
                            if len(player_clicks) == 1 and game_state.board[row][col] != "--":
                                dragging = True
                                drag_piece = game_state.board[row][col]
                                drag_pos = location
                                drag_start_square = (row, col)
                            
                        if len(player_clicks) == 2 and not dragging:  # after 2nd click
                            move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    # Check for pawn promotion
                                    if move.is_pawn_promotion:
                                        # Get promotion piece choice from user
                                        promoted_piece = showPromotionMenu(screen, move.end_col, move.end_row, game_state.white_to_move)
                                        move.promotion_choice = promoted_piece
                                    
                                    game_state.makeMove(valid_moves[i])
                                    move_made = True
                                    animate = True
                                    square_selected = ()  # reset user clicks
                                    player_clicks = []
                            if not move_made:
                                player_clicks = [square_selected]
            
            # Mouse motion handler for dragging
            elif e.type == p.MOUSEMOTION:
                if dragging:
                    drag_pos = p.mouse.get_pos()
            
            # Mouse release handler for dragging and dropping
            elif e.type == p.MOUSEBUTTONUP:
                if dragging:
                    location = p.mouse.get_pos()
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    
                    if col < 8 and row < 8:  # Check if release is on the board
                        # Create a move and make it if valid
                        move = ChessEngine.Move(drag_start_square, (row, col), game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                # Check for pawn promotion
                                if move.is_pawn_promotion:
                                    # Get promotion piece choice from user
                                    promoted_piece = showPromotionMenu(screen, move.end_col, move.end_row, game_state.white_to_move)
                                    move.promotion_choice = promoted_piece
                                
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = False  # No animation needed, we already visually moved the piece
                    
                    # Reset dragging state regardless of whether the move was valid
                    dragging = False
                    drag_piece = None
                    drag_start_square = None
                    square_selected = ()
                    player_clicks = []

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # used to pass data between threads
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                
                # Check for pawn promotion (always promote to queen for AI)
                if ai_move.is_pawn_promotion:
                    ai_move.promotion_choice = "Q"
                
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                # Only animate if the move wasn't made by dragging
                if not dragging or drag_piece is None:
                    animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False
            # Reset dragging state after move is made
            dragging = False
            drag_piece = None
            drag_start_square = None
            # Auto-scroll move log to bottom when a move is made
            move_log_scroll = max_scroll

        # Draw the game state
        drawGameState(screen, game_state, valid_moves, square_selected, dragging, drag_piece, drag_pos, drag_start_square)

        # Draw game buttons
        game_buttons = drawGameButtons(screen, BOARD_WIDTH, BOARD_HEIGHT)

        if not game_over:
            # Draw timers
            drawTimers(screen, white_time, black_time, timer_font)
            # Draw move log with scrolling
            max_scroll = drawMoveLog(screen, game_state, move_log_font, move_log_scroll)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                replay_button = drawEndGameText(screen, "Black wins by checkmate")
            else:
                replay_button = drawEndGameText(screen, "White wins by checkmate")
            # Check for replay button click
            if p.mouse.get_pressed()[0] and replay_button.collidepoint(p.mouse.get_pos()):
                replayGame(screen, clock, game_state)
                # Reset game after replay
                game_state = ChessEngine.GameState()
                valid_moves = game_state.getValidMoves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                dragging = False
                drag_piece = None
                drag_start_square = None
                white_time = 0
                black_time = 0
                move_log_scroll = 0
                if ai_thinking:
                    move_finder_process.terminate()
                    ai_thinking = False
                move_undone = True

        elif game_state.stalemate:
            game_over = True
            if game_state.stalemate_reason:
                replay_button = drawEndGameText(screen, f"Stalemate: {game_state.stalemate_reason}")
            else:
                replay_button = drawEndGameText(screen, "Stalemate")
            # Check for replay button click
            if p.mouse.get_pressed()[0] and replay_button.collidepoint(p.mouse.get_pos()):
                replayGame(screen, clock, game_state)
                # Reset game after replay
                game_state = ChessEngine.GameState()
                valid_moves = game_state.getValidMoves()
                square_selected = ()
                player_clicks = []
                move_made = False
                animate = False
                game_over = False
                dragging = False
                drag_piece = None
                drag_start_square = None
                white_time = 0
                black_time = 0
                move_log_scroll = 0
                if ai_thinking:
                    move_finder_process.terminate()
                    ai_thinking = False
                move_undone = True

        clock.tick(MAX_FPS)
        p.display.flip()


def drawTimers(screen, white_time, black_time, font):
    """
    Draw timer for both players in the log panel
    """
    screen_width, screen_height = screen.get_size()
    move_log_panel_width = screen_width - BOARD_WIDTH
    
    # Format time
    white_time_text = formatTime(white_time)
    black_time_text = formatTime(black_time)
    
    # White timer at top of log panel
    white_timer_rect = p.Rect(BOARD_WIDTH, 0, move_log_panel_width, 40)
    p.draw.rect(screen, p.Color(0, 0, 0), white_timer_rect)  # Black background
    p.draw.rect(screen, p.Color("white"), white_timer_rect, 1)
    drawText(screen, f"White: {white_time_text}", font, p.Color("white"), 
             BOARD_WIDTH + move_log_panel_width // 2, 20)
    
    # Black timer at bottom of log panel
    black_timer_rect = p.Rect(BOARD_WIDTH, BOARD_HEIGHT - 40, move_log_panel_width, 40)
    p.draw.rect(screen, p.Color(0, 0, 0), black_timer_rect)  # Black background
    p.draw.rect(screen, p.Color("white"), black_timer_rect, 1)
    drawText(screen, f"Black: {black_time_text}", font, p.Color("white"), 
             BOARD_WIDTH + move_log_panel_width // 2, BOARD_HEIGHT - 20)


def drawGameState(screen, game_state, valid_moves, square_selected, dragging, drag_piece, drag_pos, drag_start_square):
    """
    Responsible for all the graphics within current game state.
    """
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected)  # highlight squares
    drawPieces(screen, game_state.board, dragging, drag_piece, drag_pos, drag_start_square)  # draw pieces on top of squares
    # No border between board and panel


def drawBoard(screen):
    """
    Draw the squares on the board.
    Top left square is always light.
    """
    global colors
    # More vibrant colors: light cream and rich brown
    colors = [p.Color(240, 217, 181), p.Color(181, 136, 99)]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight square selected and valid moves for piece selected.
    """
    if square_selected != ():
        row, col = square_selected
        if row < 8 and col < 8 and game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):  # square_selected is a piece that can be moved
            # highlight selected square
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)  # transparency value -> 0 transparent; 255 opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board, dragging=False, drag_piece=None, drag_pos=None, drag_start_square=None):
    """
    Draw the pieces on the board using the current game_state.board
    """
    # First draw all pieces except the one being dragged
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                # If we're dragging and this is the square with the dragged piece, don't draw it here
                if dragging and drag_start_square and row == drag_start_square[0] and column == drag_start_square[1]:
                    continue
                screen.blit(IMAGES[piece + "_scaled"], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    # Draw the dragged piece last (on top of everything)
    if dragging and drag_piece and drag_piece != "--":
        piece_rect = IMAGES[drag_piece + "_scaled"].get_rect()
        piece_rect.center = drag_pos
        screen.blit(IMAGES[drag_piece + "_scaled"], piece_rect)


def drawMoveLog(screen, game_state, font, scroll_pos=0):
    """
    Draws the scrollable move log between timers.
    Returns the maximum scroll position.
    """
    screen_width, screen_height = screen.get_size()
    move_log_panel_width = screen_width - BOARD_WIDTH
    
    # Log panel is now between the timers (40px from top and bottom)
    move_log_rect = p.Rect(BOARD_WIDTH, 40, move_log_panel_width, BOARD_HEIGHT - 80)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    p.draw.rect(screen, p.Color('white'), move_log_rect, 1)
    
    # Update move log panel width based on screen size
    MOVE_LOG_PANEL_WIDTH = move_log_panel_width
    
    move_log = game_state.move_log
    move_texts = []
    
    # Define piece names dictionary
    piece_names = {
        'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight', 'p': 'pawn'
    }
    
    # Format move texts in new format: "white pawn e4 - e7 | black pawn e4 - e7"
    for i in range(0, len(move_log), 2):
        move_string = f"{i//2 + 1}. "
        
        # White's move
        if i < len(move_log):
            white_move = move_log[i]
            piece_type = white_move.piece_moved[1]
            piece_name = piece_names[piece_type]
            start_square = white_move.get_rank_file(white_move.start_row, white_move.start_col)
            end_square = white_move.get_rank_file(white_move.end_row, white_move.end_col)
            move_string += f"white {piece_name} {start_square}-{end_square}"
        
        # Add separator between white and black moves
        move_string += " | "
        
        # Black's move
        if i + 1 < len(move_log):
            black_move = move_log[i + 1]
            piece_type = black_move.piece_moved[1]
            piece_name = piece_names[piece_type]
            start_square = black_move.get_rank_file(black_move.start_row, black_move.start_col)
            end_square = black_move.get_rank_file(black_move.end_row, black_move.end_col)
            move_string += f"black {piece_name} {start_square}-{end_square}"
        
        move_texts.append(move_string)
    
    # Calculate dimensions
    padding = 5
    line_spacing = font.get_linesize() + 4  # Increased spacing for better readability
    text_y = move_log_rect.top + padding - scroll_pos
    visible_height = move_log_rect.height - 2 * padding
    
    # Calculate max scroll based on content height
    content_height = len(move_texts) * line_spacing
    max_scroll = max(0, content_height - visible_height)
    
    # Adjust scroll_pos if it exceeds max_scroll
    scroll_pos = min(scroll_pos, max_scroll)
    
    # Draw scroll bar if needed
    if content_height > visible_height:
        # Draw scroll bar track
        scroll_bar_width = 15
        scroll_track_rect = p.Rect(
            move_log_rect.right - scroll_bar_width - 5, 
            move_log_rect.top + 5, 
            scroll_bar_width, 
            move_log_rect.height - 10
        )
        p.draw.rect(screen, p.Color(50, 50, 50), scroll_track_rect)
        
        # Draw scroll bar thumb
        thumb_height = max(30, scroll_track_rect.height * visible_height / content_height)
        thumb_position = scroll_pos / max_scroll if max_scroll > 0 else 0
        thumb_top = scroll_track_rect.top + thumb_position * (scroll_track_rect.height - thumb_height)
        thumb_rect = p.Rect(
            scroll_track_rect.left,
            thumb_top, 
            scroll_bar_width, 
            thumb_height
        )
        p.draw.rect(screen, p.Color(150, 150, 150), thumb_rect)
        
        # Draw scroll buttons
        button_height = 20
        
        # Up button
        up_button_rect = p.Rect(
            scroll_track_rect.left,
            move_log_rect.top + 5,
            scroll_bar_width,
            button_height
        )
        p.draw.rect(screen, p.Color(80, 80, 80), up_button_rect)
        p.draw.rect(screen, p.Color(150, 150, 150), up_button_rect, 1)
        # Draw up arrow
        arrow_points = [
            (up_button_rect.centerx, up_button_rect.top + 5),
            (up_button_rect.left + 3, up_button_rect.bottom - 5),
            (up_button_rect.right - 3, up_button_rect.bottom - 5)
        ]
        p.draw.polygon(screen, p.Color(200, 200, 200), arrow_points)
        
        # Down button
        down_button_rect = p.Rect(
            scroll_track_rect.left,
            move_log_rect.bottom - button_height - 5,
            scroll_bar_width,
            button_height
        )
        p.draw.rect(screen, p.Color(80, 80, 80), down_button_rect)
        p.draw.rect(screen, p.Color(150, 150, 150), down_button_rect, 1)
        # Draw down arrow
        arrow_points = [
            (down_button_rect.centerx, down_button_rect.bottom - 5),
            (down_button_rect.left + 3, down_button_rect.top + 5),
            (down_button_rect.right - 3, down_button_rect.top + 5)
        ]
        p.draw.polygon(screen, p.Color(200, 200, 200), arrow_points)
    
    # Create a surface for clipping the text to the visible area
    visible_area = p.Rect(
        move_log_rect.left + padding, 
        move_log_rect.top + padding,
        move_log_rect.width - 2 * padding - (20 if content_height > visible_height else 0),
        visible_height
    )
    
    # Create a clip mask to ensure text doesn't overflow
    old_clip = screen.get_clip()
    screen.set_clip(visible_area)
    
    # Draw move texts with scroll
    for i, text in enumerate(move_texts):
        y_pos = text_y + i * line_spacing
        
        # Skip drawing text that is above or below the visible area
        if y_pos + line_spacing < move_log_rect.top + padding:
            continue
        if y_pos > move_log_rect.bottom - padding:
            break
        
        text_surface = font.render(text, True, p.Color("white"))
        screen.blit(text_surface, (move_log_rect.left + padding, y_pos))
    
    # Restore clip area
    screen.set_clip(old_clip)
    
    return max_scroll


def drawEndGameText(screen, text):
    """
    Display text in the center of the screen and show a replay button
    """
    screen_width, screen_height = screen.get_size()
    
    # Semi-transparent overlay
    overlay = p.Surface((screen_width, screen_height), p.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    # Game over text
    font = p.font.SysFont("Helvetica", max(24, min(36, SQUARE_SIZE // 2)), True, False)
    text_object = font.render(text, True, p.Color("white"))
    text_rect = text_object.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
    screen.blit(text_object, text_rect)
    
    # Replay button
    button_width = 200
    button_height = 50
    button_x = screen_width // 2
    button_y = screen_height // 2 + 50
    
    replay_button = p.Rect(button_x - button_width // 2, button_y - button_height // 2, button_width, button_height)
    p.draw.rect(screen, p.Color(80, 40, 140), replay_button)
    p.draw.rect(screen, p.Color(180, 180, 240), replay_button, 2)
    
    # Button text
    button_font = p.font.SysFont("Arial", 22, True)
    button_text = button_font.render("REPLAY GAME", True, p.Color("white"))
    button_text_rect = button_text.get_rect(center=replay_button.center)
    screen.blit(button_text, button_text_rect)
    
    return replay_button


def animateMove(move, screen, board, clock):
    """
    Animating a move
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 20  # frames to move one square (increased from 10 to 20 for smoother animation)
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured + "_scaled"], end_square)
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved + "_scaled"], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)  # Increased from default to smoother animation


def showPromotionMenu(screen, end_col, end_row, is_white_turn):
    """
    Shows a menu for selecting the piece to promote a pawn to
    Returns the piece type chosen (Q, R, B, or N)
    """
    # Save the area behind the menu to restore it later
    screen_width, screen_height = screen.get_size()
    current_surface = screen.copy()
    
    # Define menu properties
    menu_width = min(320, screen_width // 2)
    menu_height = min(120, screen_height // 4)
    menu_x = screen_width // 2 - menu_width // 2
    menu_y = screen_height // 2 - menu_height // 2
    
    # Create semi-transparent background
    overlay = p.Surface((screen_width, screen_height), p.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    # Draw menu panel
    menu_rect = p.Rect(menu_x, menu_y, menu_width, menu_height)
    p.draw.rect(screen, p.Color(40, 40, 60), menu_rect)
    p.draw.rect(screen, p.Color(100, 100, 180), menu_rect, 3)
    
    # Draw title
    title_font = p.font.SysFont("Arial", 22, True)
    title = title_font.render("Promote pawn to:", True, p.Color("white"))
    title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 25))
    screen.blit(title, title_rect)
    
    # Define promotion options
    color_prefix = "w" if is_white_turn else "b"
    piece_options = ["Q", "R", "B", "N"]
    option_rects = []
    
    # Calculate piece positions
    piece_size = min(60, menu_width // 5) 
    total_width = piece_size * len(piece_options) + 10 * (len(piece_options) - 1)
    start_x = menu_x + (menu_width - total_width) // 2
    
    # Draw piece options
    for i, piece in enumerate(piece_options):
        piece_x = start_x + i * (piece_size + 10)
        piece_y = menu_y + menu_height - piece_size - 15
        piece_rect = p.Rect(piece_x, piece_y, piece_size, piece_size)
        
        # Draw selection box
        p.draw.rect(screen, p.Color(60, 60, 100), piece_rect)
        p.draw.rect(screen, p.Color(120, 120, 200), piece_rect, 2)
        
        # Draw piece image
        piece_img = IMAGES[color_prefix + piece]
        scaled_img = p.transform.scale(piece_img, (piece_size - 6, piece_size - 6))
        img_rect = scaled_img.get_rect(center=piece_rect.center)
        screen.blit(scaled_img, img_rect)
        
        option_rects.append((piece_rect, piece))
    
    p.display.flip()
    
    # Wait for user to make a selection
    waiting_for_choice = True
    choice = "Q"  # Default to queen if user clicks outside or cancels
    
    while waiting_for_choice:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            
            if event.type == p.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = p.mouse.get_pos()
                    
                    # Check if user clicked on a piece option
                    for rect, piece in option_rects:
                        if rect.collidepoint(mouse_pos):
                            choice = piece
                            waiting_for_choice = False
                            break
                    
                    # If clicked outside the options but inside the menu, default to Queen
                    if menu_rect.collidepoint(mouse_pos):
                        waiting_for_choice = False
            
            # Also allow keyboard selection
            if event.type == p.KEYDOWN:
                if event.key == p.K_q or event.key == p.K_RETURN:
                    choice = "Q"
                    waiting_for_choice = False
                elif event.key == p.K_r:
                    choice = "R"
                    waiting_for_choice = False
                elif event.key == p.K_b:
                    choice = "B"
                    waiting_for_choice = False
                elif event.key == p.K_n:
                    choice = "N"
                    waiting_for_choice = False
                elif event.key == p.K_ESCAPE:
                    waiting_for_choice = False
    
    # Restore the screen behind the menu
    screen.blit(current_surface, (0, 0))
    p.display.flip()
    
    return choice


def replayGame(screen, clock, game_state):
    """
    Replay the game from the beginning
    """
    # Make a copy of the move log
    moves_to_replay = game_state.move_log.copy()
    if not moves_to_replay:
        return  # No moves to replay
    
    # Reset the game state to initial position
    replay_state = ChessEngine.GameState()
    board_only = True  # Only show the board during replay
    
    # Calculate replay speed based on number of moves
    move_delay = max(0.5, min(2, 20 / len(moves_to_replay)))  # Between 0.5 and 2 seconds per move
    
    # Add a "Skip" button
    button_width = 100
    button_height = 40
    screen_width, screen_height = screen.get_size()
    skip_button = p.Rect(screen_width - button_width - 10, 10, button_width, button_height)
    
    # Main replay loop
    running = True
    paused = False
    move_index = 0
    last_move_time = time.time()
    
    while running and move_index < len(moves_to_replay):
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    running = False
                elif event.key == p.K_SPACE:
                    paused = not paused
            if event.type == p.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if skip_button.collidepoint(p.mouse.get_pos()):
                        running = False  # Skip the replay
        
        # Calculate dimensions
        screen_width, screen_height = screen.get_size()
        board_size = min(screen_width, screen_height)
        square_size = board_size // 8
        
        # Only process moves if not paused
        if not paused:
            current_time = time.time()
            if current_time - last_move_time >= move_delay:
                # Make the next move
                replay_state.makeMove(moves_to_replay[move_index])
                last_move_time = current_time
                move_index += 1
        
        # Draw board and pieces
        drawBoard(screen)
        drawPieces(screen, replay_state.board)
        
        # Draw move indicator
        if move_index > 0:
            last_move = moves_to_replay[move_index-1]
            # Highlight source square
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (last_move.start_col * SQUARE_SIZE, last_move.start_row * SQUARE_SIZE))
            # Highlight destination square
            s.fill(p.Color('green'))
            screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
        
        # Draw progress info
        progress_text = f"Move: {move_index}/{len(moves_to_replay)}"
        font = p.font.SysFont("Arial", 20, True)
        progress_surface = font.render(progress_text, True, p.Color("white"))
        progress_rect = progress_surface.get_rect(topright=(screen_width - 120, 10))
        
        # Draw skip button
        p.draw.rect(screen, p.Color(80, 40, 140), skip_button)
        p.draw.rect(screen, p.Color(180, 180, 240), skip_button, 2)
        skip_text = font.render("SKIP", True, p.Color("white"))
        skip_text_rect = skip_text.get_rect(center=skip_button.center)
        screen.blit(skip_text, skip_text_rect)
        
        # Draw instruction text
        instruction = "Press SPACE to pause/resume, ESC to exit"
        inst_surface = font.render(instruction, True, p.Color("white"))
        inst_rect = inst_surface.get_rect(midbottom=(screen_width//2, screen_height - 10))
        
        # Black overlay for text background
        text_bg = p.Surface((progress_surface.get_width() + 10, progress_surface.get_height() + 5), p.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (progress_rect.left - 5, progress_rect.top - 2))
        screen.blit(progress_surface, progress_rect)
        
        # Black overlay for instruction background
        inst_bg = p.Surface((inst_surface.get_width() + 10, inst_surface.get_height() + 5), p.SRCALPHA)
        inst_bg.fill((0, 0, 0, 180))
        screen.blit(inst_bg, (inst_rect.left - 5, inst_rect.top - 2))
        screen.blit(inst_surface, inst_rect)
        
        p.display.flip()
        clock.tick(60)
    
    # Short delay before returning to main menu
    time.sleep(0.5)


if __name__ == "__main__":
    main()
