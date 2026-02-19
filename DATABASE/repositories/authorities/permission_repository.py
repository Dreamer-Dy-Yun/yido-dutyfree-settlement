###########################################
# Module name : permission_repository.py
# Module class : PermissionRepository
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 권한 관련 데이터 접근 로직
############################################

from typing import Any
from sqlalchemy import select, Select, update
from DATABASE import models
from DATABASE.repositories.base import BaseRepository
import pandas as pd
import uuid


class PermissionRepository(BaseRepository):
    """권한 관련 Repository"""
    
    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        """권한명으로 권한 조회"""
        md: type[models.Permission] = models.Permission
        stmt: Select = select(md.__table__.columns).where(md.name == name)
        result = await self.db.execute_query(stmt)
        return result.mappings().first()

    async def get_by_id(self, permission_id: uuid.UUID) -> dict[str, Any] | None:
        """ID로 권한 조회"""
        md: type[models.Permission] = models.Permission
        stmt: Select = select(md.__table__.columns).where(md.id == permission_id)
        result = await self.db.execute_query(stmt)
        return result.mappings().first()

    async def get_by_resource_action(self, resource: str, action: str) -> dict[str, Any] | None:
        """리소스와 액션으로 권한 조회"""
        md: type[models.Permission] = models.Permission
        stmt: Select = select(md.__table__.columns).where(
            md.resource == resource,
            md.action == action
        )
        result = await self.db.execute_query(stmt)
        return result.mappings().first()

    async def get_all(self, skip: int = 0, limit: int = 100, resource: str | None = None) -> list[dict[str, Any]]:
        """권한 목록 조회"""
        md: type[models.Permission] = models.Permission
        stmt: Select = select(md.__table__.columns)
        if resource:
            stmt = stmt.where(md.resource == resource)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()

    async def create(self, df: pd.DataFrame) -> int:
        """권한 생성"""
        return await self.db.batch_upsert_dataframe(models.Permission, df)

    async def update(self, permission_id: uuid.UUID, update_data: dict[str, Any]) -> int:
        """권한 정보 업데이트"""
        md: type[models.Permission] = models.Permission
        stmt = update(md).where(md.id == permission_id).values(**update_data)
        result = await self.db.execute_query(stmt)
        return result.rowcount

