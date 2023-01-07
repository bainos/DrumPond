import inspect
import curses

from curses import window
from enum import Enum, auto


class InputMode(Enum):
    WAIT = 0
    COMMAND = auto()
    INSERT = auto()
    VISUAL = auto()
    PLAYBACK = auto()


class Events(Enum):
    CURSOR_MOVE = 0
    CURSOR_SET = auto()
    K_LEFT = auto()
    K_UP = auto()
    K_RIGHT = auto()
    K_DOWN = auto()
    K_ARROWS = auto()
    K_ENTER = auto()
    K_ESC = auto()
    K_PRESS = auto()
    MODE_CHANGE = auto()
    WAIT = auto()
    COMMAND = auto()
    INSERT = auto()
    VISUAL = auto()
    PLAYBACK = auto()
    COMMAND_SEND = auto()
    DRUMTAB_READY = auto()


class Component():

    def __init__(self, name: str, stdscr: window) -> None:
        self._name = name
        self._stdscr = stdscr
        self._screen_h, self._screen_w = stdscr.getmaxyx()
        self._mode: InputMode = InputMode.WAIT
        self._mode_prev: InputMode = InputMode.WAIT
        self._mode_actions = [lambda *args: False] * len(InputMode)
        self._events = {event: list() for event in Events}
        self._events_action = [lambda *args: False] * len(Events)
        self._command: str = ""
        self._init_actions()

    def _init_actions(self) -> None:
        self._events_action[Events.K_ESC.value] = self._on_esc_keypress
        self._events_action[Events.MODE_CHANGE.value] = self._on_mode_change

    @property
    def name(self) -> str:
        return self._name

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
    def mode(self) -> InputMode:
        return self._mode

    @property
    def mode_prev(self) -> InputMode:
        return self._mode_prev

    def get_subscribers(self, event: Events):
        return self._events[event]

    def register(self, event: Events, who):
        if event not in Events:
            raise ValueError("Unknow event: {}".format(event))
        assert(isinstance(who, Component))
        if event == Events.K_ARROWS:
            self.get_subscribers(Events.K_ARROWS).append(who)
            self.get_subscribers(Events.K_LEFT).append(who)
            self.get_subscribers(Events.K_UP).append(who)
            self.get_subscribers(Events.K_RIGHT).append(who)
            self.get_subscribers(Events.K_DOWN).append(who)
        elif event == Events.MODE_CHANGE:
            self.get_subscribers(Events.MODE_CHANGE).append(who)
            self.get_subscribers(Events.WAIT).append(who)
            self.get_subscribers(Events.COMMAND).append(who)
            self.get_subscribers(Events.INSERT).append(who)
            self.get_subscribers(Events.VISUAL).append(who)
            self.get_subscribers(Events.PLAYBACK).append(who)
        else:
            self.get_subscribers(event).append(who)

    def unregister(self, event: str, who: str):
        self.get_subscribers(event).remove(who)

    def dispatch(self, event: str, message):
        for subscriber in self.get_subscribers(event):
            subscriber._events_action[event.value](message)

    def _on_esc_keypress(self, dummy) -> bool:
        if self._mode == InputMode.WAIT:
            return False
        self._mode_prev = self._mode
        self._mode = InputMode.WAIT
        return True

    def _on_mode_change(self, mode: InputMode) -> bool:
        if mode != self._mode and self._mode == InputMode.WAIT:
            self._mode_prev = self._mode
            self._mode = mode
            self._mode_actions[mode.value]()
            return True
        return False


