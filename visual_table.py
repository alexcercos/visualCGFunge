import pygame
import win32clipboard #pywin32
from cgfungeTable import CGFungeTable, TABLE_MAX_HEIGHT, TABLE_MAX_WIDTH
from test_cases import validators

class VisualCGFungeTable:
    def __init__(self):
        pygame.init()
        self.MIN_CELL_SIZE, self.MAX_CELL_SIZE = 10, 40
        self.UNDO_STACK_SIZE = 64
        self.TOOLTIP_SIZE = 10
        self.TOOLTIP_DISP = 2

        self.cell_size = 20

        self.INPUT_HEIGHT = 40
        self.BUTTON_WIDTH = 50
        self.BUTTON_HEIGHT = 30
        self.SCORE_WIDTH = 75
        self.MARGIN = 5

        self.screen = pygame.display.set_mode((self.MARGIN*2+TABLE_MAX_WIDTH * self.cell_size, self.MARGIN*2+TABLE_MAX_HEIGHT * self.cell_size + self.INPUT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Visual CGFunge")

        self.button_boxes = [None]*3
        for i in range(3):
            self.button_boxes[i] = pygame.Rect(self.screen.get_width() - self.BUTTON_WIDTH*(3-i) - 10, TABLE_MAX_HEIGHT * self.cell_size+self.MARGIN*2, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

        self.font = pygame.font.SysFont("Arial", self.cell_size-2)
        self.input_font = pygame.font.SysFont("Consolas", 22)
        self.tooltip_font = pygame.font.SysFont("Consolas", 15)
        self.score_font = pygame.font.SysFont("Consolas", 15)

        self.cgfunge = CGFungeTable()

        #Control variables
        self.redraw = True
        
        self.active_cell = None
        self.selection_cell_end = None
        self.mouse_drag = False

        self.input_active = False
        self.input_text = ''
        self.hover_row, self.hover_col = None, None
        self.running = True
        self.mouse_x, self.mouse_y = 0,0
        self.tooltip_pos = dict()
        self.tooltip_curr_limit = 0 #number of rows displayed now

        self.input_border_color = (255,255,255)

        self.ctrl_stored_nums=""

        #UNDO/REDO
        self.undo_stack = [""]*self.UNDO_STACK_SIZE
        self.undo_index = 0
        self.undo_bottom = 0
        self.undo_top = 0

        self.score = 0
        self.valid_pct = 0
    
    def get_table_string(self):
        return "\n".join(["".join(r).rstrip() for r in self.cgfunge.table]).rstrip()
    
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
            if value <= cuts[i][0]:
                cut_i = i
                break
        
        r1,g1,b1 = cuts[cut_i-1][1]
        r2,g2,b2 = cuts[cut_i][1]

        lerpv = (value - cuts[cut_i-1][0])/(cuts[cut_i][0]-cuts[cut_i-1][0])

        return (min(255,int(r1*(1-lerpv)+r2*lerpv)),
                min(255,int(g1*(1-lerpv)+g2*lerpv)),
                min(255,int(b1*(1-lerpv)+b2*lerpv)))

    def send_to_clipboard(self, custom_text=None):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        if custom_text:
            win32clipboard.SetClipboardText(custom_text)
        else:
            win32clipboard.SetClipboardText(self.get_table_string(), win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
    
    def get_clipboard(self):
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data

    def paste_clipboard_input(self):
        
        data = self.get_clipboard()
        if not data: return

        if self.input_active:
            self.input_text+=data
            self.redraw = True
        elif self.active_cell:
            lines = data.replace("\r"," ").split("\n")
            x,y = self.active_cell

            max_len = 0
            for l in lines:
                max_len=max(max_len, len(l))
            
            max_len = min(max_len,TABLE_MAX_WIDTH-x)

            for li in range(min(len(lines),TABLE_MAX_HEIGHT-y)):
                for ci in range(max_len):
                    if ci<len(lines[li]):
                        self.cgfunge.table[y+li][x+ci] = lines[li][ci]
                    else:
                        self.cgfunge.table[y+li][x+ci] = " "

            self.add_undo_state()
            self.redraw = True

    def determine_hovers(self):
        mx,my = pygame.mouse.get_pos()

        if self.mouse_x==mx and self.mouse_y==my:
            return

        self.mouse_x, self.mouse_y = mx-self.MARGIN,my-self.MARGIN
        self.hover_col = self.mouse_x // self.cell_size
        self.hover_row = self.mouse_y // self.cell_size

        if self.hover_col>=TABLE_MAX_WIDTH or self.hover_row>=TABLE_MAX_HEIGHT or self.hover_col<0 or self.hover_row<0:
            self.hover_col, self.hover_row = None, None
        
        self.redraw = True
    
    def draw_empty_square(self, color, line_width, width, height, x, y):
        pygame.draw.rect(self.screen, color, (self.MARGIN + x, self.MARGIN + y, width, height), line_width)
        self.redraw = True

    def run_simulation(self):
        self.cgfunge.reset_heatmap()
        self.cgfunge.reset_annotations()
        self.tooltip_pos.clear()

        self.score = 0
        self.valid_pct = 0
        for n,r in validators:
            res = self.cgfunge.simulate(n,r)
            if res>0:
                self.score+=res
                self.valid_pct+=1

        self.render_score()
        self.redraw = True

    def draw_cell(self, row, col):
        num = self.cgfunge.heatmap[row][col]
        char = self.cgfunge.table[row][col]
        color = self.get_color(num)
        
        # Draw the cell background
        pygame.draw.rect(self.screen, color, (self.MARGIN + col * self.cell_size, self.MARGIN+row * self.cell_size, self.cell_size, self.cell_size))
        
        # Draw the character
        text_surface = self.font.render(char, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=((self.MARGIN + col * self.cell_size) + self.cell_size // 2, (self.MARGIN + row * self.cell_size) + self.cell_size // 2))
        self.screen.blit(text_surface, text_rect)

    def render_input(self):

        self.input_box = pygame.Rect(self.SCORE_WIDTH, TABLE_MAX_HEIGHT * self.cell_size + self.MARGIN*2, self.screen.get_width() - self.BUTTON_WIDTH*3 - 20 - self.SCORE_WIDTH, self.BUTTON_HEIGHT)

        pygame.draw.rect(self.screen, (0, 0, 0), self.input_box)
        # Draw the input box border
        pygame.draw.rect(self.screen, self.input_border_color, self.input_box, 2)

        text_surface = self.input_font.render(self.input_text, True, (255, 255, 255))
        # Draw the updated text in the input box
        inp_rect = text_surface.get_rect(topleft=(self.input_box.x + 5, self.input_box.y + 5))
        self.screen.blit(text_surface, inp_rect)

        self.render_score()

    def render_score(self):
        score_box = pygame.Rect(0,TABLE_MAX_HEIGHT * self.cell_size + self.MARGIN*2, self.SCORE_WIDTH, self.INPUT_HEIGHT)

        pygame.draw.rect(self.screen, (0, 0, 0), score_box)
        
        #write
        sc_surface = self.score_font.render(str(self.score), True, (255, 255, 255))
        sc_rect = sc_surface.get_rect(topleft=(score_box.x+5, score_box.y))
        self.screen.blit(sc_surface, sc_rect)

        pct_surface = self.score_font.render(f"{self.valid_pct}%", True, (255, 255, 255))
        pct_rect = pct_surface.get_rect(topleft=(score_box.x+5, score_box.y+self.INPUT_HEIGHT//2))
        self.screen.blit(pct_surface, pct_rect)

    def redraw_complete(self):
        if not self.redraw: return

        # Clear the screen
        self.screen.fill((0, 0, 0))

        # Draw the grid
        for row in range(TABLE_MAX_HEIGHT):
            for col in range(TABLE_MAX_WIDTH):
                self.draw_cell(row, col)

        self.render_input()

        # Draw the submit button
        buttons = ["Load","Copy","Run"]
        b_colors = [(196,196,196),(255,255,196),(64,255,255)]

        for i in range(3):

            pygame.draw.rect(self.screen, b_colors[i], self.button_boxes[i])
            button_text = self.input_font.render(buttons[i], True, (0, 0, 0))
            button_rect = button_text.get_rect(center=self.button_boxes[i].center)
            self.screen.blit(button_text, button_rect)

        self.render_selection_squares()
        self.render_hover_cell()
        self.render_highlight_cell()

        self.render_tooltip()

        # Update the display
        pygame.display.flip()
        self.redraw = False

    def render_tooltip(self):
        if self.hover_row is None or self.hover_col is None:
            return
        if pygame.mouse.get_focused() == 0:
            return

        d = self.cgfunge.annotations[self.hover_row][self.hover_col]
        letter = self.cgfunge.table[self.hover_row][self.hover_col]
        text = f"{letter} ({ord(letter)})"
        #text+=f" -> {self.cgfunge.heatmap[self.hover_row][self.hover_col]}"
        lines = []

        if "error" in d:
            errors = d["error"]

            for n,e in errors:
                lines.append(f"{n}: {e}")

        if "fails" in d:
            fails = d["fails"]
            
            for n,p,e in fails:
                lines.append(f"{n}: '{p}' ('{e}')")


        self.tooltip_curr_limit = len(lines)
        displace = 0

        if self.tooltip_curr_limit>0:

            cell = (self.hover_row, self.hover_col)
            
            if cell in self.tooltip_pos:
                displace = self.tooltip_pos[cell]%self.tooltip_curr_limit
        #print("->",displace,self.tooltip_curr_limit)

        # Render each line and calculate the overall size of the tooltip
        rendered_lines = [self.tooltip_font.render(line, True, (255, 255, 255)) for line in [text]+lines[displace:displace+self.TOOLTIP_SIZE]]
        max_width = max(line.get_width() for line in rendered_lines)
        total_height = sum(line.get_height() for line in rendered_lines)

        # Position the tooltip
        if self.mouse_x > self.screen.get_width() - max_width - 15:
            tooltip_x = self.mouse_x - 15 - max_width
        else:
            tooltip_x = self.mouse_x + 15
        if self.mouse_y > self.screen.get_height() - total_height - self.INPUT_HEIGHT - self.MARGIN:
            tooltip_y = self.mouse_y - total_height
        else:
            tooltip_y = self.mouse_y
        trect = pygame.Rect(tooltip_x, tooltip_y, max_width + 4, total_height + 4)

        # Draw the background rectangle
        pygame.draw.rect(self.screen, (0, 0, 0), trect)

        # Blit each line of text onto the screen
        for i, line_surface in enumerate(rendered_lines):
            self.screen.blit(line_surface, (tooltip_x + 2, tooltip_y + 2 + i * line_surface.get_height()))

    def load_input_text(self):

        self.cgfunge.set_table_from_text(self.input_text)
        self.input_text = ''
        self.redraw = True
    
    def clear_all(self):
        if self.input_active:
            self.input_text = ""
        else:
            self.cgfunge.reset_heatmap()
            self.cgfunge.reset()
        
        self.redraw = True

    def backspace_press(self):
        if self.input_active:
            self.input_text = self.input_text[:-1]
            self.render_input()
        elif self.active_cell:
            self.generic_key_press(" ")
            self.add_undo_state()
            self.redraw = True

    def keyenter_press(self,is_shift):
        if self.input_active:
            self.load_input_text()
        elif self.active_cell:
            self.move_active_cell(0,-1 if is_shift else 1)
    
    def generic_key_press(self, unicode):
        if not unicode:return
        if self.input_active:
            self.input_text += unicode
        elif self.active_cell:
            x,y = self.active_cell
            self.cgfunge.table[y][x] = unicode[0]
        
        self.redraw = True
    
    def move_active_cell(self,movx,movy):
        if not self.active_cell: return
        self.selection_cell_end = None
        x,y = self.active_cell

        self.active_cell = ((x+movx)%TABLE_MAX_WIDTH,(y+movy)%TABLE_MAX_HEIGHT)
        self.redraw = True

    def resize_screen(self, new_width, new_height):
        WIDTH, HEIGHT = new_width, new_height
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.redraw = True

        # Calculate new cell size maintaining aspect ratio
        cell_width = self.screen.get_width() // TABLE_MAX_WIDTH
        cell_height = (self.screen.get_height() - self.INPUT_HEIGHT) // TABLE_MAX_HEIGHT
        self.cell_size = max(self.MIN_CELL_SIZE, min(cell_width, cell_height, self.MAX_CELL_SIZE))
        self.font = pygame.font.SysFont("Arial", self.cell_size-2)

        for i in range(3):
            self.button_boxes[i] = pygame.Rect(self.screen.get_width() - self.BUTTON_WIDTH*(3-i) - 10, TABLE_MAX_HEIGHT * self.cell_size + 5, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

    def set_select_cell(self, pos):
        if not self.active_cell:
            self.set_active_element()
            return
        
        x,y = pos
        x-=self.MARGIN
        y-=self.MARGIN
        x//=self.cell_size
        y//=self.cell_size

        if x<0 or x>=TABLE_MAX_WIDTH or y<0 or y>=TABLE_MAX_HEIGHT:
            self.selection_cell_end = None
            return

        if self.active_cell == (x,y):
            self.selection_cell_end = None
            return
        if self.selection_cell_end == (x,y):
            return

        self.selection_cell_end = (x,y)
        self.redraw = True

    def set_active_element(self, pos):
        self.selection_cell_end = None
        if self.input_box.collidepoint(pos):
            self.input_active = True
            self.input_border_color = (0,255,255)
            self.active_cell = None
            self.render_input()
            pygame.display.flip()
            return
        
        self.input_active = False
        self.input_border_color = (255,255,255)

        x,y = pos
        x-=self.MARGIN
        y-=self.MARGIN
        x//=self.cell_size
        y//=self.cell_size

        if x<0 or x>=TABLE_MAX_WIDTH or y<0 or y>=TABLE_MAX_HEIGHT:
            self.active_cell = None
            return
        self.active_cell = (x,y)
        self.redraw = True

    def render_highlight_cell(self):
        if not self.active_cell:
            return
        x,y = self.active_cell
        self.draw_empty_square((0,0,255), 2, self.cell_size, self.cell_size, x*self.cell_size, y*self.cell_size)
    
    def render_selection_squares(self):
        if not self.selection_cell_end:
            return
        
        x1,y1 = self.active_cell
        x2,y2 = self.selection_cell_end

        xi = min(x1,x2)
        yi = min(y1,y2)
    
        self.draw_empty_square((0,128,128), 3, self.cell_size * (1+abs(x1-x2)), self.cell_size * (1+abs(y1-y2)), xi*self.cell_size, yi*self.cell_size)

    def render_hover_cell(self):
        if self.hover_col==None or self.hover_row==None:
            return
        x,y = self.hover_col,self.hover_row
        self.draw_empty_square((64,64,64), 2, self.cell_size, self.cell_size, x*self.cell_size, y*self.cell_size)

    def add_undo_state(self):
        self.undo_index = (self.undo_index+1)%self.UNDO_STACK_SIZE
        self.undo_stack[self.undo_index] = self.get_table_string()
        self.undo_top = self.undo_index

        if self.undo_top == self.undo_bottom:
            self.undo_bottom = (self.undo_bottom+1)%self.UNDO_STACK_SIZE

    def undo(self):
        if self.undo_index==self.undo_bottom:
            return #Cannot undo
        
        self.undo_index = (self.undo_index-1)%self.UNDO_STACK_SIZE
        self.cgfunge.set_table_from_text(self.undo_stack[self.undo_index])
        self.redraw = True

    def redo(self):
        if self.undo_index==self.undo_top:
            return #Cannot redo
        
        self.undo_index = (self.undo_index+1)%self.UNDO_STACK_SIZE
        self.cgfunge.set_table_from_text(self.undo_stack[self.undo_index])
        self.redraw = True

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.resize_screen(event.w, event.h)

            elif event.type == pygame.MOUSEWHEEL:

                if self.hover_row is None or self.hover_col is None:
                    continue
                
                if self.tooltip_curr_limit<=self.TOOLTIP_SIZE:
                    continue
                
                cell = (self.hover_row, self.hover_col)

                curr = 0
                if cell in self.tooltip_pos:
                    curr = self.tooltip_pos[cell]
                
                tpos = curr - self.TOOLTIP_DISP*event.y
                if tpos<0:
                    if curr==0:
                        tpos = max(0,self.tooltip_curr_limit-self.TOOLTIP_SIZE)
                    else:
                        tpos = 0
                elif tpos>self.tooltip_curr_limit-self.TOOLTIP_SIZE+self.TOOLTIP_DISP-1:
                    tpos = 0
                self.tooltip_pos[cell]=tpos

                self.render_tooltip()
                self.redraw = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                
                if event.button!=1:
                    continue
                self.mouse_drag = True
                
                #Shift + click
                if (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.set_select_cell(event.pos)
                else:
                    self.set_active_element(event.pos)

                if self.button_boxes[0].collidepoint(event.pos):
                    self.load_input_text()
                    self.add_undo_state()
                
                if self.button_boxes[1].collidepoint(event.pos):
                    self.send_to_clipboard()
                
                if self.button_boxes[2].collidepoint(event.pos):
                    self.run_simulation()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button!=1:
                    continue
                self.mouse_drag = False

            elif event.type == pygame.MOUSEMOTION:
                if not self.mouse_drag:
                    continue
                
                self.set_select_cell(event.pos)
            

            elif event.type == pygame.KEYDOWN:

                is_shift = (pygame.key.get_mods() & pygame.KMOD_SHIFT)
                
                #CTRL + key
                if (pygame.key.get_mods() & pygame.KMOD_CTRL or pygame.key.get_mods() & pygame.KMOD_META):

                    if event.key  ==   pygame.K_0 or event.key == pygame.K_KP0:
                        self.ctrl_stored_nums+="0"
                        continue
                    if event.key  ==   pygame.K_1 or event.key == pygame.K_KP1:
                        self.ctrl_stored_nums+="1"
                        continue
                    if event.key  ==   pygame.K_2 or event.key == pygame.K_KP2:
                        self.ctrl_stored_nums+="2"
                        continue
                    if event.key  ==   pygame.K_3 or event.key == pygame.K_KP3:
                        self.ctrl_stored_nums+="3"
                        continue
                    if event.key  ==   pygame.K_4 or event.key == pygame.K_KP4:
                        self.ctrl_stored_nums+="4"
                        continue
                    if event.key  ==   pygame.K_5 or event.key == pygame.K_KP5:
                        self.ctrl_stored_nums+="5"
                        continue
                    if event.key  ==   pygame.K_6 or event.key == pygame.K_KP6:
                        self.ctrl_stored_nums+="6"
                        continue
                    if event.key  ==   pygame.K_7 or event.key == pygame.K_KP7:
                        self.ctrl_stored_nums+="7"
                        continue
                    if event.key  ==   pygame.K_8 or event.key == pygame.K_KP8:
                        self.ctrl_stored_nums+="8"
                        continue
                    if event.key  ==   pygame.K_9 or event.key == pygame.K_KP9:
                        self.ctrl_stored_nums+="9"
                        continue
                    
                    self.ctrl_stored_nums=""

                    #CTRL+ENTER
                    if event.key == pygame.K_RETURN:
                        self.run_simulation()

                    #CTRL+C
                    elif event.key == pygame.K_c:
                        if is_shift:
                            self.send_to_clipboard()
                        elif self.active_cell:
                            x,y = self.active_cell
                            if self.selection_cell_end:
                                x2,y2 = self.selection_cell_end
                                xi=min(x,x2)
                                xe=max(x,x2)+1
                                yi=min(y,y2)
                                ye=max(y,y2)+1
                                content=""
                                for r in range(yi,ye):
                                    for c in range(xi,xe):
                                        content+=self.cgfunge.table[r][c]
                                    content+="\n"
                                self.send_to_clipboard(content[:-2])
                            else:
                                self.send_to_clipboard(self.cgfunge.table[y][x])
                
                    #CTRL+V
                    elif event.key == pygame.K_v:
                        if is_shift: #send directly
                            self.cgfunge.set_table_from_text(self.get_clipboard())
                            self.add_undo_state()
                            self.redraw = True
                        else:
                            self.paste_clipboard_input()
                    
                    elif event.key == pygame.K_z:
                        self.undo()
                    
                    elif event.key == pygame.K_y:
                        self.redo()
                    
                    elif event.key == pygame.K_BACKSPACE:
                        self.clear_all()
                        self.add_undo_state()
                    
                        #ARROW KEYS
                    elif event.key == pygame.K_LEFT:
                        self.generic_key_press("<")
                        self.add_undo_state()
                    elif event.key == pygame.K_RIGHT:
                        self.generic_key_press(">")
                        self.add_undo_state()
                    elif event.key == pygame.K_DOWN:
                        self.generic_key_press("v")
                        self.add_undo_state()
                    elif event.key == pygame.K_UP:
                        self.generic_key_press("^")
                        self.add_undo_state()
                
                #ARROW KEYS
                elif event.key == pygame.K_LEFT:
                    self.move_active_cell(-1,0)
                elif event.key == pygame.K_RIGHT:
                    self.move_active_cell(1,0)
                elif event.key == pygame.K_DOWN:
                    self.move_active_cell(0,1)
                elif event.key == pygame.K_UP:
                    self.move_active_cell(0,-1)

                #ENTER
                elif event.key == pygame.K_RETURN:
                    self.keyenter_press(is_shift)

                #TAB (move)
                elif event.key == pygame.K_TAB:
                    self.move_active_cell(-1 if is_shift else 1,0)

                #BACKSPACE
                elif event.key == pygame.K_BACKSPACE:
                    self.backspace_press()
                
                elif event.key == pygame.K_ESCAPE:
                    self.active_cell = None
                    self.selection_cell_end = None
                    self.redraw = True
                
                #REST OF KEYS
                else:
                    self.generic_key_press(event.unicode)
                    self.add_undo_state()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    if not self.ctrl_stored_nums:
                        continue
                    num = int(self.ctrl_stored_nums)
                    if num==0: continue
                    self.generic_key_press(chr(num))
                    self.add_undo_state()

    def frame(self):

        self.determine_hovers()
        self.process_events()
        self.redraw_complete()

        return self.running


table = VisualCGFungeTable()

while table.frame():
    pass

# Quit Pygame
pygame.quit()
