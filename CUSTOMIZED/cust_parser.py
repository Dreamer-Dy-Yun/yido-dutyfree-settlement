###########################################
# Module name : cust_parser.py
# Module functions : Parser
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2024.10.xx (이전 프로젝트에서 작성)
# Updated at : 2025.09.17
# Supported by : -
# Note : 
#        ※ 목적 : 다양한 사이트의 API 결과 값을 동일한 방법으로 처리하기 위한 클래스
#        2025.09.17 : 파일 분할(Customized -> Parser)
#                     리턴 타입 명시(제작시 파이썬을 처음 접하여 리턴 명시 방법을 몰랐던 듯.)
#        2025.10.16 : to_datetime() 함수에서 %Y%m%d(%H%M%S) 포맷 지원
#                     ※ 날짜만 입력된 경우, %Y%m%d000000 포맷으로 변환 
#        2025.10.17 : when.err.return_() 함수 추가
#                     ※ 함수 실행 중 예외가 발생하면, return_value를 리턴
############################################

from ast import Str
from typing import TypeAlias, Dict, List, Union, Any, Callable
from datetime import datetime, date, time
from enum import Enum

JSON: TypeAlias = Union[Dict[str, Any], List[Any]]
DB_PARAMS = Union[Dict[str, Any], List[Dict[str, Any]], None]
AIO_RESULT: TypeAlias = List[Union[Any, BaseException]]


class when:
    class err:
        @staticmethod
        def fallback(result_N_return : dict[Any, Any], func: Callable, *args: Any, **kwargs: Any) -> Any | None:
            result = func(*args, **kwargs)
            if result in result_N_return:
                return result_N_return[result]
            return result


        @staticmethod
        def return_(return_value: Any | None, func: Callable, *args: Any, **kwargs: Any) -> Any | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return return_value
class Parser:

    @staticmethod
    def _is_none_or_empty(value: str | None, none_value: str = 'None') -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            # value 값이 none_value와 같거나 비어있으면 True. (즉, None 또는 Empty)
            return value.strip().lower() == none_value.lower() or not value.strip()
        return False

    @staticmethod
    def _ignore_errors(ignore_error: bool, type_name: str, func, *args) -> Any | None:
        try:
            return func(*args)
        except ValueError as e:
            if not ignore_error:
                raise ValueError(f"타입 [{type_name}](으)로 변환할 수 없는 문자열입니다. : {args[0]}") from e
            return None

    @staticmethod
    def extract_numbers(str_text: str) -> str:
        return ''.join(filter(str.isdigit, str_text))  # type: ignore # 가급적 wrapping 하고 싶지 않아 그냥 타입 이그노어 함.

    @staticmethod
    def to_datetime(str_datetime: str, format_of_strdatetime: str = "%Y%m%d(%H%M%S)", 
                    extract_numbers_only: bool = True, ignore_error: bool = False, none_value: str = 'None') -> datetime | None:
        if Parser._is_none_or_empty(str_datetime, none_value):
            return None

        if extract_numbers_only:
            str_datetime = Parser.extract_numbers(str_datetime)

        if format_of_strdatetime == "%Y%m%d(%H%M%S)" and len(str_datetime) == 8 :
            str_datetime = f"{str_datetime}000000"
        
        format_of_strdatetime = "%Y%m%d%H%M%S" if format_of_strdatetime == "%Y%m%d(%H%M%S)" else format_of_strdatetime

        return Parser._ignore_errors(ignore_error, "datetime", datetime.strptime, str_datetime, format_of_strdatetime)


    @staticmethod
    def to_date(str_date: str, format_of_strdate: str = "%Y%m%d", extract_numbers_only: bool = True,
                ignore_error: bool = False, none_value: str = 'None') -> date | None:
        if Parser._is_none_or_empty(str_date, none_value):
            return None

        if extract_numbers_only:
            str_date = Parser.extract_numbers(str_date)

        return Parser._ignore_errors(ignore_error, "date", datetime.strptime, str_date, format_of_strdate).date()

    @staticmethod
    def to_time(str_time: str, format_of_strtime: str = "%H%M%S", extract_numbers_only: bool = True,
                ignore_error: bool = False, none_value: str = 'None') -> time | None:
        if Parser._is_none_or_empty(str_time, none_value):
            return None

        if extract_numbers_only:
            str_time = Parser.extract_numbers(str_time)

        return Parser._ignore_errors(ignore_error, "time", datetime.strptime, str_time, format_of_strtime).time()

    @staticmethod
    def to_float(str_float: str, ignore_error: bool = False, none_value: str = 'None') -> float | None:
        if Parser._is_none_or_empty(str_float, none_value):
            return None
        return Parser._ignore_errors(ignore_error, "float", float, str_float)

    @staticmethod
    def to_integer(str_integer: str, ignore_error: bool = False, none_value: str = 'None') -> int | None:
        if Parser._is_none_or_empty(str_integer, none_value):
            return None
        return Parser._ignore_errors(ignore_error, "integer", int, str_integer)

    @staticmethod
    def to_boolean(str_boolean: str, ignore_error: bool = False, none_value: str = 'None') -> bool | None:
        if Parser._is_none_or_empty(str_boolean, none_value):
            return None
        return Parser._ignore_errors(ignore_error, "boolean", bool, str_boolean)

    @staticmethod
    def to_string(str_text: str, ignore_error: bool = False, none_value: str = 'None') -> bool | None:
        # ignore_error와 Parser._ignore_errors()는 사실상 필요없고,
        # 대신 리턴을 str_text로 하면 되나. 통일성을 위해 남겨 둠
        if Parser._is_none_or_empty(str_text, none_value):
            return None
        return Parser._ignore_errors(ignore_error, "string", str, str_text)


# 테스트 코드-------------------
if __name__ == "__main__":
    print(Parser.to_string("123"))
    print(Parser.to_string("None"))
    print(Parser.to_string(""))
    print(Parser.to_string(None))
    print(Parser.to_string("123", ignore_error=True))
    print(Parser.to_string("None", ignore_error=True))
    print(Parser.to_string("", ignore_error=True))
    print(Parser.to_string(None, ignore_error=True))