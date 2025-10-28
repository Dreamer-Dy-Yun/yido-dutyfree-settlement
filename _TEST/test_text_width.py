# test_text_width.py
import pytest
from text_width import TextAligner

class TestTextAligner:
    
    @pytest.fixture
    def aligner(self):
        return TextAligner()
    
    def test_init(self, aligner):
        assert aligner.texts == []
        assert aligner.max_length == 0
    
    def test_inject_text_list(self, aligner):
        texts = ["Hello", "안녕"]
        result = aligner.inject_text_list(texts)
        
        assert aligner.texts == texts
        assert result is aligner
    
    def test_string_width_consistency(self, aligner):
        """폭 계산의 일관성 테스트"""
        # 같은 문자열은 항상 같은 폭을 가져야 함
        text = "Hello"
        width1 = aligner.get_string_width(text)
        width2 = aligner.get_string_width(text)
        assert width1 == width2
        
        # 빈 문자열은 0폭
        assert aligner.get_string_width("") == 0
    
    def test_string_width_relative(self, aligner):
        """상대적 폭 비교 테스트"""
        # 영문은 한글보다 폭이 작아야 함
        english = "Hello"
        korean = "안녕"
        
        english_width = aligner.get_string_width(english)
        korean_width = aligner.get_string_width(korean)
        
        assert english_width == 5  # "Hello"는 5폭
        assert korean_width == 4   # "안녕"은 4폭
    
    def test_center_text(self, aligner):
        """중앙 정렬 테스트"""
        aligner.inject_text_list(["Hello", "안녕"])
        
        # "Hello"를 6폭으로 중앙 정렬
        result = aligner.center_text("Hello", 6)
        assert len(result) == 6
        assert result.strip() == "Hello"
    
    def test_transform(self, aligner):
        """변환 테스트"""
        texts = ["Hello", "안녕"]
        aligner.inject_text_list(texts)
        
        result = aligner.transform("Hello", prefix="◈", suffix="◈")
        assert "Hello" in result
        assert result.startswith("◈")
        assert result.endswith("◈")

if __name__ == "__main__":
    pytest.main([__file__])