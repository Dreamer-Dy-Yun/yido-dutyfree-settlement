###########################################
# Module name : service_image_ocr.py
# Module functions : run_image_ocr_background, ask_llm_ocr, upsert_ocr_receipt, upsert_ocr_passport, write_llm_usage, set_image_processing, set_image_processed
# Written by : Cursor AI / Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.05
# Updated at : 2026.03.05
# Supported by : -
# Note : 일부 리팩토링. 추후 전반적인 리팩토링 필요
#        2026.03.09 : 트랜젝션 범위 설정 등
############################################
import os
import asyncio
import mimetypes
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import select, insert, Select, Insert, update, Update, Executable
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
from CUSTOMIZED.cust_hasher import Hasher


async def run_image_ocr_background(tenant_schema: str, public_schema: str) -> None:
    db = get_db_manager()
    llm_api_key = await resolve_active_llm_api_key(db, purpose="OCR")
    llm = ChatGPT(api_key=llm_api_key.api_key, model=llm_api_key.llm_model)
    prompt_system, prompt_user = await resolve_active_ocr_prompts(db)

    stmt_tenant = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    tenant_result = await db.execute_query(stmt_tenant, schemas=[public_schema])
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise RuntimeError(f"[OCR] tenant not found for schema={tenant_schema}")

    root_dir = Path(os.getenv("ROOT_DIR", "D:/"))
    image_ocr_service = ImageOcrService(
        db=db,
        public_schema=public_schema,
        tenant_schema=tenant_schema,
        dir_root=root_dir,
        dir_base=Path(tenant.dir_base),
    )
    image_ocr_service.set_llm(llm, prompt_system, prompt_user)
    await image_ocr_service.get_unprocessed_images()
    await image_ocr_service.run()


