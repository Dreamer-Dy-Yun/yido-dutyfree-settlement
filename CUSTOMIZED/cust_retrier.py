###########################################
# Module name : cust_retrier
# Module class : Retrier
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.03
# Updated at : 2025.07.16
# Supported by : ChatGPT-4o
# Note :
#   2025.07.16 : jitter 추가
#   2025.11.19 : staticmethod 로 변경
############################################

from typing import Callable, Awaitable, Any, Optional
import asyncio
import random

class Retrier:
    @staticmethod
    async def retry(
                func: Callable[[], Awaitable[Any]], 
                on_retry: Optional[Callable[[], Awaitable[Any]]] = None, 
                attempts: int = 5, 
                delay: float = 1.0,
                max_jitter: float = 1.0 
                ) -> Any:
        """
        개요
            재수행 클래스
        매개변수
            func      : 에러 발생 시 재시도할 메인 함수
            on_retry  : (OPTIONAL) 에러 발생 시 호출할 콜백 (예: 재연결 시도)
            attempts  : 최대 재시도 횟수
            delay     : 재시도 간 대기 시간 (초)
            max_jitter: 추가 최대 무작위 대기시간 (초). 동시 재시도 방지
        사용 예시 :
            # on_retry 없는 경우
            await retrier.retry(lambda: 대상함수(매개변수,...))

            # on_retry 있는 경우
            await retrier.retry(lambda: 대상함수(매개변수,...), lambda: 동행함수(매개변수,...))

        ★재시도마다 다음과 같이 재시도 간격 증가 : delay * (2 ** (attempt-1) + random.uniform(0, max_jitter))
        """
        for attempt in range(1, attempts + 1):
            try:
                return await func()
            except Exception:
                if attempt == attempts:
                    raise
                if on_retry:
                    await on_retry()
                await asyncio.sleep(delay * (2 ** (attempt-1) + random.uniform(0, max_jitter)))
                                    