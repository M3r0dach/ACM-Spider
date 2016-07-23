import re
from tornado import gen
from urllib import parse
from app.spiders import Spider, HttpMethod
from app.logger import logger


class PojSpider(Spider):
    TAG = '[POJ]'
    domain = 'http://poj.org'
    login_url = domain + '/login'
    user_url_prefix = domain + '//userstatus?user_id={0}'

    def __init__(self):
        super(PojSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

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
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    body=post_body)
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
            print(solved_list)
            return {
                'solved': solved_count,
                'submitted': submitted_count,
                'solved_list': solved_list
            }
        except Exception as ex:
            logger.error('{} {} get Solved/Submitted error: {}'.format(self.TAG, self.account, ex))
            raise ex

    @gen.coroutine
    def run(self):
        yield self.login()
        yield self.get_solved()
