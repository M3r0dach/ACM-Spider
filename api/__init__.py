from tornado import web
from app.helpers import redis_client
from config.settings import SUPPORT_OJ


class SpiderRunnerHandler(web.RequestHandler):
    def get(self, *args, **kwargs):
        open_spiders = redis_client.get_all_open_spider()
        self.write({'error': 0, 'items': open_spiders})

    def post(self, *args, **kwargs):
        oj_name = self.get_body_argument('oj_name')
        if oj_name not in SUPPORT_OJ:
            self.write({'error': 1, 'message': '不支持的OJ'})
        else:
            redis_client.turn_on_spider(oj_name)
            self.write({'error': 0})

    def delete(self, *args, **kwargs):
        oj_name = self.get_body_argument('oj_name')
        if oj_name not in SUPPORT_OJ:
            self.write({'error': 1, 'message': '不支持的OJ'})
        else:
            redis_client.turn_off_spider(oj_name)
            self.write({'error': 0})


def make_api_app():
    return web.Application([
        (r"/api/spider/runners", SpiderRunnerHandler),
    ], debug=True)
