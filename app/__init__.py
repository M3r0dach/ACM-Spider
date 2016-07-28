import sys
import settings
from tornado import gen
from tornado.queues import Queue
from app.models import account
from app.logger import logger
from app.spiders import HduSpider, BnuSpider, VjudgeSpider, UvaSpider,\
    CodeforcesSpider, PojSpider, BestcoderSpider, ZojSpider


# account 队列
AccountQueue = Queue(maxsize=settings.MAX_QUEUE_SIZE)

# spider cache of every oj
SpiderFactory = {
    oj: Queue(maxsize=settings.SPIDER_CACHE_SIZE) for oj in settings.SUPPORT_OJ
}

# 数据缓存池
DataPool = Queue(maxsize=settings.DATA_POOL_SIZE)


def spider_init():
    logger.info('[SpiderInit] spider cache is generating ...')
    for oj, oj_queue in SpiderFactory.items():
        spider_name = settings.SUPPORT_OJ[oj] + 'Spider'
        spider_class = getattr(sys.modules['app.spiders.' + spider_name],
                               spider_name)
        while oj_queue.qsize() < oj_queue.maxsize:
            oj_queue.put(spider_class())
        logger.info('[{0}] cache queue INIT OK => size {1}'.format(spider_name, oj_queue.qsize()))


@gen.coroutine
def account_producer():
    logger.info('[AccountProducer] start producing')
    while True:
        cur = account.get_available_account()
        if cur:
            yield AccountQueue.put(cur)
            logger.info('{0} ===> account_queue(size={1})'.format(cur, AccountQueue.qsize()))
        else:
            yield gen.sleep(10)


@gen.coroutine
def spider_runner(idx):
    logger.info('[SpiderRunner #{0}] start running'.format(idx))
    while True:
        cur = yield AccountQueue.get()
        logger.info('[SpiderRunner #{0}] {1} <=== account_queue(size={2})'
                    .format(idx, cur, AccountQueue.qsize()))
        yield gen.sleep(5)
        cur.set_status(account.AccountStatus.NORMAL)
        cur.save()
        logger.info('{0} work done'.format(cur))
        AccountQueue.task_done()


@gen.coroutine
def data_pool_consumer():
    logger.info('[DataPool] consumer start working')
    while True:
        size = min(DataPool.qsize(), settings.BATCH_SAVE_SIZE)
        if size == 0:
            yield gen.sleep(10)
        else:
            pass


@gen.coroutine
def main():
    # yield [spider_runner(i) for i in range(settings.WORKER_SIZE)]

    yield HduSpider.HduSpider().run()
    # yield BnuSpider.BnuSpider().run()
    # yield VjudgeSpider.VjudgeSpider().run()
    # yield CodeforcesSpider.CodeforcesSpider().run()
    # yield PojSpider.PojSpider().run()
    # yield BestcoderSpider.BestcoderSpider().run()
    pass
