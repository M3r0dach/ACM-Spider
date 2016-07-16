import json
from tornado import gen
from urllib import parse
from html import unescape
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException


class VjudgeSpider(Spider):
    TAG = '[Virtual Judge]'
    domain = 'http://acm.hust.edu.cn'
    login_url = domain + '/vjudge/user/login.action'
    status_url = domain + '/vjudge/problem/fetchStatus.action'

    def __init__(self):
        super(VjudgeSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': 'HotWhite',
            'password': 'cuitasdf'
        })
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body)
        code = response.code
        res = json.loads(response.body.decode('utf-8'))
        if code != 200 and code != 302 or res != 'success':
            return False
        self.cookie = response.headers['Set-Cookie']
        self.has_login = True
        logger.info('{} login success'.format(self.TAG))
        return True

    @gen.coroutine
    def get_solved(self):
        pass

    @staticmethod
    def _gen_status_params(size=50):
        params = {
            'draw': 0,
            'start': 0,
            'length': size,
            'search[value]': '',
            'search[regex]': 'false',
            'un': 'HotWhite',
            'OJId': 'All',
            'probNum': '',
            'res': 0,
            'language': '',
            'orderBy': 'run_id',
            'order[0][column]': 0,
            'order[0][dir]': 'desc'
        }
        for i in range(12):
            idx = str(i)
            params['columns[' + idx + '][data]'] = idx
            params['columns[' + idx + '][name]'] = 0
            params['columns[' + idx + '][searchable]'] = 'true'
            params['columns[' + idx + '][orderable]'] = 'false'
            params['columns[' + idx + '][search][value]'] = 'false'
            params['columns[' + idx + '][search][regex]'] = 'false'
        return params

    @gen.coroutine
    def get_code(self, run_id):
        pass

    @gen.coroutine
    def get_submits(self):
        try:
            post_body = parse.urlencode(self._gen_status_params())
            response = yield self.fetch(self.status_url, method=HttpMethod.POST,
                                        headers={'cookie': self.cookie}, body=post_body)
            res = json.loads(response.body.decode('utf-8'))
            status_data = res['data']
            print(status_data)
            if len(status_data) == 0:
                return
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def run(self):
        yield self.login()
        if not self.has_login:
            raise LoginException('[]{} login error'.format(self.account))
        yield self.get_submits()
