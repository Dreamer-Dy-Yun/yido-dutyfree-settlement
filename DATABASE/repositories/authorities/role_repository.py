###########################################
# Module name : role_repository.py
# Module class : RoleRepository
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 역할 관련 데이터 접근 로직
############################################

from typing import Any
from sqlalchemy import select, Select, update, delete, insert
from sqlalchemy.exc import IntegrityError
from DATABASE import models
from DATABASE.repositories.base import BaseRepository
import pandas as pd
import uuid


class RoleRepository(BaseRepository):
    """역할 관련 Repository"""
    
    async def get_by_name(self, name: str) -> models.Role | None:
        """역할명으로 역할 조회 (ORM 객체 반환)"""
        stmt = select(models.Role).where(models.Role.name == name)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: uuid.UUID) -> models.Role | None:
        """ID로 역할 조회 (ORM 객체 반환)"""
        stmt = select(models.Role).where(models.Role.id == role_id)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, is_active: bool | None = None) -> list[dict[str, Any]]:
        """역할 목록 조회"""
        md: type[models.Role] = models.Role
        stmt: Select = select(md.__table__.columns)
        if is_active is not None:
            stmt = stmt.where(md.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()

    async def create(self, df: pd.DataFrame) -> int:
        """역할 생성"""
        return await self.db.batch_upsert_dataframe(models.Role, df)

    async def update(self, role_id: uuid.UUID, update_data: dict[str, Any]) -> int:
        """역할 정보 업데이트"""
        md: type[models.Role] = models.Role
        stmt = update(md).where(md.id == role_id).values(**update_data)
        result = await self.db.execute_query(stmt)
        return result.rowcount

    async def assign_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        """역할에 권한 할당 (ORM 방식, DBMS 독립적, 경합 방지)
        
        SELECT 없이 바로 INSERT 시도하여 원자적 연산 보장.
        IntegrityError 발생 시 이미 할당된 것으로 간주하고 무시.
        """
        async with self.db.session_maker() as session:
            try:
                stmt = insert(models.RolePermission).values(
                    role_id=role_id,
                    permission_id=permission_id
                )
                await session.execute(stmt)
                await session.commit()
            except IntegrityError:
                # Primary key 또는 unique constraint violation
                # 이미 할당되어 있으므로 정상적인 상황으로 간주하고 무시
                await session.rollback()
                return
            except Exception:
                await session.rollback()
                raise

    async def remove_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        """역할로부터 권한 제거 (ORM 방식)"""
        stmt = delete(models.RolePermission).where(
            (models.RolePermission.role_id == role_id) &
            (models.RolePermission.permission_id == permission_id)
        )
        await self.db.execute_query(stmt)

    async def get_permissions(self, role_id: uuid.UUID) -> list[dict[str, Any]]:
        """역할의 권한 목록 조회"""
        md_p: type[models.Permission] = models.Permission
        stmt = select(md_p.__table__.columns).join(
            models.RolePermission, md_p.id == models.RolePermission.permission_id
        ).where(models.RolePermission.role_id == role_id)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()

