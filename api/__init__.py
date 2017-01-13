from tornado import web
from api.handlers import SpiderWorkerHandler


def make_api_app():
    return web.Application([
        (r"/api/spider/workers", SpiderWorkerHandler),
    ], debug=True)
