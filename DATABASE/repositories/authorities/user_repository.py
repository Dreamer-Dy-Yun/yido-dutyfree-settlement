###########################################
# Module name : user_repository.py
# Module class : UserRepository
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 사용자 관련 데이터 접근 로직
############################################

from typing import Any
from sqlalchemy import select, Select, update, delete, insert
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from DATABASE import models
from DATABASE.repositories.base import BaseRepository
import pandas as pd
import uuid


class UserRepository(BaseRepository):
    """사용자 관련 Repository"""
    
    async def get_by_username(self, username: str) -> models.User | None:
        """사용자명으로 사용자 조회 (ORM 객체 반환)"""
        stmt = select(models.User).where(models.User.username == username)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> models.User | None:
        """이메일로 사용자 조회 (ORM 객체 반환)"""
        stmt = select(models.User).where(models.User.email == email)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> models.User | None:
        """ID로 사용자 조회 (ORM 객체 반환)"""
        stmt = select(models.User).where(models.User.id == user_id)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, is_active: bool | None = None) -> list[dict[str, Any]]:
        """사용자 목록 조회"""
        md: type[models.User] = models.User
        stmt: Select = select(md.__table__.columns)
        if is_active is not None:
            stmt = stmt.where(md.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()

    async def create(self, df: pd.DataFrame) -> int:
        """사용자 생성"""
        result = await self.db.upsert_batch(table=models.User, data=df)
        return int(result["cnt_success_rows"])

    async def update(self, user_id: uuid.UUID, update_data: dict[str, Any]) -> int:
        """사용자 정보 업데이트"""
        md: type[models.User] = models.User
        stmt = update(md).where(md.id == user_id).values(**update_data)
        result = await self.db.execute_query(stmt)
        return result.rowcount

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """사용자 마지막 로그인 시간 업데이트"""
        md: type[models.User] = models.User
        stmt = update(md).where(md.id == user_id).values(last_login=func.now())
        await self.db.execute_query(stmt)

