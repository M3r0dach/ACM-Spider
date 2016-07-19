from functools import wraps
from logger import logger
from tornado import gen


def try_run(times=3, duration=5):
    def decorator(function):
        @gen.coroutine
        @wraps(function)
        def wrapper(*args, **kwargs):
            left_times = times
            call_state, ret = False, None
            while left_times > 0 and call_state is False:
                try:
                    ret = yield function(*args, **kwargs)
                    if isinstance(ret, bool) and not ret:
                        call_state = False
                    elif not ret:
                        call_state = False
                    if not call_state:
                        yield gen.sleep(duration)
                except Exception as e:
                    logger.error(e)
                finally:
                    left_times -= 1
            logger.info('try run {} times'.format(times))
            if call_state is False:
                message = 'def {} call fail even if try {} times'.format(function.__name__, times)
                logger.error(message)
                raise Exception(message)
            return ret
        return wrapper
    return decorator
