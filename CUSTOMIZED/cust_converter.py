###########################################
# Module name : cust_parser.py
# Module functions : StringConverter
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2024.10.xx (이전 프로젝트에서 작성)
# Updated at : 2025.09.17
# Supported by : -
# Note : 
#        2025.09.17 : 파일 분할(Customized -> cust_converter.py)
#                     ※ 클래스 명 변경 고려중
############################################

from typing import TypeAlias, Dict, List, Union, Any
from datetime import datetime
from enum import Enum

JSON: TypeAlias = Union[Dict[str, Any], List[Any]]
DB_PARAMS = Union[Dict[str, Any], List[Dict[str, Any]], None]
AIO_RESULT: TypeAlias = List[Union[Any, BaseException]]


class StringConverter:
    class From:
        @staticmethod
        def enum(variable: Enum | str):
            return variable if isinstance(variable, str) else variable.value

    # 필요시 추가