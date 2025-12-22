###########################################
# Module name : test_data_archiver.py
# 테스트 대상 : data_archiver.DataArchiver
# Written by : GPT Test Template
# Note       : 실제 동작하는 단위 테스트 (Mock 활용)
###########################################

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from data_archiver import DataArchiver
from DATABASE import models


class MockICTDataExtractor:
    """테스트용 ICTDataExtractor Mock"""
    def __init__(self):
        self.measured_by = "test_instrument"
        self.model_name = "test_model"
        self.serial_no = "SN001"
        # df_measured 길이(3)와 일치하도록 설정 (정상 케이스용)
        self.measured_points = 3
        self.adj_val_infinity = 1.0
        self.adj_val_extreme = 2.0
        self.measured_at = datetime(2025, 1, 15, 10, 0, 0)
        self.df_measured = pd.DataFrame({
            "measured_value": [1.0, 2.0, 3.0]
        })
        self.df_spec = pd.DataFrame({
            "point": [1, 2, 3],
            "spec_min": [0.5, 1.5, 2.5],
            "spec_max": [1.5, 2.5, 3.5]
        })
    
    @property
    def suggest_file_name_spec(self):
        return "test_spec.parquet"
    
    @property
    def suggest_file_name_measured(self):
        return "test_measured.parquet"


