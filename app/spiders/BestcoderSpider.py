import json
from urllib import parse
from tornado import gen
from app.helpers.logger import logger
from app.spiders import Spider, HttpMethod


class BestcoderSpider(Spider):
    TAG = '[BestcoderSpider]'
    domain = 'http://bestcoder.hdu.edu.cn'
    index_url = domain
    login_url = domain + '/login.php?action=login'
    user_url_prefix = domain + '/rating.php?user={0}'
    rating_api_prefix = domain + '/api/api.php?type=user-rating&user={0}'

    def __init__(self):
        super(BestcoderSpider, self).__init__()
        self.cookie = None
        self.has_login = False

    @gen.coroutine
    def fetch_cookie(self):
        if self.cookie:
            return True
        response = yield self.load_page(self.index_url)
        if not response:
            return False
        self.cookie = response.headers['Set-Cookie']
        self.cookie = self.cookie.split(';')[0] + '; username={};'.format(self.account.nickname)
        logger.info('{} fetch cookie success'.format(self.TAG))
        return True

    @gen.coroutine
    def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': self.account.nickname,
            'password': self.account.password,
            'remember': 'on'
        })
        headers = dict(Host='bestcoder.hdu.edu.cn', Cookie=self.cookie)
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
        url = self.rating_api_prefix.format(self.account.nickname)
        try:
            response = yield self.fetch(url)
            if not response:
                return False
            res = json.loads(response.body.decode())
            if len(res) > 0:
                max_rating = max(res, key=lambda x: x['rating'])
                return dict(rating=res[-1]['rating'],
                            maxRating=max_rating['rating'])
        except Exception as ex:
            logger.error(ex)
            logger.error('{} {} get Rating error'.format(self.TAG, self.account))

    @gen.coroutine
    def run(self):
        if self.account.should_throttle:
            return
        general = yield self.get_rating()
        if general and 'rating' in general:
            self.account.set_general(general['rating'], general['maxRating'])
            self.account.save()
