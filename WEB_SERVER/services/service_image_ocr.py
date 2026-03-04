import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from CUSTOMIZED.cust_hasher import Hasher
from CUSTOMIZED.cust_logger import logger
from DATABASE import models
from DATABASE.models.public_model import Tenant as PublicTenant
from WEB_SERVER.routers.settings import get_db_manager
from LLM.ChatGPT.api import ChatGPT
from LLM.dto import LLMRequest, LLMResponse
from LLM_RESULT_PARSER.yido_parser import YidoParser


@lru_cache(maxsize=1)
def _get_prompt_text() -> str:
    default_prompt_path = Path(__file__).resolve().parents[2] / "LLM" / "prompt" / "prompt_yido.txt"
    prompt_path = Path(os.getenv("OCR_PROMPT_PATH", str(default_prompt_path)))
    return prompt_path.read_text(encoding="utf-8")


def _build_llm_usage_df(
    llm_response: LLMResponse,
    hash_img: str,
    hash_prompt: str,
) -> pd.DataFrame:
    usage = llm_response.usage
    if usage is None:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "llm_model": llm_response.model,
                "hash_prompt": hash_prompt,
                "ocr_name": "chatgpt",
                "hash_img": hash_img,
                "token_input": usage.prompt_tokens,
                "token_output": usage.completion_tokens,
                "token_total": usage.total_tokens,
            }
        ]
    )


async def run_image_ocr_background(tenant_schema: str, image_hashes: list[str]) -> None:
    # 중복 제거 + 빈값 제거
    target_hashes = [h for h in dict.fromkeys(image_hashes) if h]
    if not target_hashes:
        return

    db = get_db_manager()
    tenant_schemas = [tenant_schema, "public"]
    # 임시 대응: upsert INSERT 경로에서 path NOT NULL 위반 방지용 기본값
    fallback_path = "img/__tmp_ocr_path__.jpg"

    stmt_existing_paths = select(models.Image.hash, models.Image.path).where(
        models.Image.hash.in_(target_hashes)
    )
    existing_path_result = await db.execute_query(stmt_existing_paths, schemas=tenant_schemas)
    path_by_hash = {str(row.hash): str(row.path) for row in existing_path_result.all() if row.path}

    # 대상 이미지들을 먼저 processing 상태로 전환
    df_start = pd.DataFrame(
        [
            {
                "hash": h,
                "path": path_by_hash.get(h, fallback_path),
                "is_processing": True,
                "is_processed": False,
            }
            for h in target_hashes
        ]
    )
    await db.batch_upsert_dataframe(models.Image, df_start, schemas=tenant_schemas)

    # 테넌트 루트 경로 조회 (public 스키마)
    stmt_tenant = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    tenant_result = await db.execute_query(stmt_tenant, schemas=["public"])
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        logger.error(f"[OCR] tenant not found: schema={tenant_schema}")
        df_fail = pd.DataFrame(
            [
                {
                    "hash": h,
                    "path": path_by_hash.get(h, fallback_path),
                    "is_processing": False,
                    "is_processed": False,
                }
                for h in target_hashes
            ]
        )
        await db.batch_upsert_dataframe(models.Image, df_fail, schemas=tenant_schemas)
        return

    root_dir = Path(os.getenv("ROOT_DIR", "D:\\"))
    tenant_root = root_dir / tenant.path_root

    stmt_images = select(models.Image).where(models.Image.hash.in_(target_hashes))
    image_result = await db.execute_query(stmt_images, schemas=tenant_schemas)
    images = image_result.scalars().all()

    prompt_text = _get_prompt_text()
    prompt_hash = Hasher().hash(prompt_text).to_hex_string
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        logger.error("[OCR] OPENAI_API_KEY is empty")
        df_fail = pd.DataFrame(
            [
                {
                    "hash": h,
                    "path": path_by_hash.get(h, fallback_path),
                    "is_processing": False,
                    "is_processed": False,
                }
                for h in target_hashes
            ]
        )
        await db.batch_upsert_dataframe(models.Image, df_fail, schemas=tenant_schemas)
        return

    model_name = os.getenv("OCR_MODEL", "gpt-4o")
    llm = ChatGPT(api_key=api_key, model=model_name)
    try:
        for image in images:
            image_hash = str(image.hash)
            try:
                full_path = tenant_root / str(image.path)
                if not full_path.exists():
                    raise FileNotFoundError(f"image file not found: {full_path}")

                image_bytes = full_path.read_bytes()
                ext = full_path.suffix.lower()
                mime_type = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }.get(ext, "application/octet-stream")
                request = LLMRequest(
                    prompt_system=prompt_text,
                    prompt_user="이미지 OCR 결과를 JSON 형식으로 반환하라.",
                    data=image_bytes,
                    mime_type=mime_type,
                )
                llm_response = await llm.ask(request)

                parser = YidoParser(llm_response)
                parser.add_hashed_image(full_path)

                df_passport = parser.df_passport
                df_receipt = parser.df_receipt
                if not df_passport.empty:
                    df_passport = df_passport[df_passport["coordinate"].notna()]
                    if not df_passport.empty:
                        await db.batch_upsert_dataframe(
                            models.OcrPassport, df_passport, schemas=tenant_schemas
                        )
                if not df_receipt.empty:
                    df_receipt = df_receipt[df_receipt["coordinate"].notna()]
                    if not df_receipt.empty:
                        await db.batch_upsert_dataframe(
                            models.OcrReceipt, df_receipt, schemas=tenant_schemas
                        )

                df_usage = _build_llm_usage_df(llm_response, image_hash, prompt_hash)
                if not df_usage.empty:
                    await db.batch_upsert_dataframe(models.LlmUsage, df_usage, schemas=tenant_schemas)

                await db.upsert_dataframe(
                    models.Image,
                    pd.DataFrame(
                        [
                            {
                                "hash": image_hash,
                                "path": str(image.path),
                                "is_processing": False,
                                "is_processed": True,
                            }
                        ]
                    ),
                    schemas=tenant_schemas,
                )
            except Exception as e:
                logger.exception(f"[OCR] failed hash={image_hash} reason={e}")
                await db.upsert_dataframe(
                    models.Image,
                    pd.DataFrame(
                        [
                            {
                                "hash": image_hash,
                                "path": str(image.path),
                                "is_processing": False,
                                "is_processed": False,
                            }
                        ]
                    ),
                    schemas=tenant_schemas,
                )
    finally:
        await llm.close()
