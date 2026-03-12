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
from typing import Self
import pandas as pd
from CUSTOMIZED.cust_logger import logger
from PROCESSOR_MATCHING.matcher import MatchResult


class PRM_Silla(PassportReceiptMatcher):


    def _add_rank(self, name: str, df_passport: pd.DataFrame) -> pd.DataFrame:
        for index, row in df_passport.iterrows():
            df_passport.at[index, "rank"] = abs(len(row["name"]) - len(name))
        return df_passport    


    def _match(self, df_receipt: pd.DataFrame, df_passport: pd.DataFrame) -> MatchResult:
        """
        신라는 완전 매칭이므로 사실상 후보 없음.
        국가코드, 여권번호만 매칭.


        조회 비용을 줄이기 위해 우선 해당 배치 UUID 에 해당하는 모든 여권 데이터를 조회.
        반환값 : tuple[dict(str, pd.DataFrame), pd.DataFrame]
            dict(str, pd.DataFrame) : 매칭 성공. key: 영수증 uuid_record, value: 영수증 데이터 + 순위
            pd.DataFrame : 매칭 실패. 영수증 데이터
        """
        dict_with_results: dict[str, pd.DataFrame] = {}
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
            condition = condition & (df_passport["passport_no"] == passport_no)
            # condition = condition & (df_passport["name"] == name) # 굳이 이름 매칭 불필요

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


    async def _fallback_match(self) -> Self:
        """
        신라는 이름 매칭 하지 않음. 국가코드, 여권번호만 매칭.
        """
        df: pd.DataFrame = pd.concat(self._dfs_without_result)
        self._dfs_without_result = []

        async with self.db.open_session(schemas=self.schemas) as session:
            for _, row in df.iterrows():
                country_code: str = str(row["country_code"])
                passport_no: str = str(row["passport_no"])
                # name: str = str(row["name"])
                df_passport = await self._get_passport_data(session, country_code, passport_no)
                match_result: MatchResult = self._match(pd.DataFrame([row]), df_passport)
                self._dict_results.update(match_result.with_results)
                self._dfs_without_result.append(match_result.without_result)
        return self


    async def run(self, locked_by: str, try_fallback: bool = False) -> Self:

        try:
            df_verified_receipts: pd.DataFrame = await self.lock_and_fetch_verified_receipt("lock", locked_by=locked_by)
            if df_verified_receipts.empty:
                return self

            unique_uuid_batches: list[str] = df_verified_receipts["uuid_batch"].dropna().unique().tolist()
            uuid_record: str = ""
            df_passport: pd.DataFrame = pd.DataFrame()
            dfs_without_result: list[pd.DataFrame] = []
            df_receipt: pd.DataFrame = pd.DataFrame()

            for uuid_batch in unique_uuid_batches:
                df_passport = await self._get_passport_data_with_batch_uuid(uuid_batch)
                df_receipt = df_verified_receipts[df_verified_receipts["uuid_batch"] == uuid_batch]
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

            await self._flush_matched_results()
            await self.unlock_processed_receipts(locked_by)
        except Exception as e:
            logger.error(f"[PRM_Lotte] Error: {e}")
            raise
        finally:
            await self.lock_and_fetch_verified_receipt("unlock", locked_by=locked_by)

        return self