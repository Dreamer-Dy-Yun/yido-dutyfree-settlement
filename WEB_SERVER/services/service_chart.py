###########################################
# Module name : service_chart.py
# Module functions : get_statistics, get_dual_pmf_chart_data, get_single_item_trend
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 차트/분석 관련 서비스 함수
############################################

from datetime import date
from ANALYZER.spec_analyzer import SpecAnalyzer, AnalyzedFileExporter
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
import numpy as np
from typing import Any
from numpy.typing import NDArray
from .service_spec import get_spec_parquet


async def get_statistics(
        cruder: CRUDer,
        dir_spec: Path,
        model_name: str, 
        date_from: date, 
        date_to: date, 
        measured_by: str | None = None
    ) -> pd.DataFrame:

    df : pd.DataFrame = pd.DataFrame(columns=["index", "부품명","스펙", "단위", "스펙상한", "스펙하한", "중앙값","평균값","분산"])

    # 스펙 정보 확보(정규화 목적)
    _, df_spec = await get_spec_parquet(cruder, dir_spec, model_name)

    if df_spec.empty:
        raise ValueError(f"Cannot find the spec subpath. model_name : {model_name}")
    else:
        df["index"] = df_spec["index"].tolist()
        df["부품명"] = df_spec["part_name"].tolist()
        df["스펙"] = df_spec["spec"].tolist()
        df["단위"] = df_spec["unit"].tolist()
        df["스펙상한"] = df_spec["usl"].tolist()
        df["스펙하한"] = df_spec["lsl"].tolist()
        measured_points : int = len(df_spec)

    list_measured = await cruder.get_measured_data(model_name, date_from, date_to, measured_by, measured_points)

    if not list_measured:
        raise ValueError(f"Cannot find the measured data. model_name : {model_name}")
    else:
        data : NDArray[np.float64] = np.array(list_measured, dtype=np.float64)
        df["중앙값"] = np.median(data, axis=0)
        df["평균값"] = np.mean(data, axis=0)
        df["분산"] = np.std(data, axis=0)
    
    return df


async def get_dual_pmf_chart_data(
        cruder: CRUDer,
        dir_spec: Path,
        model_name: str, 
        left_date_from: date, 
        left_date_to: date, 
        left_measured_by: str | None = None,
        right_date_from: date | None = None, 
        right_date_to: date | None = None, 
        right_measured_by: str | None = None,
        resolution: int = 400
    ) -> list[dict[str, Any]]:
    # TODO : 상황 보고 데이터 송신 방법 변경
    # TODO : 에러 반환은 나중에..
    # TODO : 동작 확인되면 정리(함수로 나누어 호출).

    do_right_side : bool = True

    # 오른쪽 데이터 하나라도 없으면 왼쪽만 제공(왼쪽만 제공시 결과적으로 차트는 좌우 대칭이 됨)
    if not right_date_from and not right_date_to:
        do_right_side = False

    result : list[dict[str, Any]] = []  # 결과 타입

    # 스펙 정보 확보(정규화 목적)
    _, df_spec = await get_spec_parquet(cruder, dir_spec, model_name)

    sa = SpecAnalyzer(df_spec,resolution)

    measured_points : int = len(df_spec)

    # afe_left, afe_right의 .serialized_meta_data()를 사용해도 되지만 로직상 예쁘지 않아서 따로 처리
    meta_data = AnalyzedFileExporter(sa, model_name).serialized_meta_data()

    analyzed_left : list[tuple[int, float]] | None = None
    analyzed_right : list[tuple[int, float]] | None = None

    if True:    # 가독성을 위해(들여쓰기) ... 나중에 따로 빼든지 할 것. 근데 따로 뺴기에는 좀 애매...
        # 모델의 측정 데이터 세트 조회(현재는 postGre 안에 리스트 처리해 둬서 Postgresql에서 직접 조회)
        list_measured_left = await cruder.get_measured_data(model_name, left_date_from, left_date_to, left_measured_by, measured_points)
    
        if not list_measured_left:
            analyzed_left = AnalyzedFileExporter(sa, model_name).serialized_zero_pmf_data()
        else:
            sa_left = sa.analyze(list_measured_left)
            analyzed_left = AnalyzedFileExporter(sa_left, model_name).serialized_pmf_data()
    if do_right_side:
        # 모델의 측정 데이터 세트 조회(현재는 postGre 안에 리스트 처리해 둬서 Postgresql에서 직접 조회)
        list_measured_right = await cruder.get_measured_data(model_name, right_date_from, right_date_to, right_measured_by, measured_points)
        if not list_measured_right:
            analyzed_right = AnalyzedFileExporter(sa, model_name).serialized_zero_pmf_data()
        else:
            sa_right = sa.analyze(list_measured_right)
            analyzed_right = AnalyzedFileExporter(sa_right, model_name).serialized_pmf_data()

    for i in range(len(meta_data)):

        pmf_data : list[tuple[int, float]] = []
        pmf_data.append(analyzed_left[i])

        if analyzed_right:
            pmf_data.append(analyzed_right[i])

        single_chart_data : dict[str, Any] = {
            "specInfo": meta_data[i]['specInfo'],   
            "chartSpecLine": meta_data[i]['chartSpecLine'],   
            "pmfData": pmf_data,
        }
        result.append(single_chart_data)
    
    return result

async def get_single_item_trend(
        cruder: CRUDer,
        parent_path_spec: Path,
        measured_by: str | None = None,
        model_name: str | None = None, 
        serial_no: str | None = None, 
        resolution: int = 400
    ) -> dict[dict[str, Any]]: 
    
    data = await cruder.get_latest_measured_datum(measured_by, model_name, serial_no)

    if not data:
        raise ValueError(f"조회 조건에 해당하는 데이터가 존재하지 않습니다. \n장비명 : {measured_by}, \n모델명 : {model_name}, \n시리얼번호 : {serial_no}")

    measured_by = data['instrument_name']
    model_name = data['model_name']
    serial_no = data['serial_no']
    measured_data : list[float] = data['list_measured']

    # 스펙 정보 확보(정규화 목적)
    _, df_spec = await get_spec_parquet(cruder, parent_path_spec, model_name)

    # measured_data는 1차원 배열, SpecAnalyzer는 2차원 배열을 입력으로 받으므로, 2차원 리스트([measured_data])로 변환하여 입력
    sa = SpecAnalyzer(df_spec,resolution).analyze([measured_data])

    afe = AnalyzedFileExporter(sa, model_name)

    trend_data : dict[dict[str, Any]] = {}

    trend_data["measuredBy"] = measured_by
    trend_data["modelName"] = model_name
    trend_data["serialNo"] = serial_no
    trend_data["data"] = afe.serialized_trend_data()

    return trend_data
