from tornado import web
from api.handlers import SpiderRunnerHandler


def make_api_app():
    return web.Application([
        (r"/api/spider/runners", SpiderRunnerHandler),
    ], debug=True)
