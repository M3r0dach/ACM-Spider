from app.spiders import Spider, HttpMethod
from app.exceptions import LoginException
from tornado import gen
from urllib import parse
from logger import logger


class HduSpider(Spider):
    index_url = 'http://acm.hdu.edu.cn/'
    login_url = 'http://acm.hdu.edu.cn/userloginex.php?action=login'
    user_url_prefix = 'http://acm.hdu.edu.cn/userstatus.php?user={}'

    def __init__(self):
        super(HduSpider, self).__init__()
        self.cookie = None
        self.has_login = False
        self.account = None

    @gen.coroutine
    def fetch_cookie(self):
        response = yield self.load_page(self.index_url)
        if not response:
            return False
        self.cookie = response.headers['Set-Cookie']
        return True

    @gen.coroutine
    def login(self):
        post_body = parse.urlencode({
            'username': 'Raychat',
            'userpass': '63005610',
            'login': 'Sign In'
        })
        headers = {
            'Cookie': self.cookie
        }
        response = yield self.fetch(self.login_url,
                                    headers=headers,
                                    method=HttpMethod.POST,
                                    body=post_body)
        code = response.code
        if (code != 200 and code != 302) or response.body.find(b'Sign Out') == -1:
            return False
        logger.info('HDU: login success')
        self.has_login = True
        return True

    def logout(self):
        self.has_login = False
        self.cookie = None

    @gen.coroutine
    def get_problem_count(self):
        url = self.user_url_prefix.format('Raychat')
        response = yield self.load_page(url, {
            'Cookie': self.cookie
        })
        if not response:
            return False
        try:
            soup = self.get_lxml_bs4(response.body)
            ret = soup.find_all('td', text=['Problems Submitted', 'Problems Solved'])
            submitted = ret[0].next_sibling.text
            solved = ret[1].next_sibling.text
            return {'solved': solved, 'submitted': submitted}
        except Exception as e:
            logger.error('get Solved/Submitted count error', e)

    @gen.coroutine
    def run(self):
        if not self.cookie:
            yield self.fetch_cookie()
        if not self.has_login:
            yield self.login()
        if not self.has_login:
            raise LoginException('{} login error'.format(self.account))
        yield self.get_problem_count()
