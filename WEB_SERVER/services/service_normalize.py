###########################################
# Module name : service_normalize.py
# Module functions : normalize_and_upsert_all_models, process_and_upsert_vector_data, uniformize_length
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 정규화 관련 서비스 함수
############################################

from datetime import date
from ANALYZER.spec_analyzer import SpecAnalyzer
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
import numpy as np
from .service_spec import get_spec_parquet


async def normalize_and_upsert_all_models(cruder: CRUDer, dir_base_spec: Path, model_name: str | None = None) -> dict[str, int]:
    """
    해당 모델에 대해 normalize 테이블 업데이트.
    normalize 테이블 상의 모델별 최신 업데이트 일시 이후의 증분만 업데이트 대상
    model_name = None 전체 모델 대상

    일반적인 처리를 위한 것이기 때문에 이로 인한 성능 손실은 존재함. 
    성능 최적화를 위해서는 별도 함수 제작 필요.(본 함수를 실행하는 다른 함수도 수정 필요할 수 있음)
    """

    if model_name is None:
        model_names = await cruder.get_model_names()
    else:
        model_names = [model_name]

    cnt : int = 0
    fail_count : int = 0
    fail_infos : list[str] = []
    for model_name in model_names:
        try:
            spec_id, spec = await get_spec_parquet(cruder, dir_base_spec, model_name)
            cnt += await process_and_upsert_vector_data(cruder, model_name, spec_id, spec)
        except Exception as e:
            fail_infos.append(f"{model_name} : {e}")
            fail_count += 1
            continue
    return {"count": cnt, "fail_count": fail_count, "fail_infos": fail_infos}


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
