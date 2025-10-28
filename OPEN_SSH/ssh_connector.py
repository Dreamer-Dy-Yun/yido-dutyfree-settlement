###########################################
# Module name : ssh_connector
# Module class : OpenSSHConnector
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.02
# Updated at : 2025.07.03
# Supported by : ChatGPT-4o
# Note : 
############################################

import asyncssh
import os
import posixpath
from pathlib import Path, PurePosixPath
from typing import Literal, Sequence
from datetime import datetime, timezone
from CUSTOMIZED.cust_logger import logger, timer



class OpenSSHConnector():

    def __init__(self, hostname: str, username: str, port: int = 22, ssh_key_path: Path = None):
        self.hostname: str = hostname
        self.username: str = username
        self.ssh_key_path:Path = ssh_key_path or Path.home() / ".ssh" / "id_rsa"
        self.port: int = port

        self._conn: asyncssh.SSHClientConnection | None = None
        self._sftp: asyncssh.SFTPClient | None = None
        self.filepaths_source: set[Path] = set()
        self.dir_visited: set[PurePosixPath] = set()

        self._actions:dict = {}

    async def connect_with_private_key (self, known_hosts: Path = None, force_connect: bool = False) :
        if not force_connect and await self.is_connected():
            logger.info("📡 이미 SSH 연결이 활성화되어 있습니다.")
            return self

        await self.close() 

        if not self.ssh_key_path.exists():
            raise FileNotFoundError(f"SSH Key not found: {self.ssh_key_path}")

        kh:str = str(known_hosts) if known_hosts is not None else None

        try:
            self._conn = await asyncssh.connect(
                host=self.hostname,
                port=self.port,
                username=self.username,
                client_keys=[str(self.ssh_key_path)],
                known_hosts = kh
            )
            self._sftp = await self._conn.start_sftp_client()
            self._actions = {}
            self._actions.update({"UPLOAD": (self._sftp.put, "파일 업로드", FileUploadError)})
            self._actions.update({"DOWNLOAD": (self._sftp.get, "파일 다운로드", FileDownloadError)})
            logger.info(f"✅📶 SSH 서버 연결 성공 : {self.username}@{self.hostname} : {self.port}")
        
        except Exception as e:
            logger.exception(f"❗ SSH 서버 연결 실패 : {self.username}@{self.hostname} : {self.port}")
            raise ConnectionError(f"Unable to connect to the SSH server : {e}")
        

    async def connect_with_password (self, known_hosts: Path = None, force_connect: bool = False) :
        """미구현"""
        # TODO : 필요시 구현 
        pass


    async def get_sourcefile_list_from_multiple_dirs(
        self, 
        dir_sources: list[Path], 
        depth: int = 1, 
        after : datetime = None,
        before : datetime = None, 
        criterion : Literal["Created", "Modified"] = None
        ) -> set[Path]:
        result: set[Path] = set()
        try:
            for dir_source in dir_sources:
                result.update(await self.get_sourcefile_list(dir_source, depth, after, before, criterion))
        except Exception as e:
            logger.exception(f"Error in get_sourcefile_list_from_multiple_dirs: {e}")
            raise e
        return result


    async def get_sourcefile_list(
        self, 
        dir_source: Path, 
        depth: int = 1, 
        after : datetime = None,
        before : datetime = None, 
        criterion : Literal["Created", "Modified"] = None,
        allowed_extensions: list[str] = None
        ) -> set[Path]:
        """
        지정한 디렉토리 내의 파일 및 폴더(엔트리) 경로 목록을 반환.

        매개변수:
            directory_path: 탐색을 시작할 경로
            depth: 탐색 깊이(재귀 수준)
                 0↓: 0미만은 0과 같음
                 0 : 모든 하위 디렉토리까지 전체 탐색 (제한 없음) 
                 1 : directory_path 경로의 바로 아래(1-depth)까지만 탐색
                 2 : directory_path의 하위 디렉토리(2-depth)까지 탐색
                 n : directory_path의 n 단계 하위 디렉토리까지 탐색
            after: 생성/수정일 이후 탐색
            before: 생성/수정일 이전 탐색
            criterion: 생성일 또는 수정일 기준 탐색
            allowed_extensions: 허용된 파일 확장자 목록

        반환값:
            파일 및 폴더의 경로 목록(list)

        ★ 재귀문(Recursion) 기반이므로 Stack overflow 발생 가능성 있음.
        ★ 항상 이야기 하듯 반복문이 여러모로 안전하긴 하나 오랜만에 만들어 봄
        ★ AI가 이 코드 이해 못해서 죽어라 헛소리하니 유의할 것
            (음수 입력시 0과 동일한 동작을 하는것은 의도된 것)
            특히 abs()함수 쓴건 꽤 예쁜데, AI는 계속 의도 파악이 어렵다며 쌉소리 함. 
            next_depth != 0 으로 변경.
        """
        dir_path: str = str(dir_source)
        result: set[Path] = set()
        # entries: list[str] = await self._get_entries(dir_path)
        entries: Sequence[asyncssh.SFTPName] = await self._sftp.readdir(dir_path)  
        type_file: int = 1
        type_directory: int = 2

        for entry in entries:
            if entry.filename in [".git", ".svn", ".DS_Store", ".idea", ".vscode", ".", ".."]:
                continue

            full_path = PurePosixPath(dir_path) / entry.filename
            full_path = posixpath.normpath(str(full_path))
            stat = entry.attrs
            
            if stat.type == type_file:
                match criterion:
                    case "Created":
                        if not self.is_datetime_in_period(datetime.fromtimestamp(stat.ctime, tz=timezone.utc), after, before):
                            continue
                    case "Modified":
                        if not self.is_datetime_in_period(datetime.fromtimestamp(stat.mtime, tz=timezone.utc), after, before):
                            continue
                    case _:
                        pass
                if allowed_extensions is not None:
                    if full_path.suffix.lower() not in allowed_extensions:
                        continue
                result.add(full_path)

            if stat.type == type_directory:
                if full_path in self.dir_visited:
                    # 이미 진입한 디렉토리면 pass.(바로가기등으로 인한 순환참조 대비)
                    pass
                else:
                    self.dir_visited.add(full_path)
                    next_depth = depth - 1 
                    if next_depth != 0: 
                        result.update(await self.get_sourcefile_list(full_path, next_depth, after, before, criterion))  
        # self.filepaths_source.update(result) # 적재
        return result

    def is_datetime_in_period(self, timestamp: datetime, start:datetime|None=None, end:datetime|None=None) -> bool:
        """배타적 시간 범위 검사"""
        return (start is None or start < timestamp) and (end is None or timestamp <= end)

    async def filter_sourcefiles_by_ext(self, *extensions: str) -> None:
        """파일 확장자로 필터링"""
        extensions = tuple(e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions)
        self.filepaths_source = {path for path in self.filepaths_source if path.suffix.lower() in extensions}

    async def check_if_files_exist(self, source_path_list: list[Path]) -> dict[str, bool]: 
        results = await asyncio.gather(*(self.check_if_file_exists(path) for path in source_path_list))
        return dict(results)


    async def check_if_file_exists(self, source_path: Path) -> tuple[str, bool]: 
        strpath:str = str(source_path)
        try:
            await self._sftp.stat(strpath)
            return strpath, True
        except asyncssh.SFTPNoSuchFile:
            return strpath, False


    async def download_files(self, dir_destination: Path,  target_sources: set[str] | None = None) -> dict[str, bool]:
        """모든 파일 다운로드"""
        if target_sources is None :
            target_sources = self.filepaths_source

        timer.start(f"{self.username}@{self.hostname}")
        self._make_desti_dirs(dir_destination)
        results = await asyncio.gather(
            *[self.file_transfer("DOWNLOAD", dir_destination, path) for path in target_sources],
            return_exceptions=True
        )
        timer.end(f"{self.username}@{self.hostname}")
        # 성공한 파일만 반환
        
        download_results = {path : not isinstance(result, Exception) for path, result in zip(target_sources, results)}


        return download_results

    def _make_desti_dirs(self, dir_destination: Path):
        try:
            os.makedirs(dir_destination, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"[permission denied] 다운로드 경로({dir_destination})에 디렉터리를 만들 수 없습니다. 경로 및 권한을 확인하세요.") from e
            

    async def upload_files(self, dir_destination: Path) -> None:
        """모든 파일 업로드"""
        timer.start(f"{self.username}@{self.hostname} UPLOAD")
        os.makedirs(dir_destination, exist_ok=True)
        await asyncio.gather(*[self.file_transfer("UPLOAD",dir_destination, path) for path in self.filepaths_source])
        timer.end(f"{self.username}@{self.hostname} UPLOAD")

        
    async def file_transfer(self, mode:Literal["UPLOAD", "DOWNLOAD"], dir_destination: Path, path_sourcefile: Path) -> None:
        # 쓸데 없이 과하긴 한데... 공부 할 겸 작성
        file_destination = dir_destination / path_sourcefile.name

        if mode not in self._actions:
            raise ValueError(f"지원하지 않는 전송 모드입니다: {mode}")

        func, str_mode, error_cls = self._actions[mode]

        try:
            await func(str(path_sourcefile), str(file_destination))
            logger.info(f"✅ {str_mode} 성공 : {path_sourcefile} \n{('\t')*4} → {file_destination}")
        except Exception as e:
            raise error_cls(str(path_sourcefile), str(dir_destination)) from e
        

    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._conn is not None and self._conn._transport and not self._conn._transport._closing
    
    
    async def close(self) -> None:
        """연결 종료"""
        if self._sftp:
            self._sftp.exit()
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
        logger.info(f"✅🔌 연결 종료 : {self.username}@{self.hostname}:{self.port}")


    async def __aenter__(self):
        await self.connect_with_private_key()
        return self
    

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        if exc_type is not None:
            logger.error(f"Error Occurred: {exc_type.__name__}: {exc_val}")
        return False


    async def _validate_path_accessibility(self, dir_path: Path | str = ".") -> None:
        """경로 접근 가능성 검증"""
        try:
            norm_path : str = posixpath.normpath(str(dir_path))
            _ = await self._sftp.listdir(str(norm_path))
        except Exception as e:
            logger.exception(f"cannot access the path : {norm_path}")
            raise FileAccessError(norm_path) from e
        

    async def _get_entries(self, dir_path: Path | str = ".") -> list[str]:
        """디렉토리 엔트리 목록 반환"""
        try:
            norm_path : str = posixpath.normpath(str(dir_path))
            return await self._sftp.listdir(str(norm_path))
        except Exception as e:      
            logger.exception(f"cannot access the path : {norm_path}")
            raise FileAccessError(norm_path) from e


    async def _get_file_stat(self, target_path: Path | str) -> asyncssh.SFTPAttrs:
        """파일/디렉토리 상태 정보 반환"""
        try:
            norm_path : str = posixpath.normpath(str(target_path))
            return await self._sftp.stat(str(norm_path))
        except Exception as e:
            logger.exception(f"cannot access the info : {norm_path}")
            raise FileAccessError(norm_path) from e