class KInput(Component):

    def __init__(self, stdscr: window) -> None:
        super().__init__("kinput", stdscr)
        self._stdscr = stdscr
        self._k = 0
        self._actions: list = [None] * curses.KEY_MAX
        self._actions[curses.KEY_LEFT] = (Events.K_LEFT, curses.KEY_LEFT)
        self._actions[curses.KEY_UP] = (Events.K_UP, curses.KEY_UP)
        self._actions[curses.KEY_RIGHT] = (Events.K_RIGHT, curses.KEY_RIGHT)
        self._actions[curses.KEY_DOWN] = (Events.K_DOWN, curses.KEY_DOWN)
        self._actions[curses.KEY_ENTER] = (Events.K_ENTER, None)
        self._actions[10] = (Events.K_ENTER, None)
        self._actions[13] = (Events.K_ENTER, None)
        self._actions[27] = (Events.K_ESC, None)
        self._actions[ord(':')] = (Events.COMMAND, InputMode.COMMAND)
        self._actions[ord('i')] = (Events.INSERT, InputMode.INSERT)
        self._actions[ord('v')] = (Events.VISUAL, InputMode.VISUAL)
        self._actions[ord('p')] = (Events.PLAYBACK, InputMode.PLAYBACK)

    def listen(self) -> bool:
        self._k = self._stdscr.getch()
        # 0-9
        if self._k >= 48 and self._k <= 57:
            self.dispatch(Events.K_PRESS, self._k)
        # A-Z
        elif self._k >= 65 and self._k <= 90:
            self.dispatch(Events.K_PRESS, self._k)
        # a-z
        elif self._k >= 97 and self._k <= 122:
            self.dispatch(Events.K_PRESS, self._k)
        else:
            self.dispatch(Events.K_PRESS, self._k)
        if self._actions[self._k] is not None:
            self.dispatch(self._actions[self._k][0],
                          self._actions[self._k][1])


class Row(Component):

    def __init__(self, name: str, stdscr: window) -> None:
        super().__init__(name, stdscr)
        self._length = self.screen_size[1]
        self._content: str = " " * self._length
        self._content_l: str = ""
        self._content_r: str = ""

    def set_content(
        self,
        y: int = 0,
        x: int = 0,
        content_l: str = "",
        content_r: str = "",
    ) -> None:
        self._content_l = str(content_l)
        self._content_r = str(content_r)
        cl_len = len(self._content_l)
        cr_len = len(self._content_r)
        blank_space = " " * (self._length - cl_len - cr_len)
        self._content = self._content_l + blank_space + self._content_r
        self._stdscr.addstr(y, x, self._content)
        self._stdscr.noutrefresh()


class Header(Row):

    def __init__(self, stdscr: window) -> None:
        super().__init__("header", stdscr)

    @property
    def title(self) -> str:
        return self._content_l

    @title.setter
    def title(self, title: str):
        h, w = self.screen_size
        r = "{}x{}".format(str(h), str(w))
        self.set_content(0, 0, title, r)


class StatusBar(Row):

    def __init__(self, stdscr: window) -> None:
        super().__init__("statusbar", stdscr)
        h, w = self.screen_size
        self._h = h - 1
        self.set_content(self._h, 0,
                         "Wellcome (:",
                         "0,0")
        self._events_action[Events.CURSOR_MOVE.value] = self._on_cursor_move
        self._events_action[Events.K_ESC.value] = self._on_esc_keypress
        self._events_action[Events.MODE_CHANGE.value] = self._on_mode_change
        self._events_action[Events.COMMAND.value] = self._on_command
        self._events_action[Events.COMMAND_SEND.value] = self._on_command_send
        self._events_action[Events.INSERT.value] = self._on_insert
        self._events_action[Events.VISUAL.value] = self._on_visual
        self._events_action[Events.PLAYBACK.value] = self._on_playback

    @property
    def info(self) -> str:
        return self._content_l

    @info.setter
    def info(self, info: str = "") -> None:
        self.set_content(self._h, 0, info, self._content_r)

    def _on_cursor_move(self, yx: (int, int)) -> None:
        y, x = yx
        self.set_content(self._h, 0,
                         self._content_l,
                         "{},{}".format(str(y), str(x)))

    def _on_esc_keypress(self, dummy) -> None:
        if super()._on_esc_keypress(None):
            self.info = InputMode.WAIT

    def _on_mode_change(self, mode: InputMode) -> None:
        if super()._on_mode_change(mode):
            self.info = mode

    def _on_wait(self, dummy) -> None:
        self._on_mode_change(InputMode.WAIT)

    def _on_command(self, dummy) -> None:
        self._on_mode_change(InputMode.COMMAND)

    def _on_command_send(self, commamd) -> None:
        self.info = commamd

    def _on_insert(self, dummy) -> None:
        self._on_mode_change(InputMode.INSERT)

    def _on_visual(self, dummy) -> None:
        self._on_mode_change(InputMode.VISUAL)

    def _on_playback(self, dummy) -> None:
        self._on_mode_change(InputMode.PLAYBACK)


