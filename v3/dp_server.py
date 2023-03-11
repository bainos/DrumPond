import threading
import asyncio
import json
from types import NoneType

from dp_utils import DPUtils


class DPServer():
    def __init__(self,
                 name: str,
                 host: str = '127.0.0.1',
                 port: int = 7581
                 ) -> None:
        self.name: str = name
        self.host: str = host
        self.port: int = port
        self.bg_tasks: set[asyncio.Task] = set()
        self.clients: dict[str, asyncio.StreamWriter] = dict()
        self.stop_request: asyncio.Event = asyncio.Event()
        self.l = DPUtils().get_logger(f'{__name__}:{name}')

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    async def _handle_msg(self,
                          reader: asyncio.StreamReader,
                          writer: asyncio.StreamWriter
                          ) -> None:
        task = asyncio.current_task()
        task_name = 'unknown-task-name'
        if task is not None:
            self.bg_tasks.add(task)
            task.add_done_callback(self.bg_tasks.discard)
            task_name = task.get_name()
        else:
            return

        for bgt in self.bg_tasks:
            self.l.debug(f'{task.get_name()}:bg_len:{len(self.bg_tasks)}')
            self.l.debug(f'{task.get_name()}:bg_name:{bgt.get_name()}')
            self.l.debug(f'{task.get_name()}:bg_coro:{bgt.get_coro()}')

        self.l.debug(f'task_name:{task_name}')
        while True:
            data = await reader.read(128)
            try:
                msg = json.loads(data.decode())
            except Exception as e:
                self.l.error(json.dumps({
                    'exception': str(e),
                    'data': data.decode(),
                    'client': str(writer.get_extra_info('peername')),
                    'task': task_name,
                    }))
                break

            if msg['name'] not in self.clients.keys():
                addr = writer.get_extra_info('peername')
                self.l.debug(f'{task_name}:registering new client {msg["name"]} {addr}')
                self.clients[msg["name"]] = writer
                continue

            self.l.info(f'<({msg["name"]}) {msg["msg"]}')
            for c in self.clients.keys():
                self.clients[c].write(data)
                await self.clients[c].drain()
                self.l.debug(f'>({c}) {data.decode()}')

            if msg['msg'] == 'STOP':
                self.stop_request.set()
                break

        if len(self.clients) == 0:
            self.l.debug(f'{task_name}:no more active clients')

        for t in asyncio.all_tasks():
            self.l.debug(f'{task_name}:{t.get_name()}')

        if len(asyncio.all_tasks()) == 1:
            self.l.debug(f'{task_name}:stopping loop')

    async def main(self) -> NoneType:
        self.l.info(f'serving on {self.host}:{self.port}')
        server = await asyncio.start_server(
                    self._handle_msg,
                    host=self.host,
                    port=self.port,
                    )
        await self.stop_request.wait()
        self.stop_request.clear()
        self.l.info('stopping the server')
        server.close()
        await server.wait_closed()

    def _start(self):
        asyncio.run(self.main())

    def start(self):
        self.l.info('starting')
        threading.Thread(target=self._start).start()


