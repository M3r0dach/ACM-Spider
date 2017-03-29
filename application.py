from tornado import ioloop

from app import make_spider_app
from app.api import make_api_app
from app.helpers.logger import setup_logger, logger
from app.helpers.redis_utils import setup_redis
from config import settings

if __name__ == '__main__':
    setup_logger(settings.log_level, settings.log_dir)
    logger.info('--------------------------------------')
    logger.info('--------------------------------------')
    logger.info('[ACM-Spider] 程序启动，初始化中 .........')

    # 加入 SpiderApp 和 ApiApp 到 io_loop
    io_loop = ioloop.IOLoop().current()
    make_spider_app(io_loop)
    api_app = make_api_app()

    # 配置 redis
    setup_redis()

    # 开始运行
    api_app.listen(settings.app_port)
    io_loop.start()
