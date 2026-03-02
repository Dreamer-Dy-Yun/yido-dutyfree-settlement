import pandas as pd
from DATA_PROCESSOR.edi_processor import EdiProcessor


class EdiSilla(EdiProcessor):
    HEADER_LEVELS : list[int] = [0]

    # 한글 컬럼명 -> (영문명, dtype). DB/upsert 시 타입 맞춤용.
    def column_spec(self) -> dict[str, tuple[str, str]]:
        return {
            "점": ("branch", "string"),
            "원매출일자": ("original_sales_date", "datetime64[ns]"),
            "매출일자": ("sales_date", "datetime64[ns]"),
            "여행사명": ("travel_agency_name", "string"),
            "여행사코드": ("travel_agency_code", "string"),
            "그룹번호": ("group_no", "string"),
            "대표가이드": ("lead_guide_name", "string"),
            "출생연도": ("birth_year", "datetime64[ns]"),
            "고객명": ("customer_name", "string"),
            "BILL 번호": ("bill_no", "string"),
            "BILL 상태": ("bill_status", "string"),
            "상품위치": ("product_location", "string"),
            "카테고리": ("category", "string"),
            "브랜드명": ("brand_name", "string"),
            "상품명": ("product_name", "string"),
            "상품코드": ("product_code", "string"),
            "REF NO": ("ref_no", "string"),
            "Aging": ("aging", "float64"),
            "판매형태": ("sales_type", "string"),
            "판매수량": ("sales_quantity", "float64"),
            "판매가($)": ("unit_price_usd", "float64"),
            "총매출액($)": ("gross_sales_amount_usd", "float64"),
            "총매출액(￦)": ("gross_sales_amount_krw", "float64"),
            "순매출액($)": ("net_sales_amount_usd", "float64"),
            "순매출액(￦)": ("net_sales_amount_krw", "float64"),
            "할인액($)": ("discount_amount_usd", "float64"),
            "할인액(￦)": ("discount_amount_krw", "float64"),
        }

    def _drop_total_row(self) -> pd.DataFrame:
        df = self.data
        # 합계 행 제거: 마지막 행이 비어 있으면 제거
        if pd.isna(df.iloc[-1, 0]):
            df = df.iloc[:-1]
        return df


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import io
    from patch import fix_invalid_datetime_in_xlsx_bytes
    path = r"D:\DEV\YIDO\DATA_PROCESSOR\testdata\testdata_for_edi_silla.xlsx"
    with open(path, "rb") as f:
        patched = fix_invalid_datetime_in_xlsx_bytes(f.read())
    # 전체를 문자열로 읽어서 코드 컬럼(상품코드 등)의 선행 0이 날아가지 않는지 테스트
    df = pd.read_excel(io.BytesIO(patched), dtype=str)
    edi_silla_df = EdiSilla().set_original_data(df).parse()
    print(edi_silla_df.head())
    print(edi_silla_df.columns)
    print(edi_silla_df.info())
    print(edi_silla_df.describe())
    print(edi_silla_df.shape)
    print(edi_silla_df.dtypes)
    print(edi_silla_df.isnull().sum())
    print(edi_silla_df.isnull().sum().sum())
    print(edi_silla_df.isnull().sum().sum() / edi_silla_df.size)