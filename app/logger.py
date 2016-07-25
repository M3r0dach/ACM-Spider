import logging

# global logger
logger = logging.getLogger('app')


def setup_logger(level, pathname):
    logger.setLevel(level)
    logging.basicConfig()

    # create a file handler
    file_handler = logging.FileHandler(pathname, encoding='utf-8')
    file_handler.setLevel(level)

    # create a stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    # create a logging format
    formatter = logging.Formatter(
        '[%(asctime)s] %(filename)s/%(funcName)s::%(lineno)d'
        ' - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler)
