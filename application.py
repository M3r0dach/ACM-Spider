import settings
from tornado import ioloop
from app import account_producer, main
from app.logger import setup_logger


if __name__ == '__main__':
    setup_logger(settings.log_level, settings.log_dir)

    io_loop = ioloop.IOLoop().current()
    io_loop.spawn_callback(account_producer)
    io_loop.run_sync(main)
