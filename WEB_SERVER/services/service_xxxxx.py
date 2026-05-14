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

from sqlalchemy import select, Select
from sqlalchemy.engine import Result

from DATABASE import models
from DATABASE.dbms.db_manager import DBManager
from typing import Self





class PassportReceiptMatchingService:
    def __init__(self, db : DBManager, public_schema: str, tenant_schema: str):
        self.db : DBManager = db
        self.prompt_system : str | None = None
        self.prompt_user : str | None = None
        self.public_schema : str | None = public_schema
        self.tenant_schema : str | None = tenant_schema
        self.schemas : list[str] = [self.tenant_schema, self.public_schema]


    async def get_verified_receipt_data(self) -> Self:
        stmt : Select = select(models.VerifiedReceipt).where(models.VerifiedReceipt.is_verified.is_(True))
        result : Result[models.VerifiedReceipt | None] = await self.db.execute_query(stmt, schemas=self.schemas)
        row : models.VerifiedReceipt | None = result.scalar_one_or_none()
        return row

  