###########################################
# Module name : Customized
# Module functions : ICTDataExtractor, Raise, Parser
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.01
# Updated at : 2025.08.08
# Supported by : 
# Note : 
#        2025.07.31 : _add_visual_spec_limits 추가 및 관련 로직 변경
#        2025.08.08 : delta_spec_ratio 추가
#        2025.09.12 : 신ICT와 구ICT간의 컬럼 상이로 인하여 컬럼 체크 작성
#                     (_get_essential_column_indexes 등 추가)
#        2025.09.15 : 변경 : 초기 인덱스를 1로 변경(기존 0부터 시작)
#                     Bug Fix : encoding 추가 csv reading 시 encoding을 누락
############################################


from datetime import datetime
import os
from io import StringIO
from pathlib import Path
from CUSTOMIZED.cust_logger import logger, timer
from typing import List, cast
import pandas as pd
from dateutil import parser
import numpy as np

class ICTDataExtractor:
    """
    ★ICT 검사 데이터 파일(CSV)을 파싱하고, 주요 정보를 추출하는 클래스.
        - model             [str]               : PCB 코드(PCB 종류)
        - serial_no         [str]               : 시리얼 넘버(개별 PCB)
        - measured_at       [DateTime]          : 측정 시작시간
        - short_group_list  [list[str]]         : Short Group 목록
        - df_spec()         [Pandas.DataFrame]  : 소자별 스펙 목록을 담은 Data Frame
        - df_measured()     [Pandas.DataFrame]  :  소자별 측정 정보 목록을 담은 Data Frame
    """
    # TODO : 추후 Numpy 연산으로 변경 할 것

    def __init__(self):
        self.data_path: Path = Path("")
        self.encoding: str = ""
        self.model_name: str = ""
        self.measured_by: str = ""
        self.measured_at: datetime = datetime.now()
        self.serial_no: str = ""
        self.short_group_list: list[str] = []
        self.measured_points: int = 0
        self.adj_val_infinity: float = 0.0
        self.adj_val_extreme: float = 0.0
        self.delta_spec_ratio: float = 0.0
        self.df_original: pd.DataFrame = pd.DataFrame()
        self.df_spec: pd.DataFrame = pd.DataFrame()
        self.df_measured: pd.DataFrame = pd.DataFrame()
        self._csv_records: list = []
        self._state_handlers: dict = self._set_state_handlers()
        self._read_short_group = False
        logger.info(f"ICT_DataReader initialized with file: {self.data_path}")

    @property
    def suggest_file_name_spec(self) ->str:
        return f"{self.measured_by}_{self.model_name}({self.measured_at.strftime('%Y%m%d %H%M%S')}).parquet" 
    
    @property
    def suggest_file_name_measured(self) ->str:
        return f"{self.measured_by}_{self.serial_no}({self.measured_at.strftime('%Y%m%d %H%M%S')}).parquet" 
    
    def get(self, data_path: Path, measured_by: str = "", encoding: str = 'euc-kr', adj_val_infinity: float = 2) -> 'ICTDataExtractor':
        """
        data_path   [pathlib.Path]  : ICT 추출 대상 데이터 CSV
        measured_by [str]           : ICT 측정 호기(번호던지 별칭이던지는 추후 논의) 
        encoding    [str]           : 대상 CSV파일의 인코딩 종류. (기본값 : euc-kr)
        """
        if all([self.model_name, not self.df_original.empty]):
            # 어떤 데이터라도 있으면 자기 자신 반환
            # 싱글톤 아님에 유의
            return self
        
        self._validate_data(data_path)

        self.data_path = data_path
        self.encoding = encoding
        self.measured_by = measured_by
        header_spec : list[int] = []
        header_measured : list[int] = []

        # timer.start("IO + CPU")
        self._parse_and_dispatch_lines() # file I/O
        # timer.end("IO + CPU")
        # timer.start("CPU")
        self.get_original(encoding=self.encoding)

        self._validate_dataframe_columns()

        # 동일한 컬럼명이 존재해서 문제..
        header_spec : list[int] = self._get_essential_column_indexes(self.df_original, self._columns_for_spec())
        header_measured : list[int] = self._get_essential_column_indexes(self.df_original, self._columns_for_measured())

        self.get_parquet_measured(header_measured)
        self.get_parquet_spec(header_spec)
        self._derive_norm_factors(adj_val_infinity)
        # timer.end("CPU")
        logger.info("get() completed successfully")
        
        return self

    @staticmethod
    def _columns_for_spec() -> set[str]:
        ec : set[str] = set()
        ec.add("index")
        ec.add("Part_Name")
        ec.add("Location")
        ec.add("Std")
        ec.add("un.1")
        ec.add("Hi_Limit")
        ec.add("un.3")
        ec.add("Lo_Limit")
        ec.add("un.4")
        ec.add("Jump")
        ec.add("Hi_Pin")
        ec.add("Lo_Pin")
        # ec.add("Rect.Loc") # 신ICT에서는 사용하지 않음
        return ec

    @staticmethod
    def _columns_for_measured() -> set[str]:
        ec : set[str] = set()
        ec.add("index")
        ec.add("Step")
        ec.add("Act")
        ec.add("Meas")
        ec.add("Retray")
        ec.add("Wait")
        ec.add("R0C0")
        ec.add("MSG")
        return ec


    def _get_essential_column_indexes(self, df_original: pd.DataFrame, essential_columns: set[str]) -> list[int]:

        list_header: list[int] = df_original.columns.to_list()
        list_columns: list[int] = []

        for column in range(len(list_header)):
            if list_header[column] in essential_columns:
                essential_columns.remove(list_header[column])
                list_columns.append(column)

        if len(essential_columns) != 0:
            raise ValueError(f"Column {essential_columns} is not in the header")

        return list_columns
    
    def _parse_and_dispatch_lines(self) -> None:
        try :
            # 필요시 인코딩 추정기능 삽입
            with open(self.data_path, 'r', encoding=self.encoding, errors='replace') as x_file:
                lines = x_file.readlines()
                self._read_short_group: bool = False
                state: str = ""
                
                for line in lines:
                    state = state if state == "Step" else self._get_value(line, 0).strip().replace("\n", "")
                    if self._is_valid_line(line):
                        handler = self._state_handlers.get(state)
                        if handler:
                            handler(line)

                        if self._read_short_group:
                            self._read_short_group = self._add_short_group_list(self._get_value(line, 0))
        except UnicodeDecodeError as e:
            logger.error(f"파일 인코딩 오류: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"알 수 없는 에러: {e}", exc_info=True)
            raise

    def get_original(self, index_name: str = "index", start_index: int = 1, encoding: str = "euc-kr") -> pd.DataFrame:
        try :
            if self._csv_records:
                self.df_original = pd.read_csv(StringIO("\n".join(self._csv_records)), encoding=encoding)
                self.df_original = self.df_original.reset_index(drop=False, names=index_name)
                self.df_original[index_name] = self.df_original[index_name] + start_index
                self.measured_points = self.df_original.shape[0] # 행 수 반환
            else :
                logger.error(f"데이터 없음: {self.data_path}")
                raise ValueError(f"Data does not exists : {self.data_path}")
        except pd.errors.ParserError as e:
            logger.error(f"CSV 파싱 오류: {e}")
            raise 
        except ValueError as e:
            logger.error(f"값 변환 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"알 수 없는 에러: {e}", exc_info=True)
            raise

    
    def get_parquet_spec(self, target_col_numbers: List[int] = [0, 2, 3, 6, 7, 12, 13, 14, 15, 23, 24, 31]) -> pd.DataFrame:
        """
        df_spec에서 model, updated_at(measured_at) 컬럼이 추가.
        """

        if self.df_spec.empty:
            self.df_spec = self._get_columns_by_index(target_col_numbers).copy()
            self.df_spec.rename(columns={'Part_Name': 'part_name'}, inplace=True)
            self.df_spec.rename(columns={'Location': 'location'}, inplace=True) # TODO : 추후 내용 원본 데이터 포맷 확인되면 거기에 맞추어 Arrow struct로 변환
            self.df_spec.rename(columns={'Std': 'spec'}, inplace=True)
            self.df_spec.rename(columns={'un.1': 'unit'}, inplace=True)
            self.df_spec.rename(columns={'Hi_Limit': 'usl'}, inplace=True)
            self.df_spec.rename(columns={'un.3': 'usl.unit'}, inplace=True)
            self.df_spec.rename(columns={'Lo_Limit': 'lsl'}, inplace=True)
            self.df_spec.rename(columns={'un.4': 'lsl.unit'}, inplace=True)
            self.df_spec.rename(columns={'Jump': 'skip'}, inplace=True)
            self.df_spec.rename(columns={'Hi_Pin': 'high_voltage_pin'}, inplace=True)
            self.df_spec.rename(columns={'Lo_Pin': 'low_voltage_pin'}, inplace=True)
            # self.df_spec.rename(columns={'Rect.Loc': 'rect_location'}, inplace=True)

            cols_df: list = ['spec', 'usl', 'lsl']
            
            self.df_spec[cols_df] = self.df_spec[cols_df].apply(pd.to_numeric, errors='coerce').astype('Float64')  

            self._convert_spec_limit_to_value(self.df_spec, 'spec', 'usl', 'usl.unit')
            self._convert_spec_limit_to_value(self.df_spec, 'spec', 'lsl', 'lsl.unit')

            self.df_spec = self.df_spec.drop(columns=['usl.unit', 'lsl.unit'])

            return self.df_spec
        else:
            for_parquet: pd.DataFrame = self.df_spec.copy()
            for_parquet["model_name"] = self.model_name
            for_parquet["updated_at"] = self.measured_at
            return for_parquet

    def get_parquet_measured(self, target_col_numbers: List[int] = [0, 1, 4, 8, 22, 25, 27, 33]) -> pd.DataFrame:
        """
        df_measured에서 model, serial_no, measured_at 컬럼이 추가.
        """

        if self.df_measured.empty:
            self.df_measured = self._get_columns_by_index(target_col_numbers).copy()
            self.df_measured.rename(columns={'Step': 'step'}, inplace=True)
            self.df_measured.rename(columns={'Act': 'actual_value'}, inplace=True)
            self.df_measured.rename(columns={'Meas': 'measured_value'}, inplace=True)
            self.df_measured.rename(columns={'Retray': 'retry'}, inplace=True)
            self.df_measured.rename(columns={'Wait': 'wait'}, inplace=True)
            self.df_measured.rename(columns={'R0C0': 'correction_value'}, inplace=True)
            self.df_measured.rename(columns={'MSG': 'result'}, inplace=True)
            return self.df_measured

        else :
            for_parquet: pd.DataFrame = self.df_measured.copy() 
            for_parquet["model_name"] = self.model_name
            for_parquet["serial_no"] = self.serial_no
            for_parquet["measured_by"] = self.measured_by
            for_parquet["measured_at"] = self.measured_at
            return for_parquet

    def _derive_norm_factors(self, adj_val_infinity: float = 10, adj_val_extreme: float = 10) -> pd.DataFrame:
        """
        self.df_spec에 벡터화 연산으로 u_spec, d_spec, ucv, lcv, visual_scale 컬럼을 추가.
        
        매개변수:
            adj_val_infinity (float): UCV/LCV 계산에 사용되는 조정 계수 (기본값: 10)
            adj_val_extreme (float): 극값 기준으로 visual_scale 계산에 사용되는 스케일 계수 (기본값: 10)
        """
        self.adj_val_infinity = adj_val_infinity
        self.adj_val_extreme = adj_val_extreme 
        self.delta_spec_ratio = 1/adj_val_infinity

        # 빈 데이터 프레임 여부 확인
        self._validate_dataframe(self.df_spec)

        # TODO : 컬럼내용 확인은 추후.

        # 역공차 적용
        self._derive_reverse_tolerance_vectorize()

        # 상/하한값이 무한대일 경우의 값 조정
        self.df_spec = self._add_visual_spec_limits(adj_val_infinity/2)
        # self.df_spec = self._adjust_usl(adj_val_infinity/2)
        # self.df_spec = self._adjust_lsl(adj_val_infinity/2)

        # 값 조정
        self._derive_u_spec_vectorize()
        self._derive_d_spec_vectorize()
        self._derive_ucv_vectorize(adj_val_infinity)
        self._derive_lcv_vectorize(adj_val_infinity)
        self._derive_visual_scale_vectorize(adj_val_extreme)

        # skip 추가
        self._derive_skip_vectorize()
        
        return self.df_spec

    def _add_visual_spec_limits(self, adjustment_factor: float = 5) -> pd.DataFrame:
        '''
        스펙 상/하한 값이 ±무한대이면, 반대편 스펙 제한 값으로 조정
        if USL = +∞ : USL = Spec + (Spec - LSL) * adjustment_factor
        if LSL = -∞ : LSL = Spec - (USL - Spec) * adjustment_factor
        **SPEC 상/하한이 모두 무한대인 경우는 측정 이유 자체가 없으니 이하의 코드에서는 고려되지 않음. 필요시 추가 할 것.
        '''

        df = self.df_spec

        # 무한대인 spec limit을 찾는 마스크
        # TODO : 원본파일 무한대 처리 재확인 필요
        # 측정 방식에 따라(ex : 전압) -inf도 존재 가능할 것이라 봄.
        # inf_mask_usl: pd.Series = pd.to_numeric(df['usl'], errors='coerce') == np.inf  #중복 연산으로 인한 성능저하(결과는 맞음)
        # inf_mask_lsl: pd.Series = pd.to_numeric(df['lsl'], errors='coerce') == -np.inf  #중복 연산으로 인한 성능저하(결과는 맞음)
        
        inf_mask_usl : np.ndarray[np.bool_] = np.isposinf(df['usl'].to_numpy()) # 벡터화 연산
        inf_mask_lsl : np.ndarray[np.bool_] = np.isneginf(df['lsl'].to_numpy()) # 벡터화 연산

        result = self.df_spec.copy()
        result['visual_usl'] = df['usl']
        result['visual_lsl'] = df['lsl']

        result.loc[inf_mask_usl, 'usl'] = np.inf 
        result.loc[inf_mask_lsl, 'lsl'] = -np.inf 

        mask_specs = df.loc[inf_mask_usl, 'spec'] 
        mask_spec_limits = df.loc[inf_mask_usl, 'lsl']
        result.loc[inf_mask_usl, 'visual_usl'] = mask_specs + (mask_specs - mask_spec_limits) * adjustment_factor

        mask_specs = df.loc[inf_mask_lsl, 'spec'] 
        mask_spec_limits = df.loc[inf_mask_lsl, 'usl']
        result.loc[inf_mask_lsl, 'visual_lsl'] = mask_specs + (mask_specs - mask_spec_limits) * adjustment_factor
        
        return result


    def _adjust_usl(self, adjustment_factor: float = 5) -> pd.DataFrame:
        # TODO : 사용 안함. 삭제 예정
        '''
        # 사용 안함. 대신 add_visual_spec_limits 사용
        스펙 상한 값이 무한대이면, 스펙 하한의 값을 기준으로 스펙 상한 값을 조정 (벡터 연산)
        if USL = +∞ : USL = Spec + (Spec - LSL) * adjustment_factor
        '''

        df = self.df_spec

        # 무한대인 USL을 찾는 마스크
        inf_mask = df['usl'] == float('inf')
        
        # 무한대가 없으면 원본 반환 (copy 불필요)
        if not inf_mask.any():
            return df
        
        # 무한대가 있는 경우에만 copy
        result = df.copy()
        result.loc[inf_mask, 'usl'] = df.loc[inf_mask, 'spec'] + (df.loc[inf_mask, 'spec'] - df.loc[inf_mask, 'lsl']) * adjustment_factor
        
        return result

    def _adjust_lsl(self, adjustment_factor: float = 5) -> pd.DataFrame:
        # TODO : 사용 안함. 삭제 예정
        '''
        # 사용 안함. 대신 add_visual_spec_limits 사용
        스펙 하한 값이 무한대이면, 스펙 상한의 값을 기준으로 스펙 하한 값을 조정 (벡터 연산)
        if LSL = -∞ : LSL = Spec - (USL - Spec) * adjustment_factor
        '''
        df = self.df_spec
        
        # 무한대인 LSL을 찾는 마스크
        inf_mask = df['lsl'] == float('-inf')
        
        # 무한대가 없으면 원본 반환 (copy 불필요)
        if not inf_mask.any():
            return df
        
        # 무한대가 있는 경우에만 copy
        result = df.copy()
        result.loc[inf_mask, 'lsl'] = df.loc[inf_mask, 'spec'] - (df.loc[inf_mask, 'usl'] - df.loc[inf_mask, 'spec']) * adjustment_factor
        
        return result
    
    
    def _derive_reverse_tolerance_vectorize(self) -> None:
        """(벡터 연산) 
        역공차 여부 판단
        if spec > usl or spec < lsl : reverse_tolerance = True
        """
        df = self.df_spec
        df['reverse_tolerance'] = (df['spec'] > df['usl']) | (df['spec'] < df['lsl'])

        # 각각의 reverse_tolerance = True인 경우, usl과 lsl을 서로 바꿈
        mask : np.ndarray[np.bool_] = df['reverse_tolerance'].to_numpy()   # bool ndarray (복사 없음)

        usl : np.ndarray[np.float64] = df['usl'].to_numpy(copy=False)       
        lsl : np.ndarray[np.float64] = df['lsl'].to_numpy(copy=False)

        idx : np.ndarray[np.int32] = np.where(mask)[0]  # True 행 인덱스만
        tmp : np.ndarray[np.float64] = usl[idx].copy()  # 필요한 부분만 임시 복사 (복사 없음)
        usl[idx] = lsl[idx]
        lsl[idx] = tmp
        
        

    def _derive_skip_vectorize(self) -> None:
        """(벡터 연산) 
        if Jump == 1 : skip = True
        else : skip = False
        """
        df = self.df_spec
        df['skip'] = df['skip'].eq(1)

    def _derive_u_spec_vectorize(self) -> None:
        """(벡터 연산) μ_Spec = (USL + LSL)/2"""
        df = self.df_spec
        df['u_spec'] = (df['visual_usl'] + df['visual_lsl']) / 2

    def _derive_d_spec_vectorize(self) -> None:
        """(벡터 연산) ΔS = (USL - LSL)/2"""
        df = self.df_spec
        df['d_spec'] = (df['visual_usl'] - df['visual_lsl']) / 2

    def _derive_ucv_vectorize(self, adjustment_factor: float = 10) -> None:
        """(벡터 연산) μ_Spec + n*ΔS (상극값, n=adjustment_factor)"""
        df = self.df_spec
        df['ucv'] = df['u_spec'] + (df['d_spec'] * adjustment_factor)

    def _derive_lcv_vectorize(self, adjustment_factor: float = 10) -> None:
        """(벡터 연산) μ_Spec - n*ΔS (하극값, n=adjustment_factor)"""
        df = self.df_spec
        df['lcv'] = df['u_spec'] - (df['d_spec'] * adjustment_factor)
    
    def _derive_visual_scale_vectorize(self, scale_factor: float = 10) -> None:
        """(벡터 연산) visual_scale = scale_factor / (ucv - lcv)"""
        df = self.df_spec
        df['visual_scale'] = scale_factor / (df['ucv'] - df['lcv'])

    @staticmethod
    def derive_u_spec(usl: float , lsl: float) -> float:
        '''
        Fall back / Debug 용도
        μ_Spec = (USL + LSL)/2  # 스펙 구간의 중앙값 
        visual_usl/lsl 사용시 스펙 구간의 시각적 중앙값 (≠ Spec, ≠ 통계적 평균)
        '''
        return (usl + lsl)/2
    
    @staticmethod
    def derive_d_spec(usl: float , lsl: float) -> float:
        '''
        Fall back / Debug 용도
        ΔS = (USL - LSL)/2      # 시각적 스펙 범위의 반폭
        '''
        return (usl - lsl)/2    
    
    @staticmethod
    def derive_ucv(u_spec:float, d_spec:float, adjustment_factor:float = 10) -> float:
        '''
        Fall back / Debug 용도
        μ_Spec + n*ΔS           #상극값(클램핑)
        '''
        return u_spec + (d_spec * adjustment_factor)
    
    @staticmethod
    def derive_lcv(u_spec:float, d_spec:float, adjustment_factor:float = 10) -> float:
        '''
        Fall back / Debug 용도
        μ_Spec - n*ΔS           #하극값(클램핑)
        '''
        return u_spec - (d_spec * adjustment_factor)
    
    @staticmethod
    def derive_visual_scale(ucv:float, lcv:float, scale_factor:float = 10) -> float:
        '''
        Fall back / Debug 용도
        SF/(UCV - LCV)          # 시각 정규화를 위한 스케일 상수.
        '''
        return scale_factor/(ucv-lcv)
    
    @staticmethod
    def _convert_spec_limit_to_value(df: pd.DataFrame, colname_spec: str, colname_slv: str, colname_slu: str):
        """
        Percentage로 처리된 스펙 상/하한을 값으로 변경
        예:
            colname_spec 컬럼의 값: 200
            colname_slv 컬럼의 값: -30
            colname_slu 컬럼의 값: "%"
            >> colname_slv 컬럼의 값: -30 → 140

        매개변수 정보:
            df(Pandas.DataFrame) : df_original 혹은, df_spec이 대상
            colname_spec(str): Column name for the value of the spec
            colname_slv (str): Column name for the value of the spec limit (upper/lower)
            colname_slu (str): Column name for the unit of the spec limit (upper/lower)
        반환:
            None
        """
        mask: pd.DataFrame = (df[colname_slu] == '%')
        df.loc[mask, colname_slv] = df.loc[mask, colname_spec] * (100 + df.loc[mask, colname_slv]) / 100

        return None

    def _set_state_handlers(self):
        result = {
            "Step": self._handle_measured_data,
            "Short Group List": self._handle_short_group,
            "Date": self._handle_date,
            "Serial No.": self._handle_serial_no,
            "PCB Name": self._handle_pcb_name,
            # TODO : 필요시 추가
        }
        return result

    @staticmethod
    def _get_value(line: str, position: int = 0):
        return line.split(",")[position].strip()

    @staticmethod
    def _is_valid_line(line: str) -> bool:
        text = line.strip()
        return text != "" and "-" * 10 not in text and "=" * 10 not in text and "*" * 10 not in text

    def _add_short_group_list(self, text: str):
        str_temp: str = text.strip()
        splitted: list = str_temp.split('=')
        if len(splitted) > 1:
            self.short_group_list.append(text)
            return True
        else:
            return False

    def _handle_measured_data(self, line):
        self._csv_records.append(line.strip())

    def _handle_short_group(self, _):
        self._read_short_group = True

    def _handle_date(self, line):
        # self.measured_at = datetime.strptime(self._get_value(line, 1), '%Y-%m-%d %H:%M:%S')
        date_str = self._get_value(line, 1).strip()
        try:
            self.measured_at = parser.parse(date_str)
        except Exception as e:
            raise ValueError(f"날짜 형식을 파싱할 수 없습니다: {date_str}, 에러: {e}")
        
    def _handle_serial_no(self, line):
        self.serial_no = self._get_value(line, 1)

    def _handle_pcb_name(self, line):
        self.model_name = self._get_value(line, 1)

    def _get_columns_by_index(self, target_col_numbers: List[int]) -> pd.DataFrame:
        if self.df_original.empty:
            return pd.DataFrame()
        else:
            return cast(pd.DataFrame, self.df_original.iloc[:, target_col_numbers])

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError("DataFrame is empty")
        
    @staticmethod
    def _validate_path(fullpath : Path) -> None:
        if not Path.exists(fullpath) : 
            raise ValueError(f"Cannot Find path : {fullpath}")
        
    @staticmethod    
    def _validate_path_access(fullpath : Path) -> None:
        if not os.access(fullpath, os.R_OK) : 
            raise ValueError(f"Cannot access the path : {fullpath}")
        
    @staticmethod   
    def _is_file_empty(fullpath : Path) -> bool:
        if fullpath.stat().st_size == 0:
            return True
        else:
            return False
        
    def _validate_data(self, fullpath : Path) -> None:
        self._validate_path(fullpath)
        self._validate_path_access(fullpath)
        if self._is_file_empty(fullpath):
            logger.error(f"파일이 비어 있습니다: {fullpath}", exc_info=True)
            raise 

    def _validate_dataframe_columns(self, required_columns:list =[]) -> None:
        df = self.df_original
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")



# 테스트 코드 -----------------------------------------------
def test():
    fullpath = Path(r"D:\ICT_TEST\1호기\06DB9205165ADVNAY920001_20250902093736.csv")
    ict = ICTDataExtractor()
    ict.get(fullpath)

    ict.df_spec.to_parquet("C:/Users/user/Novas_Ez/데이터 검증.parquet", engine="pyarrow")


    print(ict.df_original)

if __name__ == "__main__":
    test()