import settings
from tornado import gen
from tornado.queues import Queue
from app.models import account
from app.logger import logger


mq = Queue(maxsize=settings.MAX_QUEUE_SIZE)


@gen.coroutine
def account_producer():
    logger.info('queue start working')
    while True:
        cur = account.get_available_account()
        if cur:
            yield mq.put(cur)
            logger.info('{} put into queue, queue size {}'.format(cur, mq.qsize()))
        else:
            yield gen.sleep(10)


@gen.coroutine
def spider_runner():
    while True:
        cur = yield mq.get()
        logger.info('{} from queue, start working'.format(cur))
        yield gen.sleep(5)
        cur.set_normal()
        cur.save()
        logger.info('{} work done'.format(cur))
        mq.task_done()


@gen.coroutine
def main():
    account.init_all()
    yield [spider_runner() for _ in range(settings.WORKER_SIZE)]

