###########################################
# Module name : cust_logger.py
# Module functions : Logger, Timer
# Written by : Yun Dae-young 
# Created at : 2025.??.??
# Updated at : 2025.11.01
# Supported by : Cursor AI
# Note : 
#        2025.11.01 : 색상 추가
#        2025.12.11 : 로그 파일 설정 추가
############################################


import logging
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from colorama import init, Fore, Style

# Windows에서 색상 지원 활성화
init(autoreset=True)

# 색상이 적용된 로그 포맷터 클래스
class ColoredFormatter(logging.Formatter):
    """레벨별 색상이 적용된 로그 포맷터"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record) -> str:
        log_color = self.COLORS.get(record.levelname, '')
        # [DEBUG] 형태로 색상 적용
        record.levelname = f"{log_color}[{record.levelname}]{Style.RESET_ALL}"
        return super().format(record)

# 기본 로거 설정
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    fmt='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False  # 부모 로거로 전파 방지


def set_logfile(path: Path, max_bytes: int = 1024 * 1024 * 5, backup_count: int = 5) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 이미 동일 파일을 쓰는 RotatingFileHandler가 붙어 있는지 확인
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", None) == str(path):
            return  # 이미 설정되어 있으면 그대로 사용

    handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )

    # 파일에는 ANSI 색상 없이 순수 텍스트 포맷 사용
    handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    logger.addHandler(handler)


class Timer:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.time_start: float = 0.0
        self.time_end: float = 0.0
        self.time_elapsed: float = 0.0

    def start(self, text: str) -> None:
        self.time_start = time.time()
        log_text : str = ""
        log_text += f"{Fore.CYAN}◈ TASK START ◈{Style.RESET_ALL} : {text}"
        self.logger.info(log_text)

    def end(self, text: str) -> None:
        self.time_end = time.time()
        self.time_elapsed = self.time_end - self.time_start
        log_text : str = ""
        log_text += f"{Fore.CYAN}◈ TASK END   ◈{Style.RESET_ALL} : {text}\n{' ' * 27}"
        log_text += f"{Fore.CYAN}◈ ELAPSED    ◈{Style.RESET_ALL} : {self.time_elapsed * 1000:.3f} ms"
        self.logger.info(log_text)

timer = Timer()