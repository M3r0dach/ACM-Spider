import settings
import time
from tornado import ioloop
from app import account_producer, main, spider_init
from app.logger import setup_logger, logger
from app.redis_client import setup_redis


if __name__ == '__main__':
    start = time.clock()
    setup_logger(settings.log_level, settings.log_dir)
    logger.info('[ACM-Spider] 程序初始化 ......')
    setup_redis()
    # spider_init()


    io_loop = ioloop.IOLoop().current()
    # io_loop.spawn_callback(account_producer)
    io_loop.run_sync(main)
    print('used time {}'.format(time.clock() - start))
