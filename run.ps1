# Windows 한글 경로 등에서 [Errno 42] 방지 - UTF-8 모드로 실행
$env:PYTHONUTF8 = "1"
python main.py
