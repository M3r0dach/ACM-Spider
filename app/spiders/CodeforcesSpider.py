import re
import json
from datetime import datetime
from tornado import gen
from app.helpers.logger import logger
from app.spiders import Spider, DataType
from app.models import submit


class CodeforcesSpider(Spider):
    TAG = '[Codeforces]'
    domain = 'http://codeforces.com'
    user_info_prefix = domain + '/api/user.info?handles={0}'
    status_prefix = domain + '/api/user.status?handle={0}&from={1}&count={2}'
    code_prefix = domain + '/contest/{0}/submission/{1}'

    def __init__(self):
        super(CodeforcesSpider, self).__init__()

    @gen.coroutine
    def get_solved(self):
        url = self.user_info_prefix.format(self.account.nickname)
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
    def get_code(self, run_id, **kwargs):
        pro_id = kwargs['pro_id']
        contest_id = re.compile(r'^\d+').match(pro_id).group()
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
            status_list = []
            for row in result:
                if is_gym(row['contestId']):
                    continue
                pro_id = '{0}{1}'.format(row['contestId'], row['problem']['index'])
                submit_at = datetime.fromtimestamp(row['creationTimeSeconds'])
                # code = yield self.get_code(row['contestId'], row['id'])
                status = {
                    'type': DataType.Submit, 'account': self.account,
                    'status': submit.SubmitStatus.BROKEN,
                    'pro_id': pro_id, 'run_id': row['id'], 'submit_time': submit_at,
                    'run_time': row['timeConsumedMillis'], 'memory': row['memoryConsumedBytes'] // 1024,
                    'lang': row['programmingLanguage'], 'code': None, 'result': row['verdict']
                }
                status_list.append(status)
            return status_list
        except Exception as e:
            logger.error(e)

    @gen.coroutine
    def get_submits(self):
        start, size = 1, 50
        while True:
            status_list = yield self.get_status(self.account.nickname, start, size)
            if not status_list or len(status_list) == 0:
                break
            logger.debug('{} {} Success to get {} new status'.format(
                self.TAG, self.account, len(status_list)))
            self.put_queue(status_list)
            start += size

    @gen.coroutine
    def run(self):
        general = yield self.get_solved()
        if general and 'rating' in general:
            self.account.set_general(general['rating'], general['maxRating'])
            self.account.save()
        yield [self.get_submits(), self.fetch_code()]
