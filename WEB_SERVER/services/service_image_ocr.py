###########################################

# Module name : service_image_ocr.py
# Module functions : run_image_ocr_background, ask_llm_ocr, upsert_ocr_receipt, upsert_ocr_passport, write_llm_usage, set_image_processing, set_image_processed
# Written by : Cursor AI / Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.05
# Updated at : 2026.03.05
# Supported by : -
# Note : 일부 리팩토링. 추후 전반적인 리팩토링 필요
############################################
import os
import asyncio
from pathlib import Path

import pandas as pd
from sqlalchemy import select, insert, Select, Insert, update, Update
from sqlalchemy.engine import Result

from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.models.public_model import LLM_API_Key, Prompt
from WEB_SERVER.routers.settings import get_db_manager
from LLM.ChatGPT.api import ChatGPT
from LLM.dto import LLMRequest, LLMResponse
from LLM_RESULT_PARSER.yido_parser import YidoParser
from DATABASE.dbms.db_manager import DBManager
from typing import Self
from LLM.llm import LLM


async def run_image_ocr_background(tenant_schema: str, public_schema: str) -> None:
    db = get_db_manager()
    llm_api_key = await resolve_active_llm_api_key(db)
    llm = ChatGPT(api_key=llm_api_key.api_key, model=llm_api_key.llm_model)
    prompt_system, prompt_user = await resolve_active_ocr_prompts(db)
    image_ocr_service = ImageOcrService(db, tenant_schema, public_schema)
    image_ocr_service.set_llm(llm, prompt_system, prompt_user)
    image_ocr_service.get_unprocessed_images()
    image_ocr_service.run()


async def resolve_active_llm_api_key(db: DBManager, llm_provider: str = "OPEN AI", llm_model: str = "gpt-4o", public_schema: str = "public") -> LLM_API_Key:
    stmt : Select = select(LLM_API_Key)
    stmt = stmt.where(LLM_API_Key.is_active == True)
    stmt = stmt.where(LLM_API_Key.llm_provider == llm_provider)
    stmt = stmt.where(LLM_API_Key.llm_model == llm_model)
    stmt = stmt.order_by(LLM_API_Key.db_updated_at.desc())
    stmt = stmt.limit(1)
    result = await db.execute_query(stmt, schemas=[public_schema])
    row = result.scalar_one_or_none()
    if row is None:
        raise RuntimeError(f"[OCR] active llm_api_key not found: provider={llm_provider}, model={llm_model}")
    return row


async def resolve_active_ocr_prompts(db) -> tuple[str, str | None, list[str]]:
    stmt_system = (
        select(Prompt)
        .where(
            Prompt.is_active == True,
            Prompt.purpose == OCR_PURPOSE,
            Prompt.type == "SYSTEM",
        )
        .order_by(Prompt.db_updated_at.desc())
        .limit(1)
    )
    stmt_user = (
        select(Prompt)
        .where(
            Prompt.is_active == True,
            Prompt.purpose == OCR_PURPOSE,
            Prompt.type == "USER",
        )
        .order_by(Prompt.db_updated_at.desc())
        .limit(1)
    )
    result_system = await db.execute_query(stmt_system, schemas=["public"])
    result_user = await db.execute_query(stmt_user, schemas=["public"])
    prompt_system = result_system.scalar_one_or_none()
    prompt_user = result_user.scalar_one_or_none()

    if prompt_system is None and prompt_user is None:
        raise RuntimeError("[OCR] active OCR prompts not found for both SYSTEM and USER")

    system_text = prompt_system.prompt if prompt_system else ""
    user_text = prompt_user.prompt if prompt_user else None
    return system_text, user_text


