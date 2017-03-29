import traceback
from functools import wraps

from tornado import gen

from app.helpers.logger import logger


#
# try_run
# @times    重试次数
# @duration 每次重试之间间隔(分钟)
#
def try_run(times=3, duration=1):
    def decorator(function):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            left_times = times
            call_state, ret = False, None
            while left_times > 0 and call_state is False:
                try:
                    if left_times != times:
                        logger.warn('[重试第 {0} 次] ===> {1}({2})'.format(
                            times - left_times, function.__name__, args))

                    ret = await function(*args, **kwargs)
                    call_state = True if ret else False
                    if not call_state:
                        await gen.sleep(duration * 60)
                except Exception as e:
                    logger.error(e)
                    logger.error(traceback.format_exc())
                finally:
                    left_times -= 1
            if call_state is False:
                message = '[已经重试 {0} 次] def {1}({2}) call fail'.format(times, function.__name__, args)
                logger.error(message)
            return ret
        return wrapper
    return decorator
