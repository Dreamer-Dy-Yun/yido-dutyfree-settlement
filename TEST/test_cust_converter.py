###########################################
# Module name : test_cust_converter.py
# 테스트 대상 : CUSTOMIZED.cust_converter.StringConverter
# Written by : Auto (Cursor AI)
###########################################

import pytest
from enum import Enum
from CUSTOMIZED.cust_converter import StringConverter


class TestStringConverter:
    """StringConverter 클래스 테스트"""

    def test_from_enum_with_enum(self):
        """From.enum() Enum 타입 테스트"""
        class TestEnum(Enum):
            VALUE1 = "value1"
            VALUE2 = "value2"
        
        result = StringConverter.From.enum(TestEnum.VALUE1)
        assert result == "value1"
        
        result = StringConverter.From.enum(TestEnum.VALUE2)
        assert result == "value2"

    def test_from_enum_with_string(self):
        """From.enum() 문자열 타입 테스트"""
        result = StringConverter.From.enum("test_string")
        assert result == "test_string"
        
        result = StringConverter.From.enum("")
        assert result == ""

    def test_from_enum_with_different_enums(self):
        """From.enum() 다른 Enum 타입 테스트"""
        class StatusEnum(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
        
        class TypeEnum(Enum):
            TYPE_A = "A"
            TYPE_B = "B"
        
        result1 = StringConverter.From.enum(StatusEnum.ACTIVE)
        assert result1 == "active"
        
        result2 = StringConverter.From.enum(TypeEnum.TYPE_A)
        assert result2 == "A"

    def test_from_enum_with_int_enum(self):
        """From.enum() 정수 값 Enum 테스트"""
        class IntEnum(Enum):
            ONE = 1
            TWO = 2
        
        result = StringConverter.From.enum(IntEnum.ONE)
        assert result == 1
        
        result = StringConverter.From.enum(IntEnum.TWO)
        assert result == 2

