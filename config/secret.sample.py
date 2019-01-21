
db_config = {
    'username': 'root',
    'pwd': '',
    'host': 'db',
    'db_name_prefix': 'acm_meter_{}'
}

redis_config = {
    'host': 'redis',
    'port': 6379,
    'db': 0
}


class RedisKey:
    prefix = 'cuit_acm.spider.'
    switch = prefix + 'switch'
    hdu = prefix + 'hdu'
    poj = prefix + 'poj'
    bnu = prefix + 'bnu'
    codeforces = prefix + 'cf'
    achieve_mq = prefix + 'achieve_mq'
