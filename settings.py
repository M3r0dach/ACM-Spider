import os
import logging
from secret import db_config

# directory
base_dir = os.path.split(os.path.realpath(__file__))[0]
log_dir = base_dir + '/log/spider.log'
log_level = logging.DEBUG

# database
DB_URI = 'mysql://{username}:{pwd}@{host}/{db_name}'.format(**db_config)
DB_SHOW_SQL = True
