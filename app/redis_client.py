import redis as py_redis
from secret import redis_config, RedisKey
from settings import SUPPORT_OJ
from app.logger import logger

redis = py_redis.StrictRedis(**redis_config)

# keys define
switch_key = RedisKey.prefix + RedisKey.switch


def setup_redis():
    if not redis.exists(switch_key):
        ret = redis.hmset(switch_key, {oj: 1 for oj in SUPPORT_OJ})
        if ret:
            logger.info('setup switch key success')
    else:
        log_spider_status()


def is_spider_opening(oj_name):
    status = int(redis.hget(switch_key, oj_name))
    return status == 1


def log_spider_status():
    logger.info('[OJ_STATUS] {0}'.format(
        redis.hgetall(switch_key)
    ))


def turn_on_spider(oj_name):
    if redis.exists(switch_key):
        redis.hset(switch_key, oj_name, 1)
    log_spider_status()


def turn_off_spider(oj_name):
    if redis.exists(switch_key):
        redis.hset(switch_key, oj_name, 0)
    log_spider_status()
