###########################################
# Module name : test_cust_hasher.py
# 테스트 대상 : CUSTOMIZED.cust_hasher.Hasher
# Written by : Auto (Cursor AI)
###########################################

import pytest
from pathlib import Path
import tempfile
import hashlib
from CUSTOMIZED.cust_hasher import Hasher


class TestHasher:
    """Hasher 클래스 테스트"""

    def test_hasher_init(self):
        """Hasher 초기화 테스트"""
        hasher = Hasher()
        assert hasher._hashed_value == bytes()
        assert hasher.value == bytes()

    def test_hash_file_success(self):
        """hash_file() 정상 케이스 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            test_content = b"test content for hashing"
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            hasher = Hasher()
            result = hasher.hash_file(temp_path)
            
            # 반환값이 자기 자신인지 확인
            assert result is hasher
            
            # 해시값이 올바르게 계산되었는지 확인
            expected_hash = hashlib.sha256(test_content).digest()
            assert hasher.value == expected_hash
            assert hasher.value != bytes()
        finally:
            # 임시 파일 삭제
            temp_path.unlink()

    def test_hash_file_not_found(self):
        """hash_file() 파일 없음 테스트 (ignore_errors=True)"""
        hasher = Hasher()
        non_existent_path = Path("/non/existent/file.txt")
        
        # ignore_errors=True (기본값)일 때 에러 없이 반환
        result = hasher.hash_file(non_existent_path, ignore_errors=True)
        assert result is hasher
        assert hasher.value == bytes()

    def test_hash_file_not_found_raise(self):
        """hash_file() 파일 없음 테스트 (ignore_errors=False)"""
        hasher = Hasher()
        non_existent_path = Path("/non/existent/file.txt")
        
        # ignore_errors=False일 때 FileNotFoundError 발생
        with pytest.raises(FileNotFoundError, match="파일이 존재하지 않습니다"):
            hasher.hash_file(non_existent_path, ignore_errors=False)

    def test_hash_file_not_a_file(self):
        """hash_file() 파일이 아닌 경우 테스트"""
        hasher = Hasher()
        # 디렉토리 경로 사용
        dir_path = Path(tempfile.gettempdir())
        
        with pytest.raises(ValueError, match="파일이 아닙니다"):
            hasher.hash_file(dir_path, ignore_errors=False)

    def test_hash_file_not_a_file_ignore_errors(self):
        """hash_file() 파일이 아닌 경우 테스트 (ignore_errors=True)"""
        hasher = Hasher()
        dir_path = Path(tempfile.gettempdir())
        
        # ignore_errors=True일 때 에러 없이 반환
        result = hasher.hash_file(dir_path, ignore_errors=True)
        assert result is hasher

    def test_hash_file_empty_file(self):
        """hash_file() 빈 파일 테스트"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            hasher = Hasher()
            hasher.hash_file(temp_path)
            
            # 빈 파일의 해시값
            expected_hash = hashlib.sha256(b"").digest()
            assert hasher.value == expected_hash
        finally:
            temp_path.unlink()

    def test_hash_file_large_file(self):
        """hash_file() 큰 파일 테스트"""
        # 1MB 크기의 테스트 파일 생성
        large_content = b"x" * (1024 * 1024)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(large_content)
            temp_path = Path(f.name)
        
        try:
            hasher = Hasher()
            hasher.hash_file(temp_path)
            
            expected_hash = hashlib.sha256(large_content).digest()
            assert hasher.value == expected_hash
        finally:
            temp_path.unlink()

    def test_value_property(self):
        """value 프로퍼티 테스트"""
        hasher = Hasher()
        assert hasher.value == bytes()
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test")
            temp_path = Path(f.name)
        
        try:
            hasher.hash_file(temp_path)
            assert isinstance(hasher.value, bytes)
            assert len(hasher.value) == 32  # SHA256은 32바이트
        finally:
            temp_path.unlink()

    def test_equals_same_hash(self):
        """equals() 같은 해시값 비교 테스트"""
        content = b"test content"
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            hasher = Hasher()
            hasher.hash_file(temp_path)
            
            expected_hash = hashlib.sha256(content).digest()
            assert hasher.equals(expected_hash) is True
        finally:
            temp_path.unlink()

    def test_equals_different_hash(self):
        """equals() 다른 해시값 비교 테스트"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            hasher = Hasher()
            hasher.hash_file(temp_path)
            
            different_hash = hashlib.sha256(b"different content").digest()
            assert hasher.equals(different_hash) is False
        finally:
            temp_path.unlink()

    def test_equals_type_error(self):
        """equals() 타입 에러 테스트"""
        hasher = Hasher()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test")
            temp_path = Path(f.name)
        
        try:
            hasher.hash_file(temp_path)
            
            # bytes가 아닌 타입 전달 시 TypeError 발생
            with pytest.raises(TypeError, match="must be type of bytes"):
                hasher.equals("not bytes")
            
            with pytest.raises(TypeError, match="must be type of bytes"):
                hasher.equals(123)
        finally:
            temp_path.unlink()

    def test_equals_empty_hash(self):
        """equals() 빈 해시값 비교 테스트"""
        hasher = Hasher()
        # 해시하지 않은 상태에서 equals 호출
        assert hasher.equals(bytes()) is True
        
        # 다른 빈 바이트와 비교
        assert hasher.equals(b"") is True

    def test_str_representation(self):
        """__str__() 테스트"""
        hasher = Hasher()
        str_repr = str(hasher)
        assert isinstance(str_repr, str)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test")
            temp_path = Path(f.name)
        
        try:
            hasher.hash_file(temp_path)
            str_repr = str(hasher)
            assert isinstance(str_repr, str)
            assert len(str_repr) > 0
        finally:
            temp_path.unlink()

    def test_hash_file_multiple_calls(self):
        """hash_file() 여러 번 호출 테스트"""
        content1 = b"first content"
        content2 = b"second content"
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f1:
            f1.write(content1)
            temp_path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f2:
            f2.write(content2)
            temp_path2 = Path(f2.name)
        
        try:
            hasher = Hasher()
            
            # 첫 번째 파일 해시
            hasher.hash_file(temp_path1)
            hash1 = hasher.value
            
            # 두 번째 파일 해시 (덮어쓰기)
            hasher.hash_file(temp_path2)
            hash2 = hasher.value
            
            assert hash1 != hash2
            assert hash2 == hashlib.sha256(content2).digest()
        finally:
            temp_path1.unlink()
            temp_path2.unlink()

