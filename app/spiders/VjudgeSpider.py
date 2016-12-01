import sys
import json
from datetime import datetime
from urllib import parse
from tornado import gen
from app.helpers.logger import logger
from app.helpers.exceptions import LoginException
from app.spiders import Spider, HttpMethod, DataType
from app.models import submit


class VjudgeSpider(Spider):
    TAG = '[Virtual Judge]'
    domain = 'http://vjudge.net'
    login_url = domain + '/user/login'
    status_url = domain + '/user/submissions?username={}&pageSize={}&maxId={}'
    code_url_prefix = domain + '/problem/source/{0}'

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
            'username': self.account.nickname,
            'password': self.account.password
        })
        headers = dict(Host='vjudge.net', Origin=self.domain,
                       Referer='http://vjudge.net/index')
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

    def get_solved(self):
        submits = self.account.submits
        solved_submits = set(map(lambda s: s.origin_oj + s.pro_id,
                             filter(lambda s: s.result == 'AC', submits)))
        submitted_submits = set(map(lambda s: s.origin_oj + s.pro_id, submits))
        solved = len(solved_submits)
        submitted = len(submitted_submits)
        return {'solved': solved, 'submitted': submitted}

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
        page_size, max_id = 500, 2 ** 31 - 1
        while True:
            url = self.status_url.format(self.account.nickname, page_size, max_id)
            response = yield self.fetch(url, method=HttpMethod.GET,
                                        headers=dict(Cookie=self.cookie))
            res = json.loads(response.body.decode('utf-8'))
            if 'error' in res:
                yield gen.sleep(60)
                continue
            status_data = res['data']
            if len(status_data) == 0:
                break
            submits_list = []
            for row in status_data:
                submit_at = datetime.fromtimestamp(int(row[9]) / 1000)
                status = {
                    'type': DataType.Submit, 'account': self.account,
                    'status': submit.SubmitStatus.BROKEN,
                    'run_id': row[0], 'pro_id': row[3], 'lang': row[7], 'run_time': row[5],
                    'memory': row[6], 'submit_time': submit_at, 'result': row[4],
                    'code': None, 'origin_oj': row[2]
                }
                submits_list.append(status)
            logger.debug('{} {} Success to get {} new status'.format(self.TAG, self.account, len(submits_list)))
            self.put_queue(submits_list)
            max_id = status_data[-1][0] - 1

    @gen.coroutine
    def fetch_code(self):
        error_submits = submit.get_error_submits(self.account)
        for run_id, in error_submits:
            code = yield self.get_code(run_id)
            if not code:
                yield gen.sleep(60 * 2)
            else:
                status = {
                    'type': DataType.Code, 'account': self.account,
                    'run_id': run_id, 'code': code
                }
                self.put_queue([status])
                yield gen.sleep(30)

    @gen.coroutine
    def run(self):
        yield self.login()
        if not self.has_login:
            raise LoginException('{} login error {}'.format(self.TAG, self.account))
        yield self.get_submits()
        general = self.get_solved()
        if general and 'solved' in general:
            self.account.set_general(general['solved'], general['submitted'])
            self.account.save()
        yield self.fetch_code()

