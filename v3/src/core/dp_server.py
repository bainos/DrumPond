import threading
import asyncio
import json

from logging import makeLogRecord
import struct
import pickle

from typing import Callable
from .dp_utils import DPUtils


class BServer():
    def __init__(self, name: str, host: str, port: int) -> None:
        self.name: str = name
        self.host: str = host
        self.port: int = port
        self.bg_tasks: set[asyncio.Task] = set()
        self.clients: dict[str, asyncio.StreamWriter] = dict()
        self.stop_request: asyncio.Event = asyncio.Event()
        self.l = DPUtils().get_logger(name='bserver',
                                      output='socket')

        @staticmethod
        async def _handle_msg(message: str) -> None:
            self.l.info(f'< {message}')

        self._callback: Callable = _handle_msg

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    def set_callback(self, cb: Callable) -> None:
        self._callback = cb

    async def _main(self) -> None:
        self.l.info(f'serving on {self.host}:{self.port}')
        server = await asyncio.start_server(
                    self._callback,
                    host=self.host,
                    port=self.port,
                    )
        await self.stop_request.wait()
        self.stop_request.clear()
        self.l.info('stopping the server')
        server.close()
        await server.wait_closed()

    def _start(self) -> None:
        asyncio.run(self._main())

    def start(self, in_thread: bool=False) -> None:
        self.l.debug('starting')
        if in_thread:
            threading.Thread(target=self._start).start()
            return
        self._start()

class DPServer(BServer):
    def __init__(self, name: str, host: str = '127.0.0.1',
                 port: int = 7581) -> None:
        super().__init__(name, host, port)
        self.set_callback(self._handle_msg)
        self.l = DPUtils().get_logger(name='dpserver',
                                      output='socket')

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

            self.l.debug(f'<({msg["name"]}) {msg["msg"]}')
            for c in self.clients.keys():
                self.clients[c].write(data)
                await self.clients[c].drain()
                self.l.debug(f'>({c}) {data.decode()}')

            if msg['msg'] == 'STOP':
                self.l.critical('LOGGER_QUIT')
                self.stop_request.set()
                break


class DPLogger(DPServer):
    def __init__(self, name: str, host: str = '127.0.0.1',
                 port: int = 9488) -> None:
        super().__init__(name, host, port)
        self.l = DPUtils.get_logger(name='dplogger',
                                    output='file')
        self.set_callback(self._handle_msg)

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

        addr = writer.get_extra_info('peername')
        self.l.debug(f'task_name:{addr!r} {task_name}')
        while True:
            chunk = await reader.read(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = await reader.read(slen)
            while len(chunk) < slen:
                chunk = chunk + await reader.read(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = makeLogRecord(obj)
            self.l.handle(record)
            if record.msg == 'LOGGER_QUIT':
                self.stop_request.set()
                break

