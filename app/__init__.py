import sys
import traceback

from tornado import gen
from tornado.queues import Queue

from app.helpers.exceptions import LoginException
from app.helpers.logger import logger
from app.helpers.redis_utils import is_spider_open
from app.models import account, submit
from app.spiders import DataPool, DataType, Spider
from app.spiders import HduSpider, BnuSpider, VjudgeSpider, CodeforcesSpider
from app.spiders import PojSpider, BestcoderSpider
from config import settings

# Account 生产消费队列
AccountQueue = Queue(maxsize=settings.ACCOUNT_QUEUE_SIZE)

# SpiderRunner 缓存池
SpiderFactory = {
    oj: Queue(maxsize=settings.SPIDER_CACHE_SIZE) for oj in settings.SUPPORT_OJ
}


def spider_init():
    """ 实例化SpiderRunner, 放入SpiderFactory """
    logger.info('[SpiderInit] 生成 SpiderRunner 缓存 ...')
    for oj, oj_queue in SpiderFactory.items():
        spider_name = settings.SUPPORT_OJ[oj] + 'Spider'
        spider_class = getattr(sys.modules['app.spiders.' + spider_name],
                               spider_name)
        while oj_queue.qsize() < oj_queue.maxsize:
            oj_queue.put_nowait(spider_class())
        logger.info('[{0}] 缓存池初始化 OK => size {1}'.format(spider_name, oj_queue.qsize()))


async def account_producer():
    """ 待爬取账号生产者 """
    logger.info('[AccountProducer] 开始获取可用账号放入队列 ...')
    while True:
        logger.info('[AccountProducer] next turn')
        cur = account.get_available_account()
        if cur and is_spider_open(cur.oj_name):
            await AccountQueue.put(cur)
            logger.info('{0} ===> 账号入队列 AccountQueue(size={1})'.format(cur, AccountQueue.qsize()))
        else:
            await gen.sleep(10)


async def spider_runner(idx):
    """ 爬虫运行地 """
    logger.info('[SpiderRunner #{0}] 开始运行 ...'.format(idx))
    while True:
        logger.info('[SpiderRunner] next turn')
        cur_account = await AccountQueue.get()
        logger.info('[SpiderRunner #{0}] {1} <=== account_queue(size={2})'
                    .format(idx, cur_account, AccountQueue.qsize()))
        # let spider.run()
        worker = await SpiderFactory[cur_account.oj_name].get()
        logger.info('[SpiderRunner #{0}] {1} get worker'
                    .format(idx, cur_account))
        worker.account = cur_account

        try:
            cur_account.set_status(account.AccountStatus.UPDATING)
            cur_account.save()
            await worker.run()
            cur_account.set_status(account.AccountStatus.NORMAL)
        except LoginException as ex:
            logger.error(ex)
            cur_account.set_status(account.AccountStatus.ACCOUNT_ERROR)
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())
            cur_account.set_status(account.AccountStatus.UPDATE_ERROR)
        finally:
            cur_account.save()

        # work done
        logger.info('[SpiderRunner #{0}] {1} work done'.format(idx, cur_account))
        SpiderFactory[cur_account.oj_name].task_done()
        AccountQueue.task_done()
        await SpiderFactory[cur_account.oj_name].put(worker)


async def data_pool_consumer():
    """ 爬取的数据消费协程 """
    logger.info('[DataPoolConsumer] 数据消费协程开启 ... ')
    while True:
        logger.info('[DataPoolConsumer] next turn')
        while DataPool.empty():
            await gen.sleep(10)
        new_data = await DataPool.get()
        logger.info('[DataPoolConsumer] get new submit {}:{}'.format(new_data['account'],new_data['run_id']))              
        # new submit
        if new_data['type'] == DataType.Submit:
            if submit.create_submit(new_data):
                logger.info('[DataPoolConsumer] 存入新提交 for <{} {} {}>'.format(
                    new_data['account'].oj_name, new_data['run_id'], new_data['account'].nickname
                ))
        # save the code
        elif new_data['type'] == DataType.Code:
            if submit.update_code(new_data):
                logger.info('[DataPoolConsumer] 更新代码 for <{} {} {}>'.format(
                    new_data['account'].oj_name, new_data['run_id'], new_data['account'].nickname
                ))
            else:
                logger.info('[DataPoolConsumer] 更新代码失败:提交不存在 for <{} {} {}>'.format(
                    new_data['account'].oj_name, new_data['run_id'], new_data['account'].nickname
                ))
        DataPool.task_done()


async def spider_main():
    await gen.multi([spider_runner(i) for i in range(settings.SPIDER_RUNNER_SIZE)])


def make_spider_app(loop):
    Spider.init_http_client()
    account.init_all()
    spider_init()
    loop.spawn_callback(data_pool_consumer)
    loop.spawn_callback(account_producer)
    loop.spawn_callback(spider_main)