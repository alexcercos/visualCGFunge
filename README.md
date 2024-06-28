# Visual CGFunge
Visual editor and batch runner for [CGFunge Prime optimization game at CodinGame](https://www.codingame.com/multiplayer/optimization/cgfunge-prime).
## Dependencies
- Python3
- Pygame (for the visuals)
- win32clipboard from pywin32 (to manage copy/pasting)
```
pip install pygame
pip install pywin32
```
In this current version, it may only be supported for windows (not tested in other operating systems).
## Usage
Execute **"visual_table.py"**, either from python idle or cmd.

Edit your code cell by cell or paste a raw text directly.

Run your code to find out which cells are visited by any validator or which validators fail (hover dark cells to review the cause of each failed validator).

Copy the resulting code to export it (paste it in a text file). **Changes are not saved after exiting the program**, to recover a previous session, copy again the resulting code and paste it again in the program.

See more details about how to use the program in the section below.

## Controls
### Mouse
- **Drag window border**: resize screen.
- **Click**: select grid cell.
- **Shift+click/drag mouse**: multiple cell selection.
- **Hover cell**: display extra information (character unicode, failed validators).
- **Scroll**: displaces tooltip information while hovering a cell, if there are more lines.
### Buttons
- **Copy**: Copies all current code to clipboard.
- **Run**: Executes each validator using the current code. Updates the score and cell shading.
### Keyboard shortcuts
- **Arrow key**: Selects next cell in that direction.
- **Ctrl+Z**: undo last change.
- **Ctrl+Y**: redo change.
- **Backspace**: Clears selected cells (inserts space).
- **Escape**: Deselects any active/selected cell.
- **Ctrl+Numbers**: writes the character represented by that unicode, after releasing Ctrl key. For example, "Ctrl+1+0+0+release Ctrl" would write "d" (unicode=100).
- **Ctrl+Arrow key**: Inserts an arrow (in CGFunge: "<>^v").
- **Ctrl+C**: copies all selected cells (if any).
- **Ctrl+V**: pastes the clipboard content in the grid, starting with the active cell (doesn't have any effect if no cell is selected).
- **Ctrl+Shift+C**: copies all of the grid (as with "Copy" button).
- **Ctrl+Shift+V**: pastes the clipboard content with the origin as reference (top-left corner).
- **Ctrl+Backspace**: Clears all grid.
- **Ctrl+Enter**: runs simulation (as with "Run" button).
- **Enter/Tab/Shift+Enter/Shift+Tab**: has the same effect as arrow keys (enter=Up, tab=Right, shift=reverse).
- **Rest of keys**: Inserts its corresponding letter in the active cell.
