import re
from tornado import gen
from urllib import parse
from app.logger import logger
from app.spiders import Spider, HttpMethod
from app.decorators import try_run


class PojSpider(Spider):
    TAG = '[POJ]'
    domain = 'http://poj.org'
    index_url = domain
    login_url = domain + '/login'
    user_url_prefix = domain + '/userstatus?user_id={0}'
    status_prefix = domain + '/status?user_id={0}&top={1}'
    source_code_prefix = domain + '/showsource?solution_id={0}'

    def __init__(self):
        super(PojSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @try_run(3)
    @gen.coroutine
    def fetch_cookie(self):
        if self.cookie:
            return True
        response = yield self.load_page(self.index_url)
        if not response:
            return False
        self.cookie = response.headers['Set-Cookie']
        self.cookie = self.cookie.split(';')[0] + ';'
        logger.info('{} fetch cookie success'.format(self.TAG))
        return True

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'user_id1': 'Raychat',
            'password1': '63005610',
            'B1': 'login',
            'url': '/'
        })
        headers = {
            'Cookie': self.cookie
        }
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body, headers=headers)
        code = response.code
        page = response.body.decode()
        if code != 200 and code != 302 or page.find('Log Out') == -1:
            return False
        self.has_login = True
        logger.info('{} login success {}'.format(self.TAG, self.account))
        return True

    @staticmethod
    def _get_solved_list(soup):

        def extract_pid(string):
            if not string:
                return
            start = string.find('(') + 1
            return string[start:-1]

        ret = []
        script_text = soup.select('td > script')[0].text
        if script_text:
            p_list = script_text.split('}')[1].split()
            for p in p_list:
                pid = extract_pid(p)
                if not pid or not pid.isdigit():
                    continue
                ret.append(pid)
        return ret

    @gen.coroutine
    def get_solved(self):
        url = self.user_url_prefix.format('Raychat')
        try:
            response = yield self.load_page(url)
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            # solved count
            solved_count = soup.find('a', href=re.compile("^status\?result=0")).text
            submitted_count = soup.find('a', href=re.compile("^status\?user_id")).text

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

    @try_run(3)
    @gen.coroutine
    def get_code(self, run_id):
        url = self.source_code_prefix.format(run_id)
        print(url)
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            pre_node = soup.find('pre')
            if not pre_node:
                return False
            logger.debug("fetch code {} success".format(run_id))
            return pre_node.text
        except Exception as ex:
            logger.error(ex)
            logger.error('{} fetch {}\'s {} code error'.format(self.TAG, 'Raychat', run_id))

    @gen.coroutine
    def fetch_status(self, first=''):
        url = self.status_prefix.format('Raychat', first)
        status_list = []
        try:
            response = yield self.load_page(url)
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            status_table = soup.find('table', class_='a')
            for row in status_table.children:
                if row.name != 'tr':
                    continue
                if row.get('class') and 'in' in row.get('class'):
                    continue
                td_text = [td.text for td in row.children if td.name == 'td']
                code = yield self.get_code(td_text[0])
                run_time = td_text[5][:-2] or '-1'
                memory = td_text[4][:-1] or '-1'
                status = {
                    'run_id': td_text[0], 'submit_time': td_text[8], 'result': td_text[3],
                    'pro_id': td_text[2], 'run_time': run_time, 'memory': memory,
                    'lang': td_text[6], 'code': code
                }
                status_list.append(status)
            return status_list
        except Exception as ex:
            logger.error(ex)
            logger.error('{} fetch status => user_id: {} top: {}'.format(self.TAG, 'Raychat', first))

    @gen.coroutine
    def get_submits(self):
        yield self.fetch_status()
        # TODO

    @gen.coroutine
    def run(self):
        yield self.fetch_cookie()
        yield self.login()
        yield self.get_solved()
        yield self.get_submits()
