from . import Spider
from tornado import gen


class ZojSpider(Spider):
    TAG = '[ZOJ]'
    domain = 'http://acm.zju.edu.cn/'

    def __init__(self):
        super(ZojSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @gen.coroutine
    def run(self):
        pass
