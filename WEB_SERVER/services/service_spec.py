###########################################
# Module name : service_spec.py
# Module functions : get_spec_parquet
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 스펙 관련 서비스 함수
############################################

from datetime import date
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path


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
    # Windows 경로 구분자(\)를 POSIX 경로 구분자(/)로 변환
    spec_path_normalized = spec_path.replace('\\', '/')
    spec_file_path: Path = dir_base_spec / spec_path_normalized

    if not spec_file_path.exists():
        raise ValueError(f"Cannot find the spec file. fullpath : {spec_file_path} \n model_name : {model_name}")

    return spec_id, pd.read_parquet(spec_file_path)
