###########################################
# Module name : cust_web_helper.py
# Module functions : export_excel
# Written by : Yun Dae-young 
# Created at : 2025.07.03
# Updated at : 2025.07.03
# Supported by : ChatGPT-4o
# Note : 
############################################

import asyncio
import functools
from typing import Callable, Awaitable, Any
from CUSTOMIZED.cust_logger import logger
import pandas as pd
from typing import Literal
from fastapi.responses import StreamingResponse
from io import BytesIO
import re


class Export:
    @staticmethod
    async def as_excel(df: pd.DataFrame | dict[str, pd.DataFrame], filename: str) -> StreamingResponse:
        """
        dict_df : [시트명 : 데이터 프레임]의 형태로 반환된 데이터
        filename : 파일 이름
        """
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as wb:
            if isinstance(df, dict) and all(isinstance(v, pd.DataFrame) for v in df.values()):
                sanitizer = _sheet_name_sanitizer()
                for sheet_name, df in df.items():
                    sheet_name = sanitizer.get(sheet_name)
                    df.to_excel(wb, index=False, sheet_name=sheet_name)
            elif isinstance(df, pd.DataFrame):
                df.to_excel(wb, index=False)
            else:
                raise ValueError("◈Invalid DataFrame Type◈\n\tType : {type(df)}")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )


class _sheet_name_sanitizer:
    INVALID_CHARS = r'[:\\/?*\[\]\']'  # 유효하지 않은 문자. :, \, /, ?, *, [, ], '
    MAX_LEN_SHT_NAME = 31               # 시트 이름의 최대 길이 
    def __init__(self):
        self._used = set()

    def set_used_sheet_names(self, sheet_names: list[str]):
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