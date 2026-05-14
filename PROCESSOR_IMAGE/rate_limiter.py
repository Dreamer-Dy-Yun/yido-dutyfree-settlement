

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """
    target_bps(초당 바이트)로 평균 처리 속도를 제한.
    interval은 속도 계산/슬립 윈도우 크기.
    """

    def __init__(self, target_bps: int, interval: float = 0.2):
        if target_bps <= 0:
            raise ValueError("target_bps must be > 0")
        self.target_bps = target_bps
        self.interval = interval
        self.budget = int(target_bps * interval)

        self._window_start = time.monotonic()
        self._used = 0

    async def consume(self, nbytes: int) -> None:
        self._used += nbytes

        if self._used < self.budget:
            return

        elapsed = time.monotonic() - self._window_start
        remain = self.interval - elapsed
        if remain > 0:
            await asyncio.sleep(remain)

        # 다음 윈도우로 리셋
        self._window_start = time.monotonic()
        self._used = 0
