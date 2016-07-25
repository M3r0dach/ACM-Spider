import json
from tornado import gen
from urllib import parse
from datetime import datetime
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException


class VjudgeSpider(Spider):
    TAG = '[Virtual Judge]'
    domain = 'http://acm.hust.edu.cn'
    login_url = domain + '/vjudge/user/login.action'
    status_url = domain + '/vjudge/status/data/'
    code_url_prefix = domain + '/vjudge/problem/source/{0}'

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
        headers = {
            'Host': 'acm.hust.edu.cn',
            'Origin': 'http://acm.hust.edu.cn',
            'Referer': 'http://acm.hust.edu.cn/vjudge/index'
        }
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body, headers=headers)
        code = response.code
        res = response.body.decode()
        if code != 200 and code != 302 or res != 'success':
            return False
        self.cookie = response.headers['Set-Cookie']
        self.has_login = True
        logger.info('{} login success {}'.format(self.TAG, self.account))
        return True

    @gen.coroutine
    def get_solved(self):
        pass

    @staticmethod
    def _gen_status_params(size=20):
        params = {
            'draw': 0,
            'start': 0,
            'length': size,
            'search[value]': '',
            'search[regex]': 'false',
            'order[0][column]': 0,
            'order[0][dir]': 'desc',
            'un': 'HotWhite',
            'OJId': 'All',
            'probNum': '',
            'res': 0,
            'language': '',
            'orderBy': 'run_id'
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
        url = self.code_url_prefix.format(run_id)
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            soup = self.get_lxml_bs4(response.body)
            code = soup.find('pre', class_='sh-c').text
            return code
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def get_submits(self):
        try:
            post_body = parse.urlencode(self._gen_status_params())
            response = yield self.fetch(self.status_url, method=HttpMethod.POST,
                                        body=post_body)
            res = json.loads(response.body.decode('utf-8'))
            status_data = res['data']
            if len(status_data) == 0:
                return
            submits_list = []
            for row in status_data:
                submit_at = datetime.fromtimestamp(int(str(row[8])[:-3]))
                code = yield self.get_code(row[0])
                status = {
                    'run_id': row[0], 'pro_id': row[12], 'lang': row[6], 'run_time': row[5],
                    'memory': row[4], 'submit_time': submit_at, 'result': row[3], 'code': code
                }
                submits_list.append(status)
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def run(self):
        yield self.login()
        if not self.has_login:
            raise LoginException('{} login error {}'.format(self.TAG, self.account))
        yield self.get_submits()
