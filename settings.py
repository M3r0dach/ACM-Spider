import os
import logging
from secret import db_config

# support oj
SUPPORT_OJ = ['hdu', 'bnu']

# directory
base_dir = os.path.split(os.path.realpath(__file__))[0]
log_dir = base_dir + '/log/spider.log'
log_level = logging.DEBUG

# database
DB_URI = 'mysql+pymysql://{username}:{pwd}@{host}/{db_name}'.format(**db_config)
DB_SHOW_SQL = False

# concurrency
SPIDER_CACHE_SIZE = 5
MAX_QUEUE_SIZE = 5
WORKER_SIZE = 2

# hours between account to update again
FETCH_TIMEDELTA = 6
