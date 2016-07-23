import redis
from secret import redis_config

redis = redis.StrictRedis(**redis_config)


def setup_redis():
    pass

