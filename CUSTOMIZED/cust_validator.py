###########################################
# Module name : cust_validator.py
# Module functions : Raise
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2024.10.xx (이전 프로젝트에서 작성)
# Updated at : 2025.09.17
# Supported by : -
# Note : 
#        2025.09.17 : 파일 분할(Customized -> cust_validator.py)
############################################

from typing import TypeAlias, Dict, List, Union, Any
from datetime import datetime
from enum import Enum

JSON: TypeAlias = Union[Dict[str, Any], List[Any]]
DB_PARAMS = Union[Dict[str, any], List[Dict[str, any]], None]
AIO_RESULT: TypeAlias = List[Union[Any, BaseException]]

class Raise:
    class If:
        @staticmethod
        def empty(variable: Any, name_variable: str = "Unassigned"):

            empty_types = (str, list, dict, set)  # 빈 값 검사 대상

            match variable:
                case None:
                    raise ValueError(f"◈None Value◈\n\tName : {name_variable}")
                case _ if isinstance(variable, empty_types):
                    if not variable:  # 변수 값이 비어 있음
                        raise ValueError(f"◈Empty Value◈\n\tName : {name_variable}\n\tType : {type(variable)}")
                case bool():
                    # 없어도 되나, 명시적으로 하기 위해.
                    pass
                case datetime():
                    # datetime 타입은 유효하므로 그대로 통과
                    pass
                case _:
                    raise ValueError(f"◈Unhandled type◈\n\tName : {name_variable}\n\tType : {type(variable)}")
            return variable

        @staticmethod
        def exceed(value: float, maximum: float):
            if value > maximum:
                raise ValueError(f"◈Exceeded value◈\n\tvalue : {value}\n\tmaximum value : {maximum}")
            return value

        @staticmethod
        def below(value: float, minimum: float, value_name: str = "value"):
            if value < minimum:
                raise ValueError(f"◈Below Minimum◈\n\t{value_name} : {value}\n\tMinimum : {minimum}")
            return value

    # class Unless:
    #     pass