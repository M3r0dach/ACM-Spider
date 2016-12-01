from tornado import ioloop
from app import make_spider_app
from app.helpers.logger import setup_logger, logger
from app.helpers.redis_client import setup_redis
from config import settings
from api import make_api_app


if __name__ == '__main__':
    setup_logger(settings.log_level, settings.log_dir)
    setup_redis()

    io_loop = ioloop.IOLoop().current()
    make_spider_app(io_loop)
    api_app = make_api_app()

    logger.info('--------------------------------------')
    logger.info('--------------------------------------')
    logger.info('[ACM-Spider] 程序启动，初始化中 .........')

    api_app.listen(8000)
    io_loop.start()
