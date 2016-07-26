from tornado import gen
from urllib import parse
from app.logger import logger
from app.spiders import Spider, HttpMethod


class BestcoderSpider(Spider):
    TAG = '[BestcoderSpider]'
    domain = 'http://bestcoder.hdu.edu.cn'
    index_url = domain
    login_url = domain + '/login.php?action=login'
    user_url_prefix = domain + '/rating.php?user={0}'
    rating_api_prefix = domain + '//api/api.php?type=user-rating&user={0}'

    def __init__(self):
        super(BestcoderSpider, self).__init__()
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
        self.cookie = self.cookie.split(';')[0] + '; username=Raychat;'
        logger.info('{} fetch cookie success'.format(self.TAG))
        return True

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': 'Raychat',
            'password': '63005610',
            'remember': 'on'
        })
        headers = {
            'Host': 'bestcoder.hdu.edu.cn',
            'Cookie': self.cookie
        }
        response = yield self.fetch(self.login_url, method=HttpMethod.POST,
                                    headers=headers, body=post_body)
        code = response.code
        page = response.body.decode('gb2312')
        if code != 200 and code != 302 or page.find('Logout') == -1:
            return False
        self.has_login = True
        logger.info('{} login success {}'.format(self.TAG, self.account))
        return True

    @gen.coroutine
    def get_rating(self):
        url = self.user_url_prefix.format('Raychat')
        try:
            response = yield self.load_page(url, {'cookie': self.cookie})
            if not response:
                return False
            soup = self.get_lxml_bs4(response.body)
            profile_heading = soup.find('div', id='profile-heading')
            if profile_heading:
                ratings = profile_heading.find_all('span', class_='bigggger')
                if len(ratings) == 2:
                    return {'solved': ratings[1].text,
                            'submitted': ratings[0].text}
        except Exception as ex:
            logger.error(ex)
            logger.error('{} {} get Rating error'.format(self.TAG, self.account))

    @gen.coroutine
    def run(self):
        yield self.fetch_cookie()
        yield self.login()
        yield self.get_rating()
