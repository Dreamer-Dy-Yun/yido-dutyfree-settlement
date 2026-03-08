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
import mimetypes
from pathlib import Path

import pandas as pd
from sqlalchemy import select, insert, Select, Insert, update, Update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.models.public_model import LLM_API_Key, Prompt, Tenant as PublicTenant
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

    stmt_tenant = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    tenant_result = await db.execute_query(stmt_tenant, schemas=[public_schema])
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise RuntimeError(f"[OCR] tenant not found for schema={tenant_schema}")

    root_dir = Path(os.getenv("ROOT_DIR", "D:/"))
    tenant_root = Path(tenant.dir_base)
    if not tenant_root.is_absolute():
        tenant_root = root_dir / tenant_root

    image_ocr_service = ImageOcrService(db, tenant_schema, public_schema, dir_base=tenant_root)
    image_ocr_service.set_llm(llm, prompt_system, prompt_user)
    await image_ocr_service.get_unprocessed_images()
    await image_ocr_service.run()


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


async def resolve_active_ocr_prompts(db: DBManager, purpose: str = "OCR") -> tuple[str, str | None]:
    stmt_system = (
        select(Prompt)
        .where(
            Prompt.is_active == True,
            Prompt.purpose == purpose,
            Prompt.type == "SYSTEM",
        )
        .order_by(Prompt.db_updated_at.desc())
        .limit(1)
    )
    stmt_user = (
        select(Prompt)
        .where(
            Prompt.is_active == True,
            Prompt.purpose == purpose,
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
    def __init__(
        self,
        db: DBManager,
        tenant_schema: str,
        public_schema: str = "public",
        dir_base: Path = Path("."),
    ):
        self.db = db
        self.unprocessed_images : pd.DataFrame | None = None
        self.llm : LLM | None = None
        self.prompt_system : str | None = None
        self.prompt_user : str | None = None
        self.public_schema : str | None = public_schema
        self.tenant_schema : str | None = tenant_schema
        self.dir_base: Path = dir_base
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
        stmt = stmt.returning(models.Image.hash, models.Image.path)
        
        result: Result[models.Image | None] = await self.db.execute_query(stmt, schemas=[self.tenant_schema])
        rows = result.mappings().all()
        self.unprocessed_images = pd.DataFrame(rows)
        return self


    async def set_image_processing(
        self,
        target_hashes: list[str],
        is_processing: bool = True,
        session: AsyncSession | None = None,
    ) -> None:
        records : list[dict] = []
        df : pd.DataFrame = pd.DataFrame()
        # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
        for hash in target_hashes:
            record : dict = {"hash": hash, "is_processing": is_processing}
            records.append(record)
        df = pd.DataFrame(records)
        await self.db.update_batch(
            table=models.Image,
            data_to_update=df,
            schemas=self.schemas,
            conflict_cols=["hash"],
            session=session,
        )


    async def set_image_processed(
        self,
        target_hashes: list[str],
        is_processed: bool = True,
        session: AsyncSession | None = None,
    ) -> None:
        records : list[dict] = []
        df : pd.DataFrame = pd.DataFrame()
        # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
        for hash in target_hashes:
            record : dict = {"hash": hash, "is_processed": is_processed}
            records.append(record)
        df = pd.DataFrame(records)
        await self.db.update_batch(
            table=models.Image,
            data_to_update=df,
            schemas=self.schemas,
            conflict_cols=["hash"],
            session=session,
        )


    async def run(self, semaphore: int = 10, col_name_hash: str = "hash") -> Self:

        if not self.prompt_system and not self.prompt_user:
            raise ValueError("prompt_system or prompt_user are required")
        if not self.llm:
            raise ValueError("llm is required")

        df_images: pd.DataFrame = self.unprocessed_images if self.unprocessed_images is not None else pd.DataFrame()
        if df_images.empty or col_name_hash not in df_images.columns:
            self.num_of_images = 0
            self.num_of_images_processed = 0
            self.num_of_images_failed = 0
            return self

        sem = asyncio.Semaphore(semaphore)

        async def _worker(hash_img: str, image_path: str) -> tuple[str, LLMResponse]:
            image_file = Path(image_path)
            if not image_file.is_absolute():
                image_file = self.dir_base / image_file
            if not image_file.exists():
                raise FileNotFoundError(f"[OCR] image file not found: {image_file}")

            image_bytes = image_file.read_bytes()
            mime_type = mimetypes.guess_type(str(image_file))[0] or "image/jpeg"
            user_prompt = f"{self.prompt_user}\n" if self.prompt_user else ""
            user_prompt += f"{col_name_hash} : {hash_img}"

            async with sem:
                llm_response = await self.llm.ask(
                    LLMRequest(
                        prompt_system=self.prompt_system,
                        prompt_user=user_prompt,
                        data=image_bytes,
                        mime_type=mime_type,
                    )
                )
                return str(hash_img), llm_response

        tasks: list[asyncio.Task[tuple[str, LLMResponse]]] = []
        for row in df_images[[col_name_hash, "path"]].itertuples(index=False):
            hash_img = str(getattr(row, col_name_hash))
            image_path = str(getattr(row, "path"))
            task = asyncio.create_task(_worker(hash_img, image_path))
            tasks.append(task)

        self.num_of_images = len(df_images)
        self.num_of_images_processed = 0
        self.num_of_images_failed = 0

        for task_done in asyncio.as_completed(tasks):
            try:
                hash_img, llm_response = await task_done
                parser = YidoParser(llm_response)
                hash_prompts = [p for p in [self.prompt_system, self.prompt_user] if p is not None]

                # 이미지 1건 처리 단위를 하나의 트랜잭션으로 보장
                async with self.db.open_session(schemas=self.schemas) as session:
                    await self.upsert_ocr_receipt(parser.df_receipt, session=session)
                    await self.upsert_ocr_passport(parser.df_passport, session=session)
                    await self.insert_llm_usage(llm_response, hash_img, hash_prompts, self.llm.model, session=session)
                    await self.set_image_processed([hash_img], True, session=session)

                self.num_of_images_processed += 1
            except Exception as e:
                self.num_of_images_failed += 1
                logger.exception(f"[OCR] failed hash={hash_img} reason={e}")
            finally:
                await self.set_image_processing([hash_img], False)

        return self


    async def upsert_ocr_receipt(self, df_receipt: pd.DataFrame, session: AsyncSession | None = None) -> None:
        if df_receipt.empty or "coordinate" not in df_receipt.columns:
            return
        df_receipt = df_receipt[df_receipt["coordinate"].notna()]
        if not df_receipt.empty:
            await self.db.upsert_batch(
                table=models.OcrReceipt,
                data=df_receipt,
                schemas=self.schemas,
                session=session,
            )


    async def upsert_ocr_passport(self, df_passport: pd.DataFrame, session: AsyncSession | None = None) -> None:
        if df_passport.empty or "coordinate" not in df_passport.columns:
            return
        df_passport = df_passport[df_passport["coordinate"].notna()]
        if not df_passport.empty:
            await self.db.upsert_batch(
                table=models.OcrPassport,
                data=df_passport,
                schemas=self.schemas,
                session=session,
            )


    async def write_ocr_receipt(self, df_receipt: pd.DataFrame) -> None:
        await self.db.upsert_batch(table=models.OcrReceipt, data=df_receipt, schemas=self.schemas)


    async def insert_llm_usage(
        self,
        llm_response: LLMResponse,
        hash_img: str,
        hash_prompts: list[str],
        llm_model: str,
        session: AsyncSession | None = None,
    ) -> None:
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
        if session is not None:
            await session.execute(stmt)
        else:
            await self.db.execute_query(stmt, schemas=self.schemas)


