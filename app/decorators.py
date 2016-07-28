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
                        logger.info('重试 {0} ===> 第 {1} 次'.format(function.__name__, times - left_times))
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
                message = '<after try {0} times> def {1} call fail'.format(times, function.__name__)
                logger.error(message)
            return ret
        return wrapper
    return decorator
