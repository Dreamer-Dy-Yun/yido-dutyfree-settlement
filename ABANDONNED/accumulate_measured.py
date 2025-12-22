
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import date, timedelta
import sys
import glob

from CUSTOMIZED.cust_logger import logger


class MeasuredDataCollector:
    """
    parquet 파일들에서 measured 데이터를 수집하여 SpecAnalyzer에 제공
    
    ★ 주요 기능:
        - get()                             : parquet 파일들 로드
        - get_dataframe()                   : DataFrame 형태로 반환  
        - get_spec_analyzer_data()          : SpecAnalyzer 입력 형태로 반환
    """
    
    def __init__(self, measured_by:str, model_name: str, date_from: date, date_to: date):
        self.directory: Path = Path("")
        self.raw_data: pd.DataFrame = pd.DataFrame()
        self.date_from: date = date_from
        self.date_to: date = date_to


    def get_target_folder_list(self, target_path: Path, measured_by:str, model_name: str, date_from: date = None, date_to: date = None) -> List[Path]:
        """
        날짜 범위에 따른 대상 폴더 경로 리스트 반환
        
        Args:
            target_path: 기본 경로
            model_name: 모델명
            date_from: 시작 날짜
            date_to: 종료 날짜
            
        Returns:
            target_path/model_name/YYYY/MM/DD 형태의 폴더 경로 리스트
        """
        if not date_from or not date_to:
            return []
        
        folder_list = []
        current_date = date_from
        
        while current_date <= date_to:
            folder_path = target_path / model_name / str(current_date.year) / f"{current_date.month:02d}" / f"{current_date.day:02d}"
            folder_list.append(folder_path)
            current_date += timedelta(days=1)
        
        return folder_list    
    
    
    def get(self, target_path: Path, date_from: Optional[date] = None, date_to: Optional[date] = None) -> None:
        """
        parquet 파일들을 로드하고 기본 전처리 수행
        
        Args:
            directory: parquet 파일들이 있는 디렉토리 경로
            date_from: 시작 날짜 (포함)
            date_to: 종료 날짜 (포함)
        """
        self.directory = Path(target_path)
        self.date_from = date_from
        self.date_to = date_to
        
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")
        
        # parquet 파일들 로드
        parquet_files = glob.glob(str(self.directory / "*.parquet"))
        
        if not parquet_files:
            logger.warning(f"No parquet files found in {self.directory}")
            return
        
        # 데이터 수집
        dfs = []
        for file_path in parquet_files:
            try:
                df = pd.read_parquet(file_path)
                if 'measured' in df.columns:
                    dfs.append(df)
                    
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        if not dfs:
            logger.warning("No valid measured data found")
            return
        
        # 데이터 결합
        self.raw_data = pd.concat(dfs, ignore_index=True)
        
        # 날짜 필터링
        self._apply_date_filter()
        
        # 정렬
        self._sort_data()
    
    
    def _apply_date_filter(self) -> None:
        """날짜 필터링 적용"""
        if (self.date_from or self.date_to) and 'measured_date' in self.raw_data.columns:
            self.raw_data['measured_date'] = pd.to_datetime(self.raw_data['measured_date']).dt.date
            
            if self.date_from:
                self.raw_data = self.raw_data[self.raw_data['measured_date'] >= self.date_from]
                
            if self.date_to:
                self.raw_data = self.raw_data[self.raw_data['measured_date'] <= self.date_to]
    
    
    def _sort_data(self) -> None:
        """데이터 정렬"""
        sort_cols = []
        if 'model' in self.raw_data.columns:
            sort_cols.append('model')
        if 'measured_date' in self.raw_data.columns:
            sort_cols.append('measured_date')
        
        if sort_cols:
            self.raw_data = self.raw_data.sort_values(sort_cols)
    
    
    def get_dataframe(self, target_columns: List[str] = None) -> pd.DataFrame:
        """
        DataFrame 형태로 데이터 반환
        
        Args:
            target_columns: 반환할 컬럼 목록 (None이면 전체)
            
        Returns:
            처리된 DataFrame
        """
        if self.raw_data.empty:
            return pd.DataFrame()
        
        if target_columns:
            available_cols = [col for col in target_columns if col in self.raw_data.columns]
            return self.raw_data[available_cols].copy()
        
        return self.raw_data.copy()
    
    
    def get_measured_column(self) -> pd.Series:
        """measured 컬럼만 반환"""
        if 'measured' in self.raw_data.columns:
            return self.raw_data['measured']
        return pd.Series(dtype=float)
    
    
    def get_spec_analyzer_data(self, group_by_model: bool = True) -> List[List[float]]:
        """
        SpecAnalyzer 입력 형태로 데이터 변환
        
        Args:
            group_by_model: 모델별로 그룹핑할지 여부
            
        Returns:
            list[list[float]]: SpecAnalyzer 호환 데이터
                              행 = 측정 세션, 열 = 측정 지점
        """
        if self.raw_data.empty or 'measured' not in self.raw_data.columns:
            return []
        
        if group_by_model and 'model' in self.raw_data.columns:
            result = []
            for model in sorted(self.raw_data['model'].unique()):
                model_data = self.raw_data[self.raw_data['model'] == model]['measured'].tolist()
                if model_data:
                    result.append(model_data)
            return result
        else:
            # 전체 데이터를 하나의 그룹으로
            measured_data = self.raw_data['measured'].tolist()
            return [measured_data] if measured_data else []


