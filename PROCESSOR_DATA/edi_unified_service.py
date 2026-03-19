# ############################################################################
# Module name : edi_unified_service.py
# Module functions : sync_edi_to_unified, fill_uuid_receipt, fill_uuid_passport, run
# Written by : Cursor AI / Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.18
# Updated at : 2026.03.18
# Supported by : -
# Note : 확인 필요(일정 부분 수정. 너무 피곤해서 지시 사항을 상세히 검토 할 수 없음. 추후 검토)
# ############################################################################

import pandas as pd
from typing import Literal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import time

from DATABASE.dbms.db_manager import DBManager
from DATABASE import models
from PROCESSOR_DATA.parsers.edi_silla import EdiSilla
from PROCESSOR_DATA.parsers.edi_lotte import EdiLotte
from CUSTOMIZED.cust_logger import logger


class EdiUnifiedService:
    """
    EDI_SILLA / EDI_LOTTE 원본을 EDI_UNIFIED 로 정규화/업서트하고,
    이후 VerifiedReceipt 기반으로 uuid_receipt 를 채우는 서비스.
    """

    def __init__(self, db: DBManager, tenant_schema: str, public_schema: str = "public"):
        self.db: DBManager = db
        self.tenant_schema: str = tenant_schema
        self.public_schema: str = public_schema
        self.schemas: list[str] = [self.tenant_schema, self.public_schema]

    async def _lock_and_fetch_unprocessed_edi(
        self,
        session: AsyncSession,
        source: Literal["SILLA", "LOTTE"],
        max_rows: int | None = None,
    ) -> pd.DataFrame:
        """
        is_processed = False 인 EDI 원본 데이터를
        UPDATE ... RETURNING 으로 한 번에 가져오면서 is_processed 를 True 로 세팅.

        - 동시 실행시에도 같은 행이 중복 선택되지 않도록 락 관점에서 안전한 패턴.
        """
        if source == "SILLA":
            table = models.EdiSilla
        else:
            table = models.EdiLotte

        stmt = (
            update(table)
            .where(table.is_processed.is_(False))
            .values(is_processed=True)
            .returning(*table.__table__.columns)
        )
        if max_rows is not None:
            stmt = stmt.limit(max_rows)

        result = await session.execute(stmt)
        mappings = result.mappings().all()
        return pd.DataFrame(mappings) if mappings else pd.DataFrame()


    async def sync_edi_to_unified(
        self,
        sources: list[Literal["SILLA", "LOTTE"]] = ["SILLA", "LOTTE"],
        max_rows: int | None = None,
    ) -> None:
        """
        1단계: EDI_SILLA / EDI_LOTTE 의 is_processed = False 인 행들을
        각 파서의 to_unified 로 정규화한 뒤, EDI_UNIFIED 로 업서트.
        이 메서드 호출 한 번은 단일 트랜잭션으로 처리된다.
        """
        async with self.db.open_session(schemas=self.schemas) as session:
            for source in sources:
                df_edi = await self._lock_and_fetch_unprocessed_edi(session, source, max_rows)
                if df_edi.empty:
                    continue

                if source == "SILLA":
                    parser = EdiSilla().set_data(df_edi)
                else:
                    parser = EdiLotte().set_data(df_edi)

                df_parsed = parser.parse()
                df_unified = parser.to_unified(df_parsed)
                if df_unified is None or df_unified.empty:
                    continue

                await self.db.upsert_batch(
                    table=models.EDI_UNIFIED,
                    data=df_unified,
                    schemas=self.schemas,
                    partial_commit=False,
                    session=session,
                )

            await session.commit()


    async def fill_uuid_receipt(
        self,
        sources: list[Literal["SILLA", "LOTTE"]] = ["SILLA", "LOTTE"],
        max_rows: int | None = None,
    ) -> None:
        """
        2단계: EDI_UNIFIED 에서 uuid_receipt 가 NULL 인 행들에 대해,
        VerifiedReceipt 를 영수증 번호/면세점 기준으로 찾아 uuid_receipt 를 채운다.
        """
        async with self.db.open_session(schemas=self.schemas) as session:
            # 매핑 대상 EDI_UNIFIED 행 조회
            stmt_unified = select(*models.EDI_UNIFIED.__table__.columns).where(
                models.EDI_UNIFIED.uuid_receipt.is_(None),
                models.EDI_UNIFIED.dutyfree_operator.in_(sources),
            )
            if max_rows is not None:
                stmt_unified = stmt_unified.limit(max_rows)

            result_unified = await session.execute(stmt_unified)
            rows_unified = result_unified.mappings().all()
            if not rows_unified:
                return

            df_unified = pd.DataFrame(rows_unified)

            # 대응되는 VerifiedReceipt 조회 (dutyfree_operator ↔ dutyfree_company, receipt_no 기반)
            dutyfree_ops = df_unified["dutyfree_operator"].dropna().unique().tolist()
            receipt_nos = (
                df_unified["receipt_no"]
                .dropna()
                .astype(str)
                .str.replace("-", "", regex=False)
                .str.replace(" ", "", regex=False)
                .unique()
                .tolist()
            )

            stmt_vr = select(*models.VerifiedReceipt.__table__.columns).where(
                models.VerifiedReceipt.dutyfree_company.in_(dutyfree_ops),
                models.VerifiedReceipt.normalized_receipt_no.in_(receipt_nos),
            )
            result_vr = await session.execute(stmt_vr)
            rows_vr = result_vr.mappings().all()
            if not rows_vr:
                return

            df_vr = pd.DataFrame(rows_vr)

            # DataFrame 기준으로 조인 (VerifiedReceipt.normalized_receipt_no 기준)
            df_unified["receipt_no_norm"] = (
                df_unified["receipt_no"]
                .astype(str)
                .str.replace("-", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df_vr["receipt_no_norm"] = df_vr["normalized_receipt_no"].fillna("").astype(str)
            if df_vr.empty:
                return

            merged = df_unified.merge(
                df_vr,
                left_on=["dutyfree_operator", "receipt_no_norm"],
                right_on=["dutyfree_company", "receipt_no_norm"],
                suffixes=("_edi", "_vr"),
                how="left",
            )

            # uuid_receipt 가 매핑된 행만 업데이트용 DF 구성
            mask_has_uuid = merged["uuid_record"].notna()
            if not mask_has_uuid.any():
                return

            df_update = merged.loc[mask_has_uuid, ["id_edi", "uuid_record"]].rename(
                columns={"id_edi": "id", "uuid_record": "uuid_receipt"}
            )

            await self.db.update_batch(
                table=models.EDI_UNIFIED,
                data_to_update=df_update,
                schemas=self.schemas,
                conflict_cols=["id"],
                partial_commit=False,
                session=session,
            )

            await session.commit()

    async def fill_uuid_passport(
        self,
        sources: list[Literal["SILLA", "LOTTE"]] = ["SILLA", "LOTTE"],
        max_rows: int | None = None,
    ) -> None:
        """
        3단계: uuid_receipt 가 채워진 EDI_UNIFIED 행들에 대해 MATCHED 를 조회,
        MATCHED.uuid_passport (확정된 여권) 가 존재하는 경우 그대로 채워 넣는다.

        - MATCHED.uuid_passport 가 NULL 인 행(후보만 있는 경우)은 여기서는 건드리지 않는다.
        """
        async with self.db.open_session(schemas=self.schemas) as session:
            # uuid_receipt 는 있으나 uuid_passport 는 아직 없는 EDI_UNIFIED 행만 대상
            stmt_unified = select(*models.EDI_UNIFIED.__table__.columns).where(
                models.EDI_UNIFIED.uuid_receipt.is_not(None),
                models.EDI_UNIFIED.uuid_passport.is_(None),
                models.EDI_UNIFIED.dutyfree_operator.in_(sources),
            )
            if max_rows is not None:
                stmt_unified = stmt_unified.limit(max_rows)

            result_unified = await session.execute(stmt_unified)
            rows_unified = result_unified.mappings().all()
            if not rows_unified:
                return

            df_unified = pd.DataFrame(rows_unified)

            # MATCHED 에서 해당 uuid_receipt 들의 최종 uuid_passport 조회
            uuid_receipts = df_unified["uuid_receipt"].dropna().unique().tolist()
            if not uuid_receipts:
                return

            stmt_matched = select(*models.MATCHED.__table__.columns).where(
                models.MATCHED.uuid_receipt.in_(uuid_receipts)
            )
            result_matched = await session.execute(stmt_matched)
            rows_matched = result_matched.mappings().all()
            if not rows_matched:
                return

            df_matched = pd.DataFrame(rows_matched)

            # uuid_receipt 기준으로 조인하여 MATCHED.uuid_passport 를 EDI_UNIFIED 에 맵핑
            merged = df_unified.merge(
                df_matched,
                left_on="uuid_receipt",
                right_on="uuid_receipt",
                suffixes=("_edi", "_m"),
                how="left",
            )

            # MATCHED 에서 확정된 uuid_passport 가 있는 행만 업데이트
            mask_has_passport = merged["uuid_passport_m"].notna()
            if not mask_has_passport.any():
                return

            df_update = merged.loc[mask_has_passport, ["id_edi", "uuid_passport_m"]].rename(
                columns={"id_edi": "id", "uuid_passport_m": "uuid_passport"}
            )

            await self.db.update_batch(
                table=models.EDI_UNIFIED,
                data_to_update=df_update,
                schemas=self.schemas,
                conflict_cols=["id"],
                partial_commit=False,
                session=session,
            )

            await session.commit()

    async def run(
        self,
        sources: list[Literal["SILLA", "LOTTE"]] = ["SILLA", "LOTTE"],
        max_rows: int | None = None,
        fill_receipt: bool = True,
        fill_passport: bool = False,
    ) -> None:
        """
        전체 EDI 매핑 파이프라인 실행 오케스트레이션.
        1) EDI_SILLA / EDI_LOTTE → EDI_UNIFIED 업서트
        2) EDI_UNIFIED.uuid_receipt 채우기 (옵션)
        3) EDI_UNIFIED.uuid_passport 채우기 (옵션)
        """
        if max_rows == 0:
            logger.info("[EDI_UNIFIED] run skipped (max_rows=0)")
            return

        t0 = time.perf_counter()
        logger.info(
            "[EDI_UNIFIED] run start | tenant_schema=%s sources=%s max_rows=%s fill_receipt=%s fill_passport=%s",
            self.tenant_schema,
            sources,
            max_rows,
            fill_receipt,
            fill_passport,
        )

        # 1) 원본 → UNIFIED 업서트
        self_start = time.perf_counter()
        await self.sync_edi_to_unified(sources=sources, max_rows=max_rows)
        self_sec_sync = round(time.perf_counter() - self_start, 3)
        logger.info("[EDI_UNIFIED] sync_edi_to_unified done | %.3fs", self_sec_sync)

        # 2) uuid_receipt 채우기
        self_sec_fill_receipt = 0.0
        if fill_receipt:
            fr_start = time.perf_counter()
            await self.fill_uuid_receipt(sources=sources, max_rows=max_rows)
            self_sec_fill_receipt = round(time.perf_counter() - fr_start, 3)
            logger.info("[EDI_UNIFIED] fill_uuid_receipt done | %.3fs", self_sec_fill_receipt)

        # 3) uuid_passport 채우기
        self_sec_fill_passport = 0.0
        if fill_passport:
            fp_start = time.perf_counter()
            await self.fill_uuid_passport(sources=sources, max_rows=max_rows)
            self_sec_fill_passport = round(time.perf_counter() - fp_start, 3)
            logger.info("[EDI_UNIFIED] fill_uuid_passport done | %.3fs", self_sec_fill_passport)

        total_sec = round(time.perf_counter() - t0, 3)
        logger.info(
            "[EDI_UNIFIED] run done | total=%.3fs sync=%.3fs fill_receipt=%.3fs fill_passport=%.3fs",
            total_sec,
            self_sec_sync,
            self_sec_fill_receipt,
            self_sec_fill_passport,
        )


