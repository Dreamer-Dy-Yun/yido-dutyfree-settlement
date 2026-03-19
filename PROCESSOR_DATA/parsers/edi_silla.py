import pandas as pd
from PROCESSOR_DATA.edi_processor import EdiProcessor
from datetime import datetime


class EdiSilla(EdiProcessor):
    HEADER_LEVELS : list[int] = [0]
    DUTYFREE_OPERATOR : str = "SILLA"

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
            "Aging": ("aging", "string"),
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


    def parse(self) -> pd.DataFrame:
        """
        기본 파싱 후, DB 제약(aging NOT NULL)을 만족하도록 aging 결측치를 ""로 보정한다.
        """
        df = super().parse()

        s: pd.Series = df["aging"]
        s = s.where(s.notna(), "")
        df["aging"] = s.astype(str).str.strip().replace({"nan": ""})

        return df


    def _parse_aging(self, text_aging: str) -> datetime:
        """안씀. 레거시"""
        if text_aging == "":
            raise ValueError("제조일자(manufactured_at) 변환 실패 : aging is empty")
        if text_aging[-2:] == "00":
            text_aging = text_aging[:-2] + "01"
        try:
            result: datetime = pd.to_datetime(text_aging, format="%y%m%d")
        except ValueError:
            raise ValueError(f"제조일자(manufactured_at) 변환 실패 : aging is invalid value ( {text_aging} )")
        return result


    def _normalize_manufactured_at_and_system_note(
        self,
        df: pd.DataFrame,
        df_unified: pd.DataFrame,
    ) -> None:
        """
        aging 컬럼을 이용해 manufactured_at을 계산하고,
        변환 실패한 경우 system_note 에 메시지를 추가한다.
        """
        raw_aging = df["aging"].astype(str).str.strip().replace("", pd.NA)

        # YYMMDD 에서 DD == "00" 인 경우 01일로 간주
        mask_dd00 = raw_aging.notna() & (raw_aging.str[-2:] == "00")
        raw_aging_adj = raw_aging.mask(mask_dd00, raw_aging.str[:-2] + "01")

        manufactured = pd.to_datetime(raw_aging_adj, format="%y%m%d", errors="coerce")
        df_unified["manufactured_at"] = manufactured

        # 변환 실패한 제조일자에 대해 system_note에 기록
        mask_invalid = raw_aging_adj.notna() & manufactured.isna()
        if mask_invalid.any():
            note_prefix = "manufactured_at 변환 실패 (aging="
            df_unified.loc[mask_invalid, "system_note"] = (
                df_unified.loc[mask_invalid, "system_note"].fillna("")
                + note_prefix
                + raw_aging_adj[mask_invalid]
                + "); "
            )


    def to_unified(self, df: pd.DataFrame) -> pd.DataFrame:
        df_unified: pd.DataFrame = pd.DataFrame(index=df.index)

        # 기본 매핑 (EDI_UNIFIED 스키마 기준)
        df_unified["dutyfree_operator"] = self.DUTYFREE_OPERATOR
        df_unified["dutyfree_branch"] = df["branch"]
        df_unified["datetime_original"] = df["original_sales_date"]
        df_unified["datetime_purchase"] = df["sales_date"]
        df_unified["customer_name"] = df["customer_name"]
        df_unified["group_no"] = df["group_no"]
        df_unified["receipt_no"] = df["bill_no"]
        df_unified["product_code"] = df["product_code"]

        df_unified["category"] = df["category"]
        df_unified["brand"] = df["brand_name"]
        # df_unified["sku"] = None
        df_unified["product_name"] = df["product_name"]
        df_unified["ref_no"] = df["ref_no"]
        df_unified["quantity"] = df["sales_quantity"]
        df_unified["gross_sales_amount_usd"] = df["gross_sales_amount_usd"]
        df_unified["net_sales_amount_usd"] = df["net_sales_amount_usd"]
        df_unified["discount_amount_usd"] = df["discount_amount_usd"]
        df_unified["gross_sales_amount_krw"] = df["gross_sales_amount_krw"]
        df_unified["net_sales_amount_krw"] = df["net_sales_amount_krw"]
        df_unified["discount_amount_krw"] = df["discount_amount_krw"]

        # system_note 초기화
        df_unified["system_note"] = ""

        # 제조일자 및 system_note 정규화
        self._normalize_manufactured_at_and_system_note(df, df_unified)

        # 빈 문자열 system_note 는 None 으로 정리
        df_unified["system_note"] = df_unified["system_note"].replace("", None)

        return df_unified



# ---------------------------------------------------------------------------
# TEST CODE
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import io
    from patch import fix_invalid_datetime_in_xlsx_bytes
    path = r"D:\DEV\YIDO\PROCESSOR_DATA\testdata\testdata_for_edi_silla.xlsx"
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