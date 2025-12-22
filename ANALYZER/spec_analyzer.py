###########################################
# Module name : spec_analyzer
# Module functions : SpecAnalyzer
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.31
# Updated at : 2025.09.12
# Supported by : Chat GPT-4o / Cursor AI
# License :
#       본 소스코드는 현상만이 주어진 상태에서, 
#       최초 구상에서 구현까지 모두 코드 작성자(Yun Dae-young)가 작성한 저작물입니다.
#
#       본 소스코드는 다수의 측정 포인트를 포함하는 공정 데이터에 대하여,
#       동적으로 변경되는 다중 스펙 환경에서 비교 가능성을 유지하기 위한
#       공정 데이터 정규화 및 표현 방법의 하나의 구현 예를 제공합니다.
#
#       Novas-ez는 본 소스코드를 Novas-ez 프로젝트 및 그에 파생되는 내부 프로젝트에 한하여
#       비독점적으로 사용할 수 있습니다.
# Note : 
#        2025.07.31 : 초기 버전 작성
#        2025.08.22 : quantize, compute_pmf 성능 개선
#        2025.08.25 : compute_pmf 성능/리스크 개선(불필요한 연산 제거), 
#                       DualPMFChart를 위한 성능 개선(매개변수 전달 방식 변경으로 기 연산된 Spec값 재사용 가능하게 변경)
#        2025.09.11 : serialized_judgement_data 추가
#                     리팩토링 : AnalysisFileExporter 변경. Spec만을 따로 연산하도록 변경하여 불필요한 재연산 방지.
#                     리팩토링 : serialized_pmf_data 추가(기 존재하던 serialized_pmf_data 는 _seriealized_chart_data로 변경)
#                     리팩토링 : 불필요한 방어적 코드 제거(try - except)
#        2025.09.12 : compute_cpk 로직 수정(타입 분류 로직 변경)
#        2025.09.15 : JSON 항목명을 Front에 맞추어 변경(OK -> ok, NG -> ng, violation_usl -> violationUsl, violation_lsl -> violationLsl)
#        2025.09.16 : 트랜드 데이터용 serialized_trend_data 추가
#        2025.09.17 : 동작에 맞게 클래스명 변경(AnalysisFileExporter -> AnalyzedFileExporter)
#        2025.10.27 : 판정 데이터 로직 수정(역공차 판정 로직 추가). 그에 따른 변수명 변경
#        2025.12.02 : _cpk_std 로직 수정
############################################

import numpy as np
import pandas as pd
import json
from datetime import datetime, date
import re
from typing import Dict, Any, Literal, Self
from pathlib import Path

from sqlalchemy.sql.selectable import _SelectFromElements
from CUSTOMIZED.cust_logger import timer, logger
from numpy.typing import NDArray


