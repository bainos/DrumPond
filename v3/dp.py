import asyncio
import logging

from dp_server import DPServer
from dp_client import DPClient
from time import sleep


if __name__ == '__main__':
    dp_server = DPServer('router')
    dp_server.log_level(logging.ERROR)
    dp_server.start()

    dp_client_1 = DPClient('dp_client_1')
    dp_client_1.log_level(logging.DEBUG)
    dp_client_1.start()

    # dp_client_2 = DPClient('dp_client_2')
    # dp_client_2.log_level(logging.ERROR)
    # dp_client_2.start()

    sleep(1)
    asyncio.run(dp_client_1.send('boom!'))
    # sleep(1)
    # asyncio.run(dp_client_2.send('yeah!'))
    sleep(1)
    asyncio.run(dp_client_1.send('sbam!'))
    sleep(1)
    # asyncio.run(dp_client_2.send('yo!'))
    # sleep(1)
    asyncio.run(dp_client_1.send('STOP'))

