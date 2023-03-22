from curses import window
from curses import KEY_LEFT, KEY_DOWN, KEY_UP, KEY_RIGHT
from typing import Callable
from ..core.dp_client import DPClient, json


class Cursor(DPClient):
    def __init__(self, stdscr: window,
                 remote_host: str = '127.0.0.1',
                 remote_port: int = 7581) -> None:
        maxy, maxx = stdscr.getmaxyx()
        self._stdscr: window = stdscr
        self._maxy: int = maxy - 2
        self._maxx: int = maxx - 2
        self._miny: int = 3
        self._minx: int = 2
        self._y: int = 3
        self._x: int = 2

        super().__init__('cursor', remote_host, remote_port)
        self._move: dict[int, Callable] = dict()
        self._move[KEY_LEFT] = self._left
        self._move[KEY_DOWN] = self._down
        self._move[KEY_UP] = self._up
        self._move[KEY_RIGHT] = self._right
        self.set_callback(self._handle_arrows)
        self._stdscr.move(self._y, self._x)

    @property
    def coordinates(self) -> tuple[int,int]:
        return self._x, self._y

    async def set_coordinates(self, y: int, x: int) -> None:
        if y <= self._maxy and y >= self._miny:
            self._y = y
        if x <= self._maxx and x >= self._minx:
            self._x = x
        self._stdscr.move(self._y, self._x)
        await self.send(json.dumps((self._y, self._x)))

    async def _left(self) -> None:
        await self.set_coordinates(self._y, self._x - 1)

    async def _up(self) -> None:
        await self.set_coordinates(self._y - 1, self._x)

    async def _right(self) -> None:
        await self.set_coordinates(self._y, self._x + 1)

    async def _down(self) -> None:
        await self.set_coordinates(self._y + 1, self._x)

    async def _handle_arrows(self, msg) -> None:
        if msg in (KEY_LEFT, KEY_DOWN, KEY_UP, KEY_RIGHT):
            self.l.debug(msg)
            await self._move[msg]()
            self._stdscr.refresh()
