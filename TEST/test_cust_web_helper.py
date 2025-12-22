###########################################
# Module name : test_cust_web_helper.py
# 테스트 대상 : CUSTOMIZED.cust_web_helper.Export, _sheet_name_sanitizer
# Written by : Auto (Cursor AI)
###########################################

import pytest
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
from CUSTOMIZED.cust_web_helper import Export, _sheet_name_sanitizer


class TestExport:
    """Export 클래스 테스트"""

    @pytest.mark.asyncio
    async def test_as_excel_dataframe(self):
        """as_excel() DataFrame 테스트"""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        
        result = await Export.as_excel(df, "test_file")
        
        assert isinstance(result, StreamingResponse)
        assert result.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "test_file.xlsx" in result.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_as_excel_dict_dataframes(self):
        """as_excel() 딕셔너리 형태 DataFrame 테스트"""
        df1 = pd.DataFrame({"col1": [1, 2, 3]})
        df2 = pd.DataFrame({"col2": ["a", "b", "c"]})
        df_dict = {"Sheet1": df1, "Sheet2": df2}
        
        result = await Export.as_excel(df_dict, "test_file")
        
        assert isinstance(result, StreamingResponse)
        assert result.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    @pytest.mark.asyncio
    async def test_as_excel_invalid_type(self):
        """as_excel() 잘못된 타입 테스트"""
        with pytest.raises(ValueError, match="Invalid DataFrame Type"):
            await Export.as_excel("not a dataframe", "test_file")


class TestSheetNameSanitizer:
    """_sheet_name_sanitizer 클래스 테스트"""

    def test_get_basic(self):
        """get() 기본 테스트"""
        sanitizer = _sheet_name_sanitizer()
        result = sanitizer.get("Sheet1")
        
        assert result == "Sheet1"

    def test_get_invalid_chars(self):
        """get() 유효하지 않은 문자 제거 테스트"""
        sanitizer = _sheet_name_sanitizer()
        result = sanitizer.get("Sheet:1/2?3*4[5]6'7")
        
        assert ":" not in result
        assert "/" not in result
        assert "?" not in result
        assert "*" not in result
        assert "[" not in result
        assert "]" not in result

    def test_get_max_length(self):
        """get() 최대 길이 제한 테스트"""
        sanitizer = _sheet_name_sanitizer()
        long_name = "A" * 50
        result = sanitizer.get(long_name)
        
        assert len(result) <= 31

    def test_get_duplicate_names(self):
        """get() 중복 이름 처리 테스트"""
        sanitizer = _sheet_name_sanitizer()
        
        result1 = sanitizer.get("Sheet1")
        result2 = sanitizer.get("Sheet1")
        result3 = sanitizer.get("Sheet1")
        
        assert result1 == "Sheet1"
        assert result2 == "Sheet1_(1)"
        assert result3 == "Sheet1_(2)"

    def test_get_empty_string(self):
        """get() 빈 문자열 테스트"""
        sanitizer = _sheet_name_sanitizer()
        result = sanitizer.get("")
        
        assert result == "Sheet"

    def test_get_whitespace(self):
        """get() 공백 제거 테스트"""
        sanitizer = _sheet_name_sanitizer()
        result = sanitizer.get("  Sheet1  ")
        
        assert result == "Sheet1"

    def test_get_quotes(self):
        """get() 따옴표 처리 테스트"""
        sanitizer = _sheet_name_sanitizer()
        result = sanitizer.get("'Sheet1'")
        
        assert result == "Sheet1"

    def test_set_used_sheet_names(self):
        """set_used_sheet_names() 테스트"""
        sanitizer = _sheet_name_sanitizer()
        sanitizer.set_used_sheet_names(["Sheet1", "Sheet2"])
        
        result = sanitizer.get("Sheet1")
        
        assert result == "Sheet1_(1)"

