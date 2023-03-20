from curses import window
from ..constants import modes as M
from ..core.dp_client import DPClient


class BaseComponent(DPClient):
    def __init__(self, name: str, stdscr: window, remote_host: str = '127.0.0.1', remote_port: int = 7581) -> None:
        super().__init__(name, remote_host, remote_port)
        self._stdscr = stdscr
        self._screen_h, self._screen_w = stdscr.getmaxyx()
        self._mode: str = M.NORMAL

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode) -> None:
        self._mode = mode
