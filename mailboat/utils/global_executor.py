from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_global_thread_pool_executor: Optional[ThreadPoolExecutor] = None


def get() -> ThreadPoolExecutor:
    if not _global_thread_pool_executor:
        _global_thread_pool_executor = ThreadPoolExecutor(
            None, "mailboat.utils.global_thread_pool_executor"
        )
    return _global_thread_pool_executor
