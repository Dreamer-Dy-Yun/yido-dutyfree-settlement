###########################################
# Module name : cust_iterator
# Module class : iterator
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.09.25
# Updated at : 2025.09.25
# Supported by : ChatGPT-4o
# Note :
#   2025.09.25 : 리스트 순회 클래스 분리
############################################

from typing import Callable, Awaitable, Any, Optional
import asyncio
import random

class iterator:
    async def loop(
                self, 
                items: list,
                func: Callable[[], Awaitable[Any]], 
                **kwargs: Any,
                ) -> Any:
        """
        개요
            리스트 순회 클래스
        매개변수
            list      : 순회할 리스트
            func      : 리스트 순회시 실행할 메인 함수
        사용 예시 :

        """
        for item in items:
            await func(**kwargs)

def test_func(item: Any, **kwargs: Any):
    print(item)
    print(kwargs)

