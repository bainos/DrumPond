import asyncio

# from logging import INFO
from logging import ERROR
from logging import DEBUG
from src.core.dp_server import DPServer
from src.core.dp_server import DPLogger
from src.core.dp_client import DPClient
from time import sleep


if __name__ == '__main__':
    dp_logger = DPLogger('logger')
    dp_logger.log_level(DEBUG)
    dp_logger.start()

    dp_server = DPServer('router')
    dp_server.log_level(ERROR)
    dp_server.start()

    dp_client_1 = DPClient('dp_client_1')
    dp_client_1.log_level(DEBUG)
    dp_client_1.start()

    dp_client_2 = DPClient('dp_client_2')
    dp_client_2.log_level(ERROR)
    dp_client_2.start()

    sleep(1)
    asyncio.run(dp_client_1.send('boom!'))
    sleep(1)
    asyncio.run(dp_client_2.send('yeah!'))
    sleep(1)
    asyncio.run(dp_client_1.send('sbam!'))
    sleep(1)
    asyncio.run(dp_client_2.send('yo!'))
    sleep(1)
    asyncio.run(dp_client_1.send('STOP'))

