###########################################
# Module name : service_instrument.py
# Module functions : upsert_instrument
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 장비(Instrument) 관련 서비스 함수
############################################

from DATABASE.cruder import CRUDer
import pandas as pd


async def upsert_instrument(
    cruder: CRUDer, 
    df: pd.DataFrame
    ) -> None:
    """ICT 장비 정보 등록/수정"""
    await cruder.upsert_instrument(df)




