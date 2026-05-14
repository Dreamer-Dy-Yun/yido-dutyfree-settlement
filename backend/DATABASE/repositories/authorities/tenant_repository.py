###########################################
# Module name : tenant_repository.py
# Module class : TenantRepository
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.01.30
# Updated at : 2026.01.30
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 테넌트(회사) 관련 데이터 접근 로직
############################################

from typing import Any
from sqlalchemy import select, Select, update
from DATABASE import models
from DATABASE.repositories.base import BaseRepository
import pandas as pd


class TenantRepository(BaseRepository):
    """테넌트(회사) 관련 Repository"""
    
    async def get_by_name(self, name: str) -> models.Tenant | None:
        """테넌트명으로 테넌트 조회 (ORM 객체 반환)"""
        stmt = select(models.Tenant).where(models.Tenant.name == name)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, tenant_id: int) -> models.Tenant | None:
        """ID로 테넌트 조회 (ORM 객체 반환)"""
        stmt = select(models.Tenant).where(models.Tenant.id == tenant_id)
        result = await self.db.execute_query(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, is_active: bool | None = None) -> list[dict[str, Any]]:
        """테넌트 목록 조회"""
        md: type[models.Tenant] = models.Tenant
        stmt: Select = select(md.__table__.columns)
        if is_active is not None:
            stmt = stmt.where(md.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()

    async def create(self, df: pd.DataFrame) -> int:
        """테넌트 생성"""
        result = await self.db.upsert_batch(table=models.Tenant, data=df)
        return int(result["cnt_success_rows"])

    async def update(self, tenant_id: int, update_data: dict[str, Any]) -> int:
        """테넌트 정보 업데이트"""
        md: type[models.Tenant] = models.Tenant
        stmt = update(md).where(md.id == tenant_id).values(**update_data)
        result = await self.db.execute_query(stmt)
        return result.rowcount

    async def get_or_create(self, name: str, description: str | None = None) -> models.Tenant:
        """테넌트 조회 또는 생성 (이름으로 조회, 없으면 생성)"""
        # 기존 테넌트 조회
        tenant = await self.get_by_name(name)
        if tenant:
            return tenant
        
        # 테넌트 생성
        tenant_df = pd.DataFrame([{
            "name": name,
            "description": description or f"{name} 회사",
            "is_active": True
        }])
        await self.create(tenant_df)
        
        # 생성된 테넌트 조회
        tenant = await self.get_by_name(name)
        if not tenant:
            raise ValueError(f"테넌트 생성 후 조회에 실패했습니다: {name}")
        
        return tenant
