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
from pathlib import Path

import pandas as pd
from sqlalchemy import select, insert, Select
from sqlalchemy.engine import Result

from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.models.public_model import Tenant as PublicTenant, LLM_API_Key, Prompt
from WEB_SERVER.routers.settings import get_db_manager
from LLM.ChatGPT.api import ChatGPT
from LLM.dto import LLMRequest, LLMResponse
from LLM_RESULT_PARSER.yido_parser import YidoParser
from DATABASE.dbms.db_manager import DBManager

OCR_PROVIDER = "OPEN AI"
OCR_MODEL = "gpt-4o"
OCR_PURPOSE = "OCR"


async def _resolve_active_llm_api_key(db) -> LLM_API_Key:
    stmt_api_key = (
        select(LLM_API_Key)
        .where(
            LLM_API_Key.is_active == True,
            LLM_API_Key.llm_provider == OCR_PROVIDER,
            LLM_API_Key.llm_model == OCR_MODEL,
        )
        .order_by(LLM_API_Key.db_updated_at.desc())
        .limit(1)
    )
    result = await db.execute_query(stmt_api_key, schemas=["public"])
    row = result.scalar_one_or_none()
    if row is None:
        raise RuntimeError(
            f"[OCR] active llm_api_key not found: provider={OCR_PROVIDER}, model={OCR_MODEL}"
        )
    return row


async def _resolve_active_ocr_prompts(db) -> tuple[str, str | None, list[str]]:
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
    hash_prompts = [p.hash for p in (prompt_system, prompt_user) if p is not None]
    return system_text, user_text, hash_prompts


def _build_llm_usage_row(
    llm_response: LLMResponse | None,
    hash_img: str,
    hash_prompts: list[str],
    llm_model: str,
) -> dict:
    usage = llm_response.usage if llm_response else None
    return {
        "llm_model": (llm_response.model if llm_response and llm_response.model else llm_model),
        "hash_prompts": hash_prompts,
        "ocr_name": "chatgpt",
        "hash_img": hash_img,
        "token_input": usage.prompt_tokens if usage else None,
        "token_output": usage.completion_tokens if usage else None,
        "token_total": usage.total_tokens if usage else None,
    }


async def run_image_ocr_background(tenant_schema: str, image_hashes: list[str]) -> None:
    # image_hashes : 어차피 DB에서 유니크 키로 존재하는 값이라 중복 가능성 없음
    # AI 가 병신짓 해 둬서 대대적인 리팩토링 필요. 
    try:
        if not image_hashes:
            return

        db = get_db_manager()
        tenant_schemas = [tenant_schema, "public"]

        # 대상 이미지들을 먼저 processing 상태로 전환
        await set_image_processing(db, tenant_schemas, image_hashes, True)

        # 테넌트 베이스 디렉토리 경로 조회 (public 스키마)
        tenant_root = await get_base_directory(db, Path(os.getenv("ROOT_DIR", "D:\\")), tenant_schema)
        if tenant_root is None:
            raise RuntimeError(f"[OCR] tenant not found: schema={tenant_schema}")

        stmt_images = select(models.Image).where(models.Image.hash.in_(image_hashes))
        image_result = await db.execute_query(stmt_images, schemas=tenant_schemas)
        images = image_result.scalars().all()

        api_key_row = await _resolve_active_llm_api_key(db)
        prompt_system, prompt_user, hash_prompts = await _resolve_active_ocr_prompts(db)
    except Exception as e:
        logger.exception(f"[OCR] failed to resolve key/prompts reason={e}")
        await set_image_processing(db, tenant_schemas, image_hashes, False)
        return

    llm_model = str(api_key_row.llm_model or OCR_MODEL)
    llm = ChatGPT(api_key=str(api_key_row.api_key), model=llm_model)
    try:
        # 비동기 처리 해야함. 이건 그냥 직렬처리나 마찬가지.
        for image in images:
            image_hash = str(image.hash)
            llm_response: LLMResponse | None = None
            try:
                full_path = tenant_root / str(image.path)
                if not full_path.exists():
                    raise FileNotFoundError(f"image file not found: {full_path}")

                llm_response = await ask_llm_ocr(llm, full_path, prompt_system, prompt_user)

                parser = YidoParser(llm_response)
                parser.add_hashed_image(full_path)

                df_passport = parser.df_passport
                df_receipt = parser.df_receipt

                if not df_passport.empty:
                    await upsert_ocr_passport(db, tenant_schemas, df_passport)
                if not df_receipt.empty:
                    await upsert_ocr_receipt(db, tenant_schemas, df_receipt)

                await write_llm_usage(db, tenant_schemas, llm_response, image_hash, hash_prompts, llm_model)

                await set_image_processed(db, tenant_schemas, [image_hash], True)
                
            except Exception as e:
                logger.exception(f"[OCR] failed hash={image_hash} reason={e}")
                try:
                    await write_llm_usage(db, tenant_schemas, llm_response, image_hash, hash_prompts, llm_model)
                except Exception as usage_err:
                    logger.exception(f"[OCR] failed to write llm_usage hash={image_hash} reason={usage_err}")

                await set_image_processing(db, tenant_schemas, [image_hash], False)
    finally:
        await llm.close()





