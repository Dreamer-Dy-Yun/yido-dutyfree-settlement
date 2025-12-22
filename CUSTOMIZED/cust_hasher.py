###########################################
# Module name : cust_hasher.py
# Module class : Hasher
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.08.?? (기억 안남)
# Updated at : 2025.09.23
# Supported by : cursor ai
# Note : 
#        2025.09.23 : 기존 파일(data_archiver.py)에서 분리
############################################

import hashlib
from pathlib import Path
from typing import Self

class Hasher:
    # TODO : 상황보고 멀티 프로세싱 고려
    """해싱한 문자열 비교(바이트 비교)"""
    def __init__(self) -> None:
        self._hashed_value: bytes = bytes()
        pass

    def hash_file(self, path_file: Path, ignore_errors: bool = True) -> Self:
        try:
            if not path_file.exists():
                raise FileNotFoundError(f"파일이 존재하지 않습니다: {path_file}")
            
            if not path_file.is_file():
                raise ValueError(f"파일이 아닙니다: {path_file}")

            with open(path_file, 'rb') as f:
                self._hashed_value = hashlib.sha256(f.read()).digest()
        except Exception as e:
            if ignore_errors:
                return self
            else:
                raise e
        return self
    
    @property
    def value(self) -> bytes:
        return self._hashed_value

    def equals(self, hashed_value_to_compare: bytes) -> bool:
        if not isinstance(hashed_value_to_compare, bytes) :
            raise TypeError(f"[hashed_value_to_compare] must be type of bytes. \ncurrent type : {type(hashed_value_to_compare)}")
        return self._hashed_value == hashed_value_to_compare
    
    def __str__(self) -> str:
        return str(self._hashed_value)