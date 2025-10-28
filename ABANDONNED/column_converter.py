###########################################
# Module name : column_converter.py
# Module functions : ColumnConverter
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.10.15
# Supported by : -
# Note : 
#        2025.10.15 : 초기 버전 작성
#        2025.10.17 : 폐기 처리(사유 : 기존 라이브러리에서 제공하는 기능 발견)
############################################

from typing import Literal
import string
import re

class ColumnConverter:

    @staticmethod
    def get_cell_address(row: int, column: int | str, return_as: Literal["A1 notation", "R1C1"] = "A1 notation") -> str | int:
        if return_as == "A1 notation":
            column = column if isinstance(column, str) else ColumnConverter.number_to_letter(column)
            return f"{column}{row}"
        elif return_as == "R1C1":
            column = column if isinstance(column, str) else ColumnConverter.letter_to_number(column)
            return f"R{row}C{column}"
    

    @staticmethod
    def get_column_letter_from_cell_address(cell_address: str, return_as_letter: bool = True) -> str | int:
        if not Validator.is_cell_address(cell_address):
            raise ValueError(f"Invalid cell address: {cell_address}")

        result : str = ''.join(ch for ch in cell_address if ch.isalpha())

        if not return_as_letter:
            result = ColumnConverter.letter_to_number(result)
        return result


    @staticmethod
    def add_column(column_a: str | int, column_b: str | int, return_as_letter: bool = True) -> str | int:

        result : str | int = 0

        base : int = ColumnConverter.letter_to_number(column_a) if isinstance(column_a, str) else int(column_a)
        step : int = ColumnConverter.letter_to_number(column_b) if isinstance(column_b, str) else int(column_b)

        result = base + step

        if result < 0:
            raise ValueError(f"Invalid column: {column_a} + {column_b} = {result}")

        if return_as_letter:
            result = ColumnConverter.number_to_letter(result)

        return result

    @staticmethod
    def number_to_letter(col_number: int) -> str:
        """
        Excel/Google Sheets 컬럼 숫자를 문자로 변환
        예: 1=A, 2=B, 26=Z, 27=AA, 28=AB 등
        """
        result : str = ""
        while col_number > 0:
            col_number -= 1
            result = chr(65 + col_number % 26) + result
            col_number //= 26 # 26으로 나눈 몫
        return result

    @staticmethod
    def letter_to_number(col_letter: str) -> int:
        """
        Excel/Google Sheets 컬럼 문자를 숫자로 변환
        예: A=1, B=2, Z=26, AA=27, AB=28 등
        """
        if not all(c in string.ascii_letters for c in col_letter):
            raise ValueError(f"Invalid column letter: {col_letter}")

        result : int = 0

        col_letter = col_letter.strip().upper()

        for char in col_letter:
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result


class Validator:
    @staticmethod
    def is_cell_address(cell_address: str | None = None, ignore_none : bool = True) -> bool:
        """
        Google Sheets 셀 주소 형식 검증
        예: A1, B2, Z26, AA1, AB123, ZZ999 등
        """

        if cell_address is None:
            if ignore_none:
                return True
            return False

        pattern = r'^[A-Z]+[1-9]\d*$'
        return bool(re.match(pattern, cell_address))

    @staticmethod
    def is_range(range_address: str | None = None, ignore_none : bool = True) -> bool:
        """
        Google Sheets 범위 형식 검증
        허용: A1:B2, A1:B, A:B, A:A, 1:1 등
        불허용: A:B1 (컬럼:셀 혼합) 
        """

        if range_address is None:
            if ignore_none:
                return True
            return False

        # (컬럼|셀):(컬럼|셀) 또는 행:행
        pattern = r'^([A-Z]+(?:[1-9]\d*)?|[1-9]\d*):([A-Z]+(?:[1-9]\d*)?|[1-9]\d*)$'
        return bool(re.match(pattern, range_address))