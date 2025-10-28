import wcwidth
import pytest

class TextAligner():

    def __init__(self) -> None:
        self.texts: list = []
        self.max_length: int = 0
        self.prefix: str = ""
        self.suffix: str = ""

    def get_string_width(self, text: str) -> int:
        """wcwidth를 사용한 정확한 문자열 폭 계산"""
        return wcwidth.wcswidth(text)

    def inject_text_list(self, texts: list):
        self.texts = texts
        if texts:
            # wcwidth로 정확한 폭 계산
            self.max_length = max(self.get_string_width(text) for text in texts)
        else:
            self.max_length = 0
        return self

    def center_text(self, text: str, width: int) -> str:
        """wcwidth 기반 중앙 정렬"""
        text_width = self.get_string_width(text)
        padding = max(0, width - text_width)
        left_padding = padding // 2
        right_padding = padding - left_padding
        return " " * left_padding + text + " " * right_padding

    def transform(self, text: str, prefix: str = "", suffix: str = "", length: int = 0) -> str:
        if not prefix:
            prefix = self.prefix
        if not suffix:
            suffix = self.suffix
        if not length:
            length = self.max_length

        return prefix + self.center_text(text, length) + suffix
    


