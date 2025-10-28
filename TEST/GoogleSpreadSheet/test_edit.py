from typing import Callable, Dict, Any, List
from google.oauth2.service_account import Credentials
import gspread
from gspread.utils import rowcol_to_a1
from pathlib import Path

# pip install gspread google-auth

# -------------------- 설정값 --------------------
SERVICE_ACCOUNT_JSON : Path = Path("C:/Users/user/Novas_Ez/google_service_account.json")  # 서비스 계정 키 파일 경로
SPREADSHEET_ID : str = "1xhdJsIsBjiXJ-rop6VsVxgze5Hf9ez2P4_IG-vvUktM"             # 예: "1AbcDEF...."
WORKSHEET_NAME = "시장불량"                      # 탭 이름
# ------------------------------------------------

def connect_with_service_account(json_path: str) -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"   # 쓰기 포함
    ]
    creds = Credentials.from_service_account_file(json_path, scopes=scopes)
    return gspread.authorize(creds)

def read_sheet(ws: gspread.Worksheet, header_row: int = 1) -> (List[str], List[List[str]]):
    """헤더 1행 + 데이터 행들 반환"""
    values = ws.get_all_values()
    if not values:
        return [], []
    header, data = values[header_row - 1], values[header_row:]
    return header, data

def build_header_index(header: List[str]) -> Dict[str, int]:
    """컬럼명 → 0-based 인덱스 맵"""
    return {h.strip(): i for i, h in enumerate(header)}

def update_rows_by_condition(
    sh: gspread.Spreadsheet,
    ws: gspread.Worksheet,
    header: List[str],
    data: List[List[str]],
    condition: Callable[[Dict[str, Any]], bool],
    target_column: str,
    value_to_write: str,
    value_input_option: str = "USER_ENTERED",
) -> int:
    """
    condition(row_dict) 가 True인 행의 target_column에 value_to_write 기록.
    효율을 위해 batch_update 사용.
    반환: 업데이트된 행 수
    """
    col_index = build_header_index(header)
    if target_column not in col_index:
        raise ValueError(f"타깃 컬럼 '{target_column}' 을(를) 헤더에서 찾을 수 없습니다. 현재 헤더: {header}")

    tgt_col_0 = col_index[target_column]  # 0-based
    ws_title = ws.title

    write_requests = []
    updated = 0

    for r_idx, row in enumerate(data, start=2):  # 시트의 실제 행 번호 (헤더가 1행)
        # 행을 dict로 변환 (없는 컬럼 접근 방지를 위해 get 사용)
        row_dict = {h: (row[i] if i < len(row) else "") for h, i in col_index.items()}

        if condition(row_dict):
            a1 = rowcol_to_a1(r_idx, tgt_col_0 + 1)
            write_requests.append({
                "range": a1,  # Worksheet.batch_update는 시트명 없이 A1만 사용
                "values": [[value_to_write]],
            })
            updated += 1

    if write_requests:
        ws.batch_update(write_requests, value_input_option=value_input_option)
    return updated

def main():
    gc = connect_with_service_account(SERVICE_ACCOUNT_JSON)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)

    header, data = read_sheet(ws)
    if not header:
        print("시트가 비어 있습니다.")
        return

    # ---------------- 조건과 타깃 설정 예시 ----------------
    # 예1) "불량여부" 컬럼이 "Y" 인 행 → "조치" 컬럼에 "재검 필요" 기록
    def cond(row: Dict[str, Any]) -> bool:
        return row.get("불량여부", "").strip().upper() == "Y"

    target_column = "조치"
    value_to_write = "재검 필요"
    # ------------------------------------------------------

    cnt = update_rows_by_condition(
        sh=sh,
        ws=ws,
        header=header,
        data=data,
        condition=cond,
        target_column=target_column,
        value_to_write=value_to_write,
        value_input_option="USER_ENTERED",  # 또는 "RAW"
    )
    print(f"업데이트 완료: {cnt}행")

if __name__ == "__main__":
    main()