class Commands(Component):

    def __init__(self, stdscr):
        super().__init__("commands", stdscr)
        self.ymin = self.xmin = self.ymax = self.xmax = 0
        self._events_action[Events.DRUMTAB_READY.value] \
            = self._on_drumtab_ready
        self.commands = {}
        for element in inspect.getmembers(
                self, predicate=inspect.ismethod):
            self.commands[element[0]] = element[1]

    def quit(self, arg=None):
        raise SystemExit

    q = quit

    def write(self, arg=None) -> None:
        row = self.ymin
        while row <= self.ymax - 1:
            col = self.xmin
            while col < self.xmax - 1:
                if self._stdscr.inch(row, col) == ord('o'):
                    self._stdscr.addch(row, col, ord('#'))
                col = col + 1
                self.dispatch(Events.CURSOR_SET, (row, col))
            row = row + 1

    w = write

    def _on_drumtab_ready(self, arg) -> None:
        self.ymin, self.xmin, self.ymax, self.xmax = arg


class CommandLine(Row):

    def __init__(self, stdscr: window) -> None:
        super().__init__("command_line", stdscr)
        self._events_action[Events.COMMAND.value] = self._on_command
        self._events_action[Events.K_ENTER.value] = self._on_enter_keypress
        self._events_action[Events.K_ESC.value] = self._on_esc_keypress
        self._events_action[Events.K_PRESS.value] = self._on_keypress
        self._events_action[Events.DRUMTAB_READY.value] \
            = self._on_drumtab_ready
        self._y, self._x = (self._screen_h-1, 1)
        self._history: list = list()
        self._commands: dict = {}
        self._cmd_arg = None
        self._active: bool = False

    def register_commands(self, commands: dict):
        self._commands = commands

    def update_command(self, c: int) -> None:
        to_list = list(self._command)
        to_list.insert(self._x, chr(c))
        self._command = "".join(to_list)

    def handle_backspace(self) -> None:
        to_list = list(self._command)
        to_list.pop(self._x-1)
        self._command = "".join(to_list)

    def _on_drumtab_ready(self, arg) -> None:
        self._cmd_arg = arg

    def _on_command(self, arg) -> None:
        self._active = True
        self._command = ":"
        self.set_content(self._screen_h-1, 0, self._command)
        self.dispatch(Events.K_RIGHT, curses.KEY_RIGHT)

    def _on_keypress(self, arg) -> None:
        if arg > 32 and arg < 126 and self._active:
            self.update_command(arg)
            self.dispatch(Events.K_RIGHT, curses.KEY_RIGHT)
            self._x = self._x + 1
        elif arg == curses.KEY_LEFT and self._x > 1:
            self._x = self._x - 1
        elif arg == curses.KEY_RIGHT and self._x < len(self._command):
            self._x = self._x + 1
        elif arg == 127 and self._x > 1:
            self.handle_backspace()
            self.dispatch(Events.K_LEFT, curses.KEY_LEFT)
            self._x = self._x - 1
        self.set_content(self._screen_h-1, 0, self._command, str(arg))

    def _on_enter_keypress(self, arg) -> None:
        self._history.append(self._command)
        self.dispatch(Events.COMMAND_SEND, self._command)
        self._active = False
        try:
            self._commands[self._command[1:]](self._cmd_arg)
            self._cmd_arg = None
        except KeyError:
            self.set_content(self._screen_h-1, 0, "> unkown command")
        self.dispatch(Events.K_ESC, None)

    def _on_esc_keypress(self, arg) -> None:
        self._active = False
        self.dispatch(Events.K_ESC, None)
        self.set_content(self._screen_h-1, 0, self._command, str(self._x))


