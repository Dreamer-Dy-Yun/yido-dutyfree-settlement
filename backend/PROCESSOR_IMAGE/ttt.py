# test_endswith.py

ALLOWED_EXTENSIONS = (".zip", ".tar.gz")

test_files = [
    "image.zip",
    "archive.tar.gz",
    "photo.jpg",
    "backup.ZIP",
    "data.zip ",
    "data2.ZiP",
]

def is_allowed(filename: str) -> bool:
    # endswith는 기본이 대소문자 구분이니, 확실히 하려면 소문자로 변환
    filename_normalized = filename.strip()  # 공백 제거
    return filename_normalized.lower().endswith(tuple(ext.lower() for ext in ALLOWED_EXTENSIONS))

if __name__ == "__main__":
    print(f"ALLOWED_EXTENSIONS = {ALLOWED_EXTENSIONS}")
    for name in test_files:
        print(f"{name!r:15} -> {is_allowed(name)}")
