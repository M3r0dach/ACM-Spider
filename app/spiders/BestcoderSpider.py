from tornado import gen
from app.spiders import Spider


class BestcoderSpider(Spider):
    TAG = '[BestcoderSpider]'
    domain = ''

    def __init__(self):
        super(BestcoderSpider, self).__init__()

    @gen.coroutine
    def run(self):
        pass
