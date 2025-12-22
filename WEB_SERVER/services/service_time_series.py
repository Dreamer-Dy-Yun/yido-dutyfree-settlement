###########################################
# Module name : service_time_series.py
# Module functions : get_time_series_data
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 시계열 데이터 관련 서비스 함수
############################################

from datetime import date
from DATABASE.cruder import CRUDer
from typing import Any


async def get_time_series_data(
    cruder: CRUDer, 
    model_name: str, 
    inspection_idx: int, 
    date_from: date, 
    date_to: date, 
    measured_by: str | None = None
    ) -> dict[str, dict[str, float]]: 
    """시계열 데이터 조회 및 변환"""

    data : list[dict[str, Any]] = await cruder.get_time_series_data(model_name, inspection_idx, date_from, date_to, measured_by)

    result: dict[str, dict[str, float]] = {}
    for row in data:
        serial_no = row['serial_no']
        measured_at = row['measured_at']
        measured_value = row['measured_value']
        result[serial_no] = {"measuredAt": measured_at, "measuredValue": measured_value}

    return result




