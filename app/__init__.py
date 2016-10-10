import sys
import settings
from tornado import gen
from tornado.queues import Queue
from app.logger import logger
from app.models import account, submit
from app.redis_client import is_spider_open
from app.exceptions import LoginException
from app.spiders import DataPool, DataType
from app.spiders import HduSpider, BnuSpider, VjudgeSpider, CodeforcesSpider
from app.spiders import PojSpider, BestcoderSpider, ZojSpider, UvaSpider


# account 队列
AccountQueue = Queue(maxsize=settings.MAX_QUEUE_SIZE)

# spider cache of every oj
SpiderFactory = {
    oj: Queue(maxsize=settings.SPIDER_CACHE_SIZE) for oj in settings.SUPPORT_OJ
}


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
        if cur and is_spider_open(cur.oj_name):
            if cur.user.id > 5:
                continue
            yield AccountQueue.put(cur)
            logger.info('{0} ===> account_queue(size={1})'.format(cur, AccountQueue.qsize()))
        else:
            yield gen.sleep(10)


@gen.coroutine
def spider_runner(idx):
    logger.info('[SpiderRunner #{0}] start running'.format(idx))
    while True:
        cur_account = yield AccountQueue.get()
        logger.info('[SpiderRunner #{0}] {1} <=== account_queue(size={2})'
                    .format(idx, cur_account, AccountQueue.qsize()))
        # let spider.run()
        worker = yield SpiderFactory[cur_account.oj_name].get()
        worker.account = cur_account
        try:
            yield worker.run()
            cur_account.set_status(account.AccountStatus.NORMAL)
        except LoginException as ex:
            logger.error(ex)
            cur_account.set_status(account.AccountStatus.ACCOUNT_ERROR)
            yield gen.sleep(60 * 2)
        except Exception as ex:
            logger.error(ex)
            cur_account.set_status(account.AccountStatus.UPDATE_ERROR)
            yield gen.sleep(60 * 2)
        finally:
            cur_account.save()

        # work done
        logger.info('[SpiderRunner #{0}] {1} work done'.format(idx, cur_account))
        SpiderFactory[cur_account.oj_name].task_done()
        AccountQueue.task_done()
        yield SpiderFactory[cur_account.oj_name].put(worker)


@gen.coroutine
def data_pool_consumer():
    logger.info('[DataPool] consumer start working for process data')
    while True:
        while DataPool.empty():
            yield gen.sleep(10)
        new_data = yield DataPool.get()
        if new_data['type'] == DataType.Submit:
            if submit.create_submit(new_data):
                logger.info('[DataPool] success new status for <{} {} {}>'.format(
                    new_data['account'].oj_name, new_data['run_id'], new_data['account'].nickname
                ))
        elif new_data['type'] == DataType.Code:
            if not submit.update_code(new_data):
                yield DataPool.put(new_data)
        DataPool.task_done()


@gen.coroutine
def main():
    yield [spider_runner(i) for i in range(settings.WORKER_SIZE)]

    # yield HduSpider.HduSpider().run()
    # yield BnuSpider.BnuSpider().run()
    # yield VjudgeSpider.VjudgeSpider().run()
    # yield CodeforcesSpider.CodeforcesSpider().run()
    # yield PojSpider.PojSpider().run()
    # yield BestcoderSpider.BestcoderSpider().run()
    pass
