import settings
import time
from tornado import ioloop
from app import account_producer, main, spider_init
from app.logger import setup_logger


if __name__ == '__main__':
    start = time.clock()
    setup_logger(settings.log_level, settings.log_dir)
    # spider_init()

    io_loop = ioloop.IOLoop().current()
    # io_loop.spawn_callback(account_producer)
    io_loop.run_sync(main)
    print('used time {}'.format(time.clock() - start))
