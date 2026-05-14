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
#        2026.02.25 : 해시 값 비교 시 문자열 비교 가능하도록 수정 등
#        2026.03.03 : overload 적용 등
#        2026.03.04 : 파일 해시 시, 청킹 추가
#        2026.05.14 : Codex - dict 입력 JSON canonical 해시 지원 추가
############################################

import hashlib
import json
from pathlib import Path
from typing import Self, Any, overload

class Hasher:
    # TODO : 상황보고 멀티 프로세싱 고려
    """해싱한 문자열 비교(바이트 비교)"""
    _encoding: str = 'utf-8'
    

    def __init__(self) -> None:
        self._hashed_value: bytes = bytes()
        pass


    def set_encoding(self, encoding: str) -> None:
        self._encoding = encoding


    @property
    def encoding(self) -> str:
        return self._encoding

    @overload
    def hash(self, contents: bytes, ignore_errors: bool = True) -> Self:
        pass

    @overload
    def hash(self, contents: str, ignore_errors: bool = True) -> Self:
        pass

    @overload
    def hash(self, contents: int, ignore_errors: bool = True) -> Self:
        pass

    @overload
    def hash(self, contents: Path, chunk_size : int = 1024 * 1024, ignore_errors: bool = True) -> Self:
        pass

    @overload
    def hash(self, contents: dict[str, Any], ignore_errors: bool = True) -> Self:
        pass

    def hash(self, contents: bytes | int | str | Path | dict[str, Any], chunk_size : int = 1024 * 1024, ignore_errors: bool = True) -> Self:
        try:
            if isinstance(contents, Path):
                return self._hash_file(contents, chunk_size)
            elif isinstance(contents, bytes):
                return self._hash_bytes(contents)
            elif isinstance(contents, str):
                return self._hash_string(contents)
            elif isinstance(contents, int):
                return self._hash_int(contents)
            elif isinstance(contents, dict):
                return self._hash_json(contents)
            else:
                raise TypeError(f"contents must be Path or bytes or str or int or dict, got {type(contents)!r}")
        except Exception as e:
            if ignore_errors:
                return self
            else:
                raise e

    def _hash_string(self, string: str) -> Self:
        self._hashed_value = hashlib.sha256(string.encode(self._encoding)).digest()
        return self
    

    def _hash_bytes(self, bytes_data: bytes) -> Self:
        # bytes는 이미 bytes이므로 encode 불필요
        self._hashed_value = hashlib.sha256(bytes_data).digest()
        return self
    

    def _hash_int(self, int: int) -> Self:
        self._hashed_value = hashlib.sha256(str(int).encode(self._encoding)).digest()
        return self

    def _hash_json(self, dict_data: dict[str, Any]) -> Self:
        json_data = json.dumps(dict_data, sort_keys=True, ensure_ascii=False, default=str)
        return self._hash_string(json_data)


    def _hash_file(self, path_file: Path, chunk_size : int = 1024 * 1024) -> Self:

        if not path_file.exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {path_file}")
        if not path_file.is_file():
            raise ValueError(f"파일이 아닙니다: {path_file}")
        hasher = hashlib.sha256()
        with open(path_file, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        
        self._hashed_value = hasher.digest()

        return self
    

    @property
    def value(self) -> bytes:
        return self._hashed_value


    def equals(self, value_to_compare: Any, is_hashed: bool = True) -> bool:
        """
        value_to_compare가 해시된 값인지 여부를 확인하고, 해시된 값이면 비교하고, 해시되지 않은 값이면 해시한 후 비교
        is_hashed == True
            value_to_compare가 bytes이면 그대로 비교
            value_to_compare가 str이면 hex 문자열을 bytes로 변환 후 비교
            value_to_compare가 그 외 타입이면 False 리턴
        is_hashed == False  -> 
            value_to_compare가 그 외 타입이면 해시 후 비교
        """
        
        encoding = self._encoding
        if is_hashed:
            if isinstance(value_to_compare, bytes):
                return self._hashed_value == value_to_compare
            elif isinstance(value_to_compare, str):
                hashed_compare = self._get_bytes_from_hex_string(value_to_compare)
                if not hashed_compare:
                    return False
                return self._hashed_value == hashed_compare
            else:
                return False
        else:
            # 해시되지 않은 값: 해시 계산 후 비교
            if isinstance(value_to_compare, bytes):
                hashed_compare = hashlib.sha256(value_to_compare).digest()
            else:
                hashed_compare = hashlib.sha256(str(value_to_compare).encode(encoding)).digest()
            return self._hashed_value == hashed_compare

    @staticmethod
    def _get_bytes_from_hex_string(s: str) -> bytes:
        try:
            return bytes.fromhex(s)
        except :
            return bytes()

    @property 
    def to_string(self) -> str:
        return str(self._hashed_value)

    @property
    def to_hex_string(self) -> str:
        return self._hashed_value.hex()

    @staticmethod
    def from_hex_string_to_bytes(hex_string: str) -> bytes:
        return bytes.fromhex(hex_string)

#TEST CODE
if __name__ == "__main__":
    hasher = Hasher()
    hasher.set_encoding("utf-8")
    hasher.hash_string("123!@#qwe")
    
    print("=== Hasher 테스트 ===")
    print(f"해시값 (bytes): {hasher.value}")
    print(f"해시값 (hex): {hasher.to_hex_string}")
    print()
    
    print("=== equals 테스트 (is_hashed=True, 기본값) ===")
    # hex 문자열로 비교
    hex_str = hasher.to_hex_string
    print(f"hex 문자열 비교: {hasher.equals(hex_str)}")  # True
    print(f"잘못된 hex 문자열: {hasher.equals('invalid_hex')}")  # False
    
    # bytes로 비교
    print(f"해시 bytes 비교: {hasher.equals(hasher.value)}")  # True
    print(f"원본 bytes 비교: {hasher.equals(b'123!@#qwe')}")  # False (원본 != 해시)
    
    # 그 외 타입
    print(f"정수 비교: {hasher.equals(123)}")  # False
    print()
    
    print("=== equals 테스트 (is_hashed=False) ===")
    # 해시되지 않은 값 비교
    print(f"원본 문자열 비교: {hasher.equals('123!@#qwe', is_hashed=False)}")  # True
    print(f"다른 문자열 비교: {hasher.equals('different', is_hashed=False)}")  # False
    
    # 정수 해시 테스트
    hasher.hash_int(123)
    print(f"정수 123 비교: {hasher.equals(123, is_hashed=False)}")  # True
    print(f"정수 456 비교: {hasher.equals(456, is_hashed=False)}")  # False
