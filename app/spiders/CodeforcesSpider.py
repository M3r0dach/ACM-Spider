import json
from tornado import gen
from datetime import datetime, time
from app.logger import logger
from app.spiders import Spider


class CodeforcesSpider(Spider):
    TAG = '[Codeforces]'
    domain = 'http://codeforces.com'
    user_info_prefix = domain + '/api/user.info?handles={0}'
    status_prefix = domain + '/api/user.status?handle={0}&from={1}&count={2}'
    code_prefix = domain + '/contest/{0}/submission/{1}'

    def __init__(self):
        super(CodeforcesSpider, self).__init__()
        self.account = None

    @gen.coroutine
    def get_solved(self):
        url = self.user_info_prefix.format('Rayn')
        try:
            response = yield self.load_page(url)
            if not response:
                return False
            ret = json.loads(response.body.decode())
            if ret['status'] != 'OK':
                return False
            user_info = ret['result'][0]
            return {
                'rating': user_info['rating'],
                'maxRating': user_info['maxRating']
            }
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def get_code(self, contest_id, run_id):
        url = self.code_prefix.format(contest_id, run_id)
        try:
            response = yield self.load_page(url)
            if not response:
                return None
            soup = self.get_lxml_bs4(response.body)
            code = soup.find('pre', class_='program-source').text
            return code
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def get_status(self, handle, start=1, length=50):
        is_gym = lambda cid: len(str(cid)) >= 6
        url = self.status_prefix.format(handle, start, length)
        try:
            response = yield self.load_page(url)
            if not response:
                return False
            response_data = json.loads(response.body.decode())
            if response_data['status'] != 'OK':
                return False
            result = response_data['result']
            for row in result:
                if is_gym(row['contestId']):
                    continue
                pro_id = '{0}{1}'.format(row['contestId'], row['problem']['index'])
                submit_at = datetime.fromtimestamp(row['creationTimeSeconds'])
                code = yield self.get_code(row['contestId'], row['id'])
                status = {
                    'pro_id': pro_id, 'run_id': row['id'], 'submit_time': submit_at,
                    'run_time': row['timeConsumedMillis'], 'memory': row['memoryConsumedBytes'] // 1024,
                    'lang': row['programmingLanguage'], 'code': code, 'result': row['verdict']
                }
                print(status)
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def get_submits(self):
        yield self.get_status('Rayn')

    @gen.coroutine
    def run(self):
        yield self.get_solved()
        yield self.get_submits()
