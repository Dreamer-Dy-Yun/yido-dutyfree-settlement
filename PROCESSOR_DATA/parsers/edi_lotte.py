import pandas as pd
from PROCESSOR_DATA.edi_processor import EdiProcessor

class EdiLotte(EdiProcessor):
    HEADER_LEVELS : list[int] = [0, 1]
    DUTYFREE_OPERATOR : str = "LOTTE"

    # 한글 컬럼명 -> (영문명, dtype). DB/upsert 시 타입 맞춤용.
    def column_spec(self) -> dict[str, tuple[str, str]]:
        """LOTTE EDI [여행사매출상세내역조회] 기준"""
        return {
            "순번": ("seq", "Int64"),
            "0": ("zero_index", "Int64"),
            "점구분": ("branch", "string"),
            "원매출일자": ("original_sales_date", "datetime64[ns]"),
            "매출일자": ("sales_date", "datetime64[ns]"),
            "여행사": ("travel_agency_name", "string"),
            "여행사코드": ("travel_agency_code", "string"),
            "가이드": ("guide_name", "string"),
            "가이드코드": ("guide_code", "string"),
            "수입/로컬": ("sales_origin_type", "string"),
            "단체번호": ("group_no", "string"),
            "고객명": ("customer_name", "string"),
            "VIP번호": ("vip_no", "string"),
            "교환권번호": ("voucher_no", "string"),
            "교환권상태": ("voucher_status", "string"),
            "카테고리": ("category", "string"),
            "브랜드": ("brand_name", "string"),
            "상품명": ("product_name", "string"),
            "상품구분": ("product_type", "string"),
            "상품코드": ("product_code", "string"),
            "Ref.No": ("ref_no", "string"),
            "Color": ("color", "string"),
            "배송구분": ("delivery_type", "string"),
            "판매방식": ("sales_type", "string"),
            "판매수량": ("sales_quantity", "float64"),
            "판매가($)": ("unit_price_usd", "float64"),
            "매출[>]총매출액($)": ("gross_sales_amount_usd", "float64"),
            "매출[>]순매출액($)": ("net_sales_amount_usd", "float64"),
            "매출[>]할인액($)": ("discount_amount_usd", "float64"),
            "매출[>]총매출액(\\)": ("gross_sales_amount_krw", "float64"),
            "매출[>]순매출액(\\)": ("net_sales_amount_krw", "float64"),
            "매출[>]할인액(\\)": ("discount_amount_krw", "float64"),
        }

    def _drop_total_row(self) -> pd.DataFrame:
        df = self.data
        if not isinstance(df.iloc[-1, 0], (int, float)):
            # 합계 행 제거
            df = df.iloc[:-1]
        return df


    def to_unified(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        롯데 EDI DataFrame을 EDI_UNIFIED 테이블용 포맷으로 정규화.
        - 컬럼 매핑
        - 제조일자(aging)은 제공되지 않으므로 manufactured_at 은 NULL 로 둔다.
        """
        df_unified: pd.DataFrame = pd.DataFrame(index=df.index)

        # 기본 매핑 (EDI_UNIFIED 스키마 기준)
        df_unified["dutyfree_operator"] = self.DUTYFREE_OPERATOR
        df_unified["dutyfree_branch"] = df["branch"]
        df_unified["datetime_original"] = df["original_sales_date"]
        df_unified["datetime_purchase"] = df["sales_date"]
        df_unified["customer_name"] = df["customer_name"]
        df_unified["group_no"] = df["group_no"]
        df_unified["receipt_no"] = df["voucher_no"]
        df_unified["product_code"] = df["product_code"]

        # 롯데에는 aging(제조일자) 정보가 없으므로 NULL 로 유지
        df_unified["manufactured_at"] = None

        # 나머지 공통 컬럼 매핑
        df_unified["category"] = df["category"]
        df_unified["brand"] = df["brand_name"]
        df_unified["product_name"] = df["product_name"]
        df_unified["ref_no"] = df["ref_no"]
        df_unified["quantity"] = df["sales_quantity"]

        df_unified["gross_sales_amount_usd"] = df["gross_sales_amount_usd"]
        df_unified["net_sales_amount_usd"] = df["net_sales_amount_usd"]
        df_unified["discount_amount_usd"] = df["discount_amount_usd"]
        df_unified["gross_sales_amount_krw"] = df["gross_sales_amount_krw"]
        df_unified["net_sales_amount_krw"] = df["net_sales_amount_krw"]
        df_unified["discount_amount_krw"] = df["discount_amount_krw"]

        # system_note 기본값 (신라와 맞추기 위해 컬럼만 생성)
        df_unified["system_note"] = None

        return df_unified

# ---------------------------------------------------------------------------
# TEST CODE
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import io
    from patch import fix_invalid_datetime_in_xlsx_bytes
    path = r"D:\DEV\YIDO\PROCESSOR_DATA\testdata\testdata_for_edi_lotte.xlsx"
    with open(path, "rb") as f:
        patched = fix_invalid_datetime_in_xlsx_bytes(f.read())
    df = pd.read_excel(io.BytesIO(patched), dtype=str)
    edi_lotte_df = EdiLotte().set_original_data(df).parse()
    print(edi_lotte_df.head())
    print(edi_lotte_df.columns)
    print(edi_lotte_df.info())
    print(edi_lotte_df.describe())
    print(edi_lotte_df.shape)
    print(edi_lotte_df.dtypes)
    print(edi_lotte_df.isnull().sum())
    print(edi_lotte_df.isnull().sum().sum())
    print(edi_lotte_df.isnull().sum().sum() / edi_lotte_df.size)