###########################################
# Module name : ssh_pool.py
# Module class : SSHConnectionPool
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.11.18
# Supported by : Cursor AI
# Note : 
#        SSH 커넥션 풀 구현
#        여러 비동기 작업에서 SSH 연결을 안전하게 공유하고 재사용하기 위한 풀
#        asyncpg.Pool 패턴을 참고하여 구현
############################################

import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from OPEN_SSH.ssh_connector import OpenSSHConnector
from CUSTOMIZED.cust_logger import logger


class SSHConnectionPool:
    """
    SSH 연결 풀 클래스
    
    여러 비동기 작업에서 SSH 연결을 안전하게 공유하고 재사용할 수 있도록 합니다.
    연결 풀을 통해 동시에 여러 작업을 병렬로 처리할 수 있습니다.
    
    사용 예시:
        # 풀 생성
        pool = SSHConnectionPool(
            hostname="example.com",
            username="user",
            port=22,
            ssh_key_path=Path("~/.ssh/id_rsa"),
            min_size=2,  # 최소 연결 수
            max_size=5   # 최대 연결 수
        )
        
        # 풀 초기화
        await pool.initialize()
        
        # 연결 획득 및 사용
        async with pool.acquire() as ssh:
            await ssh.run_command("ls -la")
            await ssh.download_files(dest, files)
        
        # 풀 종료
        await pool.close()
    """
    
    def __init__(
        self,
        hostname: str,
        username: str,
        port: int = 22,
        ssh_key_path: Optional[Path] = None,
        min_size: int = 2,
        max_size: int = 5,
        known_hosts: Optional[Path] = None
    ):
        """
        SSH 연결 풀 초기화
        
        Args:
            hostname: SSH 서버 호스트명
            username: SSH 사용자명
            port: SSH 포트 (기본값: 22)
            ssh_key_path: SSH 개인키 경로 (None이면 기본 경로 사용)
            min_size: 풀에 유지할 최소 연결 수 (기본값: 2)
            max_size: 풀에 허용할 최대 연결 수 (기본값: 5)
            known_hosts: known_hosts 파일 경로 (None이면 기본 경로 사용)
        """
        self.hostname = hostname
        self.username = username
        self.port = port
        self.ssh_key_path = ssh_key_path
        self.known_hosts = known_hosts
        self.min_size = min_size
        self.max_size = max_size
        
        # 풀 내부 상태 관리
        self._pool: asyncio.Queue[OpenSSHConnector] = asyncio.Queue(maxsize=max_size)
        self._all_connections: list[OpenSSHConnector] = []  # 모든 연결 추적
        self._created_count = 0  # 생성된 연결 수
        self._initialized = False
        self._closed = False
        self._lock = asyncio.Lock()  # 동시성 제어용 락
    
    async def initialize(self) -> None:
        """
        연결 풀 초기화
        
        min_size만큼의 연결을 미리 생성하여 풀에 추가합니다.
        이 메서드는 풀 사용 전에 반드시 호출해야 합니다.
        
        Raises:
            RuntimeError: 풀이 이미 초기화되었거나 닫혀있는 경우
        """
        if self._initialized:
            raise RuntimeError("Pool is already initialized")
        if self._closed:
            raise RuntimeError("Pool is already closed")
        
        logger.info(f"🔧 SSH 연결 풀 초기화 시작: {self.hostname}@{self.username} (min={self.min_size}, max={self.max_size})")
        
        # 최소 연결 수만큼 미리 생성
        tasks = [
            self._create_connection() 
            for _ in range(self.min_size)
        ]
        connections = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 연결만 풀에 추가
        for conn in connections:
            if isinstance(conn, Exception):
                logger.error(f"❌ 연결 생성 실패: {conn}")
                continue
            await self._pool.put(conn)
            self._all_connections.append(conn)
            self._created_count += 1
        
        self._initialized = True
        logger.info(f"✅ SSH 연결 풀 초기화 완료: {len(self._all_connections)}/{self.min_size} 연결 생성됨")
    
    async def _create_connection(self) -> OpenSSHConnector:
        """
        새로운 SSH 연결 생성
        
        Returns:
            OpenSSHConnector: 연결된 SSH 클라이언트 인스턴스
            
        Raises:
            ConnectionError: 연결 실패 시
        """
        ssh = OpenSSHConnector(
            hostname=self.hostname,
            username=self.username,
            port=self.port,
            ssh_key_path=self.ssh_key_path
        )
        
        await ssh.connect_with_private_key(
            known_hosts=self.known_hosts,
            force_connect=True
        )
        
        return ssh
    
    @asynccontextmanager
    async def acquire(self):
        """
        풀에서 연결을 획득하는 컨텍스트 매니저
        
        사용 예시:
            async with pool.acquire() as ssh:
                await ssh.run_command("ls")
        
        Yields:
            OpenSSHConnector: 사용 가능한 SSH 연결
            
        Raises:
            RuntimeError: 풀이 초기화되지 않았거나 닫혀있는 경우
            asyncio.TimeoutError: 연결을 획득할 수 없는 경우 (선택적)
        """
        if not self._initialized:
            raise RuntimeError("Pool is not initialized. Call initialize() first.")
        if self._closed:
            raise RuntimeError("Pool is closed")
        
        # 풀에서 연결 획득 시도
        ssh = await self._acquire_connection()
        
        try:
            yield ssh
        finally:
            # 사용 완료 후 풀에 반환
            await self._release_connection(ssh)
    
    async def _acquire_connection(self) -> OpenSSHConnector:
        """
        풀에서 연결을 획득하는 내부 메서드
        
        풀이 비어있고 최대 연결 수를 넘지 않았다면 새 연결을 생성합니다.
        그렇지 않으면 풀에서 기존 연결을 가져옵니다.
        
        Returns:
            OpenSSHConnector: 사용 가능한 SSH 연결
        """
        async with self._lock:
            # 풀이 비어있고 최대 연결 수를 넘지 않았다면 새 연결 생성
            if self._pool.empty() and self._created_count < self.max_size:
                logger.debug(f"📡 새 SSH 연결 생성 (현재: {self._created_count}/{self.max_size})")
                ssh = await self._create_connection()
                self._created_count += 1
                self._all_connections.append(ssh)
                return ssh
        
        # 풀에서 기존 연결 가져오기 (풀이 비어있으면 대기)
        ssh = await self._pool.get()
        
        # 연결이 유효한지 확인
        if not await ssh.is_connected():
            logger.warning(f"⚠️ 연결이 끊어짐. 새 연결 생성 중...")
            async with self._lock:
                self._created_count -= 1
                if ssh in self._all_connections:
                    self._all_connections.remove(ssh)
            
            # 새 연결 생성
            ssh = await self._create_connection()
            async with self._lock:
                self._created_count += 1
                self._all_connections.append(ssh)
        
        return ssh
    
    async def _release_connection(self, ssh: OpenSSHConnector) -> None:
        """
        사용 완료된 연결을 풀에 반환하는 내부 메서드
        
        연결이 유효한 경우에만 풀에 반환합니다.
        연결이 끊어진 경우 풀에 반환하지 않고 제거합니다.
        
        Args:
            ssh: 반환할 SSH 연결
        """
        # 연결 유효성 확인
        if not await ssh.is_connected():
            logger.warning(f"⚠️ 끊어진 연결 제거: {ssh.username}@{ssh.hostname}")
            async with self._lock:
                if ssh in self._all_connections:
                    self._all_connections.remove(ssh)
                self._created_count -= 1
            return
        
        # 풀에 반환 (풀이 가득 차 있으면 무시)
        try:
            self._pool.put_nowait(ssh)
        except asyncio.QueueFull:
            # 풀이 가득 찬 경우 연결 종료
            logger.debug(f"📡 풀이 가득 참. 연결 종료: {ssh.username}@{ssh.hostname}")
            await ssh.close()
            async with self._lock:
                if ssh in self._all_connections:
                    self._all_connections.remove(ssh)
                self._created_count -= 1
    
    async def close(self) -> None:
        """
        연결 풀 종료
        
        모든 연결을 닫고 풀을 정리합니다.
        이 메서드는 애플리케이션 종료 시 호출해야 합니다.
        """
        if self._closed:
            return
        
        self._closed = True
        logger.info(f"🔌 SSH 연결 풀 종료 시작: {len(self._all_connections)}개 연결")
        
        # 모든 연결 종료
        close_tasks = [conn.close() for conn in self._all_connections]
        await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # 상태 초기화
        self._all_connections.clear()
        self._created_count = 0
        
        # 큐 비우기
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info(f"✅ SSH 연결 풀 종료 완료")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    @property
    def size(self) -> int:
        """
        현재 풀에 있는 사용 가능한 연결 수
        
        Returns:
            int: 풀에 있는 연결 수
        """
        return self._pool.qsize()
    
    @property
    def total_connections(self) -> int:
        """
        생성된 전체 연결 수
        
        Returns:
            int: 생성된 연결 수
        """
        return self._created_count
    
    @property
    def is_closed(self) -> bool:
        """
        풀이 닫혀있는지 확인
        
        Returns:
            bool: 풀이 닫혀있으면 True
        """
        return self._closed


