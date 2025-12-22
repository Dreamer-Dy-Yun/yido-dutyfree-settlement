###########################################
# Module name : test_cust_deco_retry.py
# 테스트 대상 : CUSTOMIZED.cust_deco_retry.async_retry, async_retry_with_recovery
# Written by : Auto (Cursor AI)
###########################################

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from CUSTOMIZED.cust_deco_retry import async_retry, async_retry_with_recovery


class TestAsyncRetry:
    """async_retry 데코레이터 테스트"""

    @pytest.mark.asyncio
    async def test_async_retry_success_first_attempt(self):
        """async_retry() 첫 시도 성공 테스트"""
        call_count = 0
        
        @async_retry(exceptions=(ValueError,), max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_success_after_retries(self):
        """async_retry() 재시도 후 성공 테스트"""
        call_count = 0
        
        @async_retry(exceptions=(ValueError,), max_attempts=3, backoff_factor=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retry")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_fails_after_max_attempts(self):
        """async_retry() 최대 시도 후 실패 테스트"""
        call_count = 0
        
        @async_retry(exceptions=(ValueError,), max_attempts=3, backoff_factor=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fail")
        
        with pytest.raises(ValueError, match="always fail"):
            await test_func()
        
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_ignores_other_exceptions(self):
        """async_retry() 다른 예외 무시 테스트"""
        @async_retry(exceptions=(ValueError,), max_attempts=3)
        async def test_func():
            raise TypeError("different error")
        
        with pytest.raises(TypeError, match="different error"):
            await test_func()


class TestAsyncRetryWithRecovery:
    """async_retry_with_recovery 데코레이터 테스트"""

    @pytest.mark.asyncio
    async def test_async_retry_with_recovery_success(self):
        """async_retry_with_recovery() 성공 테스트"""
        call_count = 0
        recovery_called = False
        
        async def recovery_func():
            nonlocal recovery_called
            recovery_called = True
        
        @async_retry_with_recovery(
            exceptions=(ValueError,),
            max_attempts=3,
            backoff_factor=0.01,
            on_retry=recovery_func
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 2
        assert recovery_called is True

    @pytest.mark.asyncio
    async def test_async_retry_with_recovery_with_args(self):
        """async_retry_with_recovery() 인자 전달 테스트"""
        call_count = 0
        recovery_args = None
        
        async def recovery_func(*args):
            nonlocal recovery_args
            recovery_args = args
        
        @async_retry_with_recovery(
            exceptions=(ValueError,),
            max_attempts=3,
            backoff_factor=0.01,
            on_retry=recovery_func
        )
        async def test_func(arg1, arg2):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            return "success"
        
        result = await test_func("arg1", "arg2")
        
        assert result == "success"
        assert recovery_args == ("arg1", "arg2")

    @pytest.mark.asyncio
    async def test_async_retry_with_recovery_no_args(self):
        """async_retry_with_recovery() 인자 없는 recovery 테스트"""
        call_count = 0
        recovery_called = False
        
        async def recovery_func():
            nonlocal recovery_called
            recovery_called = True
        
        @async_retry_with_recovery(
            exceptions=(ValueError,),
            max_attempts=3,
            backoff_factor=0.01,
            on_retry=recovery_func
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert recovery_called is True

