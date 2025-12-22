###########################################
# Module name : test_cust_parser.py
# 테스트 대상 : CUSTOMIZED.cust_parser.Parser, when.err
# Written by : Auto (Cursor AI)
###########################################

import pytest
from datetime import datetime, date, time
from CUSTOMIZED.cust_parser import Parser, when


class TestParser:
    """Parser 클래스 테스트"""

    def test_extract_numbers(self):
        """extract_numbers() 테스트"""
        assert Parser.extract_numbers("abc123def456") == "123456"
        assert Parser.extract_numbers("123") == "123"
        assert Parser.extract_numbers("abc") == ""
        assert Parser.extract_numbers("") == ""

    def test_to_datetime_basic(self):
        """to_datetime() 기본 테스트"""
        result = Parser.to_datetime("20250115(120000)")
        assert result == datetime(2025, 1, 15, 12, 0, 0)
        
        result = Parser.to_datetime("20250115")
        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_to_datetime_with_format(self):
        """to_datetime() 포맷 지정 테스트"""
        # extract_numbers_only=False로 설정해야 포맷이 유지됨
        result = Parser.to_datetime("2025-01-15 12:00:00", format_of_strdatetime="%Y-%m-%d %H:%M:%S", extract_numbers_only=False)
        assert result == datetime(2025, 1, 15, 12, 0, 0)

    def test_to_datetime_extract_numbers_only(self):
        """to_datetime() 숫자만 추출 테스트"""
        result = Parser.to_datetime("2025-01-15(12:00:00)", extract_numbers_only=True)
        assert result == datetime(2025, 1, 15, 12, 0, 0)

    def test_to_datetime_none_value(self):
        """to_datetime() None 값 테스트"""
        assert Parser.to_datetime(None) is None
        assert Parser.to_datetime("None") is None
        assert Parser.to_datetime("") is None

    def test_to_datetime_ignore_error(self):
        """to_datetime() 에러 무시 테스트"""
        result = Parser.to_datetime("invalid", ignore_error=True)
        assert result is None
        
        with pytest.raises(ValueError):
            Parser.to_datetime("invalid", ignore_error=False)

    def test_to_date_basic(self):
        """to_date() 기본 테스트"""
        result = Parser.to_date("20250115")
        assert result == date(2025, 1, 15)

    def test_to_date_none_value(self):
        """to_date() None 값 테스트"""
        assert Parser.to_date(None) is None
        assert Parser.to_date("None") is None

    def test_to_date_ignore_error(self):
        """to_date() 에러 무시 테스트"""
        # extract_numbers_only=True일 때 "invalid"는 빈 문자열이 되어 None 반환
        # ignore_error=True일 때 None을 안전하게 반환해야 함
        result = Parser.to_date("invalid", ignore_error=True)
        assert result is None
        
        # 다른 잘못된 형식 테스트
        result = Parser.to_date("20251345", ignore_error=True)  # 잘못된 날짜
        assert result is None

    def test_to_time_basic(self):
        """to_time() 기본 테스트"""
        result = Parser.to_time("120000")
        assert result == time(12, 0, 0)

    def test_to_time_none_value(self):
        """to_time() None 값 테스트"""
        assert Parser.to_time(None) is None
        assert Parser.to_time("None") is None

    def test_to_float_basic(self):
        """to_float() 기본 테스트"""
        assert Parser.to_float("123.45") == 123.45
        assert Parser.to_float("0") == 0.0
        assert Parser.to_float("-123.45") == -123.45

    def test_to_float_none_value(self):
        """to_float() None 값 테스트"""
        assert Parser.to_float(None) is None
        assert Parser.to_float("None") is None

    def test_to_float_ignore_error(self):
        """to_float() 에러 무시 테스트"""
        result = Parser.to_float("invalid", ignore_error=True)
        assert result is None
        
        with pytest.raises(ValueError):
            Parser.to_float("invalid", ignore_error=False)

    def test_to_integer_basic(self):
        """to_integer() 기본 테스트"""
        assert Parser.to_integer("123") == 123
        assert Parser.to_integer("0") == 0
        assert Parser.to_integer("-123") == -123

    def test_to_integer_none_value(self):
        """to_integer() None 값 테스트"""
        assert Parser.to_integer(None) is None
        assert Parser.to_integer("None") is None

    def test_to_integer_ignore_error(self):
        """to_integer() 에러 무시 테스트"""
        result = Parser.to_integer("invalid", ignore_error=True)
        assert result is None

    def test_to_boolean_basic(self):
        """to_boolean() 기본 테스트"""
        # Python의 bool()은 빈 문자열이 아닌 모든 문자열을 True로 변환
        assert Parser.to_boolean("True") is True
        assert Parser.to_boolean("False") is True  # 빈 문자열이 아니므로 True
        assert Parser.to_boolean("1") is True
        assert Parser.to_boolean("0") is True  # 빈 문자열이 아니므로 True
        assert Parser.to_boolean("") is None  # 빈 문자열은 None

    def test_to_boolean_none_value(self):
        """to_boolean() None 값 테스트"""
        assert Parser.to_boolean(None) is None
        assert Parser.to_boolean("None") is None

    def test_to_string_basic(self):
        """to_string() 기본 테스트"""
        assert Parser.to_string("test") == "test"
        assert Parser.to_string("123") == "123"

    def test_to_string_none_value(self):
        """to_string() None 값 테스트"""
        assert Parser.to_string(None) is None
        assert Parser.to_string("None") is None
        assert Parser.to_string("") is None

    def test_none_values_custom(self):
        """커스텀 none_values 테스트"""
        assert Parser.to_string("N/A", none_values=["N/A"]) is None
        assert Parser.to_string("null", none_values=["null", "None"]) is None

    def test_ignore_case(self):
        """ignore_case 옵션 테스트"""
        assert Parser.to_string("NONE", ignore_case=True) is None
        assert Parser.to_string("none", ignore_case=True) is None
        assert Parser.to_string("NONE", ignore_case=False) == "NONE"


class TestWhenErr:
    """when.err 클래스 테스트"""

    def test_fallback_success(self):
        """fallback() 성공 케이스 테스트"""
        def test_func(x):
            return x
        
        result = when.err.fallback({1: "one", 2: "two"}, test_func, 1)
        assert result == "one"
        
        result = when.err.fallback({1: "one", 2: "two"}, test_func, 3)
        assert result == 3

    def test_fallback_not_in_dict(self):
        """fallback() 딕셔너리에 없는 값 테스트"""
        def test_func(x):
            return x
        
        result = when.err.fallback({1: "one"}, test_func, 2)
        assert result == 2

    def test_return_success(self):
        """return_() 성공 케이스 테스트"""
        def test_func(x):
            return x * 2
        
        result = when.err.return_("default", test_func, 5)
        assert result == 10

    def test_return_exception(self):
        """return_() 예외 발생 테스트"""
        def test_func(x):
            raise ValueError("test error")
        
        result = when.err.return_("default", test_func, 5)
        assert result == "default"

    def test_return_none_default(self):
        """return_() None 기본값 테스트"""
        def test_func(x):
            raise ValueError("test error")
        
        result = when.err.return_(None, test_func, 5)
        assert result is None

