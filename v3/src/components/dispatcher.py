from logging import DEBUG
from ..core.dp_server import DPServer
from ..core.dp_server import DPLogger

class Dispatcher(DPServer):
    def __init__(self, host: str = '127.0.0.1',
                 port: int = 7581) -> None:
        super().__init__('dispatcher', host, port)

    def start(self) -> None:
        dp_logger = DPLogger('logger')
        dp_logger.log_level(DEBUG)
        dp_logger.start(in_thread=True)
        super().start(in_thread=True)
