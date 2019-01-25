import json
import re
import traceback
from datetime import datetime
from urllib import parse
from zipfile import ZipFile

from tornado import gen

from app.helpers.exceptions import LoginException
from app.helpers.logger import logger
from app.models import submit
from app.spiders import Spider, HttpMethod, DataType


class VjudgeSpider(Spider):
    TAG = '[Virtual Judge]'
    domain = 'https://cn.vjudge.net'
    login_url = domain + '/user/login'
    status_url = domain + '/user/submissions?username={}&pageSize={}&maxId={}'
    code_url_prefix = domain + '/problem/source/{0}'
    code_zip_url = domain + '/user/exportSource?minRunId={0}&maxRunId={1}&ac=false'

    def __init__(self):
        super(VjudgeSpider, self).__init__()
        self.cookie = None
        self.has_login = False

    async def login(self):
        if self.has_login:
            return True
        post_body = parse.urlencode({
            'username': self.account.nickname,
            'password': self.account.password
        })
        headers = dict(Host='vjudge.net', Origin=self.domain,
                       Referer='http://vjudge.net/index')
        response = await self.fetch(self.login_url, method=HttpMethod.POST, body=post_body,
                                    headers=headers, validate_cert=False)
        code = response.code
        res = response.body.decode()
        if code != 200 and code != 302 or res != 'success':
            return False
        self.cookie = response.headers['Set-Cookie']
        self.has_login = True
        logger.info('{} login success {}'.format(self.TAG, self.account))
        return True

    def get_solved(self):
        submits = self.account.submits
        solved_submits = set(map(lambda s: s.origin_oj + s.pro_id,
                             filter(lambda s: s.result == 'AC', submits)))
        submitted_submits = set(map(lambda s: s.origin_oj + s.pro_id, submits))
        solved = len(solved_submits)
        submitted = len(submitted_submits)
        return {'solved': solved, 'submitted': submitted}

    async def get_code_zip(self, min, max):
        url = self.code_zip_url.format(min, max)
        try:
            response = await self.fetch(url, method=HttpMethod.GET,
                                        headers={'cookie': self.cookie},
                                        validate_cert=False)
            buffer = response.buffer
            with ZipFile(buffer) as code_zip:
                for name in code_zip.namelist():
                    run_id = re.split(r'/|_', name)[2]
                    logger.info('vj get code_zip run_id {}'.format(run_id))
                    with code_zip.open(name) as code_fp:
                        code = code_fp.read()
                        status = {
                            'type': DataType.Code, 'account': self.account,
                            'run_id': run_id, 'code': code
                        }
                        await self.put_queue([status])
                    await gen.sleep(5)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    async def get_code(self, run_id, **kwargs):
        url = self.code_url_prefix.format(run_id)
        try:
            response = await self.load_page(url, {'cookie': self.cookie},
                                            validate_cert=False)
            soup = self.get_lxml_bs4(response.body)
            code = soup.find('pre', class_='sh-c').text
            return code
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    async def get_submits(self):
        page_size, max_id = 500, 2 ** 31 - 1
        while True:
            url = self.status_url.format(self.account.nickname, page_size, max_id)
            response = await self.fetch(url, method=HttpMethod.GET,
                                        headers=dict(Cookie=self.cookie),
                                        validate_cert=False)
            res = json.loads(response.body.decode('utf-8'))
            if 'error' in res:
                await gen.sleep(60)
                continue
            status_data = res['data']
            if len(status_data) == 0:
                break
            submits_list = []
            for row in status_data:
                submit_at = datetime.fromtimestamp(int(row[9]) / 1000)
                status = {
                    'type': DataType.Submit, 'account': self.account,
                    'status': submit.SubmitStatus.BROKEN,
                    'run_id': row[0], 'pro_id': row[3], 'lang': row[7], 'run_time': row[5],
                    'memory': row[6], 'submit_time': submit_at, 'result': row[4],
                    'code': None, 'origin_oj': row[2]
                }
                submits_list.append(status)
            logger.debug('{} {} Success to get {} new status'.format(self.TAG, self.account, len(submits_list)))
            await self.put_queue(submits_list)
            max_id = status_data[-1][0] - 1

    async def fetch_code(self):
        error_submits = submit.get_error_submits(self.account)
        run_ids = list(map(lambda s: int(s[0]), error_submits))
        if not run_ids:
            return
        min_run_id, max_run_id = min(run_ids), max(run_ids)
        await self.get_code_zip(min_run_id, max_run_id)

    async def run(self):
        await self.login()
        if not self.has_login:
            raise LoginException('{} login error {}'.format(self.TAG, self.account))
        if not self.account.should_throttle:
            await self.get_submits()
            general = self.get_solved()
            if general and 'solved' in general:
                await self.account.set_general(general['solved'], general['submitted'])
        await self.fetch_code()

