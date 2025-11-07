###########################################
# Module name : funcs_for_api.py
# Module functions : get_dual_pmf_chart_data, get_single_item_trend, get_spec_parquet, get_instrument_names, get_model_names, get_time_series_data, normalize_and_upsert_all_models, process_and_upsert_vector_data, uniformize_length, get_defective_similarity_hits, get_serial_similarity_hits_from_defects, get_df_defects, get_similars_to_defects, get_google_spreadsheet_url_by_name
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.08.??
# Updated at : 2025.11.07
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
#        TODO : 최적화/ 분할 대상 파일
#        2025.08.?? : 초기 버전 작성
#        2025.11.07 : 유사도 관련 함수들 추가
############################################

from datetime import date
from sqlalchemy import true
from ANALYZER.spec_analyzer import SpecAnalyzer, AnalyzedFileExporter
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
import numpy as np
from typing import Any

async def get_dual_pmf_chart_data(
        cruder: CRUDer,
        parent_path_spec: Path,
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
    _, df_spec = await get_spec_parquet(cruder, parent_path_spec, model_name)

    sa = SpecAnalyzer(df_spec,resolution)

    # afe_left, afe_right의 .serialized_meta_data()를 사용해도 되지만 로직상 예쁘지 않아서 따로 처리
    meta_data = AnalyzedFileExporter(sa, model_name).serialized_meta_data()

    analized_left : list[tuple[int, float]] | None = None
    analized_right : list[tuple[int, float]] | None = None

    if True:    # 가독성을 위해(들여쓰기) ... 나중에 따로 빼든지 할 것. 근데 따로 뺴기에는 좀 애매...
        # 모델의 측정 데이터 세트 조회(현재는 postGre 안에 리스트 처리해 둬서 Postgresql에서 직접 조회)
        list_measured_left = await cruder.get_measured_data(model_name, left_date_from, left_date_to, left_measured_by)
        if not list_measured_left:
            analized_left = AnalyzedFileExporter(sa, model_name).serialized_zero_pmf_data()
        else:
            analized_left = AnalyzedFileExporter(sa.analyze(list_measured_left), model_name).serialized_pmf_data()

    if do_right_side:
        # 모델의 측정 데이터 세트 조회(현재는 postGre 안에 리스트 처리해 둬서 Postgresql에서 직접 조회)
        list_measured_right = await cruder.get_measured_data(model_name, right_date_from, right_date_to, right_measured_by)
        if not list_measured_right:
            analized_right = AnalyzedFileExporter(sa, model_name).serialized_zero_pmf_data()
        else:
            analized_right = AnalyzedFileExporter(sa.analyze(list_measured_right), model_name).serialized_pmf_data()

    for i in range(len(meta_data)):

        pmf_data : list[tuple[int, float]] = []
        pmf_data.append(analized_left[i])

        if analized_right:
            pmf_data.append(analized_right[i])

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


async def get_spec_parquet(
        cruder: CRUDer,
        dir_base_spec: Path,
        model_name: str,
        spec_id: int | None = None
    ) -> tuple[int, pd.DataFrame]:
    """
    return value : tuple[SPEC_ID (int), SPEC (pd.DataFrame)]
    """
    spec = await cruder.get_spec(model_name, spec_id)
    if spec is None:
        raise ValueError(f"Cannot find the spec subpath. model_name : {model_name}")

    spec_id = spec['id']
    spec_path = spec['path_sub_datafile']
    spec_file_path: Path = dir_base_spec / spec_path

    if not spec_file_path.exists():
        raise ValueError(f"Cannot find the spec file. fullpath : {spec_file_path} \n model_name : {model_name}")

    return spec_id, pd.read_parquet(spec_file_path)


async def get_instrument_names(cruder: CRUDer) -> list[str]: 
    return await cruder.get_instrument_names()


async def get_model_names(cruder: CRUDer) -> list[str]: 
    return await cruder.get_model_names()


async def get_time_series_data(
    cruder: CRUDer, 
    model_name: str, 
    inspection_idx: int, 
    date_from: date, 
    date_to: date, 
    measured_by: str | None = None
    ) -> dict[str, dict[str, float]]: 

    data : list[dict[str, Any]] = await cruder.get_time_series_data(model_name, inspection_idx, date_from, date_to, measured_by)

    result: dict[str, dict[str, float]] = {}
    for row in data:
        serial_no = row['serial_no']
        measured_at = row['measured_at']
        measured_value = row['measured_value']
        result[serial_no] = {"measuredAt": measured_at, "measuredValue": measured_value}

    return result


async def normalize_and_upsert_all_models(cruder: CRUDer, dir_base_spec: Path, model_name: str | None = None) -> dict[str, int]:

    result : dict[str, int] = {}
    if model_name is None:
        model_names = await cruder.get_model_names()
    else:
        model_names = [model_name]

    cnt : int = 0
    for model_name in model_names:
        spec_id, spec = await get_spec_parquet(cruder, dir_base_spec, model_name)
        cnt += await process_and_upsert_vector_data(cruder, model_name, spec_id, spec)

    return {"count": cnt}


async def process_and_upsert_vector_data(cruder: CRUDer, model_name: str, spec_id: int, spec: pd.DataFrame) -> int:

    df_to_upsert : pd.DataFrame = pd.DataFrame()
    rows_measured : list[dict] = await cruder.get_measured_since_last_normalized(model_name, latest_only=False)

    if len(rows_measured) == 0:
        return 0

    df_data : pd.DataFrame = pd.DataFrame(rows_measured)
    df_data : pd.DataFrame = df_data[df_data["model_name"] == model_name]

    df_measured : pd.DataFrame = df_data[["list_measured"]]

    sa = SpecAnalyzer(spec)
    list_measured : list[list[float]] = df_measured["list_measured"].tolist()
    data_quantized : np.ndarray = sa.analyze(list_measured).data_quantized
    data_uniformed : np.ndarray = uniformize_length(data_quantized)

    df_to_upsert["measured_id"] = df_data["id"]
    df_to_upsert["vector_visual_normed"] = data_uniformed.tolist()
    df_to_upsert["applied_spec_id"] = spec_id

    await cruder.upsert_normalized(df_to_upsert)
    
    return len(df_to_upsert)


def uniformize_length(data_quantized : list[list[float]], pad_val: float = 0.0, max_len: int = 3000) -> np.ndarray:
    arr = np.full((len(data_quantized), max_len), pad_val, dtype=float)
    for i, row in enumerate(data_quantized):
        row_len = min(len(row), max_len)
        arr[i, :row_len] = row[:row_len]
    return arr 



# 유사도 관련 함수들

async def get_defective_similarity_hits(
    cruder: CRUDer, 
    model_name: str, 
    serial_no: str, 
    defective_serials: list[str], 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine",
    except_itself: bool = False
    ) -> dict[str, dict[str, Any]]:
    """
    해당 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    유사도 결과 중 대상 시리얼 넘버(defective_serials)에 해당하는 시리얼 넘버의 유사도 결과 반환
    """
    result: dict[str, dict[str, Any]] = {}

    data_size = await cruder.get_measured_data_size(model_name=model_name)

    records = await cruder.get_relative_similarities(model_name, serial_no, data_size, top_n_rate, date_from, date_to, metric, except_itself)

    for defective_serial in defective_serials :
        if defective_serial in records:
            result[defective_serial] = records[defective_serial]
            rel_sim = result[defective_serial]["vector_visual_normed"]
            result[defective_serial]["vector_visual_normed"] = rel_sim[:len(result[defective_serial]["list_measured"])]

    if not except_itself and serial_no in records:
        result[serial_no] = records[serial_no]
        rel_sim = result[serial_no]["vector_visual_normed"]
        result[serial_no]["vector_visual_normed"] = rel_sim[:len(result[serial_no]["list_measured"])]
    
    return result


async def get_serial_similarity_hits_from_defects(
    cruder: CRUDer, 
    instrument_name: str | None = None,
    serial_no: str | None = None, 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine"
    ) -> dict[str, dict[str, Any]]:
    """
    불량 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    각 불량 모델의 시리얼 넘버(defective_serial)의 유사도 결과 반환
    """
    # TODO : 최적화 대상... 제발... 시간좀..
    result: dict[str, dict[str, Any]] = {}
    serial_info : dict[str, Any] | None = None
    model_name : str | None = None
    data_size : int | None = None    # TODO : alru_cache 대상. alru_cache 적용 시, 리프레쉬 트리거 확인 필요
    df_defective : pd.DataFrame | None = None
    df_data_sizes : pd.DataFrame | None = None
    
    def _get_data_size(model_name: str, df_data_sizes: pd.DataFrame) -> int:
        if df_data_sizes.empty:
            return 0
        filtered = df_data_sizes[df_data_sizes["model_name"] == model_name]
        return int(filtered["count"].iloc[0]) if not filtered.empty else 0

    def _add_result(serial_no: str, records: dict[str, Any], model_name: str, rank: int, df_data_sizes: pd.DataFrame) -> dict[str, Any]:
        result[serial_no] = records[serial_no]
        rel_sim = result[serial_no]["vector_visual_normed"]
        result[serial_no]["vector_visual_normed"] = rel_sim[:len(result[serial_no]["list_measured"])]
        result[serial_no]["rank"] = records[serial_no]["rank"]
        result[serial_no]["data_size"] = _get_data_size(model_name, df_data_sizes)
        result[serial_no]["rank_percent"] = round((rank / result[serial_no]["data_size"]) * 100, 6) if result[serial_no]["data_size"] > 0 else 0
        return result[serial_no]

    serial_info : dict[str, Any] = await cruder.get_latest_measured_datum(instrument_name, None, serial_no)
    model_name = serial_info["model_name"]
    df_defective = await cruder.get_external_defects_info()
    df_data_sizes = await cruder.get_measured_data_sizes(date_from=date_from, date_to=date_to)
    data_size = _get_data_size(model_name, df_data_sizes)

    # 조회 시리얼
    # 대상 시리얼만 ICT 장비명 기준 조회 (본인 혹은 해당 장비의 최신 측정치는 무조건 반환)
    single_record = await cruder.get_absolute_similarities(instrument_name, model_name, serial_no, 1, except_itself = False, return_vector=True, return_measured_values=True, anchor_serial_no=serial_no)
    result[serial_no] = _add_result(serial_no, single_record, model_name, single_record[serial_no]["rank"], df_data_sizes)
    df_defective = df_defective[df_defective["model_name"] == model_name]

    if data_size > 0:
        for xrow in df_defective.itertuples():
            print(model_name)
            defective_serial = xrow.serial_no
            print(defective_serial)
            records = await cruder.get_relative_similarities(None, model_name, defective_serial, data_size, top_n_rate, date_from, date_to, metric, True, False, False)
            if serial_no in records:
                single_record = await cruder.get_absolute_similarities(None, model_name, serial_no, 1, date_from, date_to, metric, True, True, True, defective_serial)
                result[defective_serial] = _add_result(defective_serial, single_record, model_name, records[serial_no]["rank"], df_data_sizes)

    return result


async def get_df_defects(
    cruder: CRUDer, 
    df_defective: pd.DataFrame, 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine",
    except_itself: bool = False
    ) -> pd.DataFrame:

    """
    df_defective : serial_no, model_name, instrument_name 컬럼을 가진 데이터프레임
    해당 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    유사도 결과 중 대상 시리얼 넘버(defective_serials)에 해당하는 시리얼 넘버의 유사도 결과 반환
    """
    # TODO : Pydantic의 BaseModel 사용하여 DTO 정의(리팩토링시)
    instrument_name : str | None = None
    model_name : str | None = None
    serial_no : str | None = None
    num_of_records : int | None = None

    target_models : list[str] = df_defective["model_name"].unique()
    dict_model_n_num_of_records: dict[str, int] = {}
    for model_name in target_models:
        num_of_records = await cruder.get_measured_data_size(model_name=model_name)
        dict_model_n_num_of_records[model_name] = num_of_records

    list_data : list[dict[str, Any]] = []
    for xrow in df_defective.itertuples():
        instrument_name = xrow.instrument_name    # 안 씀
        model_name = xrow.model_name
        serial_no = xrow.serial_no
        num_of_records = dict_model_n_num_of_records[model_name]
        records = await cruder.get_relative_similarities(None, model_name, serial_no, num_of_records, top_n_rate, date_from, date_to, metric, except_itself, False, False)

        for xvalue in records.values():
            xvalue["relative_similarity"] = round((1 - xvalue["rank"] / num_of_records) * 100, 5)
        list_data.extend(records.values())

    return pd.DataFrame(list_data)


async def get_similars_to_defects(cruder: CRUDer, date_from: date, date_to: date, top_n_rate : float = 0.1) -> pd.DataFrame:

    """
    불량 시리얼 넘버 조회 (DB)
    불량 시리얼 넘버와 유사한 측정치 조회 (DB)

    최적화는 안된 상태
    """
    # TODO : 여러번 조회하는데, 추후 한번으로 바꿀 것.

    df_defective = await cruder.get_external_defects_info()

    df = await get_df_defects(
        cruder, 
        df_defective=df_defective, 
        top_n_rate=top_n_rate,
        date_from=date_from,
        date_to=date_to,
        metric="cosine",
        except_itself=True
    )
    
    if df.empty :
        return pd.DataFrame({"message": ["요청 기간에 해당 데이터가 없습니다."]})
    else:
        df.sort_values(by="measured_at", ascending=False, inplace=True)
        df = df.rename(columns={'serial_query': '시장불량'})
        df = df.rename(columns={'serial_result': '유사제품'})
        df = df.rename(columns={'rank': '유사도순위'})
        df = df.rename(columns={'relative_similarity': '상대 유사도(%)'})
        df = df.rename(columns={'measured_at': '측정일시'})
        df = df.rename(columns={'distance': '유사도 거리(1-cosθ)'})

    return df


async def get_google_spreadsheet_url_by_name(cruder: CRUDer, name: str) -> str:
    service_account_info = await cruder.get_google_service_account(name)
    if service_account_info is None:
        raise ValueError(f"등록된 이름의 Google Service Account가 없습니다.")
    spreadsheet_id = service_account_info["spreadsheet_id"]
    worksheet_name = service_account_info["worksheet_name"]
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={worksheet_name}"
    return url














# # 테스트 코드-------------------
if __name__ == "__main__":
    from DATABASE import models
    from DATABASE.pg_manager import PGDBManager
    import asyncio

    model_name="DB92-05685A"
    date_from="2025-03-01"
    date_to="2025-03-11"

    PARENT_PATH = Path("C:/Users/user/Novas_Ez")

    db_manager = PGDBManager(
        models.BaseModel,
        db_name="novas_ez",
        user="admin",
        password="123!@#qwe",
        host="localhost",
        port=5432
    )

    result = asyncio.run(get_dual_pmf_chart_data(CRUDer(db_manager), PARENT_PATH, model_name,"test_name", date_from, date_to))
    print(result)
