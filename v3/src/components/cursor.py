import json
from curses import window
from curses import KEY_LEFT, KEY_DOWN, KEY_UP, KEY_RIGHT
from typing import Callable
from .base_component import BaseComponent
from ..core import dp_shm as shm


class Cursor(BaseComponent):
    def __init__(self, stdscr: window,
                 remote_host: str = '127.0.0.1',
                 remote_port: int = 7581) -> None:
        self._y: int = shm.registry['miny']
        self._x: int = shm.registry['minx']

        super().__init__('cursor', stdscr,
                         remote_host, remote_port)
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
        if y <= shm.registry['maxy'] and y >= shm.registry['miny']:
            self._y = y
        if x <= shm.registry['maxx'] and x >= shm.registry['minx']:
            self._x = x
        self._stdscr.move(self._y, self._x)
        shm.dset({'y': self._y,'x': self._x})
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
            await self._move[msg]()
            await self._handle_input(msg)
