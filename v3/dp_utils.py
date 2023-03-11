import logging


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

