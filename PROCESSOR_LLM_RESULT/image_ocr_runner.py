###########################################
# Module name : image_ocr_runner.py
# Module functions : ImageOcrRunner
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.11
# Updated at : 2026.03.11
# Supported by : -
# Note : DB 하고 직접 연결된게 맘에 안드는데 일단 급한대로 이렇게 둠.
############################################


import pandas as pd
import json
import asyncio
import mimetypes
from pathlib import Path
from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, insert, Executable, Result
from LLM.dto import LLMResponse, LLMRequest
from LLM.llm import LLM
from CUSTOMIZED.cust_hasher import Hasher
from DATABASE.dbms.db_manager import DBManager
from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from PROCESSOR_LLM_RESULT.yido_parser import YidoParser


class ImageOcrRunner:
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
        stmt : Executable = update(models.Image)
        stmt = stmt.where(models.Image.is_processing.is_(False))
        stmt = stmt.where(models.Image.is_processed.is_(False))
        stmt = stmt.values(is_processing=True)
        stmt = stmt.returning(models.Image.hash, models.Image.path, models.Image.uuid_batch)

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

        # hash_img -> uuid_batch (ZIP 배치 식별용)
        hash_to_uuid_batch: dict[str, str] = {}
        if "uuid_batch" in df_images.columns:
            for row in df_images.itertuples(index=False):
                h = str(getattr(row, col_name_hash))
                ub = getattr(row, "uuid_batch", None)
                hash_to_uuid_batch[h] = (ub or "").strip() if ub is not None else ""

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

                uuid_batch: str = hash_to_uuid_batch.get(hash_img, "")
                parser = YidoParser().add_uuid_batch(uuid_batch)
                parser.run(llm_response)
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
        stmt : Executable = insert(models.LlmUsage).values(**usage_row)
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



