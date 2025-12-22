###########################################
# Module name : ssh_connector
# Module class : OpenSSHConnector
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.02
# Updated at : 2025.07.03
# Supported by : ChatGPT-4o
# Note : 
#        TODO : 시간나면 Queue 로 비동기로 시도 할 것.(처리속도 >> 네트워크 속도 이므로 현재로써는 문제 없을 듯)
#        2025.11.12 : 함수 명 변경 (is_datetime_in_period -> is_datetime_in_range)
############################################

import asyncssh
import os
import posixpath
import uuid
from pathlib import Path, PurePosixPath
from typing import Literal, Sequence, Self
from datetime import datetime
from CUSTOMIZED.cust_logger import logger, timer
import pandas as pd
import asyncio

class OpenSSHConnector():

    def __init__(self, hostname: str, username: str, port: int = 22, ssh_key_path: Path | None = None):
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
            return self
        
        except Exception as e:
            # logger.exception(f"❗ SSH 서버 연결 실패 : {self.username}@{self.hostname} : {self.port}")  #에러 트레이스 필요할 때.
            logger.error(f"❗ SSH 서버 연결 실패 : {self.username}@{self.hostname} : {self.port} - {type(e).__name__}: {e}")
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
        allowed_extensions: list[str] = None,
        excluded_extensions: list[str] = [".git", ".svn", ".DS_Store", ".idea", ".vscode", ".", ".."]
        ) -> set[Path]:
        """
        ☆ 비효율. 로직상 수차례 통신 필요. 사용하지 않을 예정 ☆
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

        ts_start: float | None = after.timestamp() if after is not None else None
        ts_end: float | None = before.timestamp() if before is not None else None

        for entry in entries:
            if entry.filename in excluded_extensions:
                continue

            full_path = Path((dir_source / entry.filename).as_posix())
            stat = entry.attrs
            
            if stat.type == type_file:
                match criterion:
                    case "Created":
                        if not self.is_timestamp_in_range(stat.ctime, ts_start, ts_end):
                            continue
                    case "Modified":
                        if not self.is_timestamp_in_range(stat.mtime, ts_start, ts_end):
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
        self.filepaths_source.update(result) # 적재
        return result


    def is_datetime_in_range(self, timestamp: datetime, start:datetime|None=None, end:datetime|None=None) -> bool:
        """시간 범위 검사"""
        return (start is None or start < timestamp) and (end is None or timestamp <= end)
    
    
    def is_timestamp_in_range(self, timestamp: float, ts_start:float|None=None, ts_end:float|None=None) -> bool:
        """시간 범위 검사(타임스탬프 기준)"""
        return (ts_start is None or ts_start < timestamp) and (ts_end is None or timestamp <= ts_end)
    

    async def filter_sourcefiles_by_ext(self, *extensions: str) -> None:
        """파일 확장자로 필터링 (가급적 이것 말고 PowerShell/Linux 명령어 사용 할 것)"""
        extensions = tuple(e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions)
        filepaths_source = self.filepaths_source
        self.filepaths_source = {path for path in filepaths_source if Path(path).suffix.lower() in extensions}
        return self.filepaths_source

    async def check_if_files_exist(self, source_path_list: list[Path]) -> dict[str, bool]: 
        results = await asyncio.gather(*(self.check_if_file_exists(path) for path in source_path_list))
        return dict (results)

    async def check_if_file_exists(self, source_path: Path) -> tuple[str, bool]: 
        strpath:str = str(source_path)
        try:
            await self._sftp.stat(strpath)
            return strpath, True
        except asyncssh.SFTPNoSuchFile:
            return strpath, False


    async def download_files(
        self, 
        df: pd.DataFrame, 
        colname_source: str = "path_full_source", 
        colname_destination: str = "path_full_destination", 
        colname_is_retrieved: str = "is_retrieved",
        task_name: str = None,
        ) -> pd.DataFrame:
        """모든 파일 다운로드"""

        if not task_name:
            task_name = uuid.uuid4()

        msg: str = f"{self.username}@{self.hostname} (Task ID: {task_name})"

        timer.start(msg)
        logger.debug(f"Downloading files information: \n{df}")  # DEBUG
        results = await asyncio.gather(
            *[self.file_transfer("DOWNLOAD", getattr(row, colname_source), getattr(row, colname_destination)) for row in df.itertuples(index=False)],
            return_exceptions=True
        )
        timer.end(msg)
        # 성패 기재하여 반환
        df[colname_is_retrieved] = [not isinstance(result, Exception) for result in results]
        # df[colname_retrieved_at] = [datetime.now() if not isinstance(result, Exception) else None for result in results]
        return df


    async def download_single_file(self, fullpath_sourcefile: Path, fullpath_destination: Path, ) -> dict[str, bool]:
        """파일 다운로드"""
        self._make_desti_dirs(fullpath_destination.parent)
        result = await self.file_transfer("DOWNLOAD", fullpath_sourcefile, fullpath_destination)
        return result


    def _make_desti_dirs(self, dir_destination: Path) -> None:
        try:
            os.makedirs(dir_destination, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"[permission denied] 다운로드 경로({dir_destination})에 디렉터리를 만들 수 없습니다. 경로 및 권한을 확인하세요.") from e
            

    async def upload_files(self, df: pd.DataFrame, colname_source: str = "fullpath_source", colname_destination: str = "fullpath_destination") -> None:
        """모든 파일 업로드"""
        timer.start(f"{self.username}@{self.hostname} UPLOAD")
        await asyncio.gather(*[self.file_transfer("UPLOAD", getattr(row, colname_source), getattr(row, colname_destination)) for row in df.itertuples(index=False)], return_exceptions=True)
        timer.end(f"{self.username}@{self.hostname} UPLOAD")

        
    async def file_transfer(self, mode:Literal["UPLOAD", "DOWNLOAD"], fulpath_sourcefile: Path, fullpath_destination: Path, ) -> None:
        if mode not in self._actions:
            raise ValueError(f"지원하지 않는 전송 모드입니다: {mode}")

        func, str_mode, error_cls = self._actions[mode]
        tab_indent = '\t' * 4

        try:
            logger.info(f"✅ {str_mode} 시작 : {fulpath_sourcefile} \n{tab_indent} → {fullpath_destination}")
            await func(str(fulpath_sourcefile), str(fullpath_destination))
            logger.info(f"✅ {str_mode} 성공 : {fulpath_sourcefile} \n{tab_indent} → {fullpath_destination}")
        except Exception as e:
            raise error_cls(str(fulpath_sourcefile), str(fullpath_destination)) from e
        # finally:
        #     pass
        

    async def get_connection(self) -> asyncssh.SSHClientConnection:
        return self._conn


    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._conn is not None and self._conn._transport and not self._conn._transport._closing
    
    
    async def close(self) -> None:
        """연결 종료"""
        try :
            if self._sftp:
                self._sftp.exit()
            if self._conn:
                self._conn.close()
                await self._conn.wait_closed()
            logger.info(f"✅🔌 연결 종료 : {self.username}@{self.hostname}:{self.port}")
        except Exception as e:
            logger.exception(f"Error in close: {e}")
        

    async def __aenter__(self) -> Self:
        await self.connect_with_private_key()
        return self
    

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
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


    async def run_command(self, command: str) -> asyncssh.SSHCompletedProcess:
        if not await self.is_connected():
            raise SSHConnectionError(self.username, self.hostname, self.port)
        try:
            result = await self._conn.run(command)
            return result
        except Exception as e:
            logger.exception(f"SSH command execution failed: {command}")
            raise SSHCommandError(command, str(e)) from e

    def test_run(self, command: str) -> asyncssh.SSHCompletedProcess:
        """
        동기적으로 명령을 실행하는 테스트 메서드.
        이미 실행 중인 이벤트 루프가 있으면 RuntimeError를 발생시킵니다.
        비동기 컨텍스트에서는 직접 await self.run_command(command)를 사용하세요.
        """
        try:
            # 이미 실행 중인 루프가 있는지 확인
            loop = asyncio.get_running_loop()
            # 실행 중인 루프가 있으면 (get_running_loop()가 성공하면) 예외 발생
            raise RuntimeError(
                "test_run() cannot be called from a running event loop. "
                "In async context, use 'await self.run_command(command)' instead."
            )
        except RuntimeError as e:
            # get_running_loop()가 RuntimeError를 발생시킨 경우 (실행 중인 루프가 없음)
            # 에러 메시지가 "no running event loop"인 경우에만 새 루프를 생성하여 실행
            error_msg = str(e).lower()
            if "no running event loop" in error_msg or "no current event loop" in error_msg:
                return asyncio.run(self.run_command(command))
            # 다른 RuntimeError는 그대로 전파 (위에서 발생시킨 에러)
            raise


# Exception Classes

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


class SSHCommandError(SSHConnectorError):
    """Raised when an SSH command execution fails."""
    def __init__(self, command: str, reason: str | None = None):
        msg = f"[SSHCommandError] Command failed: {command}"
        if reason:
            msg += f" | Reason: {reason}"
        super().__init__(msg)

# #########################################################################
# # === 사용 예시 === 
# #########################################################################
import asyncio                      # noqa
from CUSTOMIZED.cust_retrier import Retrier    # noqa
from CUSTOMIZED import cust_powershell as ps    # noqa
import json    # noqa
import pandas as pd    # noqa
async def test_download(hostname:str, username:str, dir_source:Path, dir_destination:Path):
    rt = Retrier()
    async with OpenSSHConnector(hostname, username) as ssh:
        await rt.retry(lambda: ssh.get_sourcefile_list(dir_source), lambda: ssh.connect_with_private_key())
        # Windows PowerShell 명령어 사용

        cmd_source : str = ""
        cmd_selection : str = ""
        cmd_condition : str = ""

        cmd_source = ps.Get_ChildItem(Path(f"C:/Users/admin/Desktop/Report/DB92-05608A/2025/09/09")).entry("file").recursive(True).build()
        cmd_selection = ps.Select().full_name().creation_time(alias="CreationTime",with_milliseconds=True).build()
        cmd_condition_1 : str = ps.Filter.after(datetime(2025, 9, 5, 11, 19, 16), "creation").build()
        cmd_condition_2 : str = ps.Filter.by_extension("csv").build()
        cmd_condition = cmd_condition_1 & cmd_condition_2
        cmd_consumer : str = ps.ToJson().compress().build()
        ps_cmd = ps.PSCommand().set_source(cmd_source).set_condition(cmd_condition).set_selection(cmd_selection).set_consumer(cmd_consumer).build()
        result = await ssh.run_command(ps_cmd)
        # print(result.stdout)
        list_result = []


        json_result = json.loads(result.stdout)
        df_result = pd.DataFrame(json_result)
 
   

        cmd_source : str = ps.Get_ChildItem(Path(f"C:/Users/admin/Desktop/Report")).entry("directory").build()
        cmd_selection : str = ps.Select().name().full_name().creation_time(with_milliseconds=True).build()
        cmd_condition : str = ps.Filter.until(datetime(2025, 11, 14, 11, 19, 16), "creation").build()
        ps_cmd = ps.PSCommand().set_source(cmd_source).set_condition(cmd_condition).set_selection(cmd_selection).build()
        result = await ssh.run_command(ps_cmd)
        print(result.stdout)

        
        dir_path_str = dir_source.as_posix()
        cmd = f'powershell -Command "Get-ChildItem -Path \\"{dir_path_str}\\" -File -Recurse | Select-Object -ExpandProperty FullName"'
        result = await ssh.run_command(cmd)
        print(result.stdout)



        print(ssh.filepaths_source)
        await rt.retry(lambda: ssh.filter_sourcefiles_by_ext("txt"), lambda: ssh.connect_with_private_key())
        await rt.retry(lambda: ssh.__download_files(dir_destination), lambda: ssh.connect_with_private_key())


async def test_file_check(hostname:str, username:str, source_list: list[Path]):
    async with OpenSSHConnector(hostname, username) as ssh:
        return await ssh.check_if_files_exist(source_list)


async def main():

    tasks = []
    hostname1 = "172.30.1.72"
    username1 = "admin"
    dir_source1 = Path(f"C:/Users/{username1}/Desktop/Report")
    dir_destination1 = Path(r"C:\TEST")

    tasks.append(asyncio.create_task(test_download(hostname1, username1, dir_source1, dir_destination1)))
    # tasks.append(asyncio.create_task(test_download(hostname2, username2, dir_source2, dir_destination2)))

    await asyncio.gather(*tasks)  



if __name__ == "__main__":
    asyncio.run(main())