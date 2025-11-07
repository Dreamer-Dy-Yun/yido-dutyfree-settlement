###########################################
# Module name : test_edit.py
# Module functions : -
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.10.15
# Updated at : 2025.10.15
# Supported by : -
# Note : 
#   전용 함수라 의존성 강함. 나중에 나누어야 함.
#   리팩토링 필요.
############################################


from typing import Dict, Any, List, Literal
import asyncio
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
from pathlib import Path
from DATABASE.cruder import CRUDer
from DATABASE import models
from DATABASE.config import db_manager
import pandas as pd
from CUSTOMIZED.cust_logger import logger
import json

# pip install gspread google-auth

# -------------------- 설정값 --------------------
# INSERT INTO google_service_account (name, path_account, scopes, spreadsheet_id, worksheet_name)
# VALUES (
#     '시장불량', 
#     'C:/Users/user/Novas_Ez/google_service_account.json', 
#     ARRAY['https://www.googleapis.com/auth/spreadsheets'],
#     '1xhdJsIsBjiXJ-rop6VsVxgze5Hf9ez2P4_IG-vvUktM',
#     '시장불량'
# );
# ------------------------------------------------


def connect_with_service_account(service_account: Path, service_scopes: List[str]) -> gspread.Client:
    creds = Credentials.from_service_account_file(service_account, scopes=service_scopes)
    return gspread.authorize(creds)


def get_data_form_sheet(ws: gspread.Worksheet, target_range: str | None = None, set_first_row_as_header: bool = True, trim_headers: bool = True) -> pd.DataFrame:

    if target_range:
        values = ws.range(target_range)
    else:
        values = ws.get_all_values()
    
    if not values:
        return pd.DataFrame()

    if set_first_row_as_header:
        column_names : list[str] = values[0]
        if trim_headers:
            column_names = [name.strip() for name in column_names]
        df = pd.DataFrame(values[1:], columns=column_names)
    else:
        df = pd.DataFrame(values)

    return df


def update_google_spreadsheet(
    ws: gspread.Worksheet,
    df: pd.DataFrame,
    include_header: bool = True,
    cell_addr_start: str = "A1",
    value_input_option: str = "USER_ENTERED",
    ignore_when_empty: bool = True,
) -> int:
    """
    DataFrame 전체를 Google Sheets에 업데이트.
    반환: 업데이트된 행 수
    """
    if df.empty and ignore_when_empty:
        return 0

    start_row, start_col = gspread.utils.a1_to_rowcol(cell_addr_start)

    # DataFrame을 리스트로 변환 (헤더 포함 여부 반영)
    values : List[List[Any]] = df.values.tolist()
    if include_header:
        values = [df.columns.tolist()] + values

    # 범위 계산
    end_row : int = start_row + len(values) - 1
    end_col : int = start_col + len(df.columns) - 1

    str_range : str = f"{cell_addr_start}:{gspread.utils.rowcol_to_a1(end_row, end_col)}"
    
    # 배치 업데이트
    ws.batch_update([{
        "range": str_range,  
        "values": values
    }], value_input_option=value_input_option)
    
    return len(values)


