###########################################
# Module name : test_ssh_connector.py
# 테스트 대상 : OPEN_SSH.ssh_connector.OpenSSHConnector
# Written by : GPT Test Template
# Note       : 실제 동작하는 단위 테스트 (Mock 활용)
###########################################

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from OPEN_SSH.ssh_connector import (
    OpenSSHConnector,
    SSHConnectionError,
    FileDownloadError,
    FileUploadError,
    SSHCommandError
)


class TestOpenSSHConnector:
    """OpenSSHConnector 클래스에 대한 단위 테스트"""

    @pytest.fixture
    def ssh_connector(self):
        """OpenSSHConnector 인스턴스 생성"""
        return OpenSSHConnector(
            hostname="192.168.1.1",
            username="test_user",
            port=22,
            ssh_key_path=Path("/path/to/key")
        )

    def test_init(self, ssh_connector):
        """초기화 테스트"""
        assert ssh_connector.hostname == "192.168.1.1"
        assert ssh_connector.username == "test_user"
        assert ssh_connector.port == 22
        assert ssh_connector.ssh_key_path == Path("/path/to/key")
        assert ssh_connector._conn is None
        assert ssh_connector._sftp is None
        assert ssh_connector.filepaths_source == set()

    def test_init_default_key_path(self):
        """기본 SSH 키 경로 테스트"""
        connector = OpenSSHConnector("192.168.1.1", "test_user")
        assert connector.ssh_key_path is not None

    @pytest.mark.asyncio
    async def test_connect_with_private_key_success(self, ssh_connector):
        """connect_with_private_key() 성공 테스트"""
        mock_conn = AsyncMock()
        mock_sftp = AsyncMock()
        
        with patch('OPEN_SSH.ssh_connector.asyncssh.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_conn
            mock_conn.start_sftp_client = AsyncMock(return_value=mock_sftp)
            
            # SSH 키 파일 존재 Mock
            with patch.object(Path, 'exists', return_value=True):
                result = await ssh_connector.connect_with_private_key()
            
            assert result is ssh_connector
            assert ssh_connector._conn == mock_conn
            assert ssh_connector._sftp == mock_sftp
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_private_key_already_connected(self, ssh_connector):
        """connect_with_private_key() 이미 연결된 경우"""
        mock_conn = AsyncMock()
        mock_conn._transport._closing = False
        ssh_connector._conn = mock_conn
        
        with patch.object(ssh_connector, 'is_connected', return_value=True):
            result = await ssh_connector.connect_with_private_key(force_connect=False)
        
        assert result is ssh_connector

    @pytest.mark.asyncio
    async def test_connect_with_private_key_file_not_found(self, ssh_connector):
        """connect_with_private_key() SSH 키 파일 없음"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="SSH Key not found"):
                await ssh_connector.connect_with_private_key()

    @pytest.mark.asyncio
    async def test_connect_with_private_key_connection_error(self, ssh_connector):
        """connect_with_private_key() 연결 실패"""
        with patch.object(Path, 'exists', return_value=True), \
             patch('OPEN_SSH.ssh_connector.asyncssh.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(ConnectionError):
                await ssh_connector.connect_with_private_key()

    @pytest.mark.asyncio
    async def test_is_connected_true(self, ssh_connector):
        """is_connected() 연결된 경우"""
        mock_conn = AsyncMock()
        mock_conn._transport._closing = False
        ssh_connector._conn = mock_conn
        
        result = await ssh_connector.is_connected()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_connected_false(self, ssh_connector):
        """is_connected() 연결 안 된 경우"""
        ssh_connector._conn = None
        
        result = await ssh_connector.is_connected()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, ssh_connector):
        """close() 테스트"""
        # 실제 코드에서 exit()와 close()는 await 없이 호출됨
        mock_sftp = MagicMock()
        mock_sftp.exit = MagicMock()  # exit()는 동기 메서드
        mock_conn = MagicMock()
        mock_conn.close = MagicMock()  # close()는 동기 메서드
        mock_conn.wait_closed = AsyncMock()  # wait_closed()만 비동기
        ssh_connector._sftp = mock_sftp
        ssh_connector._conn = mock_conn
        
        await ssh_connector.close()
        
        mock_sftp.exit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_conn.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_connection(self, ssh_connector):
        """close() 연결이 없는 경우"""
        ssh_connector._sftp = None
        ssh_connector._conn = None
        
        # 에러 없이 실행되어야 함
        await ssh_connector.close()

    def test_is_datetime_in_range(self, ssh_connector):
        """is_datetime_in_range() 테스트"""
        timestamp = datetime(2025, 1, 15, 12, 0, 0)
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)
        
        assert ssh_connector.is_datetime_in_range(timestamp, start, end) is True
        assert ssh_connector.is_datetime_in_range(timestamp, start, None) is True
        assert ssh_connector.is_datetime_in_range(timestamp, None, end) is True
        assert ssh_connector.is_datetime_in_range(timestamp, None, None) is True

    def test_is_datetime_in_range_out_of_range(self, ssh_connector):
        """is_datetime_in_range() 범위 밖"""
        timestamp = datetime(2025, 2, 1)
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)
        
        assert ssh_connector.is_datetime_in_range(timestamp, start, end) is False

    def test_is_timestamp_in_range(self, ssh_connector):
        """is_timestamp_in_range() 테스트"""
        timestamp = 1705312800.0  # 2025-01-15 12:00:00
        ts_start = 1704067200.0   # 2025-01-01 00:00:00
        ts_end = 1706659200.0     # 2025-01-31 00:00:00
        
        assert ssh_connector.is_timestamp_in_range(timestamp, ts_start, ts_end) is True
        assert ssh_connector.is_timestamp_in_range(timestamp, ts_start, None) is True
        assert ssh_connector.is_timestamp_in_range(timestamp, None, ts_end) is True

    @pytest.mark.asyncio
    async def test_filter_sourcefiles_by_ext(self, ssh_connector):
        """filter_sourcefiles_by_ext() 테스트"""
        ssh_connector.filepaths_source = {
            Path("file1.txt"),
            Path("file2.csv"),
            Path("file3.txt"),
            Path("file4.json")
        }
        
        await ssh_connector.filter_sourcefiles_by_ext("txt", "csv")
        
        # txt 2개(file1, file3) + csv 1개(file2) = 3개
        assert len(ssh_connector.filepaths_source) == 3
        assert Path("file1.txt") in ssh_connector.filepaths_source
        assert Path("file2.csv") in ssh_connector.filepaths_source
        assert Path("file3.txt") in ssh_connector.filepaths_source
        assert Path("file4.json") not in ssh_connector.filepaths_source

    @pytest.mark.asyncio
    async def test_check_if_file_exists_true(self, ssh_connector):
        """check_if_file_exists() 파일 존재"""
        mock_sftp = AsyncMock()
        mock_sftp.stat = AsyncMock()
        ssh_connector._sftp = mock_sftp
        
        result = await ssh_connector.check_if_file_exists(Path("/path/to/file.txt"))
        
        assert result[0] == str(Path("/path/to/file.txt"))
        assert result[1] is True

    @pytest.mark.asyncio
    async def test_check_if_file_exists_false(self, ssh_connector):
        """check_if_file_exists() 파일 없음"""
        from asyncssh import SFTPNoSuchFile
        
        mock_sftp = AsyncMock()
        mock_sftp.stat = AsyncMock(side_effect=SFTPNoSuchFile("File not found"))
        ssh_connector._sftp = mock_sftp
        
        result = await ssh_connector.check_if_file_exists(Path("/path/to/nonexistent.txt"))
        
        assert result[1] is False

    @pytest.mark.asyncio
    async def test_check_if_files_exist(self, ssh_connector):
        """check_if_files_exist() 여러 파일"""
        mock_sftp = AsyncMock()
        mock_sftp.stat = AsyncMock()
        ssh_connector._sftp = mock_sftp
        
        files = [Path("/file1.txt"), Path("/file2.txt")]
        result = await ssh_connector.check_if_files_exist(files)
        
        assert len(result) == 2
        assert all(result.values())

    @pytest.mark.asyncio
    async def test_file_transfer_download_success(self, ssh_connector):
        """file_transfer() DOWNLOAD 성공"""
        mock_sftp = AsyncMock()
        mock_sftp.get = AsyncMock()
        ssh_connector._sftp = mock_sftp
        # _actions 초기화 (connect_with_private_key에서 설정됨)
        ssh_connector._actions = {
            "DOWNLOAD": (mock_sftp.get, "파일 다운로드", FileDownloadError),
            "UPLOAD": (mock_sftp.put, "파일 업로드", FileUploadError)
        }
        
        await ssh_connector.file_transfer(
            "DOWNLOAD",
            Path("/remote/file.txt"),
            Path("/local/file.txt")
        )
        
        mock_sftp.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_transfer_upload_success(self, ssh_connector):
        """file_transfer() UPLOAD 성공"""
        mock_sftp = AsyncMock()
        mock_sftp.put = AsyncMock()
        ssh_connector._sftp = mock_sftp
        # _actions 초기화
        ssh_connector._actions = {
            "DOWNLOAD": (mock_sftp.get, "파일 다운로드", FileDownloadError),
            "UPLOAD": (mock_sftp.put, "파일 업로드", FileUploadError)
        }
        
        await ssh_connector.file_transfer(
            "UPLOAD",
            Path("/local/file.txt"),
            Path("/remote/file.txt")
        )
        
        mock_sftp.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_transfer_invalid_mode(self, ssh_connector):
        """file_transfer() 잘못된 모드"""
        with pytest.raises(ValueError, match="지원하지 않는 전송 모드"):
            await ssh_connector.file_transfer(
                "INVALID",
                Path("/source"),
                Path("/dest")
            )

    @pytest.mark.asyncio
    async def test_file_transfer_download_error(self, ssh_connector):
        """file_transfer() DOWNLOAD 에러"""
        mock_sftp = AsyncMock()
        mock_sftp.get = AsyncMock(side_effect=Exception("Download failed"))
        ssh_connector._sftp = mock_sftp
        # _actions 초기화
        ssh_connector._actions = {
            "DOWNLOAD": (mock_sftp.get, "파일 다운로드", FileDownloadError),
            "UPLOAD": (mock_sftp.put, "파일 업로드", FileUploadError)
        }
        
        with pytest.raises(FileDownloadError):
            await ssh_connector.file_transfer(
                "DOWNLOAD",
                Path("/remote/file.txt"),
                Path("/local/file.txt")
            )

    @pytest.mark.asyncio
    async def test_download_single_file(self, ssh_connector):
        """download_single_file() 테스트"""
        mock_sftp = AsyncMock()
        mock_sftp.get = AsyncMock()
        ssh_connector._sftp = mock_sftp
        # _actions 초기화
        ssh_connector._actions = {
            "DOWNLOAD": (mock_sftp.get, "파일 다운로드", FileDownloadError),
            "UPLOAD": (mock_sftp.put, "파일 업로드", FileUploadError)
        }
        
        with patch('OPEN_SSH.ssh_connector.os.makedirs'):
            result = await ssh_connector.download_single_file(
                Path("/remote/file.txt"),
                Path("/local/file.txt")
            )
        
        mock_sftp.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_files(self, ssh_connector):
        """download_files() 테스트"""
        mock_sftp = AsyncMock()
        mock_sftp.get = AsyncMock()
        ssh_connector._sftp = mock_sftp
        
        df = pd.DataFrame({
            "path_full_source": ["/remote/file1.txt", "/remote/file2.txt"],
            "path_full_destination": ["/local/file1.txt", "/local/file2.txt"]
        })
        
        with patch('OPEN_SSH.ssh_connector.os.makedirs'):
            result = await ssh_connector.download_files(df)
        
        assert "is_retrieved" in result.columns
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_run_command_success(self, ssh_connector):
        """run_command() 성공"""
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.stdout = "command output"
        mock_conn.run = AsyncMock(return_value=mock_result)
        ssh_connector._conn = mock_conn
        
        with patch.object(ssh_connector, 'is_connected', return_value=True):
            result = await ssh_connector.run_command("ls -la")
        
        assert result.stdout == "command output"
        mock_conn.run.assert_called_once_with("ls -la")

    @pytest.mark.asyncio
    async def test_run_command_not_connected(self, ssh_connector):
        """run_command() 연결 안 됨"""
        ssh_connector._conn = None
        
        with patch.object(ssh_connector, 'is_connected', return_value=False):
            with pytest.raises(SSHConnectionError):
                await ssh_connector.run_command("ls -la")

    @pytest.mark.asyncio
    async def test_run_command_error(self, ssh_connector):
        """run_command() 명령 실행 에러"""
        mock_conn = AsyncMock()
        mock_conn.run = AsyncMock(side_effect=Exception("Command failed"))
        ssh_connector._conn = mock_conn
        
        with patch.object(ssh_connector, 'is_connected', return_value=True):
            with pytest.raises(SSHCommandError):
                await ssh_connector.run_command("invalid_command")

    @pytest.mark.asyncio
    async def test_context_manager(self, ssh_connector):
        """컨텍스트 매니저 테스트"""
        with patch.object(ssh_connector, 'connect_with_private_key', new_callable=AsyncMock) as mock_connect, \
             patch.object(ssh_connector, 'close', new_callable=AsyncMock) as mock_close:
            
            async with ssh_connector:
                pass
            
            mock_connect.assert_called_once()
            mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

