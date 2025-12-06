import re
import sys
import os
import datetime
import win32file
import pywintypes

# ----------------------------------------------
# 1) 파일명에서 날짜/시간(YYYYMMDDHHMMSS) 추출
# ----------------------------------------------
def extract_datetime_from_filename(filename: str):
    pattern = r'(\d{14})'  # 20250904111141
    match = re.search(pattern, filename)
    if not match:
        return None

    ts = match.group(1)
    return datetime.datetime.strptime(ts, "%Y%m%d%H%M%S")


# ----------------------------------------------
# 2) CreationTime 변경 (WinAPI)
# ----------------------------------------------
def set_creation_time(path: str, dt: datetime.datetime):
    handle = win32file.CreateFile(
        path,
        win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        win32file.FILE_ATTRIBUTE_NORMAL,
        None
    )

    win_dt = pywintypes.Time(dt)
    win32file.SetFileTime(handle, win_dt, win_dt, win_dt)
    handle.close()


# ----------------------------------------------
# 3) 폴더 재귀 탐색 + 생성일 변경
# ----------------------------------------------
def process_folder(root_folder: str):
    for root, dirs, files in os.walk(root_folder):
        for fname in files:
            full_path = os.path.join(root, fname)

            dt = extract_datetime_from_filename(fname)
            if dt is None:
                continue

            try:
                set_creation_time(full_path, dt)
                print(f"[OK] {full_path} → CreationTime = {dt}")
            except Exception as e:
                print(f"[ERROR] {full_path}: {e}")


# ----------------------------------------------
# 4) 실행부
# ----------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python set_creation_time.py <대상폴더>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print("폴더가 존재하지 않습니다:", folder)
        sys.exit(1)

    process_folder(folder)
