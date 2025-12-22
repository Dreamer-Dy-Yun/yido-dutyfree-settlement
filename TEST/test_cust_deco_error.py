###########################################
# Module name : test_cust_deco_error.py
# 테스트 대상 : CUSTOMIZED.cust_deco_error.handle_http_error, parse_query_params
# Written by : Auto (Cursor AI)
###########################################

import pytest
from fastapi import HTTPException
from unittest.mock import patch
from CUSTOMIZED.cust_deco_error import handle_http_error, parse_query_params
from CUSTOMIZED.cust_parser import Parser


class TestHandleHttpError:
    """handle_http_error 데코레이터 테스트"""

    @pytest.mark.asyncio
    async def test_handle_http_error_success(self):
        """handle_http_error() 성공 케이스 테스트"""
        @handle_http_error
        async def test_func():
            return {"status": "success"}
        
        result = await test_func()
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_handle_http_error_value_error(self):
        """handle_http_error() ValueError 처리 테스트"""
        @handle_http_error
        async def test_func():
            raise ValueError("validation error")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 422
        assert "validation error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_handle_http_error_general_exception(self):
        """handle_http_error() 일반 예외 처리 테스트"""
        @handle_http_error
        async def test_func():
            raise RuntimeError("internal error")
        
        with patch('CUSTOMIZED.cust_deco_error.logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await test_func()
            
            assert exc_info.value.status_code == 500
            assert "internal error" in str(exc_info.value.detail)
            mock_logger.error.assert_called_once()


class TestParseQueryParams:
    """parse_query_params 데코레이터 테스트"""

    @pytest.mark.asyncio
    async def test_parse_query_params_single_param(self):
        """parse_query_params() 단일 파라미터 변환 테스트"""
        @parse_query_params(date_param=Parser.to_date)
        @handle_http_error
        async def test_func(date_param):
            assert isinstance(date_param, type(None)) or hasattr(date_param, 'year')
            return {"date": str(date_param)}
        
        result = await test_func(date_param="20250115")
        assert "date" in result

    @pytest.mark.asyncio
    async def test_parse_query_params_multiple_params(self):
        """parse_query_params() 여러 파라미터 변환 테스트"""
        @parse_query_params(
            date_from=Parser.to_date,
            date_to=Parser.to_date,
            resolution=Parser.to_integer
        )
        @handle_http_error
        async def test_func(date_from, date_to, resolution):
            return {
                "date_from": str(date_from),
                "date_to": str(date_to),
                "resolution": resolution
            }
        
        result = await test_func(
            date_from="20250101",
            date_to="20250131",
            resolution="100"
        )
        
        assert "date_from" in result
        assert "date_to" in result
        assert result["resolution"] == 100

    @pytest.mark.asyncio
    async def test_parse_query_params_none_value(self):
        """parse_query_params() None 값 처리 테스트"""
        @parse_query_params(date_param=Parser.to_date)
        @handle_http_error
        async def test_func(date_param):
            return {"date": date_param}
        
        result = await test_func(date_param=None)
        assert result["date"] is None

    @pytest.mark.asyncio
    async def test_parse_query_params_invalid_value(self):
        """parse_query_params() 잘못된 값 처리 테스트"""
        # 데코레이터 순서: handle_http_error가 먼저 적용되어야 ValueError를 잡을 수 있음
        @handle_http_error
        @parse_query_params(date_param=Parser.to_date)
        async def test_func(date_param):
            return {"date": date_param}
        
        # ignore_error=False이므로 ValueError 발생 -> HTTPException 422로 변환
        with pytest.raises(HTTPException) as exc_info:
            await test_func(date_param="invalid")
        
        assert exc_info.value.status_code == 422
        # ValueError가 HTTPException으로 변환되었는지 확인
        assert "변환할 수 없는" in str(exc_info.value.detail) or "invalid" in str(exc_info.value.detail)

