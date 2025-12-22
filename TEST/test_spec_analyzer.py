###########################################
# Module name : test_spec_analyzer.py
# 테스트 대상 : ANALYZER.spec_analyzer.SpecAnalyzer, AnalyzedFileExporter
# Written by : Auto (Cursor AI)
###########################################

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import tempfile
from ANALYZER.spec_analyzer import SpecAnalyzer, AnalyzedFileExporter


class TestSpecAnalyzer:
    """SpecAnalyzer 클래스 테스트"""

    @pytest.fixture
    def sample_spec(self):
        """테스트용 Spec DataFrame 생성"""
        return pd.DataFrame({
            "index": [1, 2, 3],
            "part_name": ["part1", "part2", "part3"],
            "spec": [500.0, 600.0, 700.0],
            "unit": ["ohm", "ohm", "ohm"],
            "ucv": [800.0, 900.0, 1000.0],
            "lcv": [200.0, 300.0, 400.0],
            "usl": [750.0, 850.0, 950.0],
            "lsl": [250.0, 350.0, 450.0],
            "reverse_tolerance": [False, False, False],
            "skip": [False, False, False]
        })

    @pytest.fixture
    def sample_data(self):
        """테스트용 측정 데이터 생성"""
        return [
            [500.0, 600.0, 700.0],
            [510.0, 610.0, 710.0],
            [490.0, 590.0, 690.0],
            [520.0, 620.0, 720.0],
            [480.0, 580.0, 680.0],
        ]

    def test_spec_analyzer_init(self, sample_spec):
        """SpecAnalyzer 초기화 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        
        assert analyzer.spec is not None
        assert analyzer.resolution == 100
        assert analyzer.list_spec is not None
        assert len(analyzer.list_spec) == 3

    def test_spec_analyzer_run(self, sample_spec):
        """run() 메서드 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        
        assert analyzer.list_ucv is not None
        assert analyzer.list_lcv is not None
        assert analyzer.list_usl is not None
        assert analyzer.list_lsl is not None
        assert len(analyzer.list_spec) == 3
        assert len(analyzer.list_part_name) == 3

    def test_spec_analyzer_quantize_spec_only(self, sample_spec):
        """quantize() Spec만 양자화 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        
        assert analyzer.spec_quantized is not None
        assert analyzer.usl_quantized is not None
        assert analyzer.lsl_quantized is not None
        assert len(analyzer.spec_quantized) == 3

    def test_spec_analyzer_analyze(self, sample_spec, sample_data):
        """analyze() 메서드 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        result = analyzer.analyze(sample_data)
        
        assert result is analyzer
        assert analyzer.data_original is not None
        assert analyzer.data_quantized is not None
        assert analyzer.pmf is not None
        assert analyzer.list_mu is not None
        assert analyzer.list_sigma is not None

    def test_spec_analyzer_analyze_dimension_mismatch(self, sample_spec):
        """analyze() 차원 불일치 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        
        # spec rows와 data columns가 일치하지 않는 경우
        wrong_data = [[1.0, 2.0]]  # 2개 컬럼인데 spec은 3개
        
        with pytest.raises(ValueError, match="spec rows must match data columns"):
            analyzer.analyze(wrong_data)

    def test_spec_analyzer_compute_pmf(self, sample_spec, sample_data):
        """compute_pmf() 메서드 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        analyzer.analyze(sample_data)
        
        assert analyzer.pmf is not None
        assert analyzer.pmf.shape == (3, 100)  # 3개 측정 포인트, 100개 bin
        # PMF 값은 0 이상 1 이하여야 함
        assert np.all(analyzer.pmf >= 0)
        assert np.all(analyzer.pmf <= 1)

    def test_spec_analyzer_compute_cpk(self, sample_spec, sample_data):
        """compute_cpk() 메서드 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        analyzer.analyze(sample_data)
        
        assert analyzer.list_mu is not None
        assert analyzer.list_sigma is not None
        assert analyzer.list_cpk is not None
        assert analyzer.list_type_cpk is not None
        assert len(analyzer.list_cpk) == 3
        assert len(analyzer.list_type_cpk) == 3

    def test_spec_analyzer_count_inspection_outcomes(self, sample_spec, sample_data):
        """count_inspection_outcomes() 메서드 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=100)
        analyzer.analyze(sample_data)
        
        assert analyzer.list_exceeded_usl is not None
        assert analyzer.list_exceeded_lsl is not None
        assert analyzer.list_exceeded_spec_total is not None
        assert analyzer.list_between_spec_total is not None
        assert len(analyzer.list_exceeded_usl) == 3

    def test_spec_analyzer_different_resolution(self, sample_spec):
        """다른 resolution 값 테스트"""
        analyzer = SpecAnalyzer(sample_spec, resolution=200)
        assert analyzer.resolution == 200


