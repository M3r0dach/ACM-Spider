
db_config = {
    'username': '',
    'pwd': '',
    'host': 'localhost',
    'db_name_prefix': 'cuit_acm_{}'
}

redis_config = {
    'host': 'localhost',
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
