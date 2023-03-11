import threading
import asyncio
import json

from dp_utils import DPUtils


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
        self.bg_tasks: set[asyncio.Task] = set()
        self.active: bool = False
        self.stop_request: asyncio.Event = asyncio.Event()
        self.l = DPUtils().get_logger(f'{__name__}:{name}')

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    async def _handle_msg(self, message: str):
        self.l.info(f'< {message}')

    async def _listen(self):
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
            self.l.debug(f'{task_name}:listening')
            if self.reader is None:
                self.l.error(f'{task_name}:connection lost')
                raise
            data = await self.reader.read(128)
            msg = json.loads(data.decode())
            if msg['msg'] == 'STOP':
                self.l.debug(f'{task_name}:STOP received')
                self.stop_request.set()
                break

            if msg['name'] != self.name:
                await self._handle_msg(msg['msg'])

        self.l.debug(f'{task_name}:stopping')

    async def _open_connection(self):
        self.l.info('opening connection')
        self.reader, self.writer = await asyncio.open_connection(
                self.remote_host,
                self.remote_port,
            )
        self.host, self.port = self.writer.get_extra_info('peername')
        self.active = True
        self.l.info(f'client ready for {self.host}:{self.port}')
        await self.send('register me')
        await self._listen()

    async def send(self, message: str) -> None:
        self.l.info(f'> {message}')
        msg = json.dumps({'name': self.name,'msg': message})
        if self.writer is None:
            self.l.error('connection lost')
            raise
        self.writer.write(msg.encode())
        await self.writer.drain()

    async def main(self) -> None:
        t_conn = asyncio.create_task(self._open_connection(),
                                       name=f'{self.name}_c')
        # t_listen = asyncio.create_task(self._listen(),
                                         # name=f'{self.name}_l')
        self.bg_tasks.add(t_conn)
        # self.bg_tasks.add(t_listen)
        t_conn.add_done_callback(self.bg_tasks.discard)
        # t_listen.add_done_callback(self.bg_tasks.discard)
        await self.stop_request.wait()
        self.stop_request.clear()
        self.l.info('stopping the client')

    def _start(self) -> None:
        asyncio.run(self.main())

    def start(self):
        self.l.info('starting')
        threading.Thread(target=self._start).start()

