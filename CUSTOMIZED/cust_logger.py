import logging
import time

logging.basicConfig(
    level=logging.INFO,  # 또는 DEBUG, WARNING 등
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class Timer:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.time_start: float = 0.0
        self.time_end: float = 0.0
        self.time_elapsed: float = 0.0

    def start(self, text: str):
        self.time_start = time.time()
        self.logger.info(f"◈ TASK START ◈ : {text}")

    def end(self, text: str):
        self.time_end = time.time()
        self.time_elapsed = self.time_end - self.time_start
        self.logger.info(f"◈ TASK END ◈ : {text}\n{' ' * 30} ◈ ELAPSED ◈ : {self.time_elapsed * 1000:.3f} ms")

timer = Timer()