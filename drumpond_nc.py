import sys,os
import curses

from curses import window
from enum import Enum


class Cursor():
    def __init__(self, stdscr: window) -> None:
        self._y: int = 0
        self._x: int = 0
        self._history: list[(int, int)] = [(0, 0)]
        self._stdscr = stdscr

    @property
    def coordinates(self) -> (int, int):
        return self._x, self._y

    @coordinates.setter
    def coordinates(self, yx = None) -> None:
        y, x = yx
        h, v = self._stdscr.getmaxyx()
        self._y = max(0, y)
        self._y = min(h-1, y)
        self._x = max(0, x)
        self._x = min(h-1, x)

    def update(self) -> (int, int):
        self._stdscr.move(self._y, self._x)
        return self._y, self._x

    def save(self) -> (int, int):
        self._history.append((self._y, self._x))
        return self._y, self._x

    def restore(self) -> (int, int):
        self.coordinates = self._history.pop()

    def left(self) -> None:
        self.coordinates = (self._y, self._x-1)

    def up(self) -> None:
        self.coordinates = (self._y-1, self._x)

    def right(self) -> None:
        self.coordinates = (self._y, self._x+1)

    def down(self) -> None:
        self.coordinates = (self._y+1, self._x)


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
        self.x = self.y = 0
        self._status_info: str = ""
        self._cli_input = " " * (self.w - 1)
        self._k = 0

    def _init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        self.cyan_black = curses.color_pair(1)
        self.red_black = curses.color_pair(2)
        self.black_white = curses.color_pair(3)
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

    def _statusbar(self) -> (int, int):
        posstr = "{},{}".format(self.x, self.y)
        statusstr = "{}".format(self._status_info)
        statusbarstr = statusstr + " "*(self.w-len(statusstr)-len(posstr)-1)
        statusbarstr = statusbarstr + posstr
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(self.h-2, 0, statusbarstr)
        self.stdscr.attroff(curses.color_pair(3))
        return (1, self.w - 1)

    def _commandline(self) -> (int, int):
#        blankstr = " " * (self.w - len(self._cli_input) - len(str(self._k)) - 1)
#        cmdstr = self._cli_input + blankstr + str(self._k)
#        self.stdscr.addstr(self.h-1, 0, cmdstr)
#        self.status_info = self.status_info + "|" + cmdstr
        self.stdscr.addstr(self.h-1, 0, self._cli_input)
        self.stdscr.addstr(
            self.h-1,
            self.w-len(str(self._k))-1,
            str(self._k),
            curses.color_pair(4)
        )
        return (1, self.w - 1)

    @property
    def cli(self) -> str:
        return self._cli_input

    @cli.setter
    def cli(self, commandk) -> None:
        command, k = commandk
        self._cli_input = command
        self._k = k
        self._commandline()

    @property
    def cursor_yx(self) -> (int, int):
        return self.x, self.y

    @cursor_yx.setter
    def cursor_yx(self, yx) -> None:
        self.y, self.x = yx

    @property
    def status_info(self) -> str:
        return self._status_info

    @status_info.setter
    def status_info(self, status) -> None:
        self._status_info = status

    def render(self) -> None:
        header_h, header_w = self._header()
        statusbar_h, statusbar_w = self._statusbar()
        commanline_h, commandline_w = self._commandline()


class InputMode(Enum):
    WAIT = 1
    COMMAND = 2
    INSERT = 3
    VISUAL = 4
    PLAYBACK = 5


class Component():

    __events__ = (
        "mode_change",
        "esc_keypress",
        "enter_keypress",
        "arrows_keypress",
        "keypress",
    )

    def __init__(self, stdscr: window) -> None:
        self._stdscr = stdscr
        self._screen_h, self._screen_w = stdscr.getmaxyx()
        self._mode: int = InputMode.WAIT
        self._mode_prev: int = InputMode.WAIT
        self._events = {event: dict() for event in self.__events__}

    @property
    def events(self) -> dict:
        return self._events

    @property
    def screen_size(self) -> (int, int):
        return self._screen_h-1, self._screen_w-1

    @screen_size.setter
    def screen_size(self, h: int, w: int) -> None:
        self._screen_h = h
        self._screen_w = w

    @property
    def mode(self) -> int:
        return self._mode

    @mode.setter
    def mode(self, mode: int) -> None:
        self._mode_prev = self._mode
        self._mode = mode


class Raw(Component):

    def __init__(self, stdscr: window) -> None:
        super().__init__(self, stdscr)
        self._length = self.screen_size[1]
        self._content = " " * self._length

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, content: str = "", right_content: str = "") -> None
        c_len = len(content)
        rc_len = len(right_content)
        blank_space = " " * (self._length - c_len - rc_len)
        self._content = content + (" " * blank_space) + right_content
        self._stdscr.noutrefresh()