class TestDataArchiver:
    """DataArchiver 클래스에 대한 단위 테스트"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock DBManager 생성"""
        mock_db = MagicMock()
        mock_db.upsert_dataframe = AsyncMock(return_value=1)
        return mock_db

    @pytest.fixture
    def archiver(self, mock_db_manager):
        """DataArchiver 인스턴스 생성"""
        return DataArchiver(mock_db_manager)

    @pytest.fixture
    def ict_data(self):
        """Mock ICTDataExtractor 생성"""
        return MockICTDataExtractor()

    @pytest.mark.asyncio
    async def test_on_instrument(self, archiver, mock_db_manager):
        """on_instrument() 테스트"""
        result = await archiver.on_instrument(
            name="test_inst",
            host="192.168.1.1",
            user="admin",
            port=22,
            ssh_key_path="/path/to/key"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        # data_archiver에서 md.name을 키로 사용하는데, 실제로는 컬럼명이 어떻게 되는지 확인 필요
        # on_model에서는 md.name.name을 사용하지만 on_instrument에서는 md.name을 사용
        # 실제 DataFrame 컬럼명 확인
        columns = list(result.columns)
        # 컬럼명이 문자열인지 확인하고 접근
        if "name" in columns:
            assert result.iloc[0]["name"] == "test_inst"
        else:
            # Mapped 객체가 키로 사용된 경우
            assert result.iloc[0][models.Instrument.name] == "test_inst"
        
        if "host" in columns:
            assert result.iloc[0]["host"] == "192.168.1.1"
        else:
            assert result.iloc[0][models.Instrument.host] == "192.168.1.1"
        
        # accessible 컬럼 확인 (numpy boolean 타입 처리)
        accessible_value = result.iloc[0].get("accessible") or result.iloc[0].get(models.Instrument.accessible)
        assert bool(accessible_value) is False
        
        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Instrument

    @pytest.mark.asyncio
    async def test_on_instrument_no_ssh_key(self, archiver, mock_db_manager):
        """on_instrument() ssh_key_path 빈 문자열 테스트"""
        result = await archiver.on_instrument(
            name="test_inst",
            host="192.168.1.1",
            user="admin",
            port=22,
            ssh_key_path=""
        )

        assert isinstance(result, pd.DataFrame)
        # 컬럼명 확인 후 접근
        columns = list(result.columns)
        if "ssh_key_path" in columns:
            assert result.iloc[0]["ssh_key_path"] == ""
        else:
            assert result.iloc[0][models.Instrument.ssh_key_path] == ""

    @pytest.mark.asyncio
    async def test_on_model(self, archiver, mock_db_manager, ict_data):
        """on_model() 테스트"""
        await archiver.on_model(ict_data)

        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Model
        
        # DataFrame에 model_name이 포함되었는지 확인
        df_arg = call_args[0][1]
        assert df_arg.iloc[0]["name"] == "test_model"

    @pytest.mark.asyncio
    async def test_on_spec(self, archiver, mock_db_manager, ict_data):
        """on_spec() 테스트"""
        datafile_subpath = Path("SPEC/test_spec.parquet")
        datafile_hash = b"test_hash_bytes_32_chars_long!!"

        result = await archiver.on_spec(ict_data, datafile_subpath, datafile_hash)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        # 컬럼명 확인 후 접근
        columns = list(result.columns)
        if "model_name" in columns:
            assert result.iloc[0]["model_name"] == "test_model"
        else:
            assert result.iloc[0][models.Spec.model_name.name] == "test_model"
        
        # measured_points는 ict_data.measured_points 값 (3)
        if "measured_points" in columns:
            assert result.iloc[0]["measured_points"] == 3
        else:
            assert result.iloc[0][models.Spec.measured_points.name] == 3
        
        if "hashed_datafile" in columns:
            assert result.iloc[0]["hashed_datafile"] == datafile_hash
        else:
            assert result.iloc[0][models.Spec.hashed_datafile.name] == datafile_hash
        
        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Spec

    @pytest.mark.asyncio
    async def test_on_measured(self, archiver, mock_db_manager, ict_data):
        """on_measured() 테스트"""
        datafile_subpath = Path("MEASURED/test_measured.parquet")
        datafile_hash = b"test_hash_bytes_32_chars_long!!"

        result = await archiver.on_measured(ict_data, datafile_subpath, datafile_hash)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["serial_no"] == "SN001"
        assert result.iloc[0]["measured_points"] == 3  # df_measured 길이
        # numpy boolean 타입 처리
        assert bool(result.iloc[0]["passed"]) is True
        
        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Measured

    @pytest.mark.asyncio
    async def test_on_process_to_archive(self, archiver, mock_db_manager):
        """on_process_to_archive() 테스트"""
        result = await archiver.on_process_to_archive(
            instrument_name="inst1",
            model_name="model1",
            path_full_original=Path("/source/file.csv"),
            path_full_destination=Path("/dest/file.parquet"),
            is_parsed=False,
            status="PENDING",
            note="Test note",
            lock=False
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["instrument_name"] == "inst1"
        assert bool(result.iloc[0]["is_parsed"]) is False
        assert result.iloc[0]["status"] == "PENDING"
        assert bool(result.iloc[0]["is_locked"]) is False
        
        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Process

    @pytest.mark.asyncio
    async def test_on_process_to_archive_with_lock(self, archiver, mock_db_manager):
        """on_process_to_archive() lock=True 테스트"""
        result = await archiver.on_process_to_archive(
            instrument_name="inst1",
            model_name="model1",
            path_full_original=Path("/source/file.csv"),
            path_full_destination=Path("/dest/file.parquet"),
            is_parsed=False,
            status="RETRIEVED",
            note=None,
            lock=True
        )

        assert bool(result.iloc[0]["is_locked"]) is True
        assert result.iloc[0]["note"] is None

    @pytest.mark.asyncio
    async def test_raise_if_points_mismatch(self, archiver, ict_data):
        """raise_if_points_mismatch() 정상 케이스 테스트"""
        # measured_points == len(df_measured) 이므로 에러 없음
        await archiver.raise_if_points_mismatch(ict_data)
        # 에러가 발생하지 않으면 통과

    @pytest.mark.asyncio
    async def test_raise_if_points_mismatch_error(self, archiver):
        """raise_if_points_mismatch() 에러 케이스 테스트"""
        # 새로운 MockICTDataExtractor 생성 (measured_points를 다르게 설정)
        ict_data = MockICTDataExtractor()
        # measured_points를 df_measured 길이(3)와 다르게 설정
        ict_data.measured_points = 100  # 실제 df_measured 길이는 3이므로 mismatch 발생

        with pytest.raises(ValueError, match="Measured points mismatch"):
            await archiver.raise_if_points_mismatch(ict_data)

    @pytest.mark.asyncio
    async def test_save_parquet_n_upsert_spec(self, archiver, mock_db_manager, ict_data):
        """save_parquet_n_upsert() spec 타입 테스트"""
        dir_base = Path("/base")
        dir_sub = Path("SPEC")
        
        with patch('data_archiver.Path.mkdir') as mock_mkdir, \
             patch('pandas.DataFrame.to_parquet') as mock_to_parquet, \
             patch('data_archiver.Hasher') as mock_hasher_class:
            
            mock_hasher = MagicMock()
            mock_hasher.hash_file.return_value.value = b"test_hash"
            mock_hasher_class.return_value = mock_hasher
            
            await archiver.save_parquet_n_upsert(
                ict_data,
                target_process="spec",
                dir_base_destination=dir_base,
                dir_sub_destination=dir_sub
            )

            # 디렉토리 생성 확인
            mock_mkdir.assert_called_once()
            
            # parquet 저장 확인
            mock_to_parquet.assert_called_once()
            
            # upsert 호출 확인
            mock_db_manager.upsert_dataframe.assert_called_once()
            call_args = mock_db_manager.upsert_dataframe.call_args
            assert call_args[0][0] == models.Spec

    @pytest.mark.asyncio
    async def test_save_parquet_n_upsert_measured(self, archiver, mock_db_manager, ict_data):
        """save_parquet_n_upsert() measured 타입 테스트"""
        dir_base = Path("/base")
        dir_sub = Path("MEASURED")
        
        with patch('data_archiver.Path.mkdir') as mock_mkdir, \
             patch('pandas.DataFrame.to_parquet') as mock_to_parquet, \
             patch('data_archiver.Hasher') as mock_hasher_class:
            
            mock_hasher = MagicMock()
            mock_hasher.hash_file.return_value.value = b"test_hash"
            mock_hasher_class.return_value = mock_hasher
            
            await archiver.save_parquet_n_upsert(
                ict_data,
                target_process="measured",
                dir_base_destination=dir_base,
                dir_sub_destination=dir_sub
            )

            # upsert 호출 확인
            mock_db_manager.upsert_dataframe.assert_called_once()
            call_args = mock_db_manager.upsert_dataframe.call_args
            assert call_args[0][0] == models.Measured


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

