import threading
import asyncio
import logging

logging.basicConfig(level=logging.INFO)


class DPServer():
    def __init__(self, host: str = '127.0.0.1', port: int = 7581) -> None:
        self.loop = asyncio.new_event_loop()
        self.host = host
        self.port = port

    async def _handle_msg(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        logging.info(f"Received {message!r} from {addr!r}")
        if message == 'STOP':
            logging.info(f'Stopping {self.host}:{self.port}')
            writer.close()
            await writer.wait_closed()
            self.loop.stop()

    def _start(self):
        self.loop.create_task(
                asyncio.start_server(
                    self._handle_msg,
                    host=self.host,
                    port=self.port,
                    )
                )
        logging.info(f'Serving on {self.host}:{self.port}')
        self.loop.run_forever()

    def start(self):
        logging.info('Starting DrumPond')
        threading.Thread(target=self._start).start()

class DPClient():
    def __init__(self, host: str = '127.0.0.1', port: int = 7581) -> None:
        self.loop: asyncio.AbstractEventLoop | None
        self.host: str = host
        self.port: int = port
        self.id: int | None
        self.reader: asyncio.StreamReader | None
        self.writer: asyncio.StreamWriter | None
        self.active: bool = False

    async def _open_connection(self):
        self.reader, self.writer = await asyncio.open_connection(
                self.host,
                self.port,
            )
        _, self.id = self.writer.get_extra_info('peername')
        self.active = True

    def _setup(self) -> None:
        self.loop = asyncio.get_event_loop()
        asyncio.create_task(self._open_connection())

    async def _handle_msg(self, message: str):
        logging.info(f'{self.id} < {message}')

    async def _listen(self):
        while self.active:
            data = await sslf.reader.read(100)
            await self._handle_msg(data.decode())


async def tcp_echo_client(message):
    if message == 'STOP':
        await asyncio.sleep(3)

    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 7581)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    # data = await reader.read(100)
    # print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()

def client_worker():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(tcp_echo_client('Client 1'))
    loop.run_until_complete(tcp_echo_client('Client 2'))
    loop.run_until_complete(tcp_echo_client('STOP'))
    loop.stop()


if __name__ == '__main__':
    dp_server = DPServer()
    dp_server.start()
    # threading.Thread(target=server_worker).start()
    threading.Thread(target=client_worker).start()

