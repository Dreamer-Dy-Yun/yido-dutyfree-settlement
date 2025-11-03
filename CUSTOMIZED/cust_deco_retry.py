###########################################
# Module name : cust_decorator
# Module functions : async_retry, async_retry_with_recovery, _run_with_retry
# Written by : Yun Dae-young 
# Created at : 2025.07.03
# Updated at : 2025.07.03
# Supported by : ChatGPT-4o
# Note : 
############################################

import asyncio
import functools
from typing import Callable, Awaitable, Any
from CUSTOMIZED.cust_logger import logger

def async_retry(
    exceptions: tuple = (Exception,),
    max_attempts: int = 5,
    backoff_factor: float = 1.0
):
    def decorator(func: Callable[..., Awaitable[Any]] ):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await _run_with_retry(
                func, args, kwargs, exceptions, max_attempts, backoff_factor
            )
        return wrapper
    return decorator


def async_retry_with_recovery(
    exceptions: tuple = (Exception,),
    max_attempts: int = 5,
    backoff_factor: float = 1.0,
    on_retry: Callable[..., Awaitable[None]] = None
):
    """
    이 데코레이터에서 on_retry를 사용하기 위한 방법

    [1] 클래스 인스턴스(self)를 사용하는 경우 → 내부 래핑 필요
        클래스 정의 시점에는 self가 존재하지 않으므로, 데코레이터를 함수 내부에서 적용해야 함.

        예:
            class TESTCLASS:
                async def prerequisite_method(self):
                    pass
        
                async def wrapped_logic(self):
                    @async_retry_with_recovery((ValueError,), on_retry=self.prerequisite_method)\n
                    async def inner():
                        raise ValueError("Err") 
                    await inner()

    [2] 외부 함수나 인스턴스를 명시적으로 생성한 경우 → 직접 전달 가능
        self를 직접 참조하지 않기 때문에 정의 시점에 바로 넘겨도 됨.

        예:
            class TESTCLASS:
                async def prerequisite_method(self):
                    pass
            
            @async_retry_with_recovery((ValueError,), on_retry=TESTCLASS().prerequisite_method)\n
            async def execute():
                raise ValueError("Err") 
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await _run_with_retry(
                func, args, kwargs, exceptions, max_attempts, backoff_factor, on_retry
            )
        return wrapper
    return decorator


async def _run_with_retry(
    func: Callable[..., Awaitable],
    args: tuple,
    kwargs: dict,
    exceptions: tuple,
    max_attempts: int,
    backoff_factor: float,
    on_retry: Callable[..., Awaitable[None]] = None
):
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            if attempt == max_attempts:
                logger.error(f"[FAIL] {func.__name__} failed after {attempt} attempts: {e}")
                raise

            delay = backoff_factor * (2 ** (attempt - 1))
            logger.warning(f"[RETRY] {func.__name__} attempt {attempt} failed: {e}. Retrying in {delay:.1f}s")

            if on_retry:
                try:
                    from inspect import signature
                    sig = signature(on_retry)
                    if len(sig.parameters) >= 1:
                        await on_retry(*args)
                    else:
                        await on_retry()
                except Exception as rec_e:
                    logger.exception(f"[RECOVERY ERROR] during recovery_callback: {rec_e}")

            await asyncio.sleep(delay)



# TEST CODE ######################
# @async_retry((ValueError))
# async def test_async_retry():
#     print("Err 발생")
#     raise ValueError("aaaaa")

# asyncio.run(test_async_retry())

# TEST CODE ######################
# class TESTCLASS:
    
#     async def prerequisite_method(self):
#         print("선행 매서드 실행")

#     async def wrapped_logic(self):
#         @async_retry_with_recovery((ValueError,), recovery_callback=self.prerequisite_method)
#         async def inner():
#             print("Err 발생")
#             raise ValueError("aaaaa") 
#
#         await inner()
        
# tc = TESTCLASS()

# asyncio.run(tc.wrapped_logic())