class SSHConnectorError(Exception):
    """Base exception for OpenSSHConnector."""
    pass


class SSHConnectionError(SSHConnectorError):
    """Raised when SSH connection fails."""
    def __init__(self, username: str, host: str, port: int):
        msg = f"[SSHConnectionError] Cannot connect to {username}@{host}:{port}"
        super().__init__(msg)


class SFTPClientError(SSHConnectorError):
    """Raised when starting SFTP client fails."""
    def __init__(self, reason: str):
        msg = f"[SFTPClientError] {reason}"
        super().__init__(msg)


class FileAccessError(SSHConnectorError):
    """Raised when a file or directory is inaccessible."""
    def __init__(self, path: str):
        msg = f"[FileAccessError] Cannot access path: {path}"
        super().__init__(msg)


class FileDownloadError(SSHConnectorError):
    """Raised when file download fails."""
    def __init__(self, source: str, dest: str):
        msg = f"[FileDownloadError] Download failed: {source} → {dest}"
        super().__init__(msg)


class FileUploadError(SSHConnectorError):
    """Raised when file upload fails."""
    def __init__(self, source: str, dest: str):
        msg = f"[FileUploadError] Upload failed: {source} → {dest}"
        super().__init__(msg)



# #########################################################################
# # === 사용 예시 === 
# #########################################################################
import asyncio                      # noqa
from CUSTOMIZED.cust_retrier import Retrier    # noqa

