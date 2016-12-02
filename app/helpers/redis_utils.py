import redis as py_redis
from app.helpers.logger import logger
from config.secret import redis_config, RedisKey
from config.settings import SUPPORT_OJ

redis = py_redis.StrictRedis(**redis_config)


def setup_redis():
    if not redis.exists(RedisKey.switch):
        ret = redis.hmset(RedisKey.switch, {oj: 1 for oj in SUPPORT_OJ})
        if ret:
            logger.info('[redis] setup switch key success')
    log_spider_status()


def log_spider_status():
    logger.info('[OPEN Spider] {0}'.format(
        get_all_open_spider()
    ))


###################################
# redis 控制Spider开关
###################################

def get_all_open_spider():
    all_status = redis.hgetall(RedisKey.switch)
    if all_status:
        all_status = [k.decode() for k, v in all_status.items() if int(v) == 1]
    return all_status or []


def is_spider_open(oj_name):
    status = int(redis.hget(RedisKey.switch, oj_name))
    return status == 1


def turn_on_spider(oj_name):
    if redis.exists(RedisKey.switch):
        redis.hset(RedisKey.switch, oj_name, 1)
    log_spider_status()


def turn_off_spider(oj_name):
    if redis.exists(RedisKey.switch):
        redis.hset(RedisKey.switch, oj_name, 0)
    log_spider_status()