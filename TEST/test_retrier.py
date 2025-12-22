###########################################
# Module name : test_retrier.py
# 테스트 대상 : CUSTOMIZED.cust_retrier.Retrier
# Written by : Test Example
# Note : pytest를 사용한 단위 테스트 예시
############################################

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from CUSTOMIZED.cust_retrier import Retrier


class TestRetrier:
    """Retrier 클래스에 대한 단위 테스트"""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """첫 시도에서 성공하는 경우"""
        async def success_func():
            return "success"
        
        result = await Retrier.retry(success_func, attempts=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """실패 후 재시도하여 성공하는 경우"""
        call_count = 0
        
        async def fail_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await Retrier.retry(fail_then_success, attempts=5, delay=0.01)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """최대 시도 횟수 후에도 실패하는 경우"""
        async def always_fail():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await Retrier.retry(always_fail, attempts=3, delay=0.01)

    @pytest.mark.asyncio
    async def test_retry_calls_on_retry_callback(self):
        """on_retry 콜백이 호출되는지 테스트"""
        on_retry_called = False
        
        async def always_fail():
            raise ValueError("Always fails")
        
        async def on_retry():
            nonlocal on_retry_called
            on_retry_called = True
        
        with pytest.raises(ValueError):
            await Retrier.retry(always_fail, on_retry=on_retry, attempts=2, delay=0.01)
        
        # 첫 번째 실패 후 on_retry가 호출되어야 함
        assert on_retry_called is True

    @pytest.mark.asyncio
    async def test_retry_delay_increases_exponentially(self):
        """재시도 간격이 지수적으로 증가하는지 테스트"""
        call_times = []
        
        async def always_fail():
            call_times.append(asyncio.get_event_loop().time())
            raise ValueError("Always fails")
        
        start_time = asyncio.get_event_loop().time()
        
        with pytest.raises(ValueError):
            await Retrier.retry(always_fail, attempts=3, delay=0.1, max_jitter=0.0)
        
        # 첫 번째와 두 번째 시도 사이의 간격이 약 0.1초 (delay * 2^0)
        # 두 번째와 세 번째 시도 사이의 간격이 약 0.2초 (delay * 2^1)
        if len(call_times) >= 2:
            first_interval = call_times[1] - call_times[0]
            assert 0.09 < first_interval < 0.15  # jitter 없이 약 0.1초
        
        if len(call_times) >= 3:
            second_interval = call_times[2] - call_times[1]
            assert 0.19 < second_interval < 0.25  # jitter 없이 약 0.2초

    @pytest.mark.asyncio
    async def test_retry_with_return_value(self):
        """반환값이 있는 함수 테스트"""
        async def return_number():
            return 42
        
        result = await Retrier.retry(return_number)
        assert result == 42

    @pytest.mark.asyncio
    async def test_retry_with_exception_type(self):
        """특정 예외 타입만 재시도하는지 확인"""
        # Retrier는 모든 Exception을 재시도하므로
        # 이 테스트는 현재 구현에 맞게 작성
        call_count = 0
        
        async def raise_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First error")
            elif call_count == 2:
                raise TypeError("Second error")
            return "success"
        
        result = await Retrier.retry(raise_different_exceptions, attempts=3, delay=0.01)
        assert result == "success"
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

