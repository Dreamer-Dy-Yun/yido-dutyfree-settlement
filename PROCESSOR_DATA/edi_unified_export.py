import pandas as pd
from typing import Literal
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from DATABASE.dbms.db_manager import DBManager
from DATABASE import models
from CUSTOMIZED.cust_logger import logger


class EdiUnifiedExporter:
    """
    EDI_UNIFIED + VerifiedReceipt/VerifiedPassport 를 조인하여
    엑셀/보고서용 DataFrame 을 생성하는 전용 헬퍼.
    """

    def __init__(self, db: DBManager, tenant_schema: str, public_schema: str = "public"):
        self.db: DBManager = db
        self.tenant_schema: str = tenant_schema
        self.public_schema: str = public_schema
        self.schemas: list[str] = [self.tenant_schema, self.public_schema]

    async def build_export_dataframe(
        self,
        sources: list[Literal["silla", "lotte"]] = ["silla", "lotte"],
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> pd.DataFrame:
        """
        엑셀 다운로드용 DataFrame 생성.
        - 컬럼명은 한글로 변환
        - 고객명은 매핑된 데이터(VerifiedPassport/VerifiedReceipt/EDI 순)로 채움
        - 여권번호는 매핑된 VerifiedPassport.passport_no 사용
        - uuid/id 등 내부 키는 포함하지 않음
        """
        async with self.db.open_session(schemas=self.schemas) as session:
            conds = [models.EDI_Unified.dutyfree_operator.in_(sources)]
            if from_date is not None:
                conds.append(models.EDI_Unified.datetime_purchase >= from_date)
            if to_date is not None:
                # to_date는 "해당 날짜 전체"를 포함하도록 다음날 자정 미만으로 처리
                conds.append(models.EDI_Unified.datetime_purchase < (to_date + timedelta(days=1)))

            stmt = (
                select(
                    models.EDI_Unified.dutyfree_operator.label("면세점"),
                    models.EDI_Unified.dutyfree_branch.label("지점"),
                    models.EDI_Unified.datetime_purchase.label("매출일자"),
                    models.EDI_Unified.datetime_original.label("원매출일자"),
                    models.EDI_Unified.receipt_no.label("영수증번호"),
                    models.EDI_Unified.group_no.label("그룹번호"),
                    models.EDI_Unified.customer_name.label("고객명"),
                    models.VerifiedPassport.passport_no.label("여권번호"),
                    models.EDI_Unified.product_code.label("상품코드"),
                    models.EDI_Unified.product_name.label("상품명"),
                    models.EDI_Unified.category.label("카테고리"),
                    models.EDI_Unified.brand.label("브랜드"),
                    models.EDI_Unified.manufactured_at.label("제조일자"),
                    models.EDI_Unified.quantity.label("수량"),
                    models.EDI_Unified.gross_sales_amount_usd.label("총매출액($)"),
                    models.EDI_Unified.net_sales_amount_usd.label("순매출액($)"),
                    models.EDI_Unified.discount_amount_usd.label("할인액($)"),
                    models.EDI_Unified.gross_sales_amount_krw.label("총매출액(￦)"),
                    models.EDI_Unified.net_sales_amount_krw.label("순매출액(￦)"),
                    models.EDI_Unified.discount_amount_krw.label("할인액(￦)"),
                    models.VerifiedReceipt.receipt_no.label("매칭 : 영수증번호"),
                    models.VerifiedPassport.passport_no.label("매칭 : 여권번호"),
                    models.VerifiedPassport.name.label("매칭 : 구매자"),
                )
                .select_from(models.EDI_Unified)
                .outerjoin(
                    models.VerifiedReceipt,
                    models.EDI_Unified.uuid_receipt == models.VerifiedReceipt.uuid_record,
                )
                .outerjoin(
                    models.VerifiedPassport,
                    models.EDI_Unified.uuid_passport == models.VerifiedPassport.uuid_record,
                )
                .where(*conds)
            )

            result = await session.execute(stmt)
            rows = result.mappings().all()
            if not rows:
                return pd.DataFrame()

            df_export = pd.DataFrame(rows)
            logger.info("[EDI_UNIFIED][EXPORT] export rows=%s", len(df_export))
            return df_export

