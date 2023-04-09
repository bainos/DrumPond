#import multiprocessing
import threading
import asyncio
import json

from typing import Callable
from .dp_utils import DPUtils


class DPClient():
    def __init__(
            self,
            name: str,
            remote_host: str = '127.0.0.1',
            remote_port: int = 7581,
        ) -> None:
        self.name: str = name
        self.remote_host: str = remote_host
        self.remote_port: int = remote_port
        self.host: str | None
        self.port: int | None
        self.reader: asyncio.StreamReader | None
        self.writer: asyncio.StreamWriter | None
        self.additional_tasks: list[Callable] = list()
        self.bg_tasks: set[asyncio.Task] = set()
        self.active: bool = False
        self.stop_request: asyncio.Event = asyncio.Event()
        self.l= DPUtils.get_logger(name=name,
                                   output='socket')

        self._callback: Callable = self._handle_msg

    async def _handle_msg(self, message: str|int) -> None:
        self.l.info(f'< {message!r}')

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    def set_listener(self, l: Callable) -> None:
        self._listener = l

    def set_callback(self, cb: Callable) -> None:
        self._callback = cb

    async def send(self, message: str|int) -> None:
        self.l.debug(f'> {message!r}')
        msg = json.dumps({'name': self.name,'msg': message})
        if self.writer is None:
            self.l.error('connection lost')
            raise
        self.writer.write(msg.encode())
        await self.writer.drain()

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

        while self.reader is not None:
            if self.reader is None:
                self.l.error(f'{task_name}:connection lost')
                raise

            self.l.debug(f'{task_name}:listening')
            try:
                data = await self.reader.read(128)
            except Exception as e:
                self.l.critical(f'{task_name}:reader is broken:{e}')
                self.stop_request.set()
                break

            self.l.debug(f'{task_name}:decode message')
            try:
                msg = json.loads(data.decode())
            except Exception as e:
                self.l.critical(f'{task_name}:cannot decode message:{e}:{data.decode()}')
                self.stop_request.set()
                break

            self.l.debug(f'{task_name}:{msg}')
            if msg['msg'] == 'STOP':
                self.l.info(f'{task_name}:STOP received')
                self.stop_request.set()
                break

            self.l.info(f'{task_name}:handle messag fron {msg["name"]}')
            try:
                await self._callback(msg['msg'])
            except Exception as e:
                self.l.critical(f'{task_name}:client callback failure: {e!r}')
                self.stop_request.set()
                break

        self.l.info(f'{task_name}:stopping')

    async def _open_connection(self):
        self.l.debug('opening connection')
        self.reader, self.writer = await asyncio.open_connection(
                self.remote_host,
                self.remote_port,
            )
        self.host, self.port = self.writer.get_extra_info('peername')
        self.active = True
        self.l.info(f'connection to {self.host}:{self.port} ready')
        await self.send('register me')
        await self._listen()

    async def _main(self) -> None:
        t_conn = asyncio.create_task(self._open_connection(),
                                     name=f'{self.name}_c')
        self.bg_tasks.add(t_conn)
        t_conn.add_done_callback(self.bg_tasks.discard)

        for c in self.additional_tasks:
            t = asyncio.create_task(c(),name=f'{self.name}_{c.__name__}')
            self.bg_tasks.add(t)
            t.add_done_callback(self.bg_tasks.discard)

        await self.stop_request.wait()
        self.stop_request.clear()
        self.l.info('stopping')

    def _start(self) -> None:
        asyncio.run(self._main())

    def start(self, in_thread: bool=False) -> None:
        self.l.debug('starting')
        if in_thread:
            threading.Thread(target=self._start).start()
            return
        self._start()

