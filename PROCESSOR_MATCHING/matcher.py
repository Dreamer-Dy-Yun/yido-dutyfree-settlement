###########################################
# Module name : passport_receipt_matcher.py
# Module functions : PassportReceiptMatcher
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.11
# Updated at : 2026.03.11
# Supported by : -
# Note : 
############################################

from abc import ABC, abstractmethod
from sqlalchemy import Executable, update, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Self
from DATABASE.dbms.db_manager import DBManager
from DATABASE import models
import pandas as pd
from typing import Literal
from dataclasses import dataclass


@dataclass
class MatchResult:
    with_results: dict[str, pd.DataFrame]
    without_result: pd.DataFrame


class PassportReceiptMatcher(ABC):
    def __init__(self, db : DBManager, public_schema: str, tenant_schema: str):
        self.db : DBManager = db
        self.public_schema : str | None = public_schema
        self.tenant_schema : str | None = tenant_schema
        self.schemas : list[str] = [self.tenant_schema, self.public_schema]
        self._dict_with_results: dict(str, pd.DataFrame) = {}
        self._df_without_result: pd.DataFrame = pd.DataFrame()
        self._dict_results: dict(str, pd.DataFrame) = {}
        self._dfs_without_result: list[pd.DataFrame] = []


    async def unlock_processed_receipts(self, locked_by: str) -> Self:
        stmt : Executable = update(models.VerifiedReceipt)
        stmt = stmt.values(locked_by=None, is_processed=True)
        stmt = stmt.where(models.VerifiedReceipt.locked_by == locked_by)
        stmt = stmt.where(models.VerifiedReceipt.is_processed.is_(False))
        await self.db.execute_query(stmt, schemas=self.schemas)
        return self


    async def _get_passport_data_with_batch_uuid(self, uuid_batch: str) -> pd.DataFrame:
        """
        조회(연결) 비용을 줄이기 위해 우선 해당 배치 UUID 에 해당하는 모든 여권 데이터를 조회.
        """
        stmt : Executable = select(models.VerifiedPassport.__table__.columns)
        stmt = stmt.where(models.VerifiedPassport.uuid_batch == uuid_batch)
        result : Result[models.VerifiedPassport] = await self.db.execute_query(stmt, schemas=self.schemas)
        return pd.DataFrame(result.mappings().all()) if result.mappings() else pd.DataFrame()


    def to_json(self) -> dict[str, list[dict]]:
        """
        JSON 형식으로 변환하여 반환.
        {
            <uuid_record_1>: [
                <data_1>,
                <data_2>,
                ...
            ]
        }
        """
        dict_result: dict[str, list[dict]] = {}
        for uuid_record, df in self._dict_results.items():
            dict_result[uuid_record] = df.to_dict(orient="records")
        return dict_result


    async def lock_and_fetch_verified_receipt(
        self, 
        lock_or_unlock: Literal["lock", "unlock"], 
        locked_by: str | None = None, 
        max_rows: int | None = None
        ) -> pd.DataFrame:

        stmt : Executable = update(models.VerifiedReceipt)

        if lock_or_unlock.lower() == "lock":
            stmt = stmt.values(locked_by=locked_by)
            stmt = stmt.where(models.VerifiedReceipt.locked_by.is_(None))
            stmt = stmt.where(models.VerifiedReceipt.is_processed.is_(False))
        else:
            stmt = stmt.values(locked_by=None)
            stmt = stmt.where(models.VerifiedReceipt.locked_by == locked_by)

        stmt = stmt.where(models.VerifiedReceipt.is_verified.is_(True))

        if max_rows:
            stmt = stmt.limit(max_rows)

        stmt = stmt.returning(*models.VerifiedReceipt.__table__.columns)

        result : Result[models.VerifiedReceipt] = await self.db.execute_query(stmt, schemas=self.schemas)
        df_verified_receipts: pd.DataFrame = pd.DataFrame(result.mappings().all()) if result.mappings() else pd.DataFrame()
        return df_verified_receipts


    async def _flush_matched_results(self) -> None:
        """
        self._dict_results (uuid_receipt -> candidates DataFrame)를 MATCHED 테이블에 반영.
        - uuid_receipt: 영수증 uuid_record
        - uuid_passport: rank 기준으로 선택된 최종 여권 uuid_record (없으면 NULL)
        - possible_passports: 후보 여권 uuid_record 리스트
        - ranks: 후보 rank 리스트 (possible_passports 와 인덱스 일치)
        """
        if not self._dict_results:
            return

        rows: list[dict] = []
        for uuid_receipt, df_candidates in self._dict_results.items():
            if df_candidates is None or df_candidates.empty:
                rows.append(
                    {
                        "uuid_receipt": uuid_receipt,
                        "uuid_passport": None,
                        "possible_passports": [],
                        "ranks": [],
                    }
                )
                continue

            df_sorted = df_candidates
            if "rank" in df_candidates.columns:
                df_sorted = df_candidates.sort_values("rank")

            uuid_passport_list = (
                df_sorted["uuid_record"].astype(str).tolist()
                if "uuid_record" in df_sorted.columns
                else []
            )
            if "rank" in df_sorted.columns:
                rank_list = df_sorted["rank"].tolist()
            else:
                # rank 컬럼이 없으면 1,2,3,... 순서로 부여
                rank_list = list(range(1, len(uuid_passport_list) + 1))

            best_uuid_passport = uuid_passport_list[0] if uuid_passport_list else None

            rows.append(
                {
                    "uuid_receipt": uuid_receipt,
                    "uuid_passport": best_uuid_passport,
                    "possible_passports": uuid_passport_list,
                    "ranks": rank_list,
                }
            )

        df_matched = pd.DataFrame(rows)
        if not df_matched.empty:
            # pandas 가 None/빈값을 NaN(float)으로 올리면 asyncpg 가 문자열 컬럼에 대해
            # "expected str, got float" 를 발생시키므로 최소한 uuid_passport 는 NaN -> None 으로 정규화한다.
            if "uuid_passport" in df_matched.columns:
                df_matched["uuid_passport"] = df_matched["uuid_passport"].where(
                    ~df_matched["uuid_passport"].isna(), None
                )
            await self.db.upsert_batch(
                table=models.MATCHED,
                data=df_matched,
                schemas=self.schemas,
            )


    async def _get_passport_data(
        self, 
        session: AsyncSession | None, 
        country_code: str|None = None, 
        passport_no: str|None = None, 
        name: str|None = None, 
        uuid_batch: str | None = None, 
        max_rows: int | None = None
        ) -> pd.DataFrame:
        """
        단일 조회.
        와일드 카드 있으면 모드 Like 조회. 옵티마이저 믿고 감.
        """

        stmt : Executable = select(*models.VerifiedPassport.__table__.columns)
        if country_code:
            stmt = stmt.where(models.VerifiedPassport.country_code.like(country_code))
        if passport_no:
            stmt = stmt.where(models.VerifiedPassport.passport_no.like(passport_no))
        if name:
            stmt = stmt.where(models.VerifiedPassport.name.like(name))
        if uuid_batch:
            stmt = stmt.where(models.VerifiedPassport.uuid_batch.like(uuid_batch))
        if max_rows:
            stmt = stmt.limit(max_rows)

        if session:
            result: Result = await session.execute(stmt)
        else:
            result: Result = await self.db.execute_query(stmt, schemas=self.schemas)

        rows = result.mappings().all()
        return pd.DataFrame(rows) if rows else pd.DataFrame()


    @abstractmethod
    def _match(self, df_receipt: pd.DataFrame, df_passport: pd.DataFrame) -> MatchResult:
        pass


    @abstractmethod
    async def _fallback_match(self) -> pd.DataFrame:
        pass


    @abstractmethod
    async def run(self, locked_by: str, try_fallback: bool = False) -> Self:
        # TODO : _match와 _fallback_match을 좀 더 정교하게 만든 후, 공통화 예정
        pass