async def verify_n_upsert_serial_no(
    data: pd.DataFrame, 
    ws: gspread.Worksheet,
    cruder: CRUDer,
    field_name_serial_no: str = "시리얼 넘버", 
    field_name_sys_note: str = "시스템",
    field_name_detection_place: str = "검출장소",
    field_name_detected_at: str = "검출일시",
    field_name_detection_person: str = "검출자",
    field_name_note: str = "비고"
    ) -> int:
    """
    - data내의 "시리얼 넘버" 컬럼에서 시리얼 넘버가 DB에 존재하는지 확인하고, 
    - 존재하지 않는 시리얼 넘버는 "시스템" 컬럼에 내용 기록 후, field_name_sys_note만 Google Spreadsheet에 업데이트.
    - 존재하는 시리얼 넘버는 DB에 업데이트.
    """

    db_serials = set(await cruder.get_serial_nos())
    md : type[models.ExternalDefect] = models.ExternalDefect

    if field_name_serial_no not in data.columns:
        data[field_name_serial_no] = ""
    if field_name_detection_place not in data.columns:
        data[field_name_detection_place] = ""
    if field_name_detected_at not in data.columns:
        data[field_name_detected_at] = ""
    if field_name_detection_person not in data.columns:
        data[field_name_detection_person] = ""
    if field_name_note not in data.columns:
        data[field_name_note] = ""
    if field_name_sys_note not in data.columns:
        data[field_name_sys_note] = ""

    clean_serial = data[field_name_serial_no].astype(str).str.strip()
    mask_exists = clean_serial.isin(db_serials)
    mask_missing = ~clean_serial.isin(db_serials)

    data.loc[mask_missing, field_name_sys_note] = ("시리얼 넘버(" + clean_serial[mask_missing] + ")가 존재하지 않습니다.")
    data.loc[mask_exists, field_name_sys_note] = ("DataBase에 반영되었습니다")
    
    df_to_upsert = data.loc[mask_exists].copy()

    df_to_upsert = df_to_upsert.drop_duplicates(subset=[field_name_serial_no], keep="last")
        
    df_to_upsert = df_to_upsert.rename(columns={
        field_name_serial_no: md.serial_no.name,
        field_name_detection_place: md.recognized_place.name,
        field_name_detected_at: md.recognized_at.name,
        field_name_detection_person: md.recognized_by.name,
        field_name_note: md.note.name
    })
    
    # 모델에 필요한 컬럼만 선택 (불필요한 컬럼 제거)
    # model_columns = [col.name for col in md.__table__.columns]
    # df_to_upsert = df_to_upsert[[col for col in model_columns if col in df_to_upsert.columns]]

    for column in md.__table__.columns:
        col_name = column.name
        if col_name in df_to_upsert.columns:
            if str(column.type).startswith('DATETIME'):
                # NaT 객체를 None으로 변환 (astype(object) 사용. pd.to_datetime() 사용 시, NaT 객체로 강제 변환됨)
                df_to_upsert[col_name] = pd.to_datetime(df_to_upsert[col_name], errors="coerce").astype(object)
                # DB에 입력하기 위한 변환(NaT → None)
                df_to_upsert[col_name] = df_to_upsert[col_name].where(df_to_upsert[col_name].notna(), None)

    # 문자열 컬럼의 빈 문자열은 None으로
    for col in [md.recognized_by.name, md.recognized_place.name, md.note.name]:
        if col in df_to_upsert.columns:
            df_to_upsert[col] = df_to_upsert[col].replace("", None)

    # 업서트
    if not df_to_upsert.empty:
        await cruder.upsert_external_defect(df_to_upsert)

    df_sheet_vals = data[[field_name_sys_note]].replace([pd.NA], None).fillna("")
    sys_note_idx = data.columns.get_loc(field_name_sys_note)

    update_google_spreadsheet(ws, data.head(0).copy(), include_header=True, ignore_when_empty=False, cell_addr_start=gspread.utils.rowcol_to_a1(1, 1))
    update_google_spreadsheet(ws, df_sheet_vals, include_header=False, cell_addr_start=gspread.utils.rowcol_to_a1(2, sys_note_idx + 1))

    return len(df_to_upsert)


async def sync_external_defect_data(cruder: CRUDer, name:str | None = None) -> dict[str, Any]:

    result : dict[str, Any] = {
        "message": "",
        "applied_row_count": 0,
        "time_consumed_sec": 0
    }
    cnt : int = 0
    msg : str = ""
    start_time : datetime = datetime.now()

    try :
        logger.info(f"📌 {name} 데이터 동기화 시작")

        service_account_info : dict[str, Any] = await cruder.get_google_service_account(name)
        if service_account_info is None:
            raise ValueError(f"등록된 이름의 Google Service Account가 없습니다.")

        service_account : Path = Path(service_account_info["path_account"])  
        service_scopes : List[str] = service_account_info["scopes"]  
        spreadsheet_id : str = service_account_info["spreadsheet_id"]
        worksheet_name : str = service_account_info["worksheet_name"]

        gc : gspread.Client = connect_with_service_account(service_account, service_scopes)
        sh : gspread.Spreadsheet = gc.open_by_key(spreadsheet_id)
        ws : gspread.Worksheet = sh.worksheet(worksheet_name)
        df_sheet : pd.DataFrame = get_data_form_sheet(ws)
        logger.info(f"    - 구글 스프레드 시트에 [시스템] 필드 데이터 완료: {df_sheet.shape[0]}행")
        cnt = await verify_n_upsert_serial_no(df_sheet, ws, cruder)
        logger.info(f"    - {name}의 {worksheet_name}의 데이터를 DB에 반영 완료")
        msg = f"📌 [{name}] 데이터 동기화 완료 : {cnt}행"
        logger.info(msg)

    except Exception as e:
        msg = f"📌 [{name}] 데이터 동기화 오류 발생: {e}"
        cnt = -1
        logger.error(msg, exc_info=True)

    finally:
        result["applied_row_count"] = cnt        
        result["message"] = msg
        result["time_consumed_sec"] = (datetime.now() - start_time).total_seconds()
    return result


# #TEST################################################################################################
if __name__ == "__main__":
    asyncio.run(sync_external_defect_data())
