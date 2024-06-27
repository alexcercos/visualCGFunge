import pygame
import win32clipboard #pywin32
from cgfungeTable import CGFungeTable, TABLE_MAX_HEIGHT, TABLE_MAX_WIDTH

class VisualCGFungeTable:
    def __init__(self):
        pygame.init()
        self.MIN_CELL_SIZE, self.MAX_CELL_SIZE = 10, 40

        self.cell_size = 20

        self.INPUT_HEIGHT = 40
        self.BUTTON_WIDTH = 100
        self.BUTTON_HEIGHT = 30

        self.screen = pygame.display.set_mode((TABLE_MAX_WIDTH * self.cell_size, TABLE_MAX_HEIGHT * self.cell_size + self.INPUT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Visual CGFunge")

        self.font = pygame.font.SysFont(None, 16)
        self.input_font = pygame.font.SysFont(None, 24)
        self.tooltip_font = pygame.font.SysFont(None, 24)

        self.cgfunge = CGFungeTable()

        #Control variables
        self.redraw = True
        self.input_active = False
        self.input_text = ''
        self.hover_row, self.hover_col = None, None
        self.running = True
        self.mouse_x, self.mouse_y = 0,0
    
    def get_color(self, num):
        if num <10:
            if num<0:return (30,10,10)
            if num==0:return (255,255,255)
            if num==1:return (224,255,255)
            if num==2:return (224,224,255)
            if num==3:return (224,224,224)
            if num==4:return (193,224,224)
            if num==5:return (193,193,224)
            if num==6:return (193,193,193)
            if num==7:return (162,193,193)
            if num==8:return (162,162,193)
            return (162,162,162)

        cuts = [
            (10/self.cgfunge.max_heatmap, (0,255,255)), #cyan 
            (0.25, (0,255,0)), #green
            (0.5, (255,255,0)), #yellow
            (0.75, (255,128,0)), #orange
            (1.0, (255,0,0)), #red
        ]

        value = num/self.cgfunge.max_heatmap

        cut_i = 0
        for i in range(1, len(cuts)):
            if value <= cuts[i]:
                cut_i = i
                break
        
        r1,g1,b1 = cuts[cut_i-1][1]
        r2,g2,b2 = cuts[cut_i][1]

        lerpv = (value - cuts[cut_i-1][0])/(cuts[cut_i][0]-cuts[cut_i-1][0])

        return (min(255,int(r1*(1-lerpv)+r2*lerpv)),
                min(255,int(g1*(1-lerpv)+g2*lerpv)),
                min(255,int(b1*(1-lerpv)+b2*lerpv)))

    def send_to_clipboard(text): #TODO send table instead
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText('testing 123')
        win32clipboard.CloseClipboard()
    
    def determine_hovers(self):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.hover_col = self.mouse_x // self.cell_size
        self.hover_row = self.mouse_y // self.cell_size

        if self.hover_col>=TABLE_MAX_WIDTH or self.hover_row>=TABLE_MAX_HEIGHT or self.hover_col<0 or self.hover_row<0:
            self.hover_col, self.hover_row = None, None
    
    def redraw_complete(self):
        if not self.redraw: return

        # Clear the screen
        self.screen.fill((0, 0, 0))

        # Draw the grid
        for row in range(TABLE_MAX_HEIGHT):
            for col in range(TABLE_MAX_WIDTH):
                num = self.cgfunge.heatmap[row][col]
                char = self.cgfunge.table[row][col]
                color = self.get_color(num)
                
                # Draw the cell background
                pygame.draw.rect(self.screen, color, (col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size))
                
                # Draw the character
                text_surface = self.font.render(char, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=((col * self.cell_size) + self.cell_size // 2, (row * self.cell_size) + self.cell_size // 2))
                self.screen.blit(text_surface, text_rect)

        # Draw the input box
        self.input_box = pygame.Rect(10, TABLE_MAX_HEIGHT * self.cell_size + 5, self.screen.get_width() - self.BUTTON_WIDTH - 20, self.BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (255, 255, 255), self.input_box, 2)
        # Clear the input box area
        pygame.draw.rect(self.screen, (0, 0, 0), self.input_box)
        # Draw the input box border
        pygame.draw.rect(self.screen, (255, 255, 255), self.input_box, 2)
        text_surface = self.input_font.render(self.input_text, True, (255, 255, 255))
        # Draw the updated text in the input box
        inp_rect = text_surface.get_rect(topleft=(self.input_box.x + 5, self.input_box.y + 5))
        self.screen.blit(text_surface, inp_rect)

        # Draw the submit button
        self.button_box = pygame.Rect(self.screen.get_width() - self.BUTTON_WIDTH - 10, TABLE_MAX_HEIGHT * self.cell_size + 5, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (0, 255, 0), self.button_box)
        button_text = self.input_font.render("Submit", True, (0, 0, 0))
        button_rect = button_text.get_rect(center=self.button_box.center)
        self.screen.blit(button_text, button_rect)

        # Render Tooltip
        if self.hover_row is not None and self.hover_col is not None:
            tooltip_text = self .cgfunge.annotations[self.hover_row][self.hover_col]
            tooltip_surface = self.tooltip_font.render(tooltip_text, True, (255, 255, 255))
            tooltip_x = self.mouse_x
            tooltip_y = self.mouse_y  # Offset the tooltip above the mouse cursor
            self.screen.blit(tooltip_surface, (tooltip_x, tooltip_y))

        # Update the display
        pygame.display.flip()
        self.redraw = False

    def frame(self):
        self.determine_hovers()

        for event in pygame.event.get():
            self.redraw=True
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                self.redraw = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the input box is clicked
                if self.input_box.collidepoint(event.pos):
                    self.input_active = True
                else:
                    self.input_active = False
                # Check if the button is clicked
                if self.button_box.collidepoint(event.pos):
                    print("Submit",self.input_text)
                    self.cgfunge.set_table_from_text(self.input_text)
                    self.input_text = ''
                    self.redraw = True
            elif event.type == pygame.KEYDOWN:
                if self.input_active:
                    if event.key == pygame.K_RETURN:
                        print("Submit",self.input_text)
                        self.cgfunge.set_table_from_text(self.input_text)
                        self.input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL or pygame.key.get_mods() & pygame.KMOD_META):
                        # Handle paste
                        win32clipboard.OpenClipboard()
                        data = win32clipboard.GetClipboardData()
                        win32clipboard.CloseClipboard()
                        if data:
                            self.input_text+=data
                    else:
                        self.input_text += event.unicode
                    self.redraw = True
        
        # Calculate new cell size maintaining aspect ratio
        cell_width = self.screen.get_width() // TABLE_MAX_WIDTH
        cell_height = (self.screen.get_height() - self.INPUT_HEIGHT) // TABLE_MAX_HEIGHT
        self.cell_size = max(self.MIN_CELL_SIZE, min(cell_width, cell_height, self.MAX_CELL_SIZE))

        self.redraw_complete()

        return self.running


table = VisualCGFungeTable()

while table.frame():
    pass

# Quit Pygame
pygame.quit()
