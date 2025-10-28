from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Callable, Awaitable, Any
import asyncio
import os
import asyncssh


# ===== 전략 패턴: RetryPolicy =====
class RetryPolicy(ABC):
    @abstractmethod
    async def run(self, func: Callable[[], Awaitable[Any]]) -> Any:
        pass


class FixedRetry(RetryPolicy):
    def __init__(self, attempts: int = 3, delay: float = 1.0):
        self.attempts = attempts
        self.delay = delay

    async def run(self, func: Callable[[], Awaitable[Any]]) -> Any:
        for attempt in range(1, self.attempts + 1):
            try:
                return await func()
            except Exception as e:
                if attempt == self.attempts:
                    raise
                await asyncio.sleep(self.delay)


# ===== 추상 계층: FileSource =====
class FileSource(ABC):
    @abstractmethod
    async def list_files(self, base_path: Path, depth: int = 1) -> List[Path]:
        pass


class SFTPSource(FileSource):
    def __init__(self, sftp_client: asyncssh.SFTPClient):
        self._sftp = sftp_client
        self._visited = set()

    async def list_files(self, base_path: Path, depth: int = 1) -> List[Path]:
        result = []
        entries = await self._sftp.listdir(str(base_path))

        for entry in entries:
            full_path = base_path / entry
            stat = await self._sftp.stat(str(full_path))

            if stat.type == asyncssh.SFTPFileType.REGULAR:
                result.append(full_path)
            elif stat.type == asyncssh.SFTPFileType.DIRECTORY:
                if full_path in self._visited:
                    continue
                self._visited.add(full_path)
                next_depth = depth - 1
                if next_depth < 0 or depth == 0:
                    result.extend(await self.list_files(full_path, 0))
                elif next_depth > 0:
                    result.extend(await self.list_files(full_path, next_depth))
        return result


class LocalFileSource(FileSource):
    def __init__(self):
        self._visited = set()

    async def list_files(self, base_path: Path, depth: int = 1) -> List[Path]:
        result = []

        for entry in os.scandir(base_path):
            path = Path(entry.path)
            if entry.is_file():
                result.append(path)
            elif entry.is_dir():
                if path in self._visited:
                    continue
                self._visited.add(path)
                next_depth = depth - 1
                if next_depth < 0 or depth == 0:
                    result.extend(await self.list_files(path, 0))
                elif next_depth > 0:
                    result.extend(await self.list_files(path, next_depth))
        return result


# ===== 조합자 계층: FileFetcher =====
class FileFetcher:
    def __init__(self, source: FileSource, retry_policy: RetryPolicy = None):
        self.source = source
        self.retry_policy = retry_policy or FixedRetry()

    async def fetch(self, path: Path, depth: int = 1) -> List[Path]:
        return await self.retry_policy.run(lambda: self.source.list_files(path, depth))
