import redis as py_redis
from secret import redis_config, RedisKey
from settings import SUPPORT_OJ
from app.logger import logger

redis = py_redis.StrictRedis(**redis_config)

# keys define
switch_key = RedisKey.prefix + RedisKey.switch
hdu_key = RedisKey.prefix + RedisKey.hdu
poj_key = RedisKey.prefix + RedisKey.poj
bnu_key = RedisKey.prefix + RedisKey.bnu
cf_key = RedisKey.prefix + RedisKey.codeforces


def setup_redis():
    if not redis.exists(switch_key):
        ret = redis.hmset(switch_key, {oj: 1 for oj in SUPPORT_OJ})
        if ret:
            logger.info('[redis] setup switch key success')
    else:
        log_spider_status()


def get_all_open_spider():
    all_status = redis.hgetall(switch_key)
    if all_status:
        all_status = [k.decode() for k, v in all_status.items() if int(v) == 1]
    return all_status or []


def is_spider_open(oj_name):
    status = int(redis.hget(switch_key, oj_name))
    return status == 1


def log_spider_status():
    logger.info('[OPEN Spider] {0}'.format(
        get_all_open_spider()
    ))


def turn_on_spider(oj_name):
    if redis.exists(switch_key):
        redis.hset(switch_key, oj_name, 1)
    log_spider_status()


def turn_off_spider(oj_name):
    if redis.exists(switch_key):
        redis.hset(switch_key, oj_name, 0)
    log_spider_status()
