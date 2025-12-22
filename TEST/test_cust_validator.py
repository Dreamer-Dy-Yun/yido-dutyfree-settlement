###########################################
# Module name : test_cust_validator.py
# 테스트 대상 : CUSTOMIZED.cust_validator.Raise
# Written by : Auto (Cursor AI)
###########################################

import pytest
from datetime import datetime
from CUSTOMIZED.cust_validator import Raise


class TestRaiseIf:
    """Raise.If 클래스 테스트"""

    def test_empty_none(self):
        """empty() None 값 테스트"""
        with pytest.raises(ValueError, match="◈None Value◈"):
            Raise.If.empty(None, "test_variable")

    def test_empty_empty_string(self):
        """empty() 빈 문자열 테스트"""
        with pytest.raises(ValueError, match="◈Empty Value◈"):
            Raise.If.empty("", "test_variable")

    def test_empty_empty_list(self):
        """empty() 빈 리스트 테스트"""
        with pytest.raises(ValueError, match="◈Empty Value◈"):
            Raise.If.empty([], "test_variable")

    def test_empty_empty_dict(self):
        """empty() 빈 딕셔너리 테스트"""
        with pytest.raises(ValueError, match="◈Empty Value◈"):
            Raise.If.empty({}, "test_variable")

    def test_empty_empty_set(self):
        """empty() 빈 집합 테스트"""
        with pytest.raises(ValueError, match="◈Empty Value◈"):
            Raise.If.empty(set(), "test_variable")

    def test_empty_valid_string(self):
        """empty() 유효한 문자열 테스트"""
        result = Raise.If.empty("valid string", "test_variable")
        assert result == "valid string"

    def test_empty_valid_list(self):
        """empty() 유효한 리스트 테스트"""
        result = Raise.If.empty([1, 2, 3], "test_variable")
        assert result == [1, 2, 3]

    def test_empty_valid_dict(self):
        """empty() 유효한 딕셔너리 테스트"""
        result = Raise.If.empty({"key": "value"}, "test_variable")
        assert result == {"key": "value"}

    def test_empty_bool_false(self):
        """empty() False 값 테스트 (통과해야 함)"""
        result = Raise.If.empty(False, "test_variable")
        assert result is False

    def test_empty_bool_true(self):
        """empty() True 값 테스트 (통과해야 함)"""
        result = Raise.If.empty(True, "test_variable")
        assert result is True

    def test_empty_datetime(self):
        """empty() datetime 값 테스트 (통과해야 함)"""
        dt = datetime(2025, 1, 15, 10, 0, 0)
        result = Raise.If.empty(dt, "test_variable")
        assert result == dt

    def test_empty_unhandled_type(self):
        """empty() 처리되지 않은 타입 테스트"""
        with pytest.raises(ValueError, match="◈Unhandled type◈"):
            Raise.If.empty(123, "test_variable")
        
        with pytest.raises(ValueError, match="◈Unhandled type◈"):
            Raise.If.empty(3.14, "test_variable")

    def test_empty_variable_name(self):
        """empty() 변수명 포함 확인 테스트"""
        try:
            Raise.If.empty(None, "my_variable")
        except ValueError as e:
            assert "my_variable" in str(e)

    def test_exceed_value_less_than_maximum(self):
        """exceed() 값이 최대값보다 작은 경우 테스트"""
        result = Raise.If.exceed(5.0, 10.0)
        assert result == 5.0

    def test_exceed_value_equal_maximum(self):
        """exceed() 값이 최대값과 같은 경우 테스트"""
        result = Raise.If.exceed(10.0, 10.0)
        assert result == 10.0

    def test_exceed_value_greater_than_maximum(self):
        """exceed() 값이 최대값보다 큰 경우 테스트"""
        with pytest.raises(ValueError, match="◈Exceeded value◈"):
            Raise.If.exceed(15.0, 10.0)

    def test_exceed_negative_values(self):
        """exceed() 음수 값 테스트"""
        result = Raise.If.exceed(-5.0, 0.0)
        assert result == -5.0
        
        with pytest.raises(ValueError, match="◈Exceeded value◈"):
            Raise.If.exceed(1.0, 0.0)

    def test_exceed_error_message(self):
        """exceed() 에러 메시지 확인 테스트"""
        try:
            Raise.If.exceed(15.0, 10.0)
        except ValueError as e:
            assert "15.0" in str(e)
            assert "10.0" in str(e)

    def test_below_value_greater_than_minimum(self):
        """below() 값이 최소값보다 큰 경우 테스트"""
        result = Raise.If.below(10.0, 5.0, "test_value")
        assert result == 10.0

    def test_below_value_equal_minimum(self):
        """below() 값이 최소값과 같은 경우 테스트"""
        result = Raise.If.below(5.0, 5.0, "test_value")
        assert result == 5.0

    def test_below_value_less_than_minimum(self):
        """below() 값이 최소값보다 작은 경우 테스트"""
        with pytest.raises(ValueError, match="◈Below Minimum◈"):
            Raise.If.below(3.0, 5.0, "test_value")

    def test_below_default_value_name(self):
        """below() 기본 변수명 테스트"""
        with pytest.raises(ValueError, match="◈Below Minimum◈"):
            Raise.If.below(3.0, 5.0)

    def test_below_custom_value_name(self):
        """below() 커스텀 변수명 테스트"""
        try:
            Raise.If.below(3.0, 5.0, "custom_name")
        except ValueError as e:
            assert "custom_name" in str(e)
            assert "3.0" in str(e)
            assert "5.0" in str(e)

    def test_below_negative_values(self):
        """below() 음수 값 테스트"""
        result = Raise.If.below(0.0, -5.0, "test_value")
        assert result == 0.0
        
        with pytest.raises(ValueError, match="◈Below Minimum◈"):
            Raise.If.below(-10.0, -5.0, "test_value")

    def test_below_error_message(self):
        """below() 에러 메시지 확인 테스트"""
        try:
            Raise.If.below(3.0, 5.0, "my_value")
        except ValueError as e:
            assert "my_value" in str(e)
            assert "3.0" in str(e)
            assert "5.0" in str(e)

