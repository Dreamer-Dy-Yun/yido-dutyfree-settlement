###########################################
# Module name : service_common.py
# Module functions : get_instrument_names, get_model_names
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 여러 라우터/기능에서 공통으로 사용되는 조회 함수
############################################

from DATABASE.cruder import CRUDer


async def get_instrument_names(cruder: CRUDer) -> list[str]: 
    """ICT 장비 목록 조회 (공통)"""
    return await cruder.get_instrument_names()


async def get_model_names(cruder: CRUDer) -> list[str]: 
    """모델 목록 조회 (공통)"""
    return await cruder.get_model_names()




