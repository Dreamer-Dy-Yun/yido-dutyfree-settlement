###########################################
# Module name : test_ict_data_extractor.py
# 테스트 대상 : OPEN_SSH.ict_data_extractor.ICTDataExtractor
# Written by : Auto (Cursor AI)
###########################################

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
from OPEN_SSH.ict_data_extractor import ICTDataExtractor


class TestICTDataExtractor:
    """ICTDataExtractor 클래스 테스트"""

    @pytest.fixture
    def extractor(self):
        """ICTDataExtractor 인스턴스 생성"""
        return ICTDataExtractor()

    def test_init(self, extractor):
        """초기화 테스트"""
        assert extractor.data_path == Path("")
        assert extractor.encoding == ""
        assert extractor.model_name == ""
        assert extractor.measured_by == ""
        assert extractor.serial_no == ""
        assert extractor.short_group_list == []
        assert extractor.measured_points == 0
        assert extractor.df_original.empty
        assert extractor.df_spec.empty
        assert extractor.df_measured.empty

    def test_suggest_file_name_spec(self, extractor):
        """suggest_file_name_spec 프로퍼티 테스트"""
        extractor.measured_by = "inst1"
        extractor.model_name = "model1"
        extractor.measured_at = datetime(2025, 1, 15, 10, 30, 0)
        
        result = extractor.suggest_file_name_spec
        
        assert "inst1" in result
        assert "model1" in result
        assert "20250115" in result
        assert "103000" in result
        assert result.endswith(".parquet")

    def test_suggest_file_name_measured(self, extractor):
        """suggest_file_name_measured 프로퍼티 테스트"""
        extractor.measured_by = "inst1"
        extractor.serial_no = "serial1"
        extractor.measured_at = datetime(2025, 1, 15, 10, 30, 0)
        
        result = extractor.suggest_file_name_measured
        
        assert "inst1" in result
        assert "serial1" in result
        assert "20250115" in result
        assert "103000" in result
        assert result.endswith(".parquet")

    def test_columns_for_spec(self):
        """_columns_for_spec() 정적 메서드 테스트"""
        result = ICTDataExtractor._columns_for_spec()
        
        assert isinstance(result, set)
        assert "index" in result
        assert "Part_Name" in result
        assert "Std" in result
        assert "Hi_Limit" in result
        assert "Lo_Limit" in result

    def test_columns_for_measured(self):
        """_columns_for_measured() 정적 메서드 테스트"""
        result = ICTDataExtractor._columns_for_measured()
        
        assert isinstance(result, set)
        assert "index" in result
        assert "Step" in result
        assert "Act" in result
        assert "Meas" in result

    def test_get_essential_column_indexes_success(self, extractor):
        """_get_essential_column_indexes() 성공 케이스 테스트"""
        df = pd.DataFrame({
            "index": [1, 2, 3],
            "Part_Name": ["part1", "part2", "part3"],
            "Std": [100, 200, 300],
            "other": [10, 20, 30]
        })
        
        essential_columns = {"index", "Part_Name", "Std"}
        original_columns = essential_columns.copy()
        result = extractor._get_essential_column_indexes(df, essential_columns)
        
        assert result == [0, 1, 2]
        # essential_columns는 메서드 내부에서 수정됨
        assert len(essential_columns) == 0  # 모든 컬럼이 찾아짐

    def test_get_essential_column_indexes_missing_column(self, extractor):
        """_get_essential_column_indexes() 컬럼 없음 테스트"""
        df = pd.DataFrame({
            "index": [1, 2, 3],
            "Part_Name": ["part1", "part2", "part3"]
        })
        
        essential_columns = {"index", "Part_Name", "Std"}
        
        with pytest.raises(ValueError, match="Column.*is not in the header"):
            extractor._get_essential_column_indexes(df, essential_columns)

    def test_derive_u_spec(self):
        """derive_u_spec() 정적 메서드 테스트"""
        result = ICTDataExtractor.derive_u_spec(100.0, 50.0)
        
        assert result == 75.0  # (100 + 50) / 2

    def test_derive_d_spec(self):
        """derive_d_spec() 정적 메서드 테스트"""
        result = ICTDataExtractor.derive_d_spec(100.0, 50.0)
        
        assert result == 25.0  # (100 - 50) / 2

    def test_derive_ucv(self):
        """derive_ucv() 정적 메서드 테스트"""
        # u_spec = 75.0, d_spec = 25.0
        result = ICTDataExtractor.derive_ucv(75.0, 25.0, adjustment_factor=10.0)
        
        assert result == 325.0  # 75.0 + (25.0 * 10.0)

    def test_derive_lcv(self):
        """derive_lcv() 정적 메서드 테스트"""
        # u_spec = 75.0, d_spec = 25.0
        result = ICTDataExtractor.derive_lcv(75.0, 25.0, adjustment_factor=10.0)
        
        assert result == -175.0  # 75.0 - (25.0 * 10.0)

    def test_derive_visual_scale(self):
        """derive_visual_scale() 정적 메서드 테스트"""
        result = ICTDataExtractor.derive_visual_scale(100.0, 0.0, scale_factor=10.0)
        
        assert result == 0.1  # 10.0 / (100.0 - 0.0)

    @patch('builtins.open', new_callable=mock_open, read_data="Date,2025-01-15 10:30:00\nPCB_Name,model1\nSerial_No,serial1\n")
    def test_get_with_mock_file(self, mock_file, extractor):
        """get() Mock 파일 테스트"""
        test_path = Path("/test/path.csv")
        
        # Mock 설정
        with patch.object(extractor, '_validate_data'), \
             patch.object(extractor, '_parse_and_dispatch_lines'), \
             patch.object(extractor, 'get_original'), \
             patch.object(extractor, '_validate_dataframe_columns'), \
             patch.object(extractor, '_get_essential_column_indexes', return_value=[0, 1]), \
             patch.object(extractor, 'get_parquet_measured'), \
             patch.object(extractor, 'get_parquet_spec'), \
             patch.object(extractor, '_derive_norm_factors'):
            
            result = extractor.get(test_path, measured_by="inst1", encoding="utf-8")
            
            assert result is extractor
            assert extractor.data_path == test_path
            assert extractor.measured_by == "inst1"
            assert extractor.encoding == "utf-8"

    def test_get_already_has_data(self, extractor):
        """get() 이미 데이터가 있는 경우 테스트"""
        extractor.model_name = "model1"
        extractor.df_original = pd.DataFrame({"col1": [1, 2, 3]})
        
        result = extractor.get(Path("/test/path.csv"))
        
        assert result is extractor
        # 이미 데이터가 있으면 추가 처리를 하지 않고 자기 자신 반환

