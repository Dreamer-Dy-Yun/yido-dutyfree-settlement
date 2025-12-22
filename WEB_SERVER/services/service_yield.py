###########################################
# Module name : service_yield.py
# Module functions : get_daily_yield
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 수율 관련 서비스 함수
############################################

from datetime import date
from DATABASE.cruder import CRUDer
import pandas as pd


async def get_daily_yield(
        cruder: CRUDer,
        model_name: str | None = None, 
        date_from: date | None = None, 
        date_to: date | None = None, 
        measured_by: str | None = None,
        latest_only: bool = False
    ) -> pd.DataFrame:

    df : pd.DataFrame = pd.DataFrame(columns=["장비명", "모델명", "날짜", "OK", "NG", "TOTAL", "수율"])

    list_daily_yield = await cruder.get_daily_yield(model_name, date_from, date_to, measured_by, latest_only)

    if not list_daily_yield:
        raise ValueError(f"Cannot find the daily yield data. model_name : {model_name}")
    else:
        df = pd.DataFrame(list_daily_yield).rename(columns={"instrument_name": "장비명", "model_name": "모델명", "date": "날짜"})
        df["수율"] = df["OK"] / df["TOTAL"] * 100
        # 날짜를 datetime 타입으로 변환 (정렬을 위해)
        df["날짜"] = pd.to_datetime(df["날짜"])
        # 중요도 순서로 정렬: 장비명, 모델명, 날짜
        df = df.sort_values(by=["장비명", "모델명", "날짜"], ascending=[True, True, True])
        # 인덱스 리셋
        df = df.reset_index(drop=True)
        # 날짜를 다시 date 형식으로 변환 (표시용)
        df["날짜"] = df["날짜"].dt.date
        # 컬럼 순서 지정
        df = df[["장비명", "모델명",  "날짜", "OK", "NG", "TOTAL", "수율"]]
    return df
