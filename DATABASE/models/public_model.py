###########################################
# Module name : public_model.py
# Module class : Public 스키마 모델 통합
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2026.02.20
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : Public 스키마에 저장되는 모델들 (인증 및 권한 관리)
############################################

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, BigInteger, Numeric
from DATABASE.models.base_model import BaseModel



class BaseModelPublic(BaseModel):
    __abstract__ = True
    __table_args__ = {"schema": "public"}


class ServiceEmail(BaseModelPublic):
    __tablename__ = "service_email"
    
    alias: Mapped[str] = mapped_column(String(50), nullable=True, unique=False, index=True)
    e_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role : Mapped[str] = mapped_column(String(50), nullable=False, unique=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ServiceEmail(alias={self.alias}, e_mail={self.e_mail}, role={self.role}, is_active={self.is_active})>"


class Tenant(BaseModelPublic):
    __tablename__ = "tenant"
    
    country_code: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)  # 회사 소재 국가 코드
    business_no: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)  # 사업자 등록번호
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 회사명
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 별칭 (없으면 회사명)
    contact: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 대표번호
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 대표 이메일
    address: Mapped[str | None] = mapped_column(Text, nullable=True)  # 소재지
    path_root: Mapped[str] = mapped_column(Text, nullable=False)  # 루트 경로 (회사 데이터 저장 폴더)
    schema_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # 스키마 이름
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)  # 활성화 여부
    
    def __repr__(self) -> str:
        return f"<Tenant(name={self.name}, business_no={self.business_no}, is_active={self.is_active})>"



