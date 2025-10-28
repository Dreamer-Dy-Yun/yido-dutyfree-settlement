import hashlib

def hash_file(filepath):
    """파케이 파일의 바이트 전체를 SHA256 해시로 반환합니다."""
    with open(filepath, 'rb') as f:
        file_bytes = f.read()
    return hashlib.sha256(file_bytes).hexdigest()

# 사용 예시
parquet_path = 'test.parquet'
print(hash_file(parquet_path))