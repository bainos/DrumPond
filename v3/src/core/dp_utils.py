import logging

from logging.handlers import SocketHandler
from queue import Queue


class DPUtils():
    @staticmethod
    def get_logger(
            name: str,
            # sender: str,
            output: str = 'std',
            host: str = '127.0.0.1',
            port: int = 9488
            ) -> logging.Logger:

        # old_factory = logging.getLogRecordFactory()
        # def record_factory(*args, **kwargs):
            # record = old_factory(*args, **kwargs)
            # record.sender = sender
            # return record
        # logging.setLogRecordFactory(record_factory)

        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        if output == 'std':
            ch = logging.StreamHandler()
        elif output == 'file':
            ch = logging.FileHandler(filename=f'{name}.log', mode='w')
        elif output == 'socket':
            ch = SocketHandler(host, port)
        else:
            raise ValueError(
                f'{output} output type not foud,'
                ' valid types are "std", "file" and "socket"')
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


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DPQueue(Queue, metaclass=Singleton):
    pass