class SpecAnalyzer:
    """ 
    probability mass function (PMF, 확률질량함수)
    numpy의 벡터화 연산을 통한 연산 효율화 도모

    INPUT
    - data: data파일(parquet) 파일 중 측정치(measured) 모음 리스트
    - spec: spec파일(parquet) ※ derive_norm_factors()까지 연산된 값
    - resolution: 확률질량함수 그래프 해상도 (기본값: 400)

    OUTPUT
    - data_original: 원본 데이터 테이블
    - data_clipped: 클리핑 후 데이터 테이블
    - data_quantized: 양자화 후 데이터 테이블
    - pmf: 확률질량함수 테이블
    - list_ucv: 상극값 리스트
    - list_lcv: 하극값 리스트
    - list_usl: 스펙 상한 리스트
    - list_lsl: 스펙 하한 한계 리스트
    - list_mu: 스펙 평균값 리스트
    - list_sigma: 표준편차 리스트
    - list_cpk: CPK 값 리스트
    - list_type_cpk: CPK 타입 리스트
    - list_exceeded_usl: 스펙 상한 초과 수 (표준공차 : NG, 역공차 : OK)
    - list_exceeded_lsl: 스펙 하한 미만 수 (표준공차 : NG, 역공차 : OK)
    - list_exceeded_spec_total: 스펙 범위 초과/미만 총 수 (표준공차 : NG, 역공차 : OK)
    - list_between_spec_total: 스펙 범위 이내 총 수 (표준공차 : OK, 역공차 : NG)
    """

    def __init__(self, spec: pd.DataFrame,  resolution: int = 400):
        self.spec: pd.DataFrame = spec
        self.data_original: NDArray[np.float64] = None
        self.data_clipped: NDArray[np.float64] = None
        self.data_quantized: NDArray[np.int32] = None
        self.spec_quantized: NDArray[np.int32] = None
        self.usl_quantized: NDArray[np.int32] = None
        self.lsl_quantized: NDArray[np.int32] = None
        self.ucv_quantized: NDArray[np.int32] = None
        self.lcv_quantized: NDArray[np.int32] = None

        self.pmf: NDArray[np.float64] = None
        self.list_ucv: NDArray[np.float64] = None
        self.list_lcv: NDArray[np.float64] = None
        self.list_usl: NDArray[np.float64] = None
        self.list_lsl: NDArray[np.float64] = None
        self.list_mu: NDArray[np.float64] = None
        self.list_sigma: NDArray[np.float64] = None
        self.list_cpk: NDArray[np.float64] = None
        self.list_type_cpk: NDArray[object] = None
        self.list_exceeded_usl: NDArray[np.int32] = None
        self.list_exceeded_lsl: np.ndarray = None
        self.list_exceeded_spec_total: NDArray[np.int32] = None
        self.list_between_spec_total: NDArray[np.int32] = None
        self.list_spec: NDArray[np.float64] = None
        self.list_unit: NDArray[np.str_] = None
        self.list_part_name: NDArray[np.str_] = None
        self.list_index: NDArray[np.int32] = None
        self.list_reverse_tolerance: NDArray[np.bool_] = None
        self.list_skip: NDArray[np.bool_] = None
        self.list_median: NDArray[np.float64] = None
        self.resolution: int = resolution

        self.run(spec)
        
        self.analyze_spec()

    def analyze_spec(self) -> None:
        timer.start(f"analyze spec")
        self.quantize(resolution = self.resolution)
        timer.end(f"analyze_spec")
        return None

    def analyze(self, data : list[list[float]]) -> Self:

        if (len(self.spec) == len(data[0])):
            self.data_original = np.array(data) 
        else:
            raise ValueError("spec rows must match data columns")

        timer.start(f"analyze")
        # self.clip(data = self.data_original)
        self.quantize(data = self.data_original, resolution = self.resolution)
        self.compute_pmf(clipped_data = self.data_quantized, resolution = self.resolution)
        self.compute_cpk(data = self.data_original)
        self.count_inspection_outcomes(data = self.data_original)
        timer.end(f"analyze")
        return self

    def run(
            self, spec: pd.DataFrame, 
            col_name_ucv: str = "ucv", 
            col_name_lcv: str = "lcv",
            col_name_usl: str = "usl",
            col_name_lsl: str = "lsl",
            col_name_spec: str = "spec",
            col_name_unit: str = "unit",
            col_name_part_name: str = "part_name",
            col_name_index: str = "index",
            col_name_reverse_tolerance: str = "reverse_tolerance",
            col_name_skip: str = "skip"
            ) -> Self:
        self.list_ucv = np.array(spec[col_name_ucv])
        self.list_lcv = np.array(spec[col_name_lcv])
        self.list_usl = np.array(spec[col_name_usl])
        self.list_lsl = np.array(spec[col_name_lsl])
        self.list_spec = np.array(spec[col_name_spec])
        self.list_unit = np.array(spec[col_name_unit])
        self.list_part_name = np.array(spec[col_name_part_name])
        self.list_index = np.array(spec[col_name_index])
        self.list_reverse_tolerance = np.array(spec[col_name_reverse_tolerance])
        self.list_skip = np.array(spec[col_name_skip])
        return self


    def clip(self, data: np.ndarray | None = None) -> None:
        """데이터 클리핑. 안씀"""
        self.data_clipped = np.clip(data, self.list_lcv, self.list_ucv) 
        return None

    def quantize(self, data: NDArray[np.float64] | None = None, resolution: int = 400, start_with: int = 0) -> None:
        delta: np.ndarray = (self.list_ucv - self.list_lcv) / resolution

        # # 0-division 방지  >> delta가 0일 경우는 애초에 발생 해서는 안됨
        if np.any(delta == 0):
            eps = np.finfo(float).eps
            delta = np.where(delta > 0, delta, eps)

        def q_clipper(x):
            z = np.floor((x - self.list_lcv) / delta) + start_with   # float 상태
            z = np.clip(z, start_with, start_with + resolution - 1)  # 경계 자른 뒤
            return (z - start_with).astype(np.int32)     

        if data is None:
            #SPEC 만 양자화
            self.spec_quantized = q_clipper(self.list_spec)
            self.usl_quantized  = q_clipper(self.list_usl)
            self.lsl_quantized  = q_clipper(self.list_lsl)
            start = np.full_like(self.list_lcv, start_with, dtype=int)
            self.ucv_quantized = start + resolution - 1
            self.lcv_quantized = start
        else:            
            #DATA 양자화
            self.data_quantized = q_clipper(data)
        return None


    def compute_pmf(self, clipped_data: NDArray[np.int32] | None = None, resolution: int = 400, set_largest_as_1: bool = True) -> None:
        """
        PMF를 np.bincount 기반으로 계산. 
        대규모 데이터에서 np.histogram 대비 성능 개선 도모
        클리핑된 값이 들어온다는 것이 전제
        """
        if clipped_data.ndim != 2:
            raise ValueError("data_quantized must be 2D.")
        if np.min(clipped_data) < 0 or np.max(clipped_data) >= resolution:
            raise ValueError("quantized data must be in [0, resolution-1].")

        cols = clipped_data.shape[1]
        self.pmf = np.zeros((cols, resolution), dtype=np.float32)

        # d3 정규화 없을 줄 알고 계산한거라, 굳이 필요 없을수도..
        # 대상 데이터가 50만행 이상이면 최적화 고려(멀티 프로세싱. 이 부분만 병목.) 
        for i in range(cols):
            counts = np.bincount(clipped_data[:, i], minlength=resolution)

            if set_largest_as_1:
                denom = counts.max() if counts.max() > 0 else 1
            else:
                denom = counts.sum() if counts.sum() > 0 else 1

            self.pmf[i] = counts / denom            
        return None


    def compute_median(self, data: NDArray[np.float64]) -> Self:
        self.list_median = np.median(data, axis=0)  # 연산비용이 크므로 별도 연산
        return self


    def compute_cpk(self, data: NDArray[np.float64] | None = None) -> Self:
        
        # axis 0: 열 방향, 1: 행 방향
        self.list_mu = data.mean(axis=0)    # 각 측정 포인트에 대한 평균값
        self.list_sigma = data.std(axis=0)  # 각 측정 포인트에 대한 표준편차

        self._cpk_std(mu = self.list_mu, sigma = self.list_sigma, lsl = self.list_lsl, usl = self.list_usl)
        self._cpk_rev(mu = self.list_mu, sigma = self.list_sigma, lsl = self.list_lsl, usl = self.list_usl)

        return self


    def _cpk_std(self, mu: NDArray[np.float64], sigma: NDArray[np.float64], lsl: NDArray[np.float64], usl: NDArray[np.float64]) -> Self:
        """
        CPK 계산 (표준 공차 사용)
        Cpk_std = min((USL - μ) / 3σ, ( μ - LSL ) / 3σ )
        """

        # mu, sigma 자체가 계산 가능한 상태인지 판정
        mask_stat_valid = np.isfinite(mu) & np.isfinite(sigma) & (sigma > 0)

        # 기본 벡터 초기화
        list_cpl = np.full_like(lsl, np.nan, dtype=np.float64)
        list_cpu = np.full_like(usl, np.nan, dtype=np.float64)

        # Cpl, Cpu 유효 계산 포인트 판정
        mask_cpl_valid = ~np.isinf(lsl) & mask_stat_valid
        mask_cpu_valid = ~np.isinf(usl) & mask_stat_valid

        list_cpl[mask_cpl_valid] = (mu[mask_cpl_valid] - lsl[mask_cpl_valid]) / (3 * sigma[mask_cpl_valid])
        list_cpu[mask_cpu_valid] = (usl[mask_cpu_valid] - mu[mask_cpu_valid]) / (3 * sigma[mask_cpu_valid])

        # 타입 판정
        cpl_inf = np.isinf(lsl)
        cpu_inf = np.isinf(usl)

        self.list_type_cpk = np.full(lsl.shape, "", dtype=object)
        self.list_cpk = np.full(lsl.shape, np.nan, dtype=np.float64)

        mask_cpk = ~cpl_inf & ~cpu_inf & mask_stat_valid
        mask_cpl = ~cpl_inf & cpu_inf & mask_stat_valid
        mask_cpu = cpl_inf & ~cpu_inf & mask_stat_valid

        self.list_type_cpk[mask_cpk] = "Cpk"
        self.list_type_cpk[mask_cpl] = "Cpl"
        self.list_type_cpk[mask_cpu] = "Cpu"

        # Cpk 계산
        self.list_cpk[mask_cpk] = np.minimum(list_cpl[mask_cpk], list_cpu[mask_cpk])
        self.list_cpk[mask_cpl] = list_cpl[mask_cpl]
        self.list_cpk[mask_cpu] = list_cpu[mask_cpu]

        return self


    def _cpk_rev(self, mu : NDArray[np.float64], sigma : NDArray[np.float64], lsl : NDArray[np.float64], usl : NDArray[np.float64]) -> Self:
        """ 
        CPK_REV 계산 (역공차 사용) 
        Cpk_rev = max(( μ - USL) / 3σ​, ( LSL - μ ) / 3σ​​ )
        ※ 표준 공차 다음에 사용 할 것.
        """

        # 벡터화된 Cpl, Cpu 계산.
        # cpl : -inf가 아니면 계산, -inf이면 CPK에 선택되지 않도록 +inf로 처리.
        list_cpl: NDArray[np.float64] = np.empty_like(lsl, dtype=np.float64)
        mask_valid : NDArray[np.bool_] = ~np.isinf(lsl) & (sigma > 0)
        list_cpl.fill(-np.inf)
        list_cpl[mask_valid] = (lsl[mask_valid] - mu[mask_valid]) / (3 * sigma[mask_valid])
        # cpu : +inf가 아니면 계산, +inf이면 CPK에 선택되지 않도록 +inf로 처리.
        list_cpu: NDArray[np.float64] = np.empty_like(usl, dtype=np.float64)
        mask_valid : NDArray[np.bool_] = ~np.isinf(usl) & (sigma > 0)
        list_cpu.fill(-np.inf)
        list_cpu[mask_valid] = (mu[mask_valid] - usl[mask_valid]) / (3 * sigma[mask_valid])

        # 타입 결정 (벡터화)
        cpl_inf: NDArray[np.bool_] = np.isinf(lsl)    # 하한선이 없을 때 
        cpu_inf: NDArray[np.bool_] = np.isinf(usl)    # 상한선이 없을 때 
        
        mask_rev : NDArray[np.bool_] = self.list_reverse_tolerance  
        self.list_type_cpk[mask_rev] = "Rev"
        
        # CPK_REV 값 계산
        mask_cpk : NDArray[np.bool_] = ~cpl_inf & ~cpu_inf & mask_rev
        mask_cpl : NDArray[np.bool_] = ~cpl_inf & cpu_inf & mask_rev
        mask_cpu : NDArray[np.bool_] = cpl_inf & ~cpu_inf & mask_rev
        
        # CPK 값 계산 (벡터화)
        self.list_cpk[mask_cpk] = np.maximum(list_cpl[mask_cpk], list_cpu[mask_cpk])
        self.list_cpk[mask_cpl] = list_cpu[mask_cpl]
        self.list_cpk[mask_cpu] = list_cpl[mask_cpu]

        return self


    def count_inspection_outcomes(self, data: np.ndarray | None = None) -> None:

        mask_upper_limit: np.ndarray = data > self.list_usl          
        mask_lower_limit: np.ndarray = data < self.list_lsl       
        mask_ng: np.ndarray = mask_upper_limit | mask_lower_limit      
        mask_ok: np.ndarray = ~mask_ng

        self.list_exceeded_usl = np.sum(mask_upper_limit, axis=0)  
        self.list_exceeded_lsl = np.sum(mask_lower_limit, axis=0) 
        self.list_exceeded_spec_total = np.sum(mask_ng, axis=0)     
        self.list_between_spec_total = np.sum(mask_ok, axis=0)   

        return self


