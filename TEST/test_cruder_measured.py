###########################################
# Module name : test_cruder_measured.py
# 테스트 대상 : DATABASE.cruder.CRUDer (Measured 관련 메서드)
# Written by : GPT Test Template
# Note       : 실제 동작하는 단위 테스트 (Mock 활용)
###########################################

import pytest
from datetime import date, timedelta, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from sqlalchemy.sql import func

from DATABASE.cruder import CRUDer
from DATABASE import models


class TestCRUDerMeasured:
    """CRUDer의 Measured 관련 메서드 테스트"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock DBManager 생성"""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        return mock_db

    @pytest.fixture
    def cruder(self, mock_db_manager):
        """CRUDer 인스턴스 생성"""
        return CRUDer(mock_db_manager)

    @pytest.mark.asyncio
    async def test_get_measured_data_basic(self, cruder, mock_db_manager):
        """get_measured_data() 기본 동작 테스트"""
        # Mock 결과 설정
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data(
            model_name="test_model",
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31)
        )

        assert len(result) == 2
        assert result[0] == [1.0, 2.0, 3.0]
        
        # execute_query가 호출되었는지 확인
        mock_db_manager.execute_query.assert_called_once()
        call_args = mock_db_manager.execute_query.call_args[0][0]
        # SQLAlchemy select 문이 전달되었는지 확인
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_get_measured_data_with_filters(self, cruder, mock_db_manager):
        """get_measured_data() 필터 옵션 테스트"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data(
            model_name="test_model",
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
            measured_by="test_instrument",
            measured_points=100
        )

        assert result == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_by_model_name(self, cruder, mock_db_manager):
        """get_measured_data_by_model_name() 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {"id": 1, "model_name": "test", "serial_no": "SN001"}.get(key)
        mock_result.mappings.return_value.all.return_value = [mock_mapping]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_by_model_name(
            model_name="test_model",
            after=date(2025, 1, 1),
            latest_only=True
        )

        assert len(result) == 1
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_by_model_name_no_after(self, cruder, mock_db_manager):
        """get_measured_data_by_model_name() after=None 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_by_model_name(
            model_name="test_model",
            after=None,
            latest_only=False
        )

        assert result == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_since_last_normalized(self, cruder, mock_db_manager):
        """get_measured_since_last_normalized() 테스트"""
        mock_result = MagicMock()
        # dict()로 변환 가능한 Mock 객체 생성
        mock_row = {
            "id": 1,
            "instrument_name": "test_inst",
            "model_name": "test_model",
            "serial_no": "SN001",
            "list_measured": [1.0, 2.0, 3.0],
            "measured_at": datetime(2025, 1, 15)
        }
        # mappings().all()이 dict를 반환하도록 설정
        mock_result.mappings.return_value.all.return_value = [mock_row]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_since_last_normalized(
            model_name="test_model",
            latest_only=True
        )

        assert len(result) == 1
        assert result[0]["model_name"] == "test_model"
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_since_last_normalized_no_model(self, cruder, mock_db_manager):
        """get_measured_since_last_normalized() model_name=None 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_since_last_normalized(
            model_name=None,
            latest_only=False
        )

        assert result == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_measured_datum(self, cruder, mock_db_manager):
        """get_latest_measured_datum() 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "instrument_name": "test_inst",
            "model_name": "test_model",
            "serial_no": "SN001",
            "measured_at": datetime(2025, 1, 15),
            "list_measured": [1.0, 2.0, 3.0]
        }.get(key)
        mock_result.mappings.return_value.first.return_value = mock_mapping
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_latest_measured_datum(
            instrument_name="test_inst",
            model_name="test_model",
            serial_no="SN001",
            get_list_measured=True
        )

        assert result is not None
        assert result["model_name"] == "test_model"
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_measured_datum_no_list(self, cruder, mock_db_manager):
        """get_latest_measured_datum() get_list_measured=False 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "instrument_name": "test_inst",
            "model_name": "test_model",
            "serial_no": "SN001",
            "measured_at": datetime(2025, 1, 15)
        }.get(key)
        mock_result.mappings.return_value.first.return_value = mock_mapping
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_latest_measured_datum(
            get_list_measured=False
        )

        assert result is not None
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_serial_nos(self, cruder, mock_db_manager):
        """get_serial_nos() 테스트"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["SN001", "SN002", "SN003"]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_serial_nos()

        assert len(result) == 3
        assert "SN001" in result
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_time_series_data(self, cruder, mock_db_manager):
        """get_time_series_data() 테스트"""
        mock_result = MagicMock()
        mock_mapping = MagicMock()
        mock_mapping.__getitem__.side_effect = lambda key: {
            "serial_no": "SN001",
            "measured_at": "2025-01-15 10:00:00",
            "measured_value": 1.5
        }.get(key)
        mock_result.mappings.return_value.all.return_value = [mock_mapping]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_time_series_data(
            model_name="test_model",
            inspection_idx=0,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
            measured_by="test_inst"
        )

        assert len(result) == 1
        assert result[0]["serial_no"] == "SN001"
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_time_series_data_no_measured_by(self, cruder, mock_db_manager):
        """get_time_series_data() measured_by=None 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_time_series_data(
            model_name="test_model",
            inspection_idx=0,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
            measured_by=None
        )

        assert result == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_size_distinct_serial(self, cruder, mock_db_manager):
        """get_measured_data_size() distinct_serial=True 테스트"""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_size(
            instrument_name="inst1",
            model_name="model1",
            distinct_serial=True
        )

        assert result == 10
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_size_not_distinct(self, cruder, mock_db_manager):
        """get_measured_data_size() distinct_serial=False 테스트"""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 50
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_size(
            instrument_name="inst1",
            model_name="model1",
            distinct_serial=False
        )

        assert result == 50
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_size_no_filters(self, cruder, mock_db_manager):
        """get_measured_data_size() 필터 없음 테스트"""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 100
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_size(
            instrument_name=None,
            model_name=None,
            distinct_serial=True
        )

        assert result == 100
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_sizes_distinct_serial(self, cruder, mock_db_manager):
        """get_measured_data_sizes() distinct_serial=True 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"model_name": "model1", "count": 10},
            {"model_name": "model2", "count": 20}
        ]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_sizes(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
            distinct_serial=True
        )

        assert len(result) == 2
        assert result.iloc[0]["model_name"] == "model1"
        assert result.iloc[0]["count"] == 10
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_sizes_not_distinct(self, cruder, mock_db_manager):
        """get_measured_data_sizes() distinct_serial=False 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"model_name": "model1", "count": 50}
        ]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_sizes(
            distinct_serial=False
        )

        assert len(result) == 1
        assert result.iloc[0]["count"] == 50
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_measured_data_sizes_with_date_range(self, cruder, mock_db_manager):
        """get_measured_data_sizes() 날짜 범위 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"model_name": "model1", "count": 5}
        ]
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_measured_data_sizes(
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 20)
        )

        assert len(result) == 1
        mock_db_manager.execute_query.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

