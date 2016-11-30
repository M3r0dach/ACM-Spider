import pyDes
import base64

db_config = {
    'username': '',
    'pwd': '',
    'host': 'localhost',
    'db_name': 'cuit_acm'
}

redis_config = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}


class RedisKey:
    prefix = 'cuit_acm.spider.'
    switch = 'switch'
    hdu = 'hdu'
    poj = 'poj'
    bnu = 'bnu'
    codeforces = 'cf'


key = 'secret key'
iv = b"secret key"


class Security:

    @staticmethod
    def encrypt(data):
        k = pyDes.des(key, pyDes.CBC, iv, pad=None, padmode=pyDes.PAD_PKCS5)
        return base64.b64encode(k.encrypt(data))

    @staticmethod
    def decrypt(data):
        k = pyDes.des(key, pyDes.CBC, iv, pad=None, padmode=pyDes.PAD_PKCS5)
        return k.decrypt(base64.b64decode(data))