class AnalyzedFileExporter:
    def __init__(self, spec_analyzer: SpecAnalyzer, model: str):
        self.model: str = model
        self.sa: SpecAnalyzer = spec_analyzer
        self.file_name_without_extension: str = ""


    def set_file_name_without_extension(self, query_from: date, query_to: date, execution_time: datetime = datetime.now()) -> str:
        # excution_time 은 파일 분리 전송 혹은 캐싱시 사용 예정
        str_query_from: str = query_from.strftime('%Y%m%d')
        str_query_to: str = query_to.strftime('%Y%m%d')
        str_excution_time: str = execution_time.strftime('%Y%m%d_%H%M%S')
        modified_model: str = re.sub(r'[^\w\-_]', '_', self.model)
        self.file_name_without_extension = f"[{modified_model}]from{str_query_from}_to{str_query_to}_at{str_excution_time}"
        return  self.file_name_without_extension


    def to_json_file(self, folder_path:Path, file_kind: Literal["meta", "pmf"], serializable_data: Any) -> None:

        self.raise_error_if_file_name_not_set()

        file_name: Path = folder_path / f"({file_kind}){self.file_name_without_extension}.json"
        
        try :
            with open(file_name, "x") as f:
                json.dump(serializable_data, f, indent=4)
        except Exception as e:
            logger.error(f"failed to make file {file_kind} data: {e}")


    def serialized_meta_data(self) -> list[dict[str, Any]]:
        # 이 함수는 PMF 데이터와 독립
        # SPEC 데이터에만 의존
        data: list[dict[str, Any]] = []
        for i in range(len(self.sa.list_spec)):
            data.append({
                "specInfo":{
                    "idx": self.sa.list_index[i].item(),
                    "partName": self.sa.list_part_name[i],
                    "spec": self.sa.list_spec[i].item(),
                    "unit": self.sa.list_unit[i],
                    "ucv": self.sa.list_ucv[i].item(),
                    "lcv": self.sa.list_lcv[i].item(),
                    "usl": self.sa.list_usl[i].item(),
                    "lsl": self.sa.list_lsl[i].item(),
                    "reverseTolerance": self.sa.list_reverse_tolerance[i].item(),
                    "skip": self.sa.list_skip[i].item(),
                },
                "chartSpecLine":{
                    "spec": self.sa.spec_quantized[i].item(),
                    "usl": self.sa.usl_quantized[i].item(),
                    "lsl": self.sa.lsl_quantized[i].item(),
                    "ucv": self.sa.ucv_quantized[i].item(),
                    "lcv": self.sa.lcv_quantized[i].item(),
                }
            })
        return data


    def _serialized_cpk_data(self) -> list[dict[str, Any]]:
        # 이 함수는 SPEC 및 PMF 데이터에 의존
        # 안쓸 예정
        data: list[dict[str, Any]] = []
        for i in range(len(self.sa.list_between_spec_total)):
            data.append({
                    "mu": self.sa.list_mu[i].item(),
                    "sigma": self.sa.list_sigma[i].item(),
                    "cpk": self._process_inf_for_typescript(self.sa.list_cpk[i].item()),
                    "type": self.sa.list_type_cpk[i],
                })
        return data


    def _serialized_judgement_data(self) -> list[dict[str, Any]]:
        # 이 함수는 SPEC 및 PMF 데이터에 의존
        # 안쓸 예정
        data: list[dict[str, Any]] = []
        for i in range(len(self.sa.list_between_spec_total)):
            if self.sa.list_reverse_tolerance[i].item():
                violationUsl: int = 0
                violationLsl: int = 0
                violationInner: int = self.sa.list_between_spec_total[i].item()
                okTotal: int = self.sa.list_exceeded_spec_total[i].item()
                ngTotal: int = self.sa.list_between_spec_total[i].item()
            else:
                violationUsl: int = self.sa.list_exceeded_usl[i].item() 
                violationLsl: int = self.sa.list_exceeded_lsl[i].item()
                violationInner: int = 0
                okTotal: int = self.sa.list_between_spec_total[i].item()
                ngTotal: int = self.sa.list_exceeded_spec_total[i].item()  

            data.append({
                    "ok": {
                        "total": okTotal,
                    },
                    "ng": {
                        "violationUsl": violationUsl,
                        "violationLsl": violationLsl,
                        "violationInner": violationInner,
                        "total": ngTotal,
                    }
            })
        return data


    def _seriealized_chart_data(self) -> dict[int, list[tuple[int, float]]]:
        # 이 함수는 PMF 데이터에 의존
        # 안쓸 예정
        # shape[0]: 측정지점 개수, shape[1]: bin 개수
        data: dict[int, list[tuple[int, float]]] = {}
        data = {i: [(j, self.sa.pmf[i, j].item()) for j in range(self.sa.pmf.shape[1])] for i in range(self.sa.pmf.shape[0])}
        return data


    def serialized_trend_data(self) -> dict[int, dict[str, Any]]:
        data: dict[int, dict[str, Any]] = {}
        for i in range(len(self.sa.list_spec)):
            chartIdx = self.sa.list_index[i].item()
            measuredValue = self.sa.data_original[0][i].item()
            data[str(chartIdx)] = {
                "navigationIdx": chartIdx, # 차트 인덱스와 동일
                "chartIdx": chartIdx,
                "binValue": self.sa.pmf[i, :].argmax().item(),  # 최대값(1)의 bin 인덱스
                "measuredValue": measuredValue,  # 실측치. 기능 확장시 쓰일 가능성 높음
                "skip": self.sa.list_skip[i].item(),
                "passed": not(measuredValue > self.sa.list_ucv[i].item() or measuredValue < self.sa.list_lcv[i].item()),
            }
        return data