class DrumTab(Component):

    def __init__(self, stdscr: window) -> None:
        super().__init__("drumtab", stdscr)

    def draw(self) -> (int, int):
        height, width = self._stdscr.getmaxyx()
        # Render drumtab bar
        pitches = ["ride", "sn", "bd", "chp"]
        time = "4/4"
        beats, division = time.split('/')
        beats = int(beats)
        division = int(division)
        subdivision = 16
        # measures = 2
        sep = '|'
        note = '-'

        drumtab_height = len(pitches) + 1
        drumtab_rows_max = (height - 6) // drumtab_height

        notesstr_len = (subdivision // division)*beats
        pitchesstr_len_max = 0
        for p in pitches:
            if len(p) > pitchesstr_len_max:
                pitchesstr_len_max = len(p)

        measures_per_row = (width - 4 - pitchesstr_len_max) // notesstr_len
        drumtab_row_len = pitchesstr_len_max \
            + len(sep) \
            + (notesstr_len + len(sep))*measures_per_row
        start_x_drumtab_row = int(
            (width // 2) - (drumtab_row_len // 2)
            - drumtab_row_len % 2)
        start_y_drumtab_row = int(
            (height // 2)
            - (drumtab_height*drumtab_rows_max // 2)
        )
        cursor_x = start_x_drumtab_row + pitchesstr_len_max + 1
        cursor_y = start_y_drumtab_row
        cursor_x_max = cursor_x + (notesstr_len + len(sep))*measures_per_row
        cursor_y_max = cursor_y + drumtab_height*drumtab_rows_max - 1

        self.dispatch(Events.DRUMTAB_READY, (
            cursor_y, cursor_x,
            cursor_y_max, cursor_x_max
        ))

        while drumtab_rows_max > 0:
            drumtab_rows_max = drumtab_rows_max - 1
            for p in pitches:
                pitches_col = " "*(pitchesstr_len_max-len(p)) + p + sep
                notes_col = (note*notesstr_len + sep)*measures_per_row
                drumtab_row = pitches_col + notes_col
                self._stdscr.addstr(
                    start_y_drumtab_row,
                    start_x_drumtab_row,
                    drumtab_row,
                )
                start_y_drumtab_row = start_y_drumtab_row + 1

            drumtab_footer_pc = " "*(pitchesstr_len_max) + sep
            drumtab_footer = ""
            j = 1
            for i in range(subdivision):
                if not (i % 4):
                    drumtab_footer = drumtab_footer + str(j)
                    j = j + 1
                else:
                    drumtab_footer = drumtab_footer + "•"
            drumtab_footer = (drumtab_footer + sep)*measures_per_row
            self._stdscr.addstr(
                start_y_drumtab_row,
                start_x_drumtab_row,
                drumtab_footer_pc + drumtab_footer,
            )
            start_y_drumtab_row = start_y_drumtab_row + 1

        return cursor_y, cursor_x


class MainWindow(Component):

    def __init__(self, stdscr: window) -> None:
        super().__init__("main_window", stdscr)
        self._components: dict = dict()

    def register_component(self, component: Component) -> None:
        self._components[component.name] = component

    def unregister_component(self, component_name: str) -> None:
        del self._components[component_name]


class Cursor(Component):
    def __init__(self, stdscr: window) -> None:
        super().__init__("cursor", stdscr)
        self._y: int = 1
        self._x: int = 0
        self._history: list[(int, int)] = [(0, 0)]
        self._commandline: bool = False
        self._insert: bool = False
        self._stdscr = stdscr
        self._events_action[Events.CURSOR_SET.value] = self._on_cursor_set
        self._events_action[Events.K_LEFT.value] = self._left
        self._events_action[Events.K_UP.value] = self._up
        self._events_action[Events.K_RIGHT.value] = self._right
        self._events_action[Events.K_DOWN.value] = self._down
        self._events_action[Events.INSERT.value] = self._on_insert
        self._events_action[Events.K_PRESS.value] = self._on_keypress
        self._events_action[Events.COMMAND.value] = self._command_line_on
        self._events_action[Events.K_ESC.value] = self._command_line_off
        self._events_action[Events.K_ENTER.value] = self._command_line_off

    @property
    def coordinates(self) -> (int, int):
        return self._x, self._y

    @coordinates.setter
    def coordinates(self, yx: (int, int) = (0, 0)) -> None:
        y, x = yx
        if y <= self._screen_h and y >= 1:
            self._y = y
        if x <= self._screen_w and x >= 0:
            self._x = x
        self.dispatch(Events.CURSOR_MOVE, (self._y, self._x))

    def _left(self, dummy) -> None:
        self.coordinates = (self._y, self._x - 1)

    def _up(self, dummy) -> None:
        if self._commandline is False:
            self.coordinates = (self._y - 1, self._x)

    def _right(self, dummy) -> None:
        self.coordinates = (self._y, self._x + 1)

    def _down(self, dummy) -> None:
        if self._commandline is False:
            self.coordinates = (self._y + 1, self._x)

    def _on_cursor_set(self, yx: (int, int)) -> None:
        self._y, self._x = yx
        self.coordinates = (self._y, self._x)

    def move(self) -> None:
        self._stdscr.move(self._y, self._x)

    def save(self) -> (int, int):
        self._history.append((self._y, self._x))
        return self._y, self._x

    def restore(self) -> (int, int):
        self.coordinates = self._history.pop()

    def _on_insert(self, args):
        if self._insert is False:
            self._insert = True

    def _on_keypress(self, args):
        if self._insert is True \
            and self._stdscr.inch(self._y, self._x) == 45 \
                and args in [
                    111, 79,  # o, O
                    120, 88,  # x, X
                    103,      # g
                    114, 82,  # r, R
                    108, 75,  # l, L
                    32,       # space
                ]:
            if args == 32:
                args = 45
            self._stdscr.addch(self._y, self._x, args)
            self._right(None)

    def _command_line_on(self, args) -> None:
        if self._commandline is False:
            self._commandline = True
            self.save()
            self.coordinates = (self._screen_h-1, 0)

    def _command_line_off(self, args) -> None:
        if self._commandline is True:
            self._commandline = False
            self.restore()
        if self._insert is True:
            self._insert = False


def draw_menu(stdscr):
    curses.nonl()
    curses.set_escdelay(25)
    stdscr.clear()

    kinput = KInput(stdscr)
    header = Header(stdscr)
    statusbar = StatusBar(stdscr)
    commands = Commands(stdscr)
    cli = CommandLine(stdscr)
    cli.register_commands(commands.commands)
    cursor = Cursor(stdscr)
    dt = DrumTab(stdscr)

    header.title = "DrumpondNC"

    dt.register(Events.DRUMTAB_READY, commands)
    commands.register(Events.CURSOR_SET, cursor)

    kinput.register(Events.K_ARROWS, cursor)
    cli.register(Events.K_ARROWS, cursor)

    cursor.register(Events.CURSOR_MOVE, statusbar)

    kinput.register(Events.K_ESC, cli)
    kinput.register(Events.K_ESC, statusbar)
    kinput.register(Events.K_ESC, cursor)
    cli.register(Events.K_ESC, statusbar)
    cli.register(Events.K_ESC, cursor)

    kinput.register(Events.MODE_CHANGE, cursor)
    kinput.register(Events.MODE_CHANGE, cli)
    kinput.register(Events.MODE_CHANGE, statusbar)

    kinput.register(Events.K_PRESS, cursor)
    kinput.register(Events.K_PRESS, cli)

    kinput.register(Events.K_ENTER, cli)

    start_y, start_x = dt.draw()
    cursor.coordinates = (start_y, start_x)
    stdscr.refresh()
    counter = 0
    stop = False
    cursor.move()
    while not stop:

        # if counter > 10:
        #     stop = True

        kinput.listen()
        cursor.move()
        counter = counter + 1
        # stdscr.clear()
        # stdscr.refresh()


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
