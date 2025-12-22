###########################################
# Module name : test_cust_iterator.py
# 테스트 대상 : CUSTOMIZED.cust_iterator.iterator
# Written by : Auto (Cursor AI)
###########################################

import pytest
from unittest.mock import AsyncMock
from CUSTOMIZED.cust_iterator import iterator


class TestIterator:
    """iterator 클래스 테스트"""

    @pytest.mark.asyncio
    async def test_loop_basic(self):
        """loop() 기본 테스트"""
        iter_obj = iterator()
        call_count = 0
        
        async def test_func(**kwargs):
            nonlocal call_count
            call_count += 1
        
        items = [1, 2, 3]
        await iter_obj.loop(items, test_func)
        
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_loop_with_kwargs(self):
        """loop() kwargs 전달 테스트"""
        iter_obj = iterator()
        received_kwargs = None
        
        async def test_func(**kwargs):
            nonlocal received_kwargs
            received_kwargs = kwargs
        
        items = [1, 2, 3]
        await iter_obj.loop(items, test_func, key1="value1", key2="value2")
        
        assert received_kwargs == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_loop_empty_list(self):
        """loop() 빈 리스트 테스트"""
        iter_obj = iterator()
        call_count = 0
        
        async def test_func(**kwargs):
            nonlocal call_count
            call_count += 1
        
        items = []
        await iter_obj.loop(items, test_func)
        
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_loop_function_returns_value(self):
        """loop() 함수 반환값 테스트"""
        iter_obj = iterator()
        
        async def test_func(**kwargs):
            return "result"
        
        items = [1, 2, 3]
        # loop()는 반환값을 사용하지 않지만, 함수가 정상 실행되는지 확인
        result = await iter_obj.loop(items, test_func)
        
        # loop()는 반환값이 없지만, 함수가 정상 실행되었는지 확인
        assert result is None

