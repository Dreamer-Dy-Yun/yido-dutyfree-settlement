from datetime import date
from ANALYZER.spec_analyzer import SpecAnalyzer, AnalyzedFileExporter
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
import numpy as np


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
    ) -> list[dict[str, any]]:
    # TODO : 상황 보고 데이터 송신 방법 변경
    # TODO : 에러 반환은 나중에..
    # TODO : 동작 확인되면 정리(함수로 나누어 호출).

    do_right_side : bool = True

    # 오른쪽 데이터 하나라도 없으면 왼쪽만 제공(왼쪽만 제공시 결과적으로 차트는 좌우 대칭이 됨)
    if not right_date_from and not right_date_to:
        do_right_side = False

    result : list[dict[str, any]] = []  # 결과 타입

    # 스펙 정보 확보(정규화 목적)
    _, df_spec = await get_spec_parquet(cruder, parent_path_spec, model_name)

    sa = SpecAnalyzer(df_spec,resolution)

    # afe_left, afe_right의 .serialized_meta_data()를 사용해도 되지만 로직상 예쁘지 않아서 따로 처리
    meta_data = AnalyzedFileExporter(sa, model_name).serialized_meta_data()

    analized_left : list[tuple[int, float]] = None
    analized_right : list[tuple[int, float]] = None

    if True:    # 가독성을 위해 ... 나중에 따로 빼든지 할 것. 근데 따로 뺴기에는 좀 애매...
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
            analized_right = AnalyzedFileExporter(sa.analyze(list_measured_left), model_name).serialized_zero_pmf_data()
        else:
            analized_right = AnalyzedFileExporter(sa.analyze(list_measured_right), model_name).serialized_pmf_data()

    for i in range(len(meta_data)):

        pmf_data : list[tuple[int, float]] = []
        pmf_data.append(analized_left[i])

        if analized_right:
            pmf_data.append(analized_right[i])

        single_chart_data : dict[str, any] = {
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
    ) -> dict[dict[str, any]]: 
    
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

    trend_data : dict[dict[str, any]] = {}

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

    data : list[dict[str, any]] = await cruder.get_time_series_data(model_name, inspection_idx, date_from, date_to, measured_by)

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
    rows_measured : list[dict] = await cruder.get_measured_after_last_normalized(model_name, latest_only=False)

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
