###########################################
# Module name : cust_deco_error.py
# Module functions : HTTP Error Handler Decorator
# Written by : Cursor AI (model : ? (Auto))
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.10.31
# Supported by : -
# Instructed by : Yun Dae-young
############################################

import functools
from typing import Callable, Awaitable, Any
from fastapi import HTTPException
from CUSTOMIZED.cust_logger import logger


def parse_query_params(**transformations: Callable) -> Callable:
    """
    쿼리 파라미터 변환 데코레이터
    
    사용 예:
        @parse_query_params(
            left_date_from=cp.Parser.to_date,
            left_date_to=cp.Parser.to_date,
            resolution=cp.Parser.to_integer
        )
        @handle_http_error
        async def my_endpoint(
            left_date_from: str = Query(...),
            left_date_to: str = Query(...),
            resolution: str = Query(...)
        ):
            # 이미 변환된 타입으로 사용 가능
            pass
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 변환할 파라미터 처리
            for param_name, parser_func in transformations.items():
                if param_name in kwargs and kwargs[param_name] is not None:
                    kwargs[param_name] = parser_func(kwargs[param_name], ignore_error=False)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def handle_http_error(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """
    API 엔드포인트 HTTP 에러 핸들링 데코레이터
    
    ValueError -> HTTPException 422
    Exception -> HTTPException 500 (로깅 포함)
    
    사용 예:
        @router.get("/api/endpoint")
        @handle_http_error
        async def my_endpoint():
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 엔드포인트에서 의도적으로 만든 HTTPException은 그대로 전달
            raise
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Internal server error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return wrapper

