import asyncio
from curses import window
from ..core import dp_shm as shm
from ..core.dp_client import DPClient
from ..constants import modes as M
from ..constants import events as E


class Input(DPClient):
    def __init__(self, stdscr: window,
                 remote_host: str = '127.0.0.1',
                 remote_port: int = 7581) -> None:
        self._k = 0
        self._stdscr = stdscr

        shm.init()

        super().__init__('input', remote_host, remote_port)

    async def _listen(self) -> None:
        task = asyncio.current_task()
        task_name = 'unknown-task-name'
        if task is not None:
            task_name = task.get_name()
        self.l.debug(f'{task_name}:active {self.active}')
        await asyncio.sleep(0.1)
        if not self.active or self.reader is None:
            await asyncio.sleep(0.1)
            await self._listen()

        while True:
            self._k = self._stdscr.getch()
            shm.registry['k'] = self._k
            self.l.debug(f'getch: {chr(self._k)}'f'|{shm.registry}')
            if shm.registry['mode'] == M.NORMAL:
                if chr(self._k) == 'i':
                    shm.kset('mode', M.INSERT)
                    await self.send(E.MODE_CHANGE)
            if chr(self._k) == 'q':
                await self.send('STOP')
                self.stop_request.set()
                break
            else:
                await self.send(self._k)

        self.l.debug(f'{task_name}:stopping')

