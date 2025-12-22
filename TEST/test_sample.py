###########################################
# Module name : test_sample.py
# 목적       : pytest 기본 단위 테스트 템플릿
# Written by : GPT Test Template
# Note       : 새 테스트 작성 시 참고용 예제
###########################################

import pytest


def test_example_sum():
    """간단한 덧셈 예제 테스트"""
    # 준비
    a = 1
    b = 2

    # 실행
    result = a + b

    # 검증
    assert result == 3


class TestExampleClass:
    """pytest class 기반 예제"""

    def setup_method(self):
        """각 테스트 전에 실행되는 준비 코드"""
        self.value = 10

    def teardown_method(self):
        """각 테스트 후에 실행되는 정리 코드"""
        # 필요 시 정리 작업 추가
        pass

    def test_value_is_ten(self):
        """기본 값 검증 예제"""
        assert self.value == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


