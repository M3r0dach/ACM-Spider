import json
from tornado import gen
from urllib import parse
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException


class BnuSpider(Spider):
    domain = 'https://acm.bnu.edu.cn/v3'
    login_url = domain + '/ajax/login.php'
    user_url_prefix = domain + '/userinfo.php?name={}'

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
        self.cookie = response.headers['Set-Cookie']
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

    @gen.coroutine
    def get_submits(self):
        pass

    @gen.coroutine
    def run(self):
        yield self.login()
        if not self.has_login:
            raise LoginException('{} login error'.format(self.account))
        yield self.get_solved()
