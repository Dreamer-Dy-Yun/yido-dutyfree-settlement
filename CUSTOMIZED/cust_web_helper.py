###########################################
# Module name : cust_web_helper.py
# Module functions : export_excel
# Written by : Yun Dae-young 
# Created at : 2025.07.03
# Updated at : 2025.07.03
# Supported by : ChatGPT-4o
# Note : 
#       2025.12.29 : 템플릿을 사용하여 Excel 파일을 생성하는 기능 추가(Export.as_excel_via_template)
#       2025.12.29 : ExcelHelper 추가. 추후 분리 필요
############################################

from pathlib import Path
from CUSTOMIZED.cust_logger import logger
import pandas as pd
from typing import Literal
from fastapi.responses import StreamingResponse
from io import BytesIO
import re
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows

class Export:
    @staticmethod
    async def as_excel(df: pd.DataFrame | dict[str, pd.DataFrame], filename: str, include_header: bool = True, include_index: bool = False) -> StreamingResponse:
        """
        Excel 파일을 생성합니다.
        df : DataFrame 또는 [시트명 : 데이터 프레임] 또는 [시트명!셀주소 : 데이터 프레임]의 형태
            ex) {"Sheet1": df} -> 시트명 : Sheet1, 셀주소 : A1
            ex) {"Sheet1!A2": df} -> 시트명 : Sheet1, 셀주소 : A2
        filename : 파일 이름
        include_header : 헤더(컬럼명) 포함 여부
        include_index : 인덱스 포함 여부
        """
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as wb:
            if isinstance(df, dict) and all(isinstance(v, pd.DataFrame) for v in df.values()):
                sanitizer = _sheet_name_sanitizer()
                for addr, df_item in df.items():
                    # 셀 주소 파싱
                    sht_name, cell_address = ExcelHelper.split_address(addr)
                    ExcelHelper.validate_sht_name(sht_name)
                    start_cell_address, _ = ExcelHelper.split_range_address(cell_address)
                    
                    # 시트명 정리
                    sht_name = sanitizer.get(sht_name)
                    
                    # 셀 주소를 행/열로 변환 (xlsxwriter는 0-based이므로 1을 빼야 함)
                    start_row, start_col = ExcelHelper.cell_to_row_col(start_cell_address)
                    start_row -= 1  # xlsxwriter는 0-based
                    start_col -= 1  # xlsxwriter는 0-based
                    
                    df_item.to_excel(
                        wb, 
                        index=include_index, 
                        header=include_header,
                        sheet_name=sht_name,
                        startrow=start_row,
                        startcol=start_col
                    )
            elif isinstance(df, pd.DataFrame):
                df.to_excel(wb, index=include_index, header=include_header)
            else:
                raise ValueError("◈Invalid DataFrame Type◈\n\tType : {type(df)}")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )

    @staticmethod
    async def as_excel_via_template(
        dfs: dict[str, pd.DataFrame], 
        template_path: Path, 
        filename: str, 
        create_sheet: bool = False,
        include_header: bool = False,
        include_index: bool = False
    ) -> StreamingResponse:
        """
        템플릿을 사용하여 Excel 파일을 생성합니다.
        dfs : [시트명!셀주소 : 데이터 프레임] 혹은 [시트명 : 데이터 프레임]의 형태로 반환된 데이터 프레임 딕셔너리
            ex) {"Sheet1!A2:D4": df} -> 시트명 : Sheet1, 셀주소 : A2
            ex) {"Sheet1": df} -> 시트명 : Sheet1, 셀주소 : A1
        template_path : 템플릿 파일 경로
        filename : 파일 이름
        create_sheet : 시트가 없을 때 생성 여부
        include_header : 헤더(컬럼명) 포함 여부
        include_index : 인덱스 포함 여부
        """
        # keep_vba=True: VBA 매크로 및 고급 기능(슬라이서, 피벗 테이블 등) 보존
        # keep_links=True: 외부 링크 및 차트 데이터 소스 보존
        wb = openpyxl.load_workbook(template_path, keep_vba=True, keep_links=True)
        # 템플릿 파일(.xltx)을 읽었을 때 template 속성이 True로 설정될 수 있으므로 False로 변경
        wb.template = False

        for addr, df in dfs.items():
            sht_name, cell_address_to_paste_data = ExcelHelper.split_address(addr)
            ExcelHelper.validate_sht_name(sht_name)
            start_cell_address, _ = ExcelHelper.split_range_address(cell_address_to_paste_data)
            
            if sht_name not in wb.sheetnames:
                if create_sheet:
                    wb.create_sheet(title=sht_name)
                else:
                    raise ValueError(f"Sheet {sht_name} not found in template")
            
            ws = wb[sht_name]
            
            # 인덱스를 포함하지 않을 때만 리셋
            if not include_index:
                df = df.reset_index(drop=True)
            
            # 셀 주소를 (row, col) 튜플로 변환
            start_row, start_col = ExcelHelper.cell_to_row_col(start_cell_address)
            
            # DataFrame을 행 리스트로 변환
            rows = list(dataframe_to_rows(df, index=include_index, header=include_header))
            
            # 한번에 붙여넣기
            for r_idx, row_data in enumerate(rows, start=start_row):
                for c_idx, value in enumerate(row_data, start=start_col):
                    ws.cell(row=r_idx, column=c_idx, value=value)

        out_buf = BytesIO()
        wb.save(out_buf)
        out_buf.seek(0)

        return StreamingResponse(
            out_buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )


