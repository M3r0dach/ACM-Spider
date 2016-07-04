from functools import wraps
from logger import logger
from tornado import gen


def try_run(times=3):
    def decorator(function):
        @gen.coroutine
        @wraps(function)
        def wrapper(*args, **kwargs):
            left_times, call_state = times, False
            ret = None
            while left_times > 0 and call_state is False:
                try:
                    ret = yield function(*args, **kwargs)
                    call_state = True if ret is True else False
                except Exception as e:
                    logger.error(e)
                finally:
                    left_times -= 1
            if call_state is False:
                message = 'function {} call fail'.format(function.__name__)
                logger.error(message)
                raise Exception(message)
            return ret
        return wrapper
    return decorator
