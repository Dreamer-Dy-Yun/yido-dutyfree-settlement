import pandas as pd
from abc import ABC, abstractmethod
from typing import Self
from CUSTOMIZED.cust_excel_processor import ExcelProcessor
from io import BytesIO
import io


class EdiProcessor(ABC):
    """
    EDI 파서 기본 클래스.
    - 엑셀 로딩/플랫헤더/타입 변환을 모두 담당하도록 위임.
    - 하위 클래스에서 헤더 레벨과 컬럼 매핑 정의 필요.

    HEADER_LEVELS 
        헤더가 하나인 경우 : [0]
        헤더가 두 개인 경우 : [0, 1]
        헤더 위에 한줄 띄우고 헤더가 두 개인 경우 : [1, 2]
    """
    HEADER_LEVELS : list[int] = None

    def __init__(self):
        self.data = None
        self.header : list[int] | None = self.HEADER_LEVELS

    def set_data(self, contents: BytesIO | pd.DataFrame) -> Self:
        """
        BytesIO(엑셀 바이트)나 DataFrame을 받아 내부 data 프레임으로 통일.
        - BytesIO면 ExcelProcessor를 통해 읽고 플랫헤더 DataFrame으로 변환
        - 이미 DataFrame이면 그대로 사용
        """
        if isinstance(contents, BytesIO):
            self.data = self._load_data(contents, header=self.header)
        else:
            self.data = contents
        return self


    def _load_data(self, contents: BytesIO, header: list[int]) -> pd.DataFrame:
        excel_processor = ExcelProcessor(contents, header=header)
        df = excel_processor.flatten_columns().to_dataframe()
        return df

    @abstractmethod
    def column_spec(self) -> dict[str, tuple[str, str]]:
        pass

    @abstractmethod
    def _drop_total_row(self) -> pd.DataFrame:
        pass

    def parse(self) -> pd.DataFrame:
        df = self._drop_total_row().copy()

        rename_map = {k.strip(): v[0] for k, v in self.column_spec().items()}
        dtype_map = {v[0].strip(): v[1].strip() for k, v in self.column_spec().items()}
        
        df = df.rename(columns=rename_map, errors="ignore")

        type_cols = {c: dtype_map[c] for c in dtype_map if c in df.columns}

        # 1) datetime 컬럼은 pd.to_datetime으로 확정 (astype에 맡기지 않음)
        datetime_cols = [c for c, t in type_cols.items() if str(t).startswith("datetime64")]
        for col in datetime_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # 2) 나머지 타입만 astype 적용
        non_datetime_cols = {c: t for c, t in type_cols.items() if c not in datetime_cols}
        if non_datetime_cols:
            df = df.astype(non_datetime_cols, errors="ignore")

        return df