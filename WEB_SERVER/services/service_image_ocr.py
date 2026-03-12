###########################################
# Module name : service_image_ocr.py
# Module functions : run_image_ocr_background, resolve_active_llm_api_key, resolve_active_ocr_prompts
# Written by : Cursor AI / Yun Dae-young
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.05
# Updated at : 2026.03.11
# Supported by : -
# Note : OCR 러너(ImageOcrRunner)는 PROCESSOR_LLM_RESULT.image_ocr_runner 로 이전됨
############################################
import os
from pathlib import Path

from sqlalchemy import select, Select

from DATABASE.models.public_model import LLM_API_Key, Prompt, Tenant as PublicTenant
from DATABASE.dbms.db_manager import DBManager
from WEB_SERVER.routers.settings import get_db_manager
from LLM.ChatGPT.api import ChatGPT
from PROCESSOR_LLM_RESULT.image_ocr_runner import ImageOcrRunner


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
    runner = ImageOcrRunner(
        db=db,
        public_schema=public_schema,
        tenant_schema=tenant_schema,
        dir_root=root_dir,
        dir_base=Path(tenant.dir_base),
    )
    runner.set_llm(llm, prompt_system, prompt_user)
    await runner.get_unprocessed_images()
    await runner.run()


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


