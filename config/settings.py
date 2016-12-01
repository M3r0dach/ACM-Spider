import logging
import os
from config.secret import db_config

# support oj
SUPPORT_OJ = {
    'hdu': 'Hdu',
    'bnu': 'Bnu',
    'vj': 'Vjudge',
    'cf': 'Codeforces',
    'poj': 'Poj',
    # 'bc': 'Bestcoder'
}

# env
app_env = os.environ.get('SPIDER_ENV') or 'development'

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
MAX_QUEUE_SIZE = 5
WORKER_SIZE = 2

# data
DATA_POOL_SIZE = 128
BATCH_SAVE_SIZE = 10

# hours between account to update again
FETCH_TIMEDELTA = 0
