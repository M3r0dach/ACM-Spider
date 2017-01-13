import json
from html import unescape
from urllib import parse

from tornado import gen, httputil

from app.helpers.decorators import try_run
from app.helpers.exceptions import LoginException
from app.helpers.logger import logger
from app.spiders import Spider, HttpMethod, DataType
from models import submit


def gen_status_params(nickname, start=0, size=50):
    columns = 10
    params = {
        'sEcho': 1,
        'iColumns': columns,
        'iDisplayStart': start,
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
        params['sSearch_' + idx] = nickname if i == 0 else ''
        params['bRegex_' + idx] = 'false'
        params['bSearchable_' + idx] = 'true'
        params['bSortable_' + idx] = 'false'
    return params


class BnuSpider(Spider):
    TAG = '[BNU]'
    domain = 'https://acm.bnu.edu.cn/v3'
    login_url = domain + '/ajax/login.php'
    user_url_prefix = domain + '/userinfo.php?name={0}'
    status_url = domain + '/ajax/status_data.php'
    code_prefix = domain + '/ajax/get_source.php?runid={0}'

    def __init__(self):
        super(BnuSpider, self).__init__()
        self.cookie = None
        self.has_login = False

    @try_run(3)
    async def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': self.account.nickname,
            'password': self.account.password,
            'cksave': 1,
            'login': 'Login'
        })
        response = await self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body)
        code = response.code
        res = json.loads(response.body.decode('utf-8'))
        if code != 200 and code != 302 or res['code'] != 0:
            return False
        set_cookie = response.headers.get_list('Set-Cookie')
        self.cookie = ';'.join(list(
            filter(lambda cookie: cookie.find('deleted') == -1, set_cookie)
        ))
        self.has_login = True
        logger.debug('{} login success {}'.format(self.TAG, self.account))
        return True

    @staticmethod
    def _get_solved_list(soup):
        a_list = soup.find('div', id='userac').find_all('a')
        solved_list = []
        for a in a_list:
            solved_list.append(a.text)
        return solved_list

    async def get_solved(self):
        url = self.user_url_prefix.format(self.account.nickname)
        try:
            response = await self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            solved = soup.find('button', id='showac').previous_sibling.string.strip()
            submitted = soup.find('a', href='status.php?showname={}'.format(self.account.nickname)).text
            return {
                'solved': solved, 'submitted': submitted,
                # 'solved_list': self._get_solved_list(soup)
            }
        except Exception as ex:
            logger.error('{} get Solved/Submitted error {}: {}'.format(self.TAG, self.account, ex))
            raise ex

    async def get_code(self, run_id, **kwargs):
        url = self.code_prefix.format(run_id)
        try:
            response = await self.load_page(url, {'cookie': self.cookie})
            if not response:
                logger.error('{} {} Fail to load code {} page'.format(self.TAG, self.account, run_id))
                logger.error('{}: response => {}'.format(self.TAG, response))
                return False
            res = json.loads(response.body.decode('utf-8'))
            code = res['source']
            logger.debug('{} {} Success to load code {} page'.format(self.TAG, self.account, run_id))
            return unescape(code)
        except Exception as ex:
            logger.error('{} fetch {}\'s {} code error {}'.format(self.TAG, self.account, run_id, ex))

    async def get_submits(self):
        start, size = 0, 50
        while True:
            url = httputil.url_concat(self.status_url,
                                      gen_status_params(self.account.nickname, start, size))
            response = await self.fetch(url)
            res = json.loads(response.body.decode('utf-8'))
            status_data = res['aaData']
            if len(status_data) == 0:
                break
            status_list = []
            for row in status_data:
                run_time = row[5][:-3] if row[5] != '' else '-1'
                memory = row[6][:-3] if row[6] != '' else '-1'
                status = {
                    'type': DataType.Submit, 'account': self.account,
                    'status': submit.SubmitStatus.BROKEN,
                    'run_id': row[1], 'pro_id': row[2], 'result': row[3],
                    'lang': row[4], 'run_time': run_time, 'memory': memory,
                    'submit_time': row[8], 'code': None
                }
                status_list.append(status)
            logger.debug('{} {} Success to get {} new status'.format(
                self.TAG, self.account, len(status_list)))
            self.put_queue(status_list)
            start += size

    async def run(self):
        await self.login()
        if not self.has_login:
            raise LoginException('{} login error {}'.format(self.TAG, self.account))
        if self.account.should_throttle:
            await self.fetch_code()
        else:
            general = await self.get_solved()
            if general and 'solved' in general:
                self.account.set_general(general['solved'], general['submitted'])
                self.account.save()
            await gen.multi([self.get_submits(), self.fetch_code()])
