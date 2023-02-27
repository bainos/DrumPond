import threading
import asyncio
import logging
import json


class DPUtils():
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s",'
                  '"name":"%(name)s",'
                  '"level":"%(levelname)s",'
                  '"message":"%(message)s"}'
                )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger


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
        self.l = DPUtils().get_logger(f'{__name__}:{name}')

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError as e:
            self.l.info(f'{e}')
            self.l.info(f'creating new event loop')
            self.loop = asyncio.new_event_loop()

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    async def _handle_msg(self,
                          reader: asyncio.StreamReader,
                          writer: asyncio.StreamWriter
                          ) -> None:
        while True:
            data = await reader.read(128)
            try:
                msg = json.loads(data.decode())
            except Exception as e:
                self.l.error(json.dumps({
                    'exception': str(e),
                    'data': data.decode(),
                    'client': str(writer.get_extra_info('peername')),
                    }))
                break

            if msg['name'] not in self.clients.keys():
                addr = writer.get_extra_info('peername')
                self.l.info(f'registering new client {msg["name"]} {addr}')
                self.clients[f'{msg["name"]}'] = writer
                continue

            self.l.info(f'<({msg["name"]}) {msg["msg"]}')
            for c in self.clients.keys():
                self.clients[c].write(data)
                await self.clients[c].drain()

            if msg['msg'] == 'STOP':
                self.l.info(f'stopping {self.host}:{self.port}')
                break

        self.l.debug('stopping loop')
        for t in asyncio.all_tasks():
            self.l.info(t.get_name())

        self.loop.stop()

    def _start(self):
        t_server = self.loop.create_task(
                asyncio.start_server(
                    self._handle_msg,
                    host=self.host,
                    port=self.port,
                    )
                )
        self.bg_tasks.add(t_server)
        t_server.add_done_callback(self.bg_tasks.discard)
        self.l.info(f'serving on {self.host}:{self.port}')
        self.loop.run_forever()

    def start(self):
        self.l.info('starting')
        threading.Thread(target=self._start).start()


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
        self.l = DPUtils().get_logger(f'{__name__}:{name}')

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError as e:
            self.l.info(f'{e}')
            self.l.info(f'creating new event loop')
            self.loop = asyncio.new_event_loop()

    def log_level(self, level: int) -> None:
        self.l.setLevel(level)
        for h in self.l.handlers:
            h.setLevel(level)

    async def _open_connection(self):
        self.l.info('opening connection')
        self.reader, self.writer = await asyncio.open_connection(
                self.remote_host,
                self.remote_port,
            )
        self.host, self.port = self.writer.get_extra_info('peername')
        self.active = True
        self.l.info('connection ready')
        await self.send('register me')

    async def _handle_msg(self, message: str):
        self.l.info(f'< {message}')

    async def _listen(self):
        self.l.debug(f'active {self.active}')
        await asyncio.sleep(0.1)
        if not self.active or self.reader is None:
            await asyncio.sleep(0.1)
            await self._listen()

        while self.active and self.reader is not None:
            self.l.debug('listening')
            data = await self.reader.read(128)
            msg = json.loads(data.decode())
            if msg['msg'] == 'STOP':
                if self.writer is None:
                    self.l.error('connection lost')
                    raise
                self.l.info(f'stopping {self.host}:{self.port}')
                self.writer.close()
                await self.writer.wait_closed()
                break

            if msg['name'] != self.name:
                await self._handle_msg(msg['msg'])

        self.l.debug('stopping loop')
        for t in asyncio.all_tasks():
            self.l.info(t.get_name())

        self.loop.stop()

    async def send(self, message: str) -> None:
        self.l.info(f'> {message}')
        msg = json.dumps({'name': self.name,'msg': message})
        if self.writer is None:
            self.l.error('connection lost')
            raise
        self.writer.write(msg.encode())
        await self.writer.drain()

    def _start(self) -> None:
        t_conn = self.loop.create_task(self._open_connection())
        t_listen = self.loop.create_task(self._listen())
        self.bg_tasks.add(t_conn)
        self.bg_tasks.add(t_listen)
        t_conn.add_done_callback(self.bg_tasks.discard)
        t_listen.add_done_callback(self.bg_tasks.discard)
        self.loop.run_forever()

    def start(self):
        self.l.info('starting')
        threading.Thread(target=self._start).start()


from time import sleep
if __name__ == '__main__':
    dp_server = DPServer('router')
    dp_server.log_level(logging.INFO)
    dp_server.start()

    dp_client_1 = DPClient('dp_client_1')
    dp_client_1.log_level(logging.INFO)
    dp_client_1.start()

    dp_client_2 = DPClient('dp_client_2')
    dp_client_2.log_level(logging.INFO)
    dp_client_2.start()

    sleep(1)
    asyncio.run(dp_client_1.send('boom!'))
    sleep(1)
    asyncio.run(dp_client_2.send('yeah!'))
    sleep(1)
    # asyncio.run(dp_client_1.send('sbam!'))
    # sleep(1)
    # asyncio.run(dp_client_2.send('yo!'))
    # sleep(1)
    asyncio.run(dp_client_1.send('STOP'))