class ImageOcrService:
    def __init__(self, db: DBManager, tenant_schema: str, public_schema: str = "public"):
        self.db = db
        self.unprocessed_images : pd.DataFrame | None = None
        self.llm : LLM | None = None
        self.prompt_system : str | None = None
        self.prompt_user : str | None = None
        self.public_schema : str | None = public_schema
        self.tenant_schema : str | None = tenant_schema
        self.schemas : list[str] = [self.tenant_schema, self.public_schema]
        self.num_of_images : int = 0
        self.num_of_images_processed : int = 0
        self.num_of_images_failed : int = 0


    def set_llm(self, llm: LLM, prompt_system: str | None = None, prompt_user: str | None = None) -> Self:
        self.llm = llm
        self.prompt_system = prompt_system
        self.prompt_user = prompt_user
        return self


    async def get_unprocessed_images(self) -> Self:
        stmt : Update = update(models.Image)
        stmt = stmt.where(models.Image.is_processing.is_(False))
        stmt = stmt.where(models.Image.is_processed.is_(False))
        stmt = stmt.values(is_processing=True)
        stmt = stmt.returning(models.Image.hash)
        
        result: Result[models.Image | None] = await self.db.execute_query(stmt, schemas=[self.tenant_schema])
        df: pd.DataFrame = result.mappings().all()
        self.unprocessed_images = df
        return self


    async def set_image_processing(self, target_hashes: list[str], is_processing: bool = True) -> None:
        records : list[dict] = []
        df : pd.DataFrame = pd.DataFrame()
        # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
        for hash in target_hashes:
            record : dict = {"hash": hash, "is_processing": is_processing}
            records.append(record)
        df = pd.DataFrame(records)
        await self.db.update_dataframe(models.Image, df, schemas=self.schemas, conflict_cols=["hash"])


    async def set_image_processed(self, target_hashes: list[str], is_processed: bool = True) -> None:
        records : list[dict] = []
        df : pd.DataFrame = pd.DataFrame()
        # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
        for hash in target_hashes:
            record : dict = {"hash": hash, "is_processed": is_processed}
            records.append(record)
        df = pd.DataFrame(records)
        await self.db.update_dataframe(models.Image, df, schemas=self.schemas, conflict_cols=["hash"])


    async def run(self, semaphore: int = 10, col_name_hash: str = "hash") -> Self:

        if not self.prompt_system and not self.prompt_user:
            raise ValueError("prompt_system or prompt_user are required")
        if not self.llm:
            raise ValueError("llm is required")

        df_images : pd.DataFrame = self.unprocessed_images

        sem = asyncio.Semaphore(semaphore)

        async def _worker(hash_img: str) -> LLMResponse:
            user_prompt = f"{self.prompt_user}\n" if self.prompt_user else ""
            user_prompt += f"{col_name_hash} : {hash_img}"

            async with sem:
                return await self.llm.ask(LLMRequest(self.prompt_system, user_prompt))

        task_map: dict[asyncio.Task[LLMResponse], str] = {}
        for hash_img in df_images[col_name_hash]:
            task = asyncio.create_task(_worker(hash_img))
            task_map[task] = str(hash_img)

        self.num_of_images = len(df_images)
        self.num_of_images_processed = 0
        self.num_of_images_failed = 0

        for task_done in asyncio.as_completed(task_map.keys()):
            hash_img: str = task_map[task_done]
            try:
                llm_response = await task_done
                parser = YidoParser(llm_response)
                
                await self.upsert_ocr_receipt(parser.df_receipt)
                await self.upsert_ocr_passport(parser.df_passport)
                hash_prompts = [p for p in [self.prompt_system, self.prompt_user] if p is not None]
                await self.insert_llm_usage(llm_response, hash_img, hash_prompts, self.llm.model)
                self.num_of_images_processed += 1
                await self.set_image_processed([hash_img], True)
            except Exception as e:
                self.num_of_images_failed += 1
                logger.exception(f"[OCR] failed hash={hash_img} reason={e}")
            finally:
                await self.set_image_processing([hash_img], False)

        return self


    async def upsert_ocr_receipt(self, df_receipt: pd.DataFrame) -> None:
        df_receipt = df_receipt[df_receipt["coordinate"].notna()]
        if not df_receipt.empty:
            await self.db.batch_upsert_dataframe(models.OcrReceipt, df_receipt, schemas=self.schemas)


    async def upsert_ocr_passport(self, df_passport: pd.DataFrame) -> None:
        df_passport = df_passport[df_passport["coordinate"].notna()]
        if not df_passport.empty:
            await self.db.batch_upsert_dataframe(models.OcrPassport, df_passport, schemas=self.schemas)


    async def write_ocr_receipt(self, df_receipt: pd.DataFrame) -> None:
        await self.db.batch_upsert_dataframe(models.OcrReceipt, df_receipt, schemas=self.schemas)


    async def insert_llm_usage(self, llm_response: LLMResponse, hash_img: str, hash_prompts: list[str], llm_model: str) -> None:
        usage = llm_response.usage if llm_response else None
        usage_row : dict = {}
        usage_row["llm_model"] = self.llm.model
        usage_row["hash_prompts"] = hash_prompts
        usage_row["ocr_name"] = self.llm.name
        usage_row["hash_img"] = hash_img
        usage_row["token_input"] = usage.prompt_tokens if usage else None
        usage_row["token_output"] = usage.completion_tokens if usage else None
        usage_row["token_total"] = usage.total_tokens if usage else None
        stmt : Insert = insert(models.LlmUsage).values(**usage_row)
        await self.db.execute_query(stmt, schemas=self.schemas)


