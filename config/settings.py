import logging
import os
from config.secret import db_config

# support oj
SUPPORT_OJ = dict(
    hdu='Hdu',
    bnu='Bnu',
    poj='Poj',
    vj='Vjudge',
    cf='Codeforces',
    bc='Bestcoder'
)

# env
app_env = os.environ.get('ACM_SPIDER_ENV') or 'development'
app_port = os.environ.get('ACM_SPIDER_PORT') or 8000

# directory
base_dir = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])
log_dir = base_dir + '/log/{}.log'.format(app_env)
log_level = logging.DEBUG

# database
db_config['db_name'] = db_config['db_name_prefix'].format(app_env)
DB_URI = 'mysql+pymysql://{username}:{pwd}@{host}/{db_name}?charset=utf8'.format(**db_config)
DB_SHOW_SQL = False

# concurrency
SPIDER_CACHE_SIZE = 5
ACCOUNT_QUEUE_SIZE = 5
SPIDER_RUNNER_SIZE = 3

# data
DATA_POOL_SIZE = 128

# minutes between account to update again
FETCH_TIMEDELTA = 0 if app_env == 'development' else 60
