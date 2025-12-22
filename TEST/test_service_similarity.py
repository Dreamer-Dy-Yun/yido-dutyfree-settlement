###########################################
# Module name : test_service_similarity.py
# 테스트 대상 : WEB_SERVER.services.service (Similarity 관련 함수)
# Written by : Auto (Cursor AI)
###########################################

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from WEB_SERVER.services.service import get_serial_similarity_hits_from_defects
from DATABASE.cruder import CRUDer
import pandas as pd


class TestServiceSimilarity:
    """Service의 Similarity 관련 함수 테스트"""

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
    async def test_get_serial_similarity_hits_from_defects_no_serial_info(self, cruder, mock_db_manager):
        """get_serial_similarity_hits_from_defects() serial_info가 None인 경우 테스트"""
        # get_latest_measured_datum이 None 반환
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db_manager.execute_query.return_value = mock_result

        with pytest.raises(ValueError, match="시리얼 번호.*에 해당하는 측정 데이터를 찾을 수 없습니다"):
            await get_serial_similarity_hits_from_defects(
                cruder=cruder,
                instrument_name="inst1",
                serial_no="serial1",
                top_n_rate=0.01
            )

    @pytest.mark.asyncio
    async def test_get_serial_similarity_hits_from_defects_no_vector_data(self, cruder, mock_db_manager):
        """get_serial_similarity_hits_from_defects() 정규화된 벡터 데이터가 없는 경우 테스트"""
        # get_latest_measured_datum 호출
        mock_result1 = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "instrument_name": "inst1",
            "measured_at": date(2025, 1, 1),
            "list_measured": [1.0, 2.0, 3.0]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row1
        
        # get_external_defects_info 호출
        mock_result2 = MagicMock()
        mock_result2.mappings.return_value.all.return_value = []
        
        # get_measured_data_sizes 호출
        mock_result3 = MagicMock()
        mock_result3.mappings.return_value.all.return_value = []
        
        # get_absolute_similarities 호출 (빈 딕셔너리 반환)
        mock_result4 = MagicMock()
        mock_result4.mappings.return_value.first.return_value = None  # get_vector_data가 None 반환
        
        mock_db_manager.execute_query.side_effect = [
            mock_result1,  # get_latest_measured_datum
            mock_result2,  # get_external_defects_info
            mock_result3,  # get_measured_data_sizes
            mock_result4   # get_vector_data (빈 벡터)
        ]

        with pytest.raises(ValueError, match="정규화된 벡터 데이터가 없습니다"):
            await get_serial_similarity_hits_from_defects(
                cruder=cruder,
                instrument_name="inst1",
                serial_no="serial1",
                top_n_rate=0.01
            )

    @pytest.mark.asyncio
    async def test_get_serial_similarity_hits_from_defects_empty_record(self, cruder, mock_db_manager):
        """get_serial_similarity_hits_from_defects() single_record가 빈 딕셔너리인 경우 테스트"""
        # get_latest_measured_datum 호출
        mock_result1 = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "instrument_name": "inst1",
            "measured_at": date(2025, 1, 1),
            "list_measured": [1.0, 2.0, 3.0]
        }[key]
        mock_result1.mappings.return_value.first.return_value = mock_row1
        
        # get_external_defects_info 호출
        mock_result2 = MagicMock()
        mock_result2.mappings.return_value.all.return_value = []
        
        # get_measured_data_sizes 호출
        mock_result3 = MagicMock()
        mock_result3.mappings.return_value.all.return_value = []
        
        # get_vector_data 호출
        mock_result4 = MagicMock()
        mock_row4 = MagicMock()
        mock_row4.__getitem__.side_effect = lambda key: {
            "model_name": "model1",
            "serial_no": "serial1",
            "vector_visual_normed": [0.1, 0.2, 0.3]
        }[key]
        mock_result4.mappings.return_value.first.return_value = mock_row4
        
        # get_absolute_similarities 호출 (빈 딕셔너리 반환)
        mock_result5 = MagicMock()
        mock_result5.mappings.return_value.all.return_value = []  # 빈 결과
        
        mock_db_manager.execute_query.side_effect = [
            mock_result1,  # get_latest_measured_datum
            mock_result2,  # get_external_defects_info
            mock_result3,  # get_measured_data_sizes
            mock_result4,  # get_vector_data
            mock_result5   # get_absolute_similarities (빈 결과)
        ]

        with pytest.raises(ValueError, match="정규화된 벡터 데이터가 없습니다"):
            await get_serial_similarity_hits_from_defects(
                cruder=cruder,
                instrument_name="inst1",
                serial_no="serial1",
                top_n_rate=0.01
            )

    @pytest.mark.asyncio
    async def test_normalize_and_upsert_all_models_success(self, cruder, mock_db_manager):
        """normalize_and_upsert_all_models() 성공 케이스 테스트"""
        from WEB_SERVER.services.service import normalize_and_upsert_all_models
        from pathlib import Path
        
        # get_model_names 호출
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = ["model1", "model2"]
        
        # get_spec 호출
        mock_result2 = MagicMock()
        mock_row2 = MagicMock()
        mock_row2.__getitem__.side_effect = lambda key: {
            "id": 1,
            "path_sub_datafile": "test.parquet"
        }[key]
        mock_result2.mappings.return_value.first.return_value = mock_row2
        
        # get_measured_since_last_normalized 호출
        mock_result3 = MagicMock()
        mock_result3.mappings.return_value.all.return_value = []
        
        mock_db_manager.execute_query.side_effect = [
            mock_result1,  # get_model_names
            mock_result2,  # get_spec (model1)
            mock_result3,  # get_measured_since_last_normalized (model1)
            mock_result2,  # get_spec (model2)
            mock_result3,  # get_measured_since_last_normalized (model2)
        ]

        with patch('WEB_SERVER.services.service.get_spec_parquet', new_callable=AsyncMock) as mock_get_spec:
            mock_get_spec.return_value = (1, MagicMock())  # spec_id, spec DataFrame
            
            with patch('WEB_SERVER.services.service.process_and_upsert_vector_data', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = 0
                
                result = await normalize_and_upsert_all_models(
                    cruder=cruder,
                    dir_base_spec=Path("/test"),
                    model_name=None
                )

                assert isinstance(result, dict)
                assert "count" in result
                assert "fail_count" in result
                assert "fail_infos" in result

    @pytest.mark.asyncio
    async def test_normalize_and_upsert_all_models_with_failures(self, cruder, mock_db_manager):
        """normalize_and_upsert_all_models() 일부 모델 실패 케이스 테스트"""
        from WEB_SERVER.services.service import normalize_and_upsert_all_models
        from pathlib import Path
        
        # get_model_names 호출
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = ["model1", "model2"]
        
        mock_db_manager.execute_query.side_effect = [
            mock_result1,  # get_model_names
        ]

        with patch('WEB_SERVER.services.service_normalize.get_spec_parquet', new_callable=AsyncMock) as mock_get_spec:
            # model1은 성공, model2는 실패
            mock_get_spec.side_effect = [
                (1, MagicMock()),  # model1 성공
                ValueError("Spec not found")  # model2 실패
            ]
            
            with patch('WEB_SERVER.services.service_normalize.process_and_upsert_vector_data', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = 5
                
                result = await normalize_and_upsert_all_models(
                    cruder=cruder,
                    dir_base_spec=Path("/test"),
                    model_name=None
                )

                assert isinstance(result, dict)
                assert result["count"] == 5  # model1만 성공
                assert result["fail_count"] == 1  # model2 실패
                assert len(result["fail_infos"]) == 1