async def test_download(hostname:str, username:str, dir_source:Path, dir_destination:Path):
    rt = Retrier()
    async with OpenSSHConnector(hostname, username) as ssh:
        await rt.retry(lambda: ssh.get_sourcefile_list(dir_source), lambda: ssh.connect_with_private_key())

        print(ssh.filepaths_source)
        await rt.retry(lambda: ssh.filter_sourcefiles_by_ext("csv"), lambda: ssh.connect_with_private_key())
        await rt.retry(lambda: ssh.download_files(dir_destination), lambda: ssh.connect_with_private_key())


async def test_file_check(hostname:str, username:str, source_list: list[Path]):
    async with OpenSSHConnector(hostname, username) as ssh:
        return await ssh.check_if_files_exist(source_list)
    
async def main():
    # hostname = "172.30.1.68"
    # username = "user"
    # dir_source1 = Path(r"C:/users/user/Desktop/CSVs")
    # dir_source2 = Path(r"C:/users/user/Desktop/HTMLs")

    # a = await test_file_check(hostname, username, [dir_source1, dir_source2])

    # print(a)


    tasks = []
    hostname1 = "192.168.0.104"
    username1 = "knigh"
    dir_source1 = Path(rf"C:\users\{username1}\Desktop\test")
    dir_destination1 = Path(r"C:\TEST")

    # hostname2 = "172.30.1.68"
    # username2 = "user"
    # dir_source2 = Path(r"C:/users/user/Desktop/CSVs")
    # dir_destination2 = Path(r"C:\Users\윤대영\PycharmProjects\Novas_ez\TEST\testDL02")

    tasks.append(asyncio.create_task(test_download(hostname1, username1, dir_source1, dir_destination1)))
    # tasks.append(asyncio.create_task(test_download(hostname2, username2, dir_source2, dir_destination2)))

    await asyncio.gather(*tasks)  



if __name__ == "__main__":
    asyncio.run(main())