# 편의 함수들 (기존 API 호환성) >> 이하는 Cursor가 만든 아무짝에도 쓸모 없는 코드. 이놈은 뭐 시켜 놓으면 진짜 쓸데 없는것만 처 만듦
def accumulate_measured_data(directory: Path, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
    """
    편의 함수: 간단한 데이터 수집
    
    Args:
        directory: parquet 파일들이 있는 디렉토리 경로
        date_from: 시작 날짜 (포함)
        date_to: 종료 날짜 (포함)
    
    Returns:
        처리된 DataFrame
    """
    collector = MeasuredDataCollector()
    collector.get(directory, date_from, date_to)
    return collector.get_dataframe()


def get_measured_column_only(directory: Path, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.Series:
    """
    편의 함수: measured 열만 반환
    
    Args:
        directory: parquet 파일들이 있는 디렉토리 경로
        date_from: 시작 날짜 (포함)
        date_to: 종료 날짜 (포함)
    
    Returns:
        measured 열만 포함된 Series
    """
    collector = MeasuredDataCollector()
    collector.get(directory, date_from, date_to)
    return collector.get_measured_column()


def get_spec_analyzer_data(directory: Path, date_from: Optional[date] = None, date_to: Optional[date] = None, group_by_model: bool = True) -> List[List[float]]:
    """
    SpecAnalyzer용 데이터 준비
    
    Args:
        directory: parquet 파일들이 있는 디렉토리 경로
        date_from: 시작 날짜 (포함)
        date_to: 종료 날짜 (포함)
        group_by_model: 모델별로 그룹핑할지 여부
    
    Returns:
        list[list[float]]: SpecAnalyzer 호환 데이터
    """
    collector = MeasuredDataCollector()
    collector.get(directory, date_from, date_to)
    return collector.get_spec_analyzer_data(group_by_model)


# 테스트 함수
def test_data_collection():
    """테스트용 데이터 수집"""
    test_dir = Path("./test_parquet_files/")
    
    if not test_dir.exists():
        print(f"Test directory not found: {test_dir}")
        return
    
    print("=== MeasuredDataCollector 테스트 ===")
    
    # 1. 기본 사용법
    collector = MeasuredDataCollector()
    collector.get(test_dir)
    
    df_result = collector.get_dataframe()
    print(f"수집된 데이터: {df_result.shape}")
    print(df_result.head())
    
    # 2. SpecAnalyzer 형태 변환
    spec_data = collector.get_spec_analyzer_data(group_by_model=True)
    print(f"\nSpecAnalyzer 형태: {len(spec_data)} groups")
    for i, group in enumerate(spec_data):
        print(f"  Group {i}: {len(group)} measurements")
    
    # 3. 편의 함수 테스트
    from datetime import date
    filtered_data = get_spec_analyzer_data(
        test_dir, 
        date_from=date(2025, 1, 15), 
        date_to=date(2025, 2, 15)
    )
    print(f"\n날짜 필터링: {len(filtered_data)} groups")


if __name__ == "__main__":
    test_data_collection()