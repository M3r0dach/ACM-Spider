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
                    if left_times != times:
                        logger.warn('重试第 {0} 次 ===> {1}({2})'.format(times - left_times,
                                                                     function.__name__, args))
                    ret = yield function(*args, **kwargs)
                    if isinstance(ret, bool):
                        call_state = ret
                    elif not ret:
                        call_state = False
                    else:
                        call_state = True
                    if not call_state:
                        yield gen.sleep(duration)
                except Exception as e:
                    logger.error(e)
                finally:
                    left_times -= 1
            if call_state is False:
                message = '<After try {0} times> def {1}({2}) call fail'.format(times, function.__name__, args)
                logger.error(message)
            return ret
        return wrapper
    return decorator
