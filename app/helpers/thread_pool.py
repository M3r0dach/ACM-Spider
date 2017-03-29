from concurrent.futures import ThreadPoolExecutor
from config import settings

# 公用线程池
ThreadPool = ThreadPoolExecutor(max_workers=settings.THREAD_POOL_SIZE)