async def resolve_active_llm_api_key(
    db: DBManager,
    purpose: str = "OCR",
    public_schema: str = "public",
) -> LLM_API_Key:
    """
    활성화된 LLM API Key 중에서 목적(purpose)과 제공사(provider)에 맞는 가장 최근 키를 조회한다.
    모델명은 DB에 저장된 값을 그대로 사용하며, 코드에서 하드코딩하지 않는다.
    """
    stmt: Select = select(LLM_API_Key)
    stmt = stmt.where(LLM_API_Key.is_active == True)
    stmt = stmt.where(LLM_API_Key.purpose == purpose)
    stmt = stmt.order_by(LLM_API_Key.db_updated_at.desc())
    stmt = stmt.limit(1)
    result = await db.execute_query(stmt, schemas=[public_schema])
    row = result.scalar_one_or_none()
    if row is None:
        raise RuntimeError(
            f"[OCR] active llm_api_key not found: purpose={purpose}"
        )
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
    def __init__(self, db : DBManager, public_schema: str, tenant_schema: str, dir_root: Path, dir_base: Path = Path(".")):
        self.db : DBManager = db
        self.unprocessed_images : pd.DataFrame | None = None
        self.llm : LLM | None = None
        self.prompt_system : str | None = None
        self.prompt_user : str | None = None
        self.public_schema : str | None = public_schema
        self.tenant_schema : str | None = tenant_schema
        self.dir_root: Path = dir_root
        self.dir_base: Path = dir_base
        self.schemas : list[str] = [self.tenant_schema, self.public_schema]
        self.num_of_images : int = 0
        self.num_of_images_processed : int = 0
        self.num_of_images_failed : int = 0


    def set_llm(self, llm: LLM, prompt_system: str | None = None, prompt_user: str | None = None) -> Self:
        self.llm = llm
        self.prompt_system = prompt_system
        self.prompt_user = prompt_user
        self.hash_prompt_system = Hasher().hash(prompt_system).to_hex_string if prompt_system else None
        self.hash_prompt_user = Hasher().hash(prompt_user).to_hex_string if prompt_user else None
        return self


    async def get_unprocessed_images(self) -> Self:
        stmt : Update = update(models.Image)
        stmt = stmt.where(models.Image.is_processing.is_(False))
        stmt = stmt.where(models.Image.is_processed.is_(False))
        stmt = stmt.values(is_processing=True)
        stmt = stmt.returning(models.Image.hash, models.Image.path)
        
        result: Result[models.Image | None] = await self.db.execute_query(stmt, schemas=self.schemas)
        rows = result.mappings().all()
        self.unprocessed_images = pd.DataFrame(rows)
        return self


    async def set_image_processing(self, session: AsyncSession | None , target_hashes: list[str], is_processing: bool = True) -> None:
        stmt : Executable = update(models.Image).where(models.Image.hash.in_(target_hashes)).values(is_processing=is_processing)
        if session is not None:
            await session.execute(stmt)
        else:
            await self.db.execute_query(stmt, schemas=self.schemas)


    async def set_image_processed(self,session: AsyncSession | None, target_hashes: list[str], is_processed: bool = True) -> None:
        stmt : Executable = update(models.Image).where(models.Image.hash.in_(target_hashes)).values(is_processed=is_processed)
        if session is not None:
            await session.execute(stmt)
        else:
            await self.db.execute_query(stmt, schemas=self.schemas)


    def initialize_counters(self) -> Self:
        self.num_of_images = 0
        self.num_of_images_processed = 0
        self.num_of_images_failed = 0
        return self


    async def run(self, semaphore: int = 10, col_name_hash: str = "hash", col_name_path: str = "path") -> Self:

        if not self.prompt_system and not self.prompt_user:
            raise ValueError("prompt_system or prompt_user are required")
        if not self.llm:
            raise ValueError("llm is required")

        self.initialize_counters()
        df_images: pd.DataFrame = self.unprocessed_images if self.unprocessed_images is not None else pd.DataFrame()
        if df_images.empty or col_name_hash not in df_images.columns:
            return self
        sem = asyncio.Semaphore(semaphore)

        tasks: list[asyncio.Task[tuple[str, LLMResponse | None, Exception | None]]] = []
        for row in df_images[[col_name_hash, col_name_path]].itertuples(index=False):
            hash_img : str = str(getattr(row, col_name_hash))
            image_path : Path = self.dir_root / self.dir_base / str(getattr(row, col_name_path))
            task : asyncio.Task[tuple[str, LLMResponse | None, Exception | None]] = asyncio.create_task(
                self._worker_safe(hash_img, image_path, sem, col_name_hash)
            )
            tasks.append(task)

        self.num_of_images = len(df_images)

        for task_done in asyncio.as_completed(tasks):
            hash_img: str | None = None
            try:
                hash_img, llm_response, worker_error = await task_done
                logger.info(f"[AI OCR] hash_img={hash_img} llm_response={llm_response} worker_error={worker_error}")
                if worker_error is not None:
                    # 워커에서 이미 예외가 잡힌 경우(파일 없음 등) -> 실패 처리만 하고 다음 이미지로 진행
                    raise worker_error
                if llm_response is None:
                    raise RuntimeError("[AI OCR] llm_response is None")

                parser = YidoParser(llm_response)
                df_receipt: pd.DataFrame = parser.df_receipt.copy()
                df_passport: pd.DataFrame = parser.df_passport.copy()
                hash_prompts: list[str] = [p for p in [self.hash_prompt_system, self.hash_prompt_user] if p]

                self._inject_ocr_hashes(df_receipt, hash_img)
                self._inject_ocr_hashes(df_passport, hash_img)

                # 이미지 1건 처리 단위를 하나의 트랜잭션으로 보장
                async with self.db.open_session(schemas=self.schemas) as session:
                    await self.upsert_ocr_receipt(session, df_receipt)
                    await self.upsert_ocr_passport(session, df_passport)
                    await self.insert_llm_usage(session, llm_response, hash_img, hash_prompts, self.llm.model)
                    await self.update_result_to_image(session, hash_img, df_receipt, df_passport, note=llm_response.content.get("note", None))
                self.num_of_images_processed += 1
            except Exception as e:
                self.num_of_images_failed += 1
                if hash_img:
                    await self.set_image_processing(None, [hash_img], False)
                logger.exception(f"[AI OCR] failed. hash={hash_img or 'unknown'} reason={e}")
                # 여기서는 예외를 상위로 전파하지 않고, 다음 작업으로 계속 진행한다.
        return self


    async def _worker_safe(
        self,
        hash_img: str,
        image_path: Path,
        sem: asyncio.Semaphore,
        col_name_hash: str = "hash"
    ) -> tuple[str, LLMResponse | None, Exception | None]:
        try:
            _, llm_response = await self._worker(hash_img, image_path, sem, col_name_hash)
            return hash_img, llm_response, None
        except Exception as e:
            return hash_img, None, e


    async def _worker(self, hash_img: str, image_path: str, sem: asyncio.Semaphore, col_name_hash: str = "hash") -> tuple[str, LLMResponse]:
  
        image_file = Path(image_path)
        if not image_file.is_absolute():
            image_file = self.dir_root / self.dir_base / image_file
        if not image_file.exists():
            raise FileNotFoundError(f"[OCR] image file not found: {image_file}")

        image_bytes : bytes = image_file.read_bytes()
        mime_type : str = mimetypes.guess_type(str(image_file))[0] or "image/jpeg"
        user_prompt : str = ""
        user_prompt += f"{self.prompt_user}\n" if self.prompt_user else ""
        user_prompt += f"{col_name_hash} : {hash_img}" # 확인용 해시 정보 추가

        llm_request : LLMRequest = LLMRequest(
            prompt_system=self.prompt_system,
            prompt_user=user_prompt,
            data=image_bytes,
            mime_type=mime_type,
        )

        async with sem:
            llm_response : LLMResponse = await self.llm.ask(llm_request)
            return str(hash_img), llm_response


    async def update_result_to_image(
        self, 
        session: AsyncSession, 
        hash_img: str, 
        df_receipt: pd.DataFrame, 
        df_passport: pd.DataFrame, 
        is_processing: bool = False,
        is_processed: bool = True,
        note: str | None = None
    ) -> None:
        img_types : list[str] = []
        classified : bool = True
        if not df_receipt.empty:
            img_types.append(f"receipt : {len(df_receipt)}")
        if not df_passport.empty:
            img_types.append(f"passport : {len(df_passport)}")
        if df_receipt.empty and df_passport.empty:
            img_types.append("unknown")
            classified = False
        note  = "/ ".join(img_types) + (f"\n {note}" if note else "")

        stmt : Executable
        stmt = update(models.Image)
        stmt = stmt.where(models.Image.hash == hash_img)
        stmt = stmt.values(is_classified=classified, note=note, is_processing=is_processing, is_processed=is_processed)
        await session.execute(stmt)


    async def upsert_ocr_receipt(self, session: AsyncSession, df_receipt: pd.DataFrame) -> None:
        if not df_receipt.empty:
            await self.db.upsert_batch(table=models.OcrReceipt, data=df_receipt, schemas=self.schemas, session=session)


    async def upsert_ocr_passport(self, session: AsyncSession, df_passport: pd.DataFrame) -> None:
        for col in ["date_of_birth", "date_of_issue", "date_of_expiry"]:
            if col in df_passport.columns:
                df_passport[col] = pd.to_datetime(df_passport[col], errors="coerce").dt.date
        if not df_passport.empty:
            await self.db.upsert_batch(table=models.OcrPassport, data=df_passport, schemas=self.schemas, session=session)


    async def insert_llm_usage(
        self,
        session: AsyncSession,
        llm_response: LLMResponse,
        hash_img: str,
        hash_prompts: list[str],
        llm_model: str,
    ) -> None:
        usage = llm_response.usage if llm_response else None
        usage_row : dict = {}
        usage_row["llm_model"] = llm_model
        usage_row["hash_prompts"] = hash_prompts
        usage_row["ocr_name"] = self.llm.model
        usage_row["hash_img"] = hash_img
        usage_row["token_input"] = usage.prompt_tokens if usage else None
        usage_row["token_output"] = usage.completion_tokens if usage else None
        usage_row["token_total"] = usage.total_tokens if usage else None
        stmt : Insert = insert(models.LlmUsage).values(**usage_row)
        await session.execute(stmt)


    def _inject_ocr_hashes(self, df: pd.DataFrame, hash_img: str) -> None:
        # 완전 필요없어 보이는데 만들어 놨네
        if df.empty:
            return
        df["hash_img"] = hash_img
        if "hash_ocr_result" in df.columns:
            return
        hashes: list[str] = []
        for row in df.to_dict(orient="records"):
            payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
            hashes.append(Hasher().hash(payload).to_hex_string)
        df["hash_ocr_result"] = hashes



