###########################################
# Module name : test_cust_hasher.py
# Module functions : Hasher 클래스 테스트
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.25
# Supported by : Cursor AI
# Note : cust_hasher.py의 Hasher 클래스 테스트
############################################

import pytest
import hashlib
import tempfile
from pathlib import Path
from CUSTOMIZED.cust_hasher import Hasher


class TestHasher:
    """Hasher 클래스 테스트"""

    def test_hash_string(self):
        """문자열 해시 테스트"""
        hasher = Hasher()
        hasher.hash("test123")
        
        expected = hashlib.sha256("test123".encode('utf-8')).digest()
        assert hasher.value == expected

    def test_hash_bytes(self):
        """bytes 해시 테스트"""
        hasher = Hasher()
        test_bytes = b"test123"
        hasher.hash(test_bytes)
        
        expected = hashlib.sha256(test_bytes).digest()
        assert hasher.value == expected

    def test_hash_int(self):
        """정수 해시 테스트"""
        hasher = Hasher()
        hasher.hash(123)
        
        expected = hashlib.sha256("123".encode('utf-8')).digest()
        assert hasher.value == expected

    def test_hash_file(self):
        """파일 해시 테스트"""
        hasher = Hasher()
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test file content")
            temp_path = Path(f.name)
        
        try:
            hasher.hash(temp_path)
            expected = hashlib.sha256(b"test file content").digest()
            assert hasher.value == expected
        finally:
            temp_path.unlink()

    def test_hash_file_not_exists(self):
        """존재하지 않는 파일 해시 테스트 (ignore_errors=True)"""
        hasher = Hasher()
        fake_path = Path("nonexistent_file.txt")
        
        hasher.hash(fake_path, ignore_errors=True)
        # 에러 무시 시 빈 bytes 반환
        assert hasher.value == bytes()

    def test_equals_bytes_is_hashed_true(self):
        """equals: bytes 비교 (is_hashed=True)"""
        hasher = Hasher()
        hasher.hash("test123")
        
        # 같은 해시 bytes와 비교
        assert hasher.equals(hasher.value, is_hashed=True) == True
        
        # 다른 해시 bytes와 비교
        other_hasher = Hasher()
        other_hasher.hash("different")
        assert hasher.equals(other_hasher.value, is_hashed=True) == False

    def test_equals_hex_string_is_hashed_true(self):
        """equals: hex 문자열 비교 (is_hashed=True)"""
        hasher = Hasher()
        hasher.hash("test123")
        
        # hex 문자열로 변환 후 비교
        hex_str = hasher.to_hex_string
        assert hasher.equals(hex_str, is_hashed=True) == True
        
        # 잘못된 hex 문자열
        assert hasher.equals("invalid_hex", is_hashed=True) == False
        
        # 빈 문자열
        assert hasher.equals("", is_hashed=True) == False

    def test_equals_other_type_is_hashed_true(self):
        """equals: 그 외 타입 비교 (is_hashed=True)"""
        hasher = Hasher()
        hasher.hash("test123")
        
        # int 타입
        assert hasher.equals(123, is_hashed=True) == False
        
        # list 타입
        assert hasher.equals([1, 2, 3], is_hashed=True) == False

    def test_equals_is_hashed_false(self):
        """equals: 해시되지 않은 값 비교 (is_hashed=False)"""
        hasher = Hasher()
        hasher.hash("test123")
        
        # 같은 문자열 비교
        assert hasher.equals("test123", is_hashed=False) == True
        
        # 다른 문자열 비교
        assert hasher.equals("different", is_hashed=False) == False
        
        # 정수 비교
        hasher.hash(123)
        assert hasher.equals(123, is_hashed=False) == True
        assert hasher.equals(456, is_hashed=False) == False

    def test_to_hex_string(self):
        """hex 문자열 변환 테스트"""
        hasher = Hasher()
        hasher.hash("test123")
        
        hex_str = hasher.to_hex_string
        assert isinstance(hex_str, str)
        assert len(hex_str) == 64  # SHA-256은 32 bytes = 64 hex 문자
        
        # 다시 bytes로 변환 가능한지 확인
        restored = bytes.fromhex(hex_str)
        assert restored == hasher.value

    def test_from_hex_string_to_bytes(self):
        """hex 문자열을 bytes로 변환 테스트"""
        test_hex = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        result = Hasher.from_hex_string_to_bytes(test_hex)
        
        assert isinstance(result, bytes)
        assert len(result) == 32  # SHA-256은 32 bytes

    def test_set_encoding(self):
        """인코딩 설정 테스트"""
        hasher = Hasher()
        hasher.set_encoding("utf-8")
        assert hasher.encoding == "utf-8"
        
        hasher.set_encoding("latin-1")
        assert hasher.encoding == "latin-1"

    def test_encoding_property(self):
        """인코딩 프로퍼티 테스트"""
        hasher = Hasher()
        assert hasher.encoding == "utf-8"  # 기본값
        
        hasher.set_encoding("utf-16")
        assert hasher.encoding == "utf-16"

    def test_equals_default_is_hashed(self):
        """equals 기본값 테스트 (is_hashed=True가 기본값)"""
        hasher = Hasher()
        hasher.hash("test123")
        
        # 기본값은 is_hashed=True
        hex_str = hasher.to_hex_string
        assert hasher.equals(hex_str) == True  # 기본값 사용
        
        # 해시되지 않은 값은 False
        assert hasher.equals("test123") == False  # hex 문자열이 아니므로 False

    def test_chaining(self):
        """메서드 체이닝 테스트"""
        hasher = Hasher()
        result = hasher.hash("test").hash(123).hash("final")
        
        assert result is hasher
        assert hasher.value == hashlib.sha256("final".encode('utf-8')).digest()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
