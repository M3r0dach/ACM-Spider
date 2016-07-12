import json
from tornado import gen, httputil
from urllib import parse
from html import unescape
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException


class BnuSpider(Spider):
    domain = 'https://acm.bnu.edu.cn/v3'
    login_url = domain + '/ajax/login.php'
    user_url_prefix = domain + '/userinfo.php?name={0}'
    status_url = domain + '/ajax/status_data.php'
    code_prefix = domain + '/ajax/get_source.php?runid={0}'

    def __init__(self):
        super(BnuSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': 'Rayn',
            'password': '63005610',
            'cksave': 1,
            'login': 'Login'
        })
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body)
        code = response.code
        res = json.loads(response.body.decode('utf-8'))
        if code != 200 and code != 302 or res['code'] != 0:
            return False
        set_cookie = response.headers.get_list('Set-Cookie')
        self.cookie = ';'.join(list(filter(lambda cookie: cookie.find('deleted') == -1, set_cookie)))
        self.has_login = True
        logger.info('BNU login success')
        return True

    @staticmethod
    def _get_solved_list(soup):
        a_list = soup.find('div', id='userac').find_all('a')
        solved_list = []
        for a in a_list:
            solved_list.append(a.text)
        return solved_list

    @gen.coroutine
    def get_solved(self):
        url = self.user_url_prefix.format('Rayn')
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            solved = soup.find('button', id='showac').previous_sibling.string.strip()
            submitted = soup.find('a', href='status.php?showname={}'.format('Rayn')).text
            return {
                'solved': solved, 'submitted': submitted,
                'solved_list': self._get_solved_list(soup)
            }
        except Exception as ex:
            logger.error('{} get Solved/Submitted error: {}'.format(self.account, ex))
            raise ex

    @staticmethod
    def _gen_status_params(size=50):
        columns = 10
        params = {
            'sEcho': 1,
            'iColumns': columns,
            'iDisplayStart': 0,
            'iDisplayLength': size,
            'sSearch': '',
            'bRegex': 'false',
            'iSortCol_0': 1,
            'sSortDir_0': 'desc',
            'iSortingCols': 1
        }
        for i in range(10):
            idx = str(i)
            params['mDataProp_' + idx] = i
            params['sSearch_' + idx] = 'Rayn' if i == 0 else ''
            params['bRegex_' + idx] = 'false'
            params['bSearchable_' + idx] = 'true'
            params['bSortable_' + idx] = 'false'
        return params

    @gen.coroutine
    def get_code(self, run_id):
        url = self.code_prefix.format(run_id)
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            res = json.loads(response.body.decode('utf-8'))
            code = res['source']
            return unescape(code)
        except Exception as ex:
            logger.error('[BNU] fetch {}\'s {} code error {}'.format('Rayn', run_id, ex))

    @gen.coroutine
    def get_submits(self):
        url = httputil.url_concat(self.status_url, self._gen_status_params())
        response = yield self.fetch(url)
        res = json.loads(response.body.decode('utf-8'))
        status_data = res['aaData']
        if len(status_data) == 0:
            return
        for row in status_data:
            run_time = row[5][:-3] if row[5] != '' else '-1'
            memory = row[6][:-3] if row[6] != '' else '-1'
            code = yield self.get_code(row[1])
            status = {
                'run_id': row[1], 'pro_id': row[2], 'result': row[3], 'lang': row[4],
                'run_time': run_time, 'memory': memory, 'submit_time': row[8], 'code': code
            }
            print(code)
            # TODO

    @gen.coroutine
    def run(self):
        yield self.login()
        if not self.has_login:
            raise LoginException('{} login error'.format(self.account))
        yield self.get_solved()
        yield self.get_submits()
