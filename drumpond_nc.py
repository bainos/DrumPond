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
        if self._k >= 65 and self._k <= 90:
            self.dispatch(Events.K_PRESS, self._k)
        # a-z
        if self._k >= 97 and self._k <= 122:
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

    def _on_cursor_move(self, yx: (int, int) = (0, 0)) -> None:
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


class Commands():

    def quit(self):
        pass

    q = quit


class CommandLine(Row):

    def __init__(self, stdscr: window) -> None:
        super().__init__("command_line", stdscr)
        self._events_action[Events.COMMAND.value] = self._on_command
        self._events_action[Events.K_ENTER.value] = self._on_enter_keypress
        self._events_action[Events.K_ESC.value] = self._on_esc_keypress
        self._events_action[Events.K_PRESS.value] = self._on_keypress
        self._command: str = ":"
        self._history: list = list()
        self._commands: dict = dict()
        self._active: bool = False
        for element in inspect.getmembers(
                Commands, predicate=inspect.ismethod):
            self._commands[element[0]] = element[1]

    def _on_command(self, arg) -> None:
        self._active = True
        self.set_content(self._screen_h-1, 0, self._command)
        self.dispatch(Events.K_RIGHT, curses.KEY_RIGHT)

    def _on_keypress(self, arg) -> None:
        if not self._active:
            return
        self._command = self._command + chr(arg)
        self.set_content(self._screen_h-1, 0, self._command)
        self.dispatch(Events.K_RIGHT, curses.KEY_RIGHT)

    def _on_enter_keypress(self, arg) -> None:
        self._history.append(self._command)
        self.dispatch(Events.COMMAND_SEND, self._command)
        self._command = ":"
        self._active = False
        self.dispatch(Events.K_ESC, None)

    def _on_esc_keypress(self, arg) -> None:
        self._command = ":"
        self._active = False
        self.dispatch(Events.K_ESC, None)


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
        self._stdscr = stdscr
        self._events_action[Events.K_LEFT.value] = self._left
        self._events_action[Events.K_UP.value] = self._up
        self._events_action[Events.K_RIGHT.value] = self._right
        self._events_action[Events.K_DOWN.value] = self._down
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
        self.coordinates = (self._y - 1, self._x)

    def _right(self, dummy) -> None:
        self.coordinates = (self._y, self._x + 1)

    def _down(self, dummy) -> None:
        self.coordinates = (self._y + 1, self._x)

    def move(self) -> None:
        self._stdscr.move(self._y, self._x)

    def save(self) -> (int, int):
        self._history.append((self._y, self._x))
        return self._y, self._x

    def restore(self) -> (int, int):
        self.coordinates = self._history.pop()

    def _handle_cli(self) -> None:
        pass

    def _command_line_on(self, args) -> None:
        if self._commandline is not True:
            self._commandline = True
            self.save()
            self.coordinates = (self._screen_h-1, 0)

    def _command_line_off(self, args) -> None:
        if self._commandline is True:
            self._commandline = False
            self.restore()


def draw_menu(stdscr):
    curses.nonl()
    curses.set_escdelay(25)
    stdscr.clear()

    kinput = KInput(stdscr)
    header = Header(stdscr)
    statusbar = StatusBar(stdscr)
    cli = CommandLine(stdscr)
    cursor = Cursor(stdscr)

    header.title = "DrumpondNC"

    kinput.register(Events.K_ARROWS, cursor)
    cli.register(Events.K_ARROWS, cursor)

    cursor.register(Events.CURSOR_MOVE, statusbar)

    kinput.register(Events.K_ESC, statusbar)
    kinput.register(Events.K_ESC, cursor)
    kinput.register(Events.K_ESC, cli)
    cli.register(Events.K_ESC, statusbar)
    cli.register(Events.K_ESC, cursor)

    kinput.register(Events.MODE_CHANGE, statusbar)
    kinput.register(Events.MODE_CHANGE, cli)
    kinput.register(Events.MODE_CHANGE, cursor)

    kinput.register(Events.K_PRESS, cli)

    kinput.register(Events.K_ENTER, cli)

    cursor.coordinates = (1, 0)
    stdscr.refresh()
    counter = 0
    stop = False
    cursor.move()
    while not stop:

        if counter > 10:
            stop = True

        kinput.listen()
        cursor.move()
        counter = counter + 1
        # stdscr.clear()
        # stdscr.refresh()


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
