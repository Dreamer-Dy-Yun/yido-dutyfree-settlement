
import pandas as pd
from typing import Self
from edi_processor import EdiProcessor

class EdiLotte(EdiProcessor):

    def set_original_data(self, df : pd.DataFrame) -> Self:
        self.original_data = df
        return self

    def parse(self) -> pd.DataFrame:
        return self.original_data.rename(
            columns={
                "순번": "seq",
                "0": "zero_index",  # 용도에 맞게 나중에 수정 가능
                "점구분": "branch",
                "원매출일자": "original_sales_date",
                "매출일자": "sales_date",
                "여행사": "travel_agency_name",
                "여행사코드": "travel_agency_code",
                "가이드": "guide_name",
                "가이드코드": "guide_code",
                "수입/로컬": "sales_origin_type",
                "단체번호": "group_no",
                "고객명": "customer_name",
                "VIP번호": "vip_no",
                "교환권번호": "voucher_no",
                "교환권상태": "voucher_status",
                "카테고리": "category",
                "브랜드": "brand_name",
                "상품명": "product_name",
                "상품구분": "product_type",
                "상품코드": "product_code",
                "Ref.No": "ref_no",
                "Color": "color",
                "배송구분": "delivery_type",
                "판매방식": "sales_type",
                "판매수량": "sales_quantity",
                "판매가($)": "unit_price_usd",

                # 매출 관련 (플랫헤더: '매출[>]' 접두 포함)
                "매출[>]총매출액($)": "gross_sales_amount_usd",
                "매출[>]순매출액($)": "net_sales_amount_usd",
                "매출[>]할인액($)": "discount_amount_usd",
                "매출[>]총매출액(\\)": "gross_sales_amount_krw",
                "매출[>]순매출액(\\)": "net_sales_amount_krw",
                "매출[>]할인액(\\)": "discount_amount_krw",
            },
            errors="ignore",
        )   