# TODO : 나중에 분리 할 것
class ExcelHelper:
    @staticmethod
    def cell_to_row_col(cell_address: str) -> tuple[int, int]:
        """
        셀 주소를 (row, col) 튜플로 변환
        예: "A2" -> (2, 1), "B3" -> (3, 2)
        """
        column_str, row = openpyxl.utils.cell.coordinate_from_string(cell_address.strip())
        col = openpyxl.utils.cell.column_index_from_string(column_str)
        return row, col

    @staticmethod
    def split_range_address(range_cell_address: str, raise_error: bool = True) -> tuple[str, str]:
        parts : list[str] = range_cell_address.split(":")  
        start_cell_address : str = ""
        end_cell_address : str = ""
        if len(parts) > 2:
            raise ValueError(f"Invalid address format: {range_cell_address} (multiple ':' found)")
        elif len(parts) == 1:
            start_cell_address = range_cell_address
        else :
            start_cell_address = parts[0].strip()
            end_cell_address = parts[1].strip()
            ExcelHelper.validate_cell_address(end_cell_address, raise_error)

        ExcelHelper.validate_cell_address(start_cell_address, raise_error)
        
        return start_cell_address, end_cell_address

    @staticmethod
    def split_address(address : str) -> tuple[str, str]:
        parts : list[str] = address.split("!")
        if len(parts) > 2:
            raise ValueError(f"Invalid address format: {address} (multiple '!' found)")
        elif len(parts) == 1:
            return address, "A1"
        else :
            return parts[0], parts[1]

    @staticmethod
    def validate_sht_name(sht_name: str, raise_error: bool = True) -> bool:
        invalid_chars = r'[:\\/?*\[\]\'!]'
        if any(char in sht_name for char in invalid_chars):
            if raise_error:
                raise ValueError(f"Invalid sheet name: {sht_name}")
            else:
                return False
        else:
            return True

    @staticmethod
    def validate_cell_address(cell_address: str, raise_error: bool = True, err_msg: str | None = None) -> bool:
        try : 
            openpyxl.utils.cell.coordinate_from_string(cell_address.strip())
            return True
        except :
            if raise_error:
                if err_msg:
                    raise ValueError(err_msg)
                else:
                    raise ValueError(f"Invalid cell address: {cell_address}")
            else:
                return False




class _sheet_name_sanitizer:
    INVALID_CHARS = r'[:\\/?*\[\]\'!]'  # 유효하지 않은 문자. :, \, /, ?, *, [, ], ', !
    MAX_LEN_SHT_NAME = 31               # 시트 이름의 최대 길이 
    def __init__(self):
        self._used = set()

    def set_used_sheet_names(self, sheet_names: list[str]) -> None:
        self._used = set(sheet_names)

    def get(self, name: str, default: str = "Sheet") -> str:
        s = (name or "").strip().strip("'")  # 문자열 양쪽의 공백과 작은따옴표 제거
        s = re.sub(self.INVALID_CHARS, "_", s) or default
        s = s.replace("'", "''")        # 시트 명에 '는 허용되나, 이스케이프 필요
        s = s[:self.MAX_LEN_SHT_NAME]        # 시트 이름의 최대 길이 제한
        return self._modify_sheet_name(s)

    def _modify_sheet_name(self, sheet_name: str) -> str:
        if self._used is not None:
            base = sheet_name
            i = 1
            while sheet_name in self._used:
                suffix = f"_({i})"
                sheet_name = (base[: self.MAX_LEN_SHT_NAME - len(suffix)]) + suffix
                i += 1
            self._used.add(sheet_name)
        return sheet_name



if __name__ == "__main__":
    used = set()
    sanitizer = _sheet_name_sanitizer()
    print(sanitizer.get("Sheet1"))
    print(sanitizer.get("Sheet1"))
    print(sanitizer.get("Sheet1"))
    print(sanitizer.get("Sheet1"))
    print(sanitizer.get("Sheet1"))
    print(sanitizer.get("Sheet1"))