async def get_base_directory(db: DBManager, root_directory: Path, tenant_schema: str, public_schema: str = "public") -> Path | None:
    stmt : Select = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    tenant_result: Result[PublicTenant | None] = await db.execute_query(stmt, schemas=[public_schema])
    tenant: PublicTenant | None = tenant_result.scalar_one_or_none()
    return None if tenant is None else root_directory / tenant.dir_root


async def ask_llm_ocr(llm: ChatGPT, path_img: Path, prompt_system: str, prompt_user: str) -> LLMResponse:
    image_bytes = path_img.read_bytes()
    ext = path_img.suffix.lower()
    mime_type = get_mime_type(ext)
    request = LLMRequest(prompt_system, prompt_user, image_bytes, mime_type,)
    return await llm.ask(request)


def get_mime_type(ext: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


async def upsert_ocr_receipt(db: DBManager, schemas : list[str], df_receipt: pd.DataFrame) -> None:
    df_receipt = df_receipt[df_receipt["coordinate"].notna()]
    if not df_receipt.empty:
        await db.batch_upsert_dataframe(models.OcrReceipt, df_receipt, schemas=schemas)


async def upsert_ocr_passport(db: DBManager, schemas : list[str], df_passport: pd.DataFrame) -> None:
    df_passport = df_passport[df_passport["coordinate"].notna()]
    if not df_passport.empty:
        await db.batch_upsert_dataframe(models.OcrPassport, df_passport, schemas=schemas)


async def write_ocr_receipt(db: DBManager, schemas : list[str], df_receipt: pd.DataFrame) -> None:
    await db.batch_upsert_dataframe(models.OcrReceipt, df_receipt, schemas=schemas)


async def write_llm_usage(db: DBManager, schemas : list[str], llm_response: LLMResponse, image_hash: str, hash_prompts: list[str], llm_model: str) -> None:
    usage_row = _build_llm_usage_row(llm_response, image_hash, hash_prompts, llm_model)
    await db.execute_query(insert(models.LlmUsage).values(**usage_row), schemas=schemas)


async def set_image_processing(db: DBManager, schemas : list[str], target_hashes = list[str], is_processing: bool = True) -> None:
    # 대상 이미지들을 먼저 processing 상태로 전환
    records : list[dict] = []
    df : pd.DataFrame = pd.DataFrame()
    # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
    for hash in target_hashes:
        record : dict = {"hash": hash, "is_processing": is_processing, "is_processed": False}
        records.append(record)
    df = pd.DataFrame(records)
    await db.update_dataframe(models.Image, df, schemas=schemas, conflict_cols=["hash"])


async def set_image_processed(db: DBManager, schemas : list[str], target_hashes = list[str], is_processed: bool = True) -> None:
    # 대상 이미지들을 먼저 processing 상태로 전환
    records : list[dict] = []
    df : pd.DataFrame = pd.DataFrame()
    # 난 이게 더 이뻐 보임... 성능 좀 손해봐도..
    for hash in target_hashes:
        record : dict = {"hash": hash, "is_processing": False, "is_processed": is_processed}
        records.append(record)
    df = pd.DataFrame(records)
    await db.update_dataframe(models.Image, df, schemas=schemas, conflict_cols=["hash"])