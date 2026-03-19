import pandas as pd
from typing import Literal
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from DATABASE.dbms.db_manager import DBManager
from DATABASE import models


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
            # EDI_UNIFIED 기본 데이터 조회
            stmt = select(models.EDI_UNIFIED).where(
                models.EDI_UNIFIED.dutyfree_operator.in_(sources)
            )
            if from_date is not None:
                stmt = stmt.where(models.EDI_UNIFIED.datetime_purchase >= from_date)
            if to_date is not None:
                stmt = stmt.where(models.EDI_UNIFIED.datetime_purchase <= to_date)

            result = await session.execute(stmt)
            rows = result.mappings().all()
            if not rows:
                return pd.DataFrame()

            df_uni = pd.DataFrame(rows)

            # VerifiedReceipt / VerifiedPassport 조인용 데이터 준비
            uuid_receipts = df_uni["uuid_receipt"].dropna().unique().tolist() if "uuid_receipt" in df_uni.columns else []
            uuid_passports = df_uni["uuid_passport"].dropna().unique().tolist() if "uuid_passport" in df_uni.columns else []

            df_vr = pd.DataFrame()
            df_vp = pd.DataFrame()

            if uuid_receipts:
                stmt_vr = select(models.VerifiedReceipt).where(
                    models.VerifiedReceipt.uuid_record.in_(uuid_receipts)
                )
                res_vr = await session.execute(stmt_vr)
                rows_vr = res_vr.mappings().all()
                if rows_vr:
                    df_vr = pd.DataFrame(rows_vr)

            if uuid_passports:
                stmt_vp = select(models.VerifiedPassport).where(
                    models.VerifiedPassport.uuid_record.in_(uuid_passports)
                )
                res_vp = await session.execute(stmt_vp)
                rows_vp = res_vp.mappings().all()
                if rows_vp:
                    df_vp = pd.DataFrame(rows_vp)

        # pandas 상에서 조인 처리
        df_merged = df_uni

        if not df_vr.empty and "uuid_receipt" in df_merged.columns:
            df_merged = df_merged.merge(
                df_vr[["uuid_record", "name"]],
                left_on="uuid_receipt",
                right_on="uuid_record",
                how="left",
                suffixes=("", "_vr"),
            )

        if not df_vp.empty and "uuid_passport" in df_merged.columns:
            df_merged = df_merged.merge(
                df_vp[["uuid_record", "name", "passport_no"]],
                left_on="uuid_passport",
                right_on="uuid_record",
                how="left",
                suffixes=("", "_vp"),
            )

        # 고객명 및 여권번호 확정
        name_cols = []
        if "name_vp" in df_merged.columns:
            name_cols.append("name_vp")
        if "name_vr" in df_merged.columns:
            name_cols.append("name_vr")
        if "customer_name" in df_merged.columns:
            name_cols.append("customer_name")

        def _choose_name(row) -> str | None:
            for col in name_cols:
                val = row.get(col)
                if pd.notna(val) and val != "":
                    return val
            return None

        if name_cols:
            df_merged["고객명"] = df_merged.apply(_choose_name, axis=1)
        else:
            df_merged["고객명"] = None

        passport_col = "passport_no" if "passport_no" in df_merged.columns else None
        if passport_col:
            df_merged["여권번호"] = df_merged[passport_col]
        else:
            df_merged["여권번호"] = None

        # 엑셀용 출력 컬럼 구성 (한글 헤더)
        df_export = pd.DataFrame()
        df_export["면세점"] = df_merged.get("dutyfree_operator")
        df_export["지점"] = df_merged.get("dutyfree_branch")
        df_export["매출일자"] = df_merged.get("datetime_purchase")
        df_export["원매출일자"] = df_merged.get("datetime_original")
        df_export["영수증번호"] = df_merged.get("receipt_no")
        df_export["그룹번호"] = df_merged.get("group_no")
        df_export["고객명"] = df_merged.get("고객명")
        df_export["여권번호"] = df_merged.get("여권번호")
        df_export["상품코드"] = df_merged.get("product_code")
        df_export["상품명"] = df_merged.get("product_name")
        df_export["카테고리"] = df_merged.get("category")
        df_export["브랜드"] = df_merged.get("brand")
        df_export["제조일자"] = df_merged.get("manufactured_at")
        df_export["수량"] = df_merged.get("quantity")
        df_export["총매출액($)"] = df_merged.get("gross_sales_amount_usd")
        df_export["순매출액($)"] = df_merged.get("net_sales_amount_usd")
        df_export["할인액($)"] = df_merged.get("discount_amount_usd")
        df_export["총매출액(￦)"] = df_merged.get("gross_sales_amount_krw")
        df_export["순매출액(￦)"] = df_merged.get("net_sales_amount_krw")
        df_export["할인액(￦)"] = df_merged.get("discount_amount_krw")
        df_export["시스템메모"] = df_merged.get("system_note")

        return df_export

