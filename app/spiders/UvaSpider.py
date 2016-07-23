from tornado import gen
from app.spiders import Spider


class UvaSpider(Spider):
    TAG = '[UvaSpider]'
    domain = ''

    def __init__(self):
        super(UvaSpider, self).__init__()

    @gen.coroutine
    def run(self):
        pass
