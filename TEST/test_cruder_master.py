###########################################
# Module name : test_cruder_master.py
# 테스트 대상 : DATABASE.cruder.CRUDer (Instrument, Model, Spec 관련 메서드)
# Written by : GPT Test Template
# Note       : 실제 동작하는 단위 테스트 (Mock 활용)
###########################################

import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from DATABASE.cruder import CRUDer
from DATABASE import models


class TestCRUDerMaster:
    """CRUDer의 마스터 데이터(Instrument, Model, Spec) 관련 메서드 테스트"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock DBManager 생성"""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        mock_db.upsert_dataframe = AsyncMock(return_value=1)
        return mock_db

    @pytest.fixture
    def cruder(self, mock_db_manager):
        """CRUDer 인스턴스 생성"""
        return CRUDer(mock_db_manager)

    # Instrument 관련 테스트
    @pytest.mark.asyncio
    async def test_get_instrument_names(self, cruder, mock_db_manager):
        """get_instrument_names() 테스트"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["inst1", "inst2", "inst3"]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_instrument_names()

        assert len(result) == 3
        assert "inst1" in result
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_base_dir_destinations(self, cruder, mock_db_manager):
        """get_base_dir_destinations() 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "name": "inst1",
            "dir_base_destination": "/path/to/dest"
        }.get(key)
        mock_result.mappings.return_value.all.return_value = [mock_mapping]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_base_dir_destinations()

        assert len(result) == 1
        assert result[0]["name"] == "inst1"
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_base_dir_destinations_with_filter(self, cruder, mock_db_manager):
        """get_base_dir_destinations() instrument_name 필터 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "name": "inst1",
            "dir_base_destination": "/path/to/dest"
        }.get(key)
        mock_result.mappings.return_value.all.return_value = [mock_mapping]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_base_dir_destinations(instrument_name="inst1")

        assert len(result) == 1
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instrument_infos(self, cruder, mock_db_manager):
        """get_instrument_infos() 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "name": "inst1",
            "host": "192.168.1.1",
            "user": "admin",
            "port": 22,
            "activated": True
        }.get(key)
        mock_result.mappings.return_value.all.return_value = [mock_mapping]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_instrument_infos()

        assert len(result) == 1
        assert result[0]["name"] == "inst1"
        assert result[0]["activated"] is True
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_instrument_infos_with_filter(self, cruder, mock_db_manager):
        """get_instrument_infos() instrument_name 필터 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_instrument_infos(instrument_name="inst1")

        assert result == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_instrument(self, cruder, mock_db_manager):
        """upsert_instrument() 테스트"""
        df = pd.DataFrame({
            "name": ["inst1"],
            "host": ["192.168.1.1"],
            "user": ["admin"],
            "port": [22]
        })

        await cruder.upsert_instrument(df)

        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Instrument

    # Model 관련 테스트
    @pytest.mark.asyncio
    async def test_get_model_names(self, cruder, mock_db_manager):
        """get_model_names() 테스트"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["model1", "model2"]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_model_names()

        assert len(result) == 2
        assert "model1" in result
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_model_names(self, cruder, mock_db_manager):
        """upsert_model_names() 테스트"""
        df = pd.DataFrame({
            "name": ["model1", "model2"]
        })
        mock_db_manager.upsert_dataframe.return_value = 2

        result = await cruder.upsert_model_names(df)

        assert result == 2
        mock_db_manager.upsert_dataframe.assert_called_once()
        call_args = mock_db_manager.upsert_dataframe.call_args
        assert call_args[0][0] == models.Model

    # Spec 관련 테스트
    @pytest.mark.asyncio
    async def test_get_spec(self, cruder, mock_db_manager):
        """get_spec() 기본 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "id": 1,
            "model_name": "test_model",
            "measured_points": 100,
            "updated_at": datetime(2025, 1, 15)
        }.get(key)
        mock_result.mappings.return_value.first.return_value = mock_mapping
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_spec(model_name="test_model")

        assert result is not None
        assert result["model_name"] == "test_model"
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spec_with_spec_id(self, cruder, mock_db_manager):
        """get_spec() spec_id 필터 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "id": 1,
            "model_name": "test_model"
        }.get(key)
        mock_result.mappings.return_value.first.return_value = mock_mapping
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_spec(model_name="test_model", spec_id=1)

        assert result is not None
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spec_with_updated_at(self, cruder, mock_db_manager):
        """get_spec() updated_at 필터 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_spec(
            model_name="test_model",
            updated_at=date(2025, 1, 1)
        )

        assert result is None
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spec_not_found(self, cruder, mock_db_manager):
        """get_spec() 결과 없음 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_spec(model_name="nonexistent_model")

        assert result is None
        mock_db_manager.execute_query.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

