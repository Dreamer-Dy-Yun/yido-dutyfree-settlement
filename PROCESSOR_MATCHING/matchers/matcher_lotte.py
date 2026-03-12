###########################################
# Module name : matcher_lotte.py
# Module functions : PRM_Lotte
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.12
# Updated at : 2026.03.12
# Supported by : -
# Note : 
############################################

from PROCESSOR_MATCHING.matcher import PassportReceiptMatcher
from sqlalchemy import select, Executable, Result, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Self
from DATABASE import models
import pandas as pd
import uuid
from collections import defaultdict
from pathlib import Path
from CUSTOMIZED.cust_logger import logger
from dataclasses import dataclass


@dataclass
class MatchResult:
    with_results: dict[str, pd.DataFrame]
    without_result: pd.DataFrame


class PRM_Lotte(PassportReceiptMatcher):


    async def _get_verified_passport_datum(self, country_code: str, passport_no: str, name: str, uuid_batch: str) -> Self:
        # 안씀
        stmt : Executable = select(models.VerifiedPassport)
        stmt = stmt.where(models.VerifiedPassport.country_code == country_code)
        stmt = stmt.where(models.VerifiedPassport.passport_no == passport_no)
        stmt = stmt.where(models.VerifiedPassport.name == name)
        stmt = stmt.where(models.VerifiedPassport.uuid_batch == uuid_batch)
        stmt = stmt.limit(1)
        result : Result[models.VerifiedPassport] = await self.db.execute_query(stmt, schemas=self.schemas)
        verified_passport: models.VerifiedPassport | None = result.scalar_one_or_none()
        return verified_passport


    def _m_purchaser_for_df(self, text:str) -> str:
        """
        첫글자와 마지막자 외에는 *로 마스킹. 
        """
        first_char: str = text[0]
        last_char: str = text[-1]
        if first_char == "*":
            first_char = ""
        if last_char == "*":
            last_char = ""
        return first_char + ".*" + last_char


    def _m_passport_number_for_df(self, text:str) -> str:
        first_4chars: str = text[0:4]
        return first_4chars + ".*"


    def _m_purchaser_for_sql(self, text:str) -> str:
        """
        첫글자와 마지막자 외에는 *로 마스킹. 
        """
        first_char: str = text[0]
        last_char: str = text[-1]
        if first_char == "*":
            first_char = ""
        if last_char == "*":
            last_char = ""
        return first_char + "%" + last_char


    def _m_passport_number_for_sql(self, text:str) -> str:
        first_4chars: str = text[0:4]
        return first_4chars + "%"


    async def _get_passport_data(self, session: AsyncSession | None, country_code: str, passport_no: str, name: str, uuid_batch: str | None = None, max_rows: int | None = None) -> pd.DataFrame:
        """
        단일 조회.
        와일드 카드 있으면 모드 Like 조회. 옵티마이저 믿고 감.
        """
        stmt : Executable = select(models.VerifiedPassport)
        stmt = stmt.where(models.VerifiedPassport.country_code.like(country_code))
        stmt = stmt.where(models.VerifiedPassport.passport_no.like(passport_no))
        stmt = stmt.where(models.VerifiedPassport.name.like(name))
        if uuid_batch:
            stmt = stmt.where(models.VerifiedPassport.uuid_batch.like(uuid_batch))
        if max_rows:
            stmt = stmt.limit(max_rows)

        if session:
            result : Result[models.VerifiedPassport] = await session.execute(stmt)
        else:
            result : Result[models.VerifiedPassport] = await self.db.execute_query(stmt, schemas=self.schemas)

        return pd.DataFrame(result.mappings().all()) if result.mappings() else pd.DataFrame()


    async def _get_passport_data_with_batch_uuid(self, uuid_batch: str) -> pd.DataFrame:
        """
        조회(연결) 비용을 줄이기 위해 우선 해당 배치 UUID 에 해당하는 모든 여권 데이터를 조회.
        """
        stmt : Executable = select(models.VerifiedPassport)
        stmt = stmt.where(models.VerifiedPassport.uuid_batch == uuid_batch)
        result : Result[models.VerifiedPassport] = await self.db.execute_query(stmt, schemas=self.schemas)
        return pd.DataFrame(result.mappings().all()) if result.mappings() else pd.DataFrame()


    def _match(self, df_receipt: pd.DataFrame, df_passport: pd.DataFrame) -> MatchResult:
        """
        조회 비용을 줄이기 위해 우선 해당 배치 UUID 에 해당하는 모든 여권 데이터를 조회.
        반환값 : tuple[dict(str, pd.DataFrame), pd.DataFrame]
            dict(str, pd.DataFrame) : 매칭 성공. key: 영수증 uuid_record, value: 영수증 데이터 + 순위
            pd.DataFrame : 매칭 실패. 영수증 데이터
        """
        dict_with_results: dict(str, pd.DataFrame) = {}
        list_without_result: list = []
        dict_temp: dict[str, str] = {}
        df_temp: pd.DataFrame = pd.DataFrame()
        condition: pd.Series = pd.Series(False)
        for _, row in df_receipt.iterrows():
            country_code: str = str(row["country_code"])
            passport_no: str = str(row["passport_no"])
            name: str = str(row["name"])
            uuid_batch: str = str(row["uuid_batch"])
            uuid_record: str = str(row["uuid_record"])

            condition = df_passport["country_code"] == country_code
            condition = condition & (df_passport["passport_no"].str.match(self._m_passport_number_for_df(passport_no)))
            condition = condition & (df_passport["name"].str.match(self._m_purchaser_for_df(name)))

            df_temp = df_passport[condition]

            dict_temp = {}
            dict_temp["country_code"] = country_code
            dict_temp["passport_no"] = passport_no
            dict_temp["name"] = name
            dict_temp["uuid_batch"] = uuid_batch
            dict_temp["uuid_record"] = uuid_record 

            if df_temp.empty:
                """단일행 데이터 프레임 key: 영수증 uuid_record, value: 영수증 데이터"""
                list_without_result.append(row)
            else:
                """다중행 데이터 프레임 key: 영수증 uuid_record, value: 여권 데이터 + 순위"""
                dict_with_results[uuid_record] = self._add_rank(name, df_temp)

        return MatchResult(with_results=dict_with_results, without_result=pd.DataFrame(list_without_result))



    async def _fallback_match(self) -> pd.DataFrame:
        df: pd.DataFrame = pd.concat(self._dfs_without_result)
        self._dfs_without_result = []

        async with self.db.open_session(schemas=self.schemas) as session:
            for _, row in df.iterrows():
                country_code: str = str(row["country_code"])
                passport_no: str = self._m_passport_number_for_sql(str(row["passport_no"]))
                name: str = self._m_purchaser_for_sql(str(row["name"]))
                df_passport = await self._get_passport_data(session, country_code, passport_no, name)
                match_result: MatchResult = self._match(row, df_passport) # 2차 매칭
                self._dict_results.update(match_result.with_results)
                self._dfs_without_result.append(match_result.without_result)
        

    async def run(self, locked_by: str, try_fallback: bool = False) -> Self:

        try:
            df_verified_receipts: pd.DataFrame = await self.lock_and_fetch_verified_receipt("lock", locked_by=locked_by)
            if df_verified_receipts.empty:
                return self

            unique_uuid_records: list[str] = df_verified_receipts["uuid_record"].dropna().unique().tolist()
            df_passport: pd.DataFrame = pd.DataFrame()
            dfs_without_result: list[pd.DataFrame] = []
            df_receipt: pd.DataFrame = pd.DataFrame()

            for uuid_record in unique_uuid_records:
                df_passport = await self._get_passport_data_with_batch_uuid(uuid_record)
                df_receipt = df_verified_receipts[df_verified_receipts["uuid_record"] == uuid_record]
                if df_passport.empty:
                    dfs_without_result.append(df_receipt)
                    continue
                match_result: MatchResult = self._match(df_receipt, df_passport) # 1차 매칭
                self._dict_results.update(match_result.with_results)
                self._dfs_without_result.append(match_result.without_result)

            if try_fallback:
                await self._fallback_match()

            for df in self._dfs_without_result:
                uuid_record = df["uuid_record"][0]
                self._dict_results.update({uuid_record: pd.DataFrame()}) # 최종 매칭 실패 : 빈 데이터프레임

            await self.mark_processed_verified_receipt(locked_by=locked_by, is_processed=True)
        except Exception as e:
            logger.error(f"[PRM_Lotte] Error: {e}")
            raise
        finally:
            await self.lock_and_fetch_verified_receipt("unlock", locked_by=locked_by)

        return self