# export interface TrendData {
#     [key: number]: TrendDatum;
# }

# export interface TrendDatum {
#     navigationIdx: number;   // 네비게이터 인덱스 (추적/비교용)
#     chartIdx: number;        // 차트 인덱스 (차트 매핑용)
#     value: number;           // 값 (차트의 Bin 크기(resolution)로 정규화된 값)
# }

    def serialized_pmf_data(self) -> list[dict[str, Any]]:
        '''
        아래와 같은 느낌의 데이터
        "pmfData": [
        {
          "data": [(0, 0.1), (1, 0.1), (2, 0.3), (3, 0.6), (4, 0.9), (5, 1.0), (6, 0.6), (7, 0.6), (8, 0.3), (9, 0.1), (10, 0.0)...],
          "judgementInfo": { "ok": { "total": 18 }, "ng": { "violationUsl": 1, "violationLsl": 1, "total": 2 } },
          "cpkInfo": { "mu": 0.53, "sigma": 0.015, "cpk": 1.2, "type": "Cpk" }
        },
        
        '''
        # shape[0]: 측정지점 개수, shape[1]: bin 개수
        data: list[dict[str, Any]] = []

        for i in range(len(self.sa.list_spec)):
            # _serialized_judgement_data, _serialized_cpk_data 를 사용하지 않는 것은 반복문을 줄이기 위함. 사실 써도 큰 차이는 없을 듯
            # 나중에 테스트 해 보고 가독성 높이는 방안 고려
            if self.sa.list_reverse_tolerance[i].item():
                violationUsl: int = 0
                violationLsl: int = 0
                violationInner: int = self.sa.list_between_spec_total[i].item()
                okTotal: int = self.sa.list_exceeded_spec_total[i].item()
                ngTotal: int = self.sa.list_between_spec_total[i].item()
            else:
                violationUsl: int = self.sa.list_exceeded_usl[i].item() 
                violationLsl: int = self.sa.list_exceeded_lsl[i].item()
                violationInner: int = 0
                okTotal: int = self.sa.list_between_spec_total[i].item()
                ngTotal: int = self.sa.list_exceeded_spec_total[i].item()  

            data.append({
                "data": [(j, self.sa.pmf[i, j].item()) for j in range(self.sa.pmf.shape[1])],
                "judgementInfo":{
                    "ok": {
                        "total": okTotal,
                    },
                    "ng": {
                        "violationUsl": violationUsl,
                        "violationLsl": violationLsl,
                        "violationInner": violationInner,
                        "total": ngTotal,
                    }
                },
                "cpkInfo": {
                    "mu": self.sa.list_mu[i].item(),
                    "sigma": self.sa.list_sigma[i].item(),
                    "cpk": self._process_inf_for_typescript(self.sa.list_cpk[i].item()),
                    "type": str(self.sa.list_type_cpk[i]),
                }
            })
        return data

    def serialized_zero_pmf_data(self) -> list[dict[str, Any]]:
        '''
        빈 데이터 반환. 측정 데이터가 없을 때 사용
        '''
        # shape[0]: 측정지점 개수, shape[1]: bin 개수
        data: list[dict[str, Any]] = []

        for i in range(len(self.sa.list_spec)):
            # _serialized_judgement_data, _serialized_cpk_data 를 사용하지 않는 것은 반복문을 줄이기 위함. 사실 써도 큰 차이는 없을 듯
            # 나중에 테스트 해 보고 가독성 높이는 방안 고려
            data.append({
                "data": [(i, 1) for i in range(len(self.sa.spec))],
                "judgementInfo":{
                    "ok": {
                        "total": 0,
                    },
                    "ng": {
                        "violationUsl": 0,
                        "violationLsl": 0,
                        "violationInner": 0,
                        "total": 0,
                    }
                },
                "cpkInfo": {
                    "mu": 0,
                    "sigma": 0,
                    "cpk": "undefined",
                    "type": "-",
                }
            })
        return data

    def _process_inf_for_typescript(self, number) -> str:
        if np.isinf(number):
            return "Infinity" if number > 0 else "-Infinity"
        return str(number)

    def pmf_data_to_feather_file(self, folder_path: Path) -> None:
        # 상황 보고 사용
        self.raise_error_if_file_name_not_set()
        
        file_name: Path = folder_path / f"{self.file_name_without_extension}.feather"

        try:
            # 파일 존재 체크 (덮어쓰기 방지)
            if file_name.exists():
                raise FileExistsError(f"File already exists: {file_name}")
            
            # PMF 데이터를 DataFrame으로 변환
            df_pmf = pd.DataFrame(self.sa.pmf)
            df_pmf.columns = [f"bin_{i}" for i in range(df_pmf.shape[1])]
            df_pmf.index = [f"point_{i}" for i in range(df_pmf.shape[0])]
            
            # Feather 파일로 저장
            df_pmf.to_feather(file_name)
            
        except Exception as e:
            logger.error(f"failed to make file pmf: {e}")


    def raise_error_if_file_name_not_set(self) -> None:
        if self.file_name_without_extension == "":
            raise ValueError("file_name_without_extension is not set. execute [set_file_name_without_extension()] first.")
        

