from app.spiders import Spider, HttpMethod
from tornado import gen
from urllib import parse


class HduSpider(Spider):
    login_url = 'http://acm.hdu.edu.cn/userloginex.php?action=login'

    def __init__(self):
        super(HduSpider, self).__init__()

    @gen.coroutine
    def login(self):
        post_body = parse.urlencode({
            'username': 'Raychat',
            'userpass': '63005610',
            'login': 'Sign In'
        })
        headers = {
            'Cookie': 'PHPSESSID=vaphch5ppl9mvuf75jp1l8j373'
        }
        response = yield self.fetch(self.login_url,
                                    headers=headers,
                                    method=HttpMethod.POST,
                                    body=post_body)
        code = response.code
        if (code != 200 and code != 302) or response.body.find(b'Sign Out') == -1:
            return False
        print('login success')
        return True

    @gen.coroutine
    def run(self):
        pass
