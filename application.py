import settings
import time
from tornado import ioloop
from app.models import account
from app.logger import setup_logger, logger
from app.redis_client import setup_redis, get_all_open_spider
from app import account_producer, main, spider_init,\
    data_pool_consumer


if __name__ == '__main__':
    start = time.clock()
    setup_logger(settings.log_level, settings.log_dir)
    logger.info('--------------------------------------')
    logger.info('--------------------------------------')
    logger.info('[ACM-Spider] 程序启动，初始化中 .........')
    setup_redis()
    spider_init()
    account.init_all()

    io_loop = ioloop.IOLoop().current()
    io_loop.spawn_callback(data_pool_consumer)
    io_loop.spawn_callback(account_producer)
    io_loop.run_sync(main)
    print('used time {}'.format(time.clock() - start))
