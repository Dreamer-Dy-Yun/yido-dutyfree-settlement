###########################################
# Module name : cust_excel_processor.py
# Module class : ExcelProcessor
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.27
# Updated at : 2026.02.27
# Supported by : -
# Note : 
############################################
import pandas as pd
from pathlib import Path
from typing import Self
from io import BytesIO
from pandas._typing import DtypeArg

class ExcelProcessor:
    def __init__(self, path_excel: Path | BytesIO, header: list[int] = [0, 1], dtype: DtypeArg | None = str):
        self._df: pd.DataFrame | None = pd.read_excel(path_excel, header=header, dtype=dtype)
        self._path_excel = path_excel
        self._header = header

    def to_dataframe(self) -> pd.DataFrame:
        return self._df

    def flatten_columns(self, delimiter: str = "[>]") -> Self:
        self._df.columns = self._flatten_columns(self._df.columns, delimiter)
        return self

    def _flatten_columns(self, df_columns : pd.MultiIndex, delimiter: str = "[>]") -> list[str]:
        # Flattening
        col_names : list[str] = []

        if df_columns.nlevels == 1:
            return df_columns.tolist()

        for header_column in df_columns.tolist():
            col_name : list[str] = []
            for level in header_column:
                if level.startswith("Unnamed"):
                    pass
                else:
                    col_name.append(str(level))
            col_names.append(delimiter.join(col_name))

        return col_names



# TEST ################################################################
if __name__ == "__main__":
    xlpath = r"C:\Users\dev\Downloads\(LOTTE)여행사매출상세내역조회_20250421144251.xlsx"

    excel_processor = ExcelProcessor(xlpath, header=[0, 1])
    df = excel_processor.flatten_columns().to_dataframe()

    for column in df.columns:
        print(column)