def serialize_data(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: serialize_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_data(v) for v in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj
    

# ##############################################################################
# ####간편 테스트 용 데이터########################################################


def test_data():

    raw_data = [
        [0, 1, 2],
        ["part_name1", "part_name2", "part_name3"],
        [400, 500, 600],
        ["ohm", "ohm", "ohm"],
        [790, 890, 990],
        [210, 310, 410],
        [760, 840, 940],
        [240, 340, 440],
        [False, False, True],
        [False, True, False],
    ]

    # 트랜스포즈 후 DataFrame 생성
    spec = pd.DataFrame(list(zip(*raw_data)), columns=["index", "part_name", "spec", "unit","ucv", "lcv", "usl", "lsl", "reverse_tolerance", "skip"])

    print(spec)

    data = [
        [854.7295987, 878.1470284, 98.69373038],
        [680.894332, 119.3643627, 350.605619],
        [370.1649447, 535.2242048, 588.678936],
        [620.0723164, 355.5313368, 441.4124078],
        [579.7496174, 76.26142033, 601.2531271],
        [790, 890, 990],
        [370.1649447, 535.2242048, 588.678936],
       ]

    C = SpecAnalyzer(spec, 10)
    C = C.analyze(data)
    AFE = AnalyzedFileExporter(C, "test")
    AFE.serialized_meta_data()
    # AFE.pmf_data_to_feather_file()
    AFE._serialized_cpk_data()
    AFE._serialized_judgement_data()
    AFE._seriealized_chart_data()
    AFE.serialized_pmf_data()
    AFE.serialized_trend_data()
    
    print(C.data_original)
    print(C.data_clipped)
    print(C.data_quantized)
    print(C.pmf)
    print(C.list_exceeded_usl)
    print(C.list_exceeded_lsl)
    print(C.list_exceeded_spec_total)
    print(C.list_between_spec_total)
    print(C.list_cpk)
    print(C.list_type_cpk)
    print(C.list_mu)
    print(C.list_sigma)

if __name__ == "__main__":
    test_data()
