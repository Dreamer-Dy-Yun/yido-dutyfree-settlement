###########################################
# Module name : service_google.py
# Module functions : get_google_spreadsheet_url_by_name
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : Google 서비스 관련 함수
############################################

from DATABASE.cruder import CRUDer


async def get_google_spreadsheet_url_by_name(cruder: CRUDer, name: str) -> str:
    """Google 스프레드시트 URL 조회"""
    service_account_info = await cruder.get_google_service_account(name)
    if service_account_info is None:
        raise ValueError(f"등록된 이름의 Google Service Account가 없습니다.")
    spreadsheet_id = service_account_info["spreadsheet_id"]
    worksheet_name = service_account_info["worksheet_name"]
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={worksheet_name}"
    return url




