from DATABASE.cruder import CRUDer
from DATABASE import config
from datetime import date
import asyncio
import pandas as pd
from ANALYZER.spec_analyzer import SpecAnalyzer 
from WEB_SERVER.funcs_for_api import get_spec_parquet
from pathlib import Path
import numpy as np

# 

cruder = CRUDer(config.db_manager)

async def normalize_and_upsert_all_models(cruder: CRUDer, dir_base_spec: Path, model_name: str | None = None) -> int:

    if model_name is None:
        model_names = await cruder.get_model_names()
    else:
        model_names = [model_name]

    cnt : int = 0
    for model_name in model_names:
        spec_id, spec = await get_spec_parquet(cruder, dir_base_spec, model_name)
        cnt += await process_and_upsert_vector_data(cruder, model_name, spec_id, spec)

    return cnt


async def process_and_upsert_vector_data(cruder: CRUDer, model_name: str, spec_id: int, spec: pd.DataFrame) -> int:
    """
    1. normalized 테이블에서 마지막 정규화된 데이터 확인
    2. measured 테이블의 데이터를 조회하여 벡터화 
    3. 벡터화된 데이터를 normalized 테이블에 업데이트
    """


    df_to_upsert : pd.DataFrame = pd.DataFrame()
    rows_measured_unnormalized : list[dict] = await cruder.get_measured_since_last_normalized(model_name, latest_only=False)

    if len(rows_measured_unnormalized) == 0:
        return 0

    df_data : pd.DataFrame = pd.DataFrame(rows_measured_unnormalized)
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











if __name__ == "__main__":
    asyncio.run(normalize_and_upsert_all_models(cruder, Path("C:/Users/user/Novas_Ez")))
