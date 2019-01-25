from bs4 import BeautifulSoup
from tornado import gen, httpclient
from tornado.queues import Queue

from app.helpers.exceptions import LoadPageException
from app.helpers.logger import logger
from app.models import submit
from config import settings

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64)AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/51.0.2704.103 Safari/537.36'

# 数据缓存池
DataPool = Queue(maxsize=settings.DATA_POOL_SIZE)


# crawl data type
class DataType:
    Submit = 0
    Code = 1


# http methods
class HttpMethod:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


# 所有Spider的基类
class Spider:
    TAG = '[BASE]'

    def __init__(self):
        self.account = None

    def __repr__(self):
        return '<{}Spider>'.format(self.TAG)

    ########################
    # 静态的工具方法
    ########################

    @staticmethod
    def init_http_client():
        try:
            httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
            logger.info('[ACM-Spider] 配置 CurlAsyncHTTPClient 成功')
        except Exception as ex:
            logger.error('[ACM-Spider] 配置 CurlAsyncHTTPClient 失败: {}'.format(ex))

    @staticmethod
    def fetch(url, callback=None, raise_error=True, **kwargs):
        http_client = httpclient.AsyncHTTPClient()
        return http_client.fetch(url, callback=callback, raise_error=raise_error,
                                 user_agent=USER_AGENT, **kwargs)

    @staticmethod
    def get_bs4(markup, parser):
        return BeautifulSoup(markup, parser)

    @staticmethod
    def get_lxml_bs4(markup):
        return BeautifulSoup(markup, 'lxml')

    @staticmethod
    async def load_page(url, headers=None, **kwargs):
        response = None
        try:
            response = await Spider.fetch(url, headers=headers, **kwargs)
        except httpclient.HTTPError as ex:
            logger.error('加载 {} 失败: {}'.format(url, ex))
            raise LoadPageException('加载 {} 失败: {}'.format(url, ex))
        finally:
            return response

    @staticmethod
    async def put_queue(item_list):
        for item in item_list:
            if 'account' in item:
                await DataPool.put(item)
        logger.info('Success to put {} item into queue'.format(len(item_list)))


    ########################
    # 抽象方法
    ########################

    def get_code(self, run_id, **kwargs):
        """ 留给子类实现具体逻辑 """
        raise Exception('没有具体实现')

    def run(self):
        """ 留给子类实现具体逻辑 """
        raise Exception('没有具体实现')

    async def fetch_code(self):
        error_submits = submit.get_error_submits(self.account)
        logger.info('{} has {} error submits'.format(self.account, len(error_submits)))
        for run_id, pro_id in error_submits:
            logger.info('start to get code {}:{}'.format(self.account, run_id))
            code = await self.get_code(run_id, pro_id=pro_id)
            if not code:
                logger.info('code error {}:{}, waited 120s'.format(self.account, run_id))
                await gen.sleep(60 * 2)
            else:
                status = {
                    'type': DataType.Code, 'account': self.account,
                    'run_id': run_id, 'code': code
                }
                logger.info('{}:{} put queue'.format(self.account, run_id))
                await self.put_queue([status])
                await gen.sleep(30)
                logger.info('finished getting code {}:{}'.format(self.account, run_id))
