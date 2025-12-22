###########################################
# Module name : test_cruder_vector.py
# 테스트 대상 : DATABASE.cruder.CRUDer (Vector Similarity 관련 메서드)
# Written by : Auto (Cursor AI)
###########################################

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from DATABASE.cruder import CRUDer


class TestCRUDerVector:
    """CRUDer의 Vector Similarity 관련 메서드 테스트"""

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
    async def test_get_vector_data_success(self, cruder, mock_db_manager):
        """get_vector_data() 성공 케이스 테스트"""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result.mappings.return_value.first.return_value = mock_row
        mock_db_manager.execute_query.return_value = mock_result

        model_name, serial_no, vector = await cruder.get_vector_data("serial1")

        assert model_name == "model1"
        assert serial_no == "serial1"
        assert vector == [0.1, 0.2, 0.3]
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vector_data_not_found(self, cruder, mock_db_manager):
        """get_vector_data() 데이터 없음 테스트"""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db_manager.execute_query.return_value = mock_result

        model_name, serial_no, vector = await cruder.get_vector_data("serial1")

        assert model_name == ""
        assert serial_no == ""
        assert vector == []
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_relative_similarities_success(self, cruder, mock_db_manager):
        """get_relative_similarities() 성공 케이스 테스트"""
        # get_vector_data 호출
        mock_result1 = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row
        
        # get_absolute_similarities 호출 (내부적으로 _get_similarities_by_metric 호출)
        mock_result2 = MagicMock()
        mock_result2.mappings.return_value.all.return_value = []
        
        mock_db_manager.execute_query.side_effect = [mock_result1, mock_result2]

        result = await cruder.get_relative_similarities(
            instrument_name="inst1",
            model_name="model1",
            serial_no="serial1",
            num_of_records=100,
            top_k_rate=0.01
        )

        assert isinstance(result, dict)
        assert len(mock_db_manager.execute_query.call_args_list) >= 2

    @pytest.mark.asyncio
    async def test_get_relative_similarities_invalid_top_k_rate(self, cruder, mock_db_manager):
        """get_relative_similarities() 잘못된 top_k_rate 테스트"""
        with pytest.raises(ValueError, match="top_k_rate must be between 0.0 and 1.0"):
            await cruder.get_relative_similarities(
                instrument_name="inst1",
                model_name="model1",
                serial_no="serial1",
                num_of_records=100,
                top_k_rate=1.5
            )

    @pytest.mark.asyncio
    async def test_get_absolute_similarities_no_vector(self, cruder, mock_db_manager):
        """get_absolute_similarities() 벡터 없음 테스트"""
        # get_vector_data가 빈 벡터 반환
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db_manager.execute_query.return_value = mock_result

        result = await cruder.get_absolute_similarities(
            instrument_name="inst1",
            model_name="model1",
            serial_no="serial1",
            top_k=10
        )

        assert result == {}
        mock_db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_absolute_similarities_invalid_metric(self, cruder, mock_db_manager):
        """get_absolute_similarities() 잘못된 metric 테스트"""
        # get_vector_data 호출
        mock_result1 = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row
        mock_db_manager.execute_query.return_value = mock_result1

        with pytest.raises(ValueError, match="Invalid metric"):
            await cruder.get_absolute_similarities(
                instrument_name="inst1",
                model_name="model1",
                serial_no="serial1",
                top_k=10,
                metric="invalid"
            )

    @pytest.mark.asyncio
    async def test_get_absolute_similarities_euclidean_metric(self, cruder, mock_db_manager):
        """get_absolute_similarities() euclidean metric 테스트"""
        # get_vector_data 호출
        mock_result1 = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row
        
        # _get_similarities_by_metric 호출 (euclidean)
        mock_result2 = MagicMock()
        mock_result2.mappings.return_value.all.return_value = []
        
        mock_db_manager.execute_query.side_effect = [mock_result1, mock_result2]

        result = await cruder.get_absolute_similarities(
            instrument_name="inst1",
            model_name="model1",
            serial_no="serial1",
            top_k=10,
            metric="euclidean"
        )

        assert isinstance(result, dict)
        assert len(mock_db_manager.execute_query.call_args_list) >= 2

    @pytest.mark.asyncio
    async def test_get_absolute_similarities_manhattan_metric(self, cruder, mock_db_manager):
        """get_absolute_similarities() manhattan metric 테스트"""
        # get_vector_data 호출
        mock_result1 = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row
        
        # _get_similarities_by_metric 호출 (manhattan)
        mock_result2 = MagicMock()
        mock_result2.mappings.return_value.all.return_value = []
        
        mock_db_manager.execute_query.side_effect = [mock_result1, mock_result2]

        result = await cruder.get_absolute_similarities(
            instrument_name="inst1",
            model_name="model1",
            serial_no="serial1",
            top_k=10,
            metric="manhattan"
        )

        assert isinstance(result, dict)
        assert len(mock_db_manager.execute_query.call_args_list) >= 2

