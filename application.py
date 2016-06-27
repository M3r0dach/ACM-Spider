from tornado import gen, ioloop
from app.logger import setup_logger
from settings import log_dir, log_level
from app.spiders import HduSpider


@gen.coroutine
def main():
    yield HduSpider.HduSpider().login()


if __name__ == '__main__':
    setup_logger(log_level, log_dir)

    io_loop = ioloop.IOLoop().current()
    io_loop.run_sync(main)
