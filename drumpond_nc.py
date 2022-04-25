import sys,os
import curses

from curses import window

class MainWindow():
    def __init__(self, stdscr: window) -> None:
        self.stdscr = stdscr
        self.is_startup: bool = True
        self.command_mode: bool = False
        self.command_input: str = ""
        self.h, self.w = stdscr.getmaxyx()
        self.tab_title: str = "DrumPondNC v0.0"
        self.whstr: str = "W{}xH{}".format(self.w, self.h)
        self._init_colors()


    def _init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        self.cyan_black   = curses.color_pair(1)
        self.red_black    = curses.color_pair(2)
        self.black_white  = curses.color_pair(3)
        self.yellow_black = curses.color_pair(4)


    def _rigth(self, string: str = "") -> int:
        return self.w - len(string) - 1


    def _header(self) -> (int, int):
        self.stdscr.addstr(
            0, 0,
            self.tab_title, self.red_black
        )
        self.stdscr.addstr(
            0, self._rigth(self.whstr),
            self.whstr, self.cyan_black
        )
        return (1, self.w - 1)

    def render(self) -> None:
        header_h, header_w = self._header()


def draw_menu(stdscr):
    k = 0
    cursor_x = 0
    cursor_y = 0

    command_mode = False
    command_input = ""

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    mw = MainWindow(stdscr)

#    # Start colors in curses
#    curses.start_color()
#    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
#    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
#    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
#    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    # Loop where k is the last character pressed
    while (k != ord('!')):

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if command_mode:
            if k == 10:
                if command_input == ":q":
                    break
                cursor_x = old_cursor_x
                cursor_y = old_cursor_y
                command_mode = False
            else:
                command_input = command_input+chr(k)
                cursor_x = cursor_x+1
        else:
            if k == curses.KEY_DOWN:
                cursor_y = cursor_y + 1
            elif k == curses.KEY_UP:
                cursor_y = cursor_y - 1
            elif k == curses.KEY_RIGHT:
                cursor_x = cursor_x + 1
            elif k == curses.KEY_LEFT:
                cursor_x = cursor_x - 1
            elif k == 27: # ESC
                stdscr.nodelay(True)
                n = stdscr.getch()
                if n == -1:
                    command_mode = True
                    command_input = ""
                    statusbarstr = ""
                    old_cursor_x = cursor_x
                    old_cursor_y = cursor_y
                    cursor_x = 0
                    cursor_y = height-1
                # Return to delay
                stdscr.nodelay(False)

        cursor_x = max(0, cursor_x)
        cursor_x = min(width-1, cursor_x)

        cursor_y = max(0, cursor_y)
        cursor_y = min(height-1, cursor_y)

        # Declaration of strings
        posstr = "{},{}".format(cursor_x,cursor_y)
        statusstr = "{}".format(type(stdscr))
        statusbarstr = statusstr + " "*(width-len(statusstr)-len(posstr)-1)
        statusbarstr = statusbarstr + posstr

        # Rendering header bar
        mw.render()
#        tab_title = "DrumPondNC v0.0"
#        whstr = "W{}xH{}".format(width, height)
#        stdscr.addstr(0, 0, tab_title, curses.color_pair(2))
#        stdscr.addstr(0, width-len(whstr)-1, whstr, curses.color_pair(1))

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-2, 0, statusbarstr)
        stdscr.attroff(curses.color_pair(3))

        # Render command line
        stdscr.addstr(height-1, 0, command_input)
        stdscr.addstr(height-1, width-len(str(k))-1, str(k), curses.color_pair(4))

        # Render drumtab bar
        pitches = ["ride", "sn", "bd", "chp"]
        time = "4/4"
        measures, division = time.split('/')
        measures = int(measures)
        division = int(division)
        subdivision = 16
        notesstr_len = (subdivision // division)*measures
        sep = '|'
        note = '-'
        pitchesstr_len_max = 0
        for p in pitches:
            if len(p) > pitchesstr_len_max:
                pitchesstr_len_max = len(p)

        drumtab_row_len = pitchesstr_len_max + len(sep) + notesstr_len + len(sep)
        start_x_drumtab_row = int((width // 2) - (drumtab_row_len // 2) - drumtab_row_len % 2)
        start_y_drumtab_row = int(
            (height // 2)
            - (len(pitches) // 2)
            - 4 # header + statusbar + command line + drumtab footer
        )
        for p in pitches:
            pitches_col = " "*(pitchesstr_len_max-len(p)) + p + sep
            notes_col = note*notesstr_len + sep
            drumtab_row = pitches_col + notes_col
            stdscr.addstr(
                start_y_drumtab_row,
                start_x_drumtab_row,
                drumtab_row,
            )
            start_y_drumtab_row = start_y_drumtab_row + 1
            
        drumtab_footer = " "*(pitchesstr_len_max) + sep
        j = 1
        for i in range(subdivision):
            if not (i % 4):
                drumtab_footer = drumtab_footer + str(j)
                j = j + 1
            else:
                drumtab_footer = drumtab_footer + note
        drumtab_footer = drumtab_footer + sep
        stdscr.addstr(
            start_y_drumtab_row,
            start_x_drumtab_row,
            drumtab_footer,
        )
        
#        # Print wellcome message
#        if k == 0:
#            # Centering calculations
#            title = "Press '!' to exit"[:width-1]
#            start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
#            start_y = int((height // 2) - 2)
#
#            # Turning on attributes for title
#            stdscr.attron(curses.color_pair(2))
#            stdscr.attron(curses.A_BOLD)
#            stdscr.addstr(start_y, start_x_title, title)
#            stdscr.attroff(curses.color_pair(2))
#            stdscr.attroff(curses.A_BOLD)

        # Set cursor position
        stdscr.move(cursor_y, cursor_x)

        # Refresh the screen
        #stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()

def main():
    curses.wrapper(draw_menu)

if __name__ == "__main__":
    main()
