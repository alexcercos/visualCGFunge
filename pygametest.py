import pygame
import random
import pygame.scrap

# Initialize Pygame
pygame.init()


# Constants
ROWS, COLS = 30, 40
CELL_SIZE = 20
MIN_CELL_SIZE = 10
MAX_CELL_SIZE = 40
FONT_SIZE = 16
INPUT_HEIGHT = 40
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30

# Create the screen with resizable flag
screen = pygame.display.set_mode((COLS * CELL_SIZE, ROWS * CELL_SIZE + INPUT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Character Grid")

# Font setup
font = pygame.font.SysFont(None, FONT_SIZE)
input_font = pygame.font.SysFont(None, 24)

# Generate matrices
char_matrix = [[chr(random.randint(65, 90)) for _ in range(COLS)] for _ in range(ROWS)]
num_matrix = [[random.randint(0, 100) for _ in range(COLS)] for _ in range(ROWS)]

# Function to get color based on number (simple gradient)
def get_color(num):
    return (num * 2.55, 0, 255 - num * 2.55)

# Initial draw flag
redraw = True
input_active = False
input_text = ''

pygame.scrap.init()
# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            redraw = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the input box is clicked
            if input_box.collidepoint(event.pos):
                input_active = True
            else:
                input_active = False
            # Check if the button is clicked
            if button_box.collidepoint(event.pos):
                print(f"Submitted text: {input_text}")
                input_text = ''
                redraw = True
        elif event.type == pygame.KEYDOWN:
            if input_active:
                if event.key == pygame.K_RETURN:
                    print(f"Submitted text: {input_text}")
                    input_text = ''
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL or pygame.key.get_mods() & pygame.KMOD_META):

                    # Handle paste
                    if pygame.scrap.get(pygame.SCRAP_TEXT):
                        pasted_text = pygame.scrap.get("text/plain;charset=utf-8").decode().replace('\x00',"")
                        input_text += pasted_text
                else:
                    input_text += event.unicode
                redraw = True
    
    # Calculate new cell size maintaining aspect ratio
    cell_width = screen.get_width() // COLS
    cell_height = (screen.get_height() - INPUT_HEIGHT) // ROWS
    CELL_SIZE = max(MIN_CELL_SIZE, min(cell_width, cell_height, MAX_CELL_SIZE))

    if redraw:
        # Clear the screen
        screen.fill((0, 0, 0))

        # Draw the grid
        for row in range(ROWS):
            for col in range(COLS):
                num = num_matrix[row][col]
                char = char_matrix[row][col]
                color = get_color(num)
                
                # Draw the cell background
                pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                
                # Draw the character
                text_surface = font.render(char, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=((col * CELL_SIZE) + CELL_SIZE // 2, (row * CELL_SIZE) + CELL_SIZE // 2))
                screen.blit(text_surface, text_rect)

        # Draw the input box
        input_box = pygame.Rect(10, ROWS * CELL_SIZE + 5, screen.get_width() - BUTTON_WIDTH - 20, BUTTON_HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
        # Clear the input box area
        pygame.draw.rect(screen, (0, 0, 0), input_box)
        # Draw the input box border
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
        
        text_surface = input_font.render(input_text, True, (255, 255, 255))
        # Draw the updated text in the input box
        inp_rect = text_surface.get_rect(topleft=(input_box.x + 5, input_box.y + 5))
        screen.blit(text_surface, inp_rect)

        # Draw the submit button
        button_box = pygame.Rect(screen.get_width() - BUTTON_WIDTH - 10, ROWS * CELL_SIZE + 5, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(screen, (0, 255, 0), button_box)
        button_text = input_font.render("Submit", True, (0, 0, 0))
        button_rect = button_text.get_rect(center=button_box.center)
        screen.blit(button_text, button_rect)

        # Update the display
        pygame.display.flip()
        redraw = False

# Quit Pygame
pygame.quit()
