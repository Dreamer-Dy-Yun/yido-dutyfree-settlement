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
from sqlalchemy import Executable, update
from sqlalchemy.engine import Result
from typing import Self
from DATABASE.dbms.db_manager import DBManager
from DATABASE import models
import pandas as pd
from typing import Literal
from matchers.matcher_silla import PRM_Silla
from matchers.matcher_lotte import PRM_Lotte


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


    async def mark_processed_verified_receipt(self, locked_by: str, is_processed: bool = True) -> Self:
        stmt : Executable = update(models.VerifiedReceipt)
        stmt = stmt.values(locked_by=locked_by)
        stmt = stmt.where(models.VerifiedReceipt.locked_by.is_(None))
        stmt = stmt.where(models.VerifiedReceipt.is_processed.is_(is_processed))
        await self.db.execute_query(stmt, schemas=self.schemas)
        return self


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
            stmt = stmt.where(models.VerifiedReceipt.locked_by.is_(locked_by))

        stmt = stmt.where(models.VerifiedReceipt.is_verified.is_(True))

        if max_rows:
            stmt = stmt.limit(max_rows)

        stmt = stmt.returning(models.VerifiedReceipt)

        result : Result[models.VerifiedReceipt] = await self.db.execute_query(stmt, schemas=self.schemas)
        df_verified_receipts: pd.DataFrame = pd.DataFrame(result.mappings().all()) if result.mappings() else pd.DataFrame()
        return df_verified_receipts


    @abstractmethod
    async def _fallback_match(self) -> pd.DataFrame:
        pass


    @abstractmethod
    async def run(self, locked_by: str, try_fallback: bool = False) -> Self:
        pass


dict_matcher: dict[str, type[PassportReceiptMatcher]] = {
    "silla": PRM_Silla,
    "lotte": PRM_Lotte,
}   