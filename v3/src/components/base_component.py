from curses import window
from ..core.dp_client import DPClient
from ..core import dp_shm as shm


class BaseComponent(DPClient):
    def __init__(self, name: str, stdscr: window, remote_host: str = '127.0.0.1', remote_port: int = 7581) -> None:
        super().__init__(name, remote_host, remote_port)
        self._stdscr = stdscr

    async def _handle_input(self, msg) -> None:
        self.l.debug(f'< {msg}')
        # self._stdscr.refresh()
        self._stdscr.noutrefresh()

class Row(BaseComponent):
    def __init__(self, name: str, stdscr: window,
                 remote_host: str = '127.0.0.1',
                 remote_port: int = 7581) -> None:
        super().__init__(name, stdscr,
                         remote_host, remote_port)
        self._content: str = " " * shm.registry['winw']
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
        blank_space = " " * (shm.registry['winw'] - cl_len - cr_len)
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
        r = "{}x{}".format(str(shm.registry['winh']),
                           str(shm.registry['winw']))
        self.set_content(0, 0, title, r)