# 사용 예시
async def example_usage():
    """
    SSH 연결 풀 사용 예시
    
    여러 작업을 병렬로 처리하면서 연결을 효율적으로 재사용합니다.
    """
    # 풀 생성 및 초기화
    async with SSHConnectionPool(
        hostname="example.com",
        username="user",
        port=22,
        min_size=2,
        max_size=5
    ) as pool:
        
        # 여러 작업을 병렬로 실행
        async def download_files(model_name: str):
            async with pool.acquire() as ssh:
                # 각 작업이 독립적인 연결을 사용
                await ssh.run_command(f"ls /path/to/{model_name}")
                # 파일 다운로드 등 작업 수행
        
        # 병렬 실행
        tasks = [
            download_files(f"model_{i}") 
            for i in range(10)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    # 테스트 코드
    import asyncio
    
    async def test():
        async with SSHConnectionPool(
            hostname="localhost",
            username="test",
            min_size=2,
            max_size=5
        ) as pool:
            print(f"풀 크기: {pool.size}")
            print(f"전체 연결 수: {pool.total_connections}")
            
            # 여러 작업 병렬 실행
            async def task(i: int):
                async with pool.acquire() as ssh:
                    print(f"작업 {i}: 연결 획득")
                    await asyncio.sleep(0.1)
                    print(f"작업 {i}: 완료")
            
            await asyncio.gather(*[task(i) for i in range(10)])
    
    # asyncio.run(test())  # 실제 테스트 시 주석 해제

