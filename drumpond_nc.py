import inspect
import curses

from curses import window
from enum import Enum


class InputMode(Enum):
    WAIT = 1
    COMMAND = 2
    INSERT = 3
    VISUAL = 4
    PLAYBACK = 5


class Component():

    __events__ = (
        "arrow_keypress",
        "cursor_move",
        "enter_keypress",
        "esc_keypress",
        "keypress",
        "mode_change",
    )

    def __init__(self, name: str, stdscr: window) -> None:
        self._name = name
        self._stdscr = stdscr
        self._screen_h, self._screen_w = stdscr.getmaxyx()
        self._mode: InputMode = InputMode.WAIT
        self._mode_prev: InputMode = InputMode.WAIT
        self._events = {event: dict() for event in self.__events__}

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

    def get_subscribers(self, event: str):
        return self._events[event]

    def register(self, event: str, who):
        if event not in self.__events__:
            raise ValueError("Unknow event: {}".format(event))
        assert(isinstance(who, Component))
        callback = getattr(who, "on_"+event)
        self.get_subscribers(event)[who] = callback

    def unregister(self, event: str, who: str):
        del self.get_subscribers(event)[who]

    def dispatch(self, event: str, message):
        for subscriber, callback in self.get_subscribers(event).items():
            callback(message)

    def on_esc_keypress(self, dummy) -> bool:
        if self._mode == InputMode.WAIT:
            return False
        self._mode_prev = self._mode
        self._mode = InputMode.WAIT
        return True

    def on_mode_change(self, mode: InputMode) -> bool:
        if mode != self._mode and self._mode == InputMode.WAIT:
            self._mode_prev = self._mode
            self._mode = mode
            return True
        return False


class KInput(Component):

    def __init__(self, stdscr: window) -> None:
        super().__init__("kinput", stdscr)
        self._stdscr = stdscr
        self._k = 0
        self._actions: list = [None] * curses.KEY_MAX
        self._actions[curses.KEY_LEFT] = (
            "arrow_keypress", curses.KEY_LEFT)
        self._actions[curses.KEY_UP] = (
            "arrow_keypress", curses.KEY_UP)
        self._actions[curses.KEY_RIGHT] = (
            "arrow_keypress", curses.KEY_RIGHT)
        self._actions[curses.KEY_DOWN] = (
            "arrow_keypress", curses.KEY_DOWN)
        self._actions[curses.KEY_ENTER] = (
            "enter_keypress", None)
        self._actions[10] = (  # ENTER
            "enter_keypress", None)
        self._actions[13] = (  # ENTER
            "enter_keypress", None)
        self._actions[27] = (  # ESC
            "esc_keypress", None)
        self._actions[ord(':')] = (
            "mode_change", InputMode.COMMAND)
        self._actions[ord('i')] = (
            "mode_change", InputMode.INSERT)
        self._actions[ord('v')] = (
            "mode_change", InputMode.VISUAL)
        self._actions[ord('p')] = (
            "mode_change", InputMode.PLAYBACK)

    def listen(self) -> bool:
        self._k = self._stdscr.getch()
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

    @property
    def info(self) -> str:
        return self._content_l

    @info.setter
    def info(self, info: str = "") -> None:
        self.set_content(self._h, 0, info, self._content_r)

    def on_cursor_move(self, yx: (int, int) = (0, 0)) -> None:
        y, x = yx
        self.set_content(self._h, 0,
                         self._content_l,
                         "{},{}".format(str(y), str(x)))

    def on_esc_keypress(self, dummy) -> None:
        if super().on_esc_keypress(None):
            self.info = InputMode.WAIT

    def on_mode_change(self, mode: InputMode) -> None:
        if super().on_mode_change(mode):
            self.info = mode


class Commands():

    def quit(self):
        pass

    q = quit


class CommandLine(Row):

    def __init__(self, stdscr: window) -> None:
        super().__init__("command_line", stdscr)
        self._command: str = ""
        self._history: list = list()
        self._commands = dict()
        for element in inspect.getmembers(
                Commands, predicate=inspect.ismethod):
            self._commands[element[0]] = element[1]


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
        self._y: int = 0
        self._x: int = 0
        self._history: list[(int, int)] = [(0, 0)]
        self._stdscr = stdscr

    @property
    def coordinates(self) -> (int, int):
        return self._x, self._y

    @coordinates.setter
    def coordinates(self, yx: (int, int) = (0, 0)) -> None:
        y, x = yx
        h, v = self._stdscr.getmaxyx()
        self._y = max(0, y)
        self._y = min(h-1, y)
        self._x = max(0, x)
        self._x = min(h-1, x)
        self.dispatch("cursor_move", (self._y, self._x))

    def move(self) -> None:
        self._stdscr.move(self._y, self._x)

    def save(self) -> (int, int):
        self._history.append((self._y, self._x))
        return self._y, self._x

    def restore(self) -> (int, int):
        self.coordinates = self._history.pop()

    def on_arrow_keypress(self, arrow):
        if arrow == curses.KEY_LEFT:
            self.coordinates = (self._y, self._x-1)
        elif arrow == curses.KEY_UP:
            self.coordinates = (self._y-1, self._x)
        elif arrow == curses.KEY_RIGHT:
            self.coordinates = (self._y, self._x+1)
        elif arrow == curses.KEY_DOWN:
            self.coordinates = (self._y+1, self._x)


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
    kinput.register("arrow_keypress", cursor)
    cursor.register("cursor_move", statusbar)

    kinput.register("esc_keypress", statusbar)
    kinput.register("esc_keypress", cli)
    kinput.register("esc_keypress", cursor)

    kinput.register("mode_change", statusbar)
    kinput.register("mode_change", cli)
    kinput.register("mode_change", cursor)

    cursor.coordinates = (1, 0)
    stdscr.refresh()
    counter = 0
    stop = False
    while not stop:

        if counter > 10:
            stop = True

        cursor.move()
        kinput.listen()
        counter = counter + 1
        # stdscr.clear()
        # stdscr.refresh()


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
