###########################################
# Module name : test_file_retriever.py
# 테스트 대상 : data_retriever.FileRetriever
# Written by : Test Example
# Note : pytest를 사용한 단위 테스트 예시 (Mock 활용)
############################################

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import pandas as pd

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_retriever import FileRetriever
from DATABASE.cruder import CRUDer
from OPEN_SSH.ssh_connector import OpenSSHConnector


class TestFileRetriever:
    """FileRetriever 클래스에 대한 단위 테스트"""

    @pytest.fixture
    def mock_cruder(self):
        """CRUDer Mock 생성"""
        cruder = MagicMock(spec=CRUDer)
        return cruder

    @pytest.fixture
    def mock_ssh(self):
        """OpenSSHConnector Mock 생성"""
        ssh = AsyncMock(spec=OpenSSHConnector)
        ssh.is_connected = AsyncMock(return_value=True)
        return ssh

    @pytest.fixture
    def file_retriever(self, mock_cruder):
        """FileRetriever 인스턴스 생성"""
        return FileRetriever(mock_cruder)

    def test_set_instrument_infos(self, file_retriever):
        """set_instrument_infos 메서드 테스트"""
        result = file_retriever.set_instrument_infos(
            instrument_name="test_instrument",
            host="192.168.1.1",
            user="test_user",
            port=22,
            ssh_key_path="/path/to/key",
            dir_base_source="/source",
            dir_destination_base="/destination"
        )
        
        assert result is file_retriever  # Fluent interface
        assert file_retriever.instrument_name == "test_instrument"
        assert file_retriever.hostname == "192.168.1.1"
        assert file_retriever.username == "test_user"
        assert file_retriever.port == 22
        assert file_retriever.is_instrument_info_set is True

    @pytest.mark.asyncio
    async def test_run_without_instrument_info(self, file_retriever):
        """instrument_info가 설정되지 않은 경우"""
        # is_instrument_info_set가 False인 상태
        await file_retriever.run()
        
        # 에러 로그가 기록되어야 함 (실제로는 logger를 mock해야 함)

    @pytest.mark.asyncio
    async def test_run_without_ssh_connection(self, file_retriever, mock_cruder):
        """SSH 연결이 없는 경우"""
        file_retriever.set_instrument_infos(
            instrument_name="test",
            host="192.168.1.1",
            user="test",
            port=22,
            ssh_key_path="/path/to/key",
            dir_base_source="/source",
            dir_destination_base="/dest"
        )
        file_retriever.ssh = None
        
        with pytest.raises(ConnectionError):
            await file_retriever.run()

    @pytest.mark.asyncio
    async def test_run_with_disconnected_ssh(self, file_retriever, mock_ssh, mock_cruder):
        """SSH 연결이 끊어진 경우"""
        file_retriever.set_instrument_infos(
            instrument_name="test",
            host="192.168.1.1",
            user="test",
            port=22,
            ssh_key_path="/path/to/key",
            dir_base_source="/source",
            dir_destination_base="/dest"
        )
        mock_ssh.is_connected = AsyncMock(return_value=False)
        file_retriever.ssh = mock_ssh
        
        with pytest.raises(ConnectionError):
            await file_retriever.run()

    @pytest.mark.asyncio
    async def test_connect_to_instrument_success(self, file_retriever, mock_cruder):
        """SSH 연결 성공 테스트"""
        mock_ssh_instance = AsyncMock()
        mock_ssh_instance.is_connected = AsyncMock(return_value=True)
        
        with patch('data_retriever.OpenSSHConnector') as mock_ssh_class:
            mock_ssh_class.return_value.connect_with_private_key = AsyncMock(return_value=mock_ssh_instance)
            mock_cruder.upsert_instrument = AsyncMock()
            
            result = await file_retriever.connect_to_instrument()
            
            assert file_retriever.ssh is not None
            assert file_retriever.accessible is True

    @pytest.mark.asyncio
    async def test_connect_to_instrument_failure(self, file_retriever, mock_cruder):
        """SSH 연결 실패 테스트"""
        file_retriever.set_instrument_infos(
            instrument_name="test",
            host="192.168.1.1",
            user="test",
            port=22,
            ssh_key_path="/path/to/key",
            dir_base_source="/source",
            dir_destination_base="/dest"
        )
        
        with patch('data_retriever.OpenSSHConnector') as mock_ssh_class:
            mock_ssh_instance = AsyncMock()
            mock_ssh_instance.connect_with_private_key = AsyncMock(side_effect=ConnectionError("Connection failed"))
            mock_ssh_class.return_value = mock_ssh_instance
            mock_cruder.upsert_instrument = AsyncMock()
            
            await file_retriever.connect_to_instrument()
            
            # 연결 실패 시 ssh는 None이거나 accessible이 False여야 함
            # 실제 구현에 따라 다를 수 있음
            assert file_retriever.accessible is False or file_retriever.ssh is None

    @pytest.mark.asyncio
    async def test_get_latest_created_time(self, file_retriever, mock_cruder):
        """get_latest_created_time() 메서드 테스트"""
        from datetime import datetime
        
        mock_cruder.get_latest_created_time = AsyncMock(return_value=datetime(2025, 1, 15, 10, 0, 0))
        
        result = await file_retriever.get_latest_created_time("test_instrument", "test_model")
        
        assert result == datetime(2025, 1, 15, 10, 0, 0)
        mock_cruder.get_latest_created_time.assert_called_once_with("test_instrument", "test_model")

    @pytest.mark.asyncio
    async def test_get_latest_created_time_no_model(self, file_retriever, mock_cruder):
        """get_latest_created_time() model_name 없음 테스트"""
        from datetime import datetime
        
        mock_cruder.get_latest_created_time = AsyncMock(return_value=datetime(2025, 1, 15, 10, 0, 0))
        
        result = await file_retriever.get_latest_created_time("test_instrument", None)
        
        assert result == datetime(2025, 1, 15, 10, 0, 0)
        mock_cruder.get_latest_created_time.assert_called_once_with("test_instrument", None)

    @pytest.mark.asyncio
    async def test_get_latest_created_times(self, file_retriever, mock_cruder):
        """get_latest_created_times() 메서드 테스트"""
        from datetime import datetime
        
        mock_data = [
            {
                "instrument_name": "inst1",
                "model_name": "model1",
                "path_full_source": "/path/file1.csv",
                "created_at": datetime(2025, 1, 15, 10, 0, 0)
            },
            {
                "instrument_name": "inst1",
                "model_name": "model2",
                "path_full_source": "/path/file2.csv",
                "created_at": datetime(2025, 1, 16, 10, 0, 0)
            }
        ]
        mock_cruder.get_latest_created_times = AsyncMock(return_value=mock_data)
        
        result = await file_retriever.get_latest_created_times("inst1")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "instrument_name" in result.columns
        assert "model_name" in result.columns
        mock_cruder.get_latest_created_times.assert_called_once_with("inst1")

    def test_make_void_dataframe_for_process(self, file_retriever):
        """make_void_dataframe_for_process 메서드 테스트"""
        df = file_retriever.make_void_dataframe_for_process()
        
        assert isinstance(df, pd.DataFrame)
        expected_columns = [
            'instrument_name', 'model_name', 'path_full_source', 
            'path_full_destination', 'is_retrieved', 'retrieved_at', 
            'created_at', 'hashed'
        ]
        assert list(df.columns) == expected_columns
        assert len(df) == 0


# 통합 테스트 예시 (실제 DB나 SSH 연결 없이)
class TestFileRetrieverIntegration:
    """FileRetriever 통합 테스트 (Mock을 사용한)"""

    @pytest.mark.asyncio
    async def test_full_retrieval_workflow(self):
        """전체 파일 리트리버 워크플로우 테스트"""
        # 이 테스트는 실제 구현에 맞게 수정 필요
        # Mock을 사용해서 전체 흐름을 테스트
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