class KInput():

    def __init__(
        self,
        stdscr: window,
    ) -> None:
        self._stdscr = stdscr

    def get_subscribers(self, event):
        return self.events[event]

    def register(self, event, who, callback=None):
        if callback is None:
            callback = getattr(who, 'update')
        self.get_subscribers(event)[who] = callback

    def unregister(self, event, who):
        del self.get_subscribers(event)[who]

    def _mode_switch(self, mode: InputMode) -> None:
        self._prev_mode = self._mode
        self._mode = mode

    def _esc(self) -> bool:
        if self._k == 27:
            self._mode_switch(InputMode.WAIT)
            self._command = ""
            return True
        return False

    def _enter(self) -> bool:
        if self._k == curses.KEY_ENTER or self._k == 13:
            return True
        return False

    def _arrows(self) -> bool:
        if self._k == curses.KEY_LEFT:
            self._cursor.left()
            return True
        elif self._k == curses.KEY_UP:
            self._cursor.up()
            return True
        elif self._k == curses.KEY_RIGHT:
            self._cursor.right()
            return True
        elif self._k == curses.KEY_DOWN:
            self._cursor.down()
            return True
        return False

    def _handle_command(self) -> None:
        # self._arrows()
        # TODO Implement custom arrows action for up
        # and down to browse command history
        if self._enter():
            if self._command in self._command_history:
                self._command_history.sort(
                    key=self._command.__eq__
                )
            else:
                self._command_history.append(self._command)
            if self._command == "q":
                self._quit = True
                return
            self._cursor.restore()
            self._mode = InputMode.WAIT
            self._command = " " * (self._mw.w - len(str(self._k)) - 1)
            # return

        self._command = self._command + chr(self._k)
        self._mw.cli = (self._command, self._k)
        self._cursor.right()

    def _wait(self) -> None:
        if self._arrows():
            return
        if self._k == ord(':'):
            self._mode_switch(InputMode.COMMAND)
        if self._k == ord('i'):
            self._mode_switch(InputMode.INSERT)
        if self._k == ord('v'):
            self._mode_switch(InputMode.VISUAL)
        if self._k == ord('b'):
            self._mode_switch(InputMode.PLAYBACK)

    def _insert(self) -> None:
        self._arrows()

    def _visual(self) -> None:
        self._arrows()

    def _playback(self) -> None:
        self._arrows()

    def _handle_input(self) -> (int, str):
        self._k = self._stdscr.getch()
        if self._esc():
            self._mw.status_info = "WAIT"
            self._wait()
            return (self._k, chr(self._k))
        if (self._mode == InputMode.WAIT):
            self._mw.status_info = "WAIT"
            self._wait()
        elif (self._mode == InputMode.COMMAND):
            if self._prev_mode != self._mode:
                y, x = self._cursor.save()
                self._mw.status_info = "{}|{}|{},{}".format(
                    self._prev_mode,
                    self._mode,
                    str(y),
                    str(x)
                )
                self._cursor.coordinates = (self._mw.h, 0)
                self._prev_mode = self._mode
            self._handle_command()
        elif (self._mode == InputMode.INSERT):
            self._mw.status_info = "INSERT"
            self._insert()
        elif (self._mode == InputMode.VISUAL):
            self._mw.status_info = "VISUAL"
            self._visual()
        elif (self._mode == InputMode.PLAYBACK):
            self._mw.status_info = "PLAYBACK"
            self._playback()
        return (self._k, chr(self._k))

    def listen(self) -> bool:
        k, kstr = self._handle_input()
        if self._quit:
            return False
        self._mw.cursor_yx = self._cursor.coordinates
        self._mw.render()
        self._cursor.update()
        return True


def draw_drumtab(stdscr):
    height, width = stdscr.getmaxyx()
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
        - 4  # header + statusbar + command line + drumtab footer
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


def draw_menu(stdscr):
    curses.nonl()
    cur = Cursor(stdscr=stdscr)
    mw = MainWindow(stdscr=stdscr)
    ki = KInput(
        stdscr=stdscr,
        cursor=cur,
        main_window=mw,
    )

    stdscr.clear()
    stdscr.refresh()
    mw.render()
    cur.coordinates = (0, 0)
    cur.update()

    counter = 0

    # Loop where k is the last character pressed
    while (ki.listen()):

        if counter > 30:
            break

        counter = counter + 1

        # stdscr.clear()
        # stdscr.refresh()

        # mw.render()


def main():
    curses.set_escdelay(25)
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
