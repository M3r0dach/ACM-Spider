from tornado import gen
from urllib import parse
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException


class HduSpider(Spider):
    TAG = '[HDU]'
    domain = 'http://acm.hdu.edu.cn'
    index_url = domain
    login_url = domain + '/userloginex.php?action=login'
    user_url_prefix = domain + '/userstatus.php?user={0}'
    status_prefix = domain + '/status.php?user={0}&first={1}'
    source_code_prefix = domain + '/viewcode.php?rid={0}'

    def __init__(self):
        super(HduSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @gen.coroutine
    def fetch_cookie(self):
        if self.cookie:
            return True
        response = yield self.load_page(self.index_url)
        if not response:
            return False
        self.cookie = response.headers['Set-Cookie']
        logger.info('{} fetch cookie success'.format(self.TAG))
        return True

    @staticmethod
    def _get_solved_list(soup):

        def extract_pid(string):
            if not string:
                return
            start = string.find('(') + 1
            end = string.find(',')
            return string[start:end]

        ret = []
        script_text = soup.select('p > script')[0].text
        if script_text:
            p_list = script_text.split(';')
            for p in p_list:
                pid = extract_pid(p)
                if not pid or not pid.isdigit():
                    continue
                ret.append(pid)
        return ret

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': 'Raychat',
            'userpass': '63005610',
            'login': 'Sign In'
        })
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    headers={'cookie': self.cookie}, body=post_body)
        code = response.code
        page = response.body.decode()
        if (code != 200 and code != 302) or page.find('Sign Out') == -1:
            return False
        logger.info('{} login success'.format(self.TAG))
        self.has_login = True
        return True

    def logout(self):
        self.has_login = False
        self.cookie = None

    @gen.coroutine
    def get_solved(self):
        url = self.user_url_prefix.format('Raychat')
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            # solved count
            count = soup.find_all('td', text=['Problems Submitted', 'Problems Solved'])
            submitted_count = count[0].next_sibling.text
            solved_count = count[1].next_sibling.text

            # solved list
            solved_list = self._get_solved_list(soup)
            return {
                'solved': solved_count,
                'submitted': submitted_count,
                'solved_list': solved_list
            }
        except Exception as ex:
            logger.error('{} {} get Solved/Submitted error: {}'.format(self.TAG, self.account, ex))
            raise ex

    @gen.coroutine
    def get_code(self, run_id):
        url = self.source_code_prefix.format(run_id)
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            code = soup.find('textarea', id='usercode').text
            return code
        except Exception as ex:
            logger.error('{} fetch {}\'s {} code error'.format(self.TAG, 'Raychat', run_id), ex)

    @gen.coroutine
    def fetch_status(self, first):
        url = self.status_prefix.format('Raychat', first)
        status_list = []
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            status_table = soup.find('table', class_='table_text')
            for row in status_table.children:
                if row.name != 'tr':
                    continue
                if row.get('class') and 'table_header' in row.get('class'):
                    continue
                td_text = [td.text for td in row.children]
                code = yield self.get_code(td_text[0])
                status = {
                    'run_id': td_text[0], 'submit_time': td_text[1], 'result': td_text[2],
                    'pro_id': td_text[3], 'run_time': td_text[4][:-2], 'memory': td_text[5][:-1],
                    'lang': td_text[7], 'code': code
                }
                status_list.append(status)
            return status_list
        except Exception as ex:
            logger.error('{} fetch status nickname: {} first: {}'.format(self.TAG, 'Raychat', first), ex)

    @gen.coroutine
    def get_submits(self):
        first = ''
        while True:
            status_list = yield self.fetch_status(first)
            if not status_list:
                return
            # TODO

    @gen.coroutine
    def run(self):
        yield self.fetch_cookie()
        yield self.login()
        if not self.has_login:
            raise LoginException('{} login error {}'.format(self.TAG, self.account))
        yield self.get_solved()
        yield self.get_submits()