class TestAnalyzedFileExporter:
    """AnalyzedFileExporter 클래스 테스트"""

    @pytest.fixture
    def sample_analyzer(self):
        """테스트용 SpecAnalyzer 생성"""
        spec = pd.DataFrame({
            "index": [1, 2],
            "part_name": ["part1", "part2"],
            "spec": [500.0, 600.0],
            "unit": ["ohm", "ohm"],
            "ucv": [800.0, 900.0],
            "lcv": [200.0, 300.0],
            "usl": [750.0, 850.0],
            "lsl": [250.0, 350.0],
            "reverse_tolerance": [False, False],
            "skip": [False, False]
        })
        analyzer = SpecAnalyzer(spec, resolution=100)
        analyzer.analyze([[500.0, 600.0], [510.0, 610.0]])
        return analyzer

    def test_analyzed_file_exporter_init(self, sample_analyzer):
        """AnalyzedFileExporter 초기화 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        assert exporter.model == "test_model"
        assert exporter.sa is sample_analyzer
        assert exporter.file_name_without_extension == ""

    def test_set_file_name_without_extension(self, sample_analyzer):
        """set_file_name_without_extension() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        query_from = date(2025, 1, 1)
        query_to = date(2025, 1, 31)
        execution_time = datetime(2025, 1, 15, 10, 0, 0)
        
        result = exporter.set_file_name_without_extension(query_from, query_to, execution_time)
        
        assert result == exporter.file_name_without_extension
        assert "test_model" in result
        assert "20250101" in result
        assert "20250131" in result

    def test_serialized_meta_data(self, sample_analyzer):
        """serialized_meta_data() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        data = exporter.serialized_meta_data()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert "specInfo" in data[0]
        assert "chartSpecLine" in data[0]
        assert data[0]["specInfo"]["idx"] == 1
        assert data[0]["specInfo"]["partName"] == "part1"

    def test_serialized_pmf_data(self, sample_analyzer):
        """serialized_pmf_data() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        data = exporter.serialized_pmf_data()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert "data" in data[0]
        assert "judgementInfo" in data[0]
        assert "cpkInfo" in data[0]
        assert isinstance(data[0]["data"], list)

    def test_serialized_trend_data(self, sample_analyzer):
        """serialized_trend_data() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        data = exporter.serialized_trend_data()
        
        assert isinstance(data, dict)
        assert "1" in data or 1 in data
        assert "navigationIdx" in data.get("1", data.get(1, {}))

    def test_serialized_zero_pmf_data(self, sample_analyzer):
        """serialized_zero_pmf_data() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        data = exporter.serialized_zero_pmf_data()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["judgementInfo"]["ok"]["total"] == 0

    def test_raise_error_if_file_name_not_set(self, sample_analyzer):
        """raise_error_if_file_name_not_set() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        
        with pytest.raises(ValueError, match="file_name_without_extension is not set"):
            exporter.to_json_file(Path("/tmp"), "meta", {})

    def test_to_json_file(self, sample_analyzer):
        """to_json_file() 테스트"""
        exporter = AnalyzedFileExporter(sample_analyzer, "test_model")
        exporter.set_file_name_without_extension(date(2025, 1, 1), date(2025, 1, 31))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {"test": "data"}
            exporter.to_json_file(Path(tmpdir), "meta", test_data)
            
            # 파일이 생성되었는지 확인
            files = list(Path(tmpdir).glob("*.json"))
            assert len(files) == 1
            assert "(meta)" in files[0].name

