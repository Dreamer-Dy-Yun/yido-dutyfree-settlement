###########################################
# Module name : yido_parser.py
# Module functions : YidoParser
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.06
# Updated at : 2026.02.09
# Supported by : -
# Note : 
#        ※ 목적 : LLM OCR 결과를 파싱하여 DataFrame으로 반환
#        2026.02.06 : 파일 생성
############################################


import pandas as pd
import json
from typing import Any, Optional, Self
import time
import uuid
from LLM.dto import LLMResponse, LLMUsage
from datetime import datetime, timezone
from pathlib import Path
from CUSTOMIZED.cust_hasher import Hasher

class YidoParser:
    def __init__(self):
        """
        YidoParser 초기화

        Args:
            llm_response: LLM 응답 객체
            path_image: 이미지 경로
        """
        self.request_id: str = str(uuid.uuid4())  # 비동기 환경에서 고유 식별자
        self.model: str = ""
        self.start_time: float = 0.0
        self._df_receipt: pd.DataFrame = pd.DataFrame()
        self._df_passport: pd.DataFrame = pd.DataFrame()
        self._df_usage: pd.DataFrame = pd.DataFrame()
        self._uuid_batch: str = ""
        self.hashed_image: str = ""


    def add_uuid_batch(self, uuid_batch: str) -> Self:
        self._uuid_batch = uuid_batch
        return self

    def add_hashed_image(self, path_image: Path) -> None:
        self.hashed_image = Hasher().hash(path_image, ignore_errors=True).value.hex()
        
        if not self.df_receipt.empty: 
            self.df_receipt["hash_img"] = self.hashed_image

        if not self.df_passport.empty:
            self.df_passport["hash_img"] = self.hashed_image


    def _parse_usage(self, usage: Optional[LLMUsage], start_time: float) -> pd.DataFrame:
        if usage is None:
            self._df_usage = pd.DataFrame()
            return

        return pd.DataFrame([{
            "request_id": self.request_id, 
            "start_time": datetime.fromtimestamp(start_time, tz=timezone.utc),
            "model": self.model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "elapsed_time": time.time() - start_time,
        }])

    def _parse_receipts(self, receipts: list[dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame([self._parse_receipt(receipt) for receipt in receipts])

    def _parse_passports(self, passports: list[dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame([self._parse_passport(passport) for passport in passports])

    def _parse_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        dict_temp: dict[str, Any] = {
            "dutyfree_company": (receipt.get("dutyfree_company") or "").strip() or None,
            "group_no": (receipt.get("group_no") or "").strip() or None,
            "receipt_no": (receipt.get("receipt_no") or "").strip() or None,
            "country_code": (receipt.get("country_code") or "").strip() or None,
            "passport_no": (receipt.get("passport_no") or "").strip() or None,
            "purchaser": (receipt.get("purchaser") or "").strip() or None,
            "coordinate": receipt.get("coordinate"),  # JSON 형식
        }
        return {
            **dict_temp,
            "hash_ocr_result": Hasher().hash(dict_temp).value.hex(),
            "uuid_batch": self._uuid_batch,
            "uuid_record": str(uuid.uuid4()).hex(),
        }

    def _parse_passport(self, passport: dict[str, Any]) -> dict[str, Any]:
        dict_temp: dict[str, Any] = {
            "country_code": (passport.get("country_code") or "").strip() or None,
            "passport_no": (passport.get("passport_no") or "").strip() or None,
            "name": (passport.get("name") or "").strip() or None,
            "gender": (passport.get("gender") or "").strip() or None,
            "place_of_birth": (passport.get("place_of_birth") or "").strip() or None,
            "date_of_birth": (passport.get("date_of_birth") or "").strip() or None,
            "place_of_issue": (passport.get("place_of_issue") or "").strip() or None,
            "date_of_issue": (passport.get("date_of_issue") or "").strip() or None,
            "date_of_expiry": (passport.get("date_of_expiry") or "").strip() or None,
            "authority": (passport.get("authority") or "").strip() or None,
            "coordinate": passport.get("coordinate"),  # JSON 형식
        }
        return {
            **dict_temp,
            "hash_ocr_result": Hasher().hash(dict_temp).value.hex(),
            "uuid_batch": self._uuid_batch,
            "uuid_record": str(uuid.uuid4()).hex(),
        }


    def _parse_json(self, content: str) -> dict[str, Any]:
        """JSON 문자열을 파싱 (이미 마크다운 코드 블록은 ChatGPT에서 제거됨)"""
        if not content or not content.strip():
            raise ValueError("Response content is empty")
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}\nResponse content: {content[:500]}")

    def run(self, llm_response: LLMResponse) -> None:
        """응답 내용을 파싱하여 DataFrame 생성"""
        
        receipts = llm_response.content.get("receipts", {}).get("list", [])
        passports = llm_response.content.get("passports", {}).get("list", [])
        usage = llm_response.usage if llm_response.usage else None

        self.model = llm_response.model
        self.start_time = llm_response.start_time
        
        self._df_receipt = self._parse_receipts(receipts)
        self._df_passport = self._parse_passports(passports)
        self._df_usage = self._parse_usage(usage, self.start_time)

    @property
    def df_receipt(self) -> pd.DataFrame:
        return self._df_receipt
    
    @property
    def df_passport(self) -> pd.DataFrame:
        return self._df_passport

    @property
    def df_usage(self) -> pd.DataFrame:
        return self._df_usage