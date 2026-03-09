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

from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, BigInteger, Numeric, Enum as SQLEnum
from .base_model import BaseModel
from CUSTOMIZED.cust_logger import logger


class ServiceAccountRole(Enum):
    """서비스 계정 역할"""
    SMTP_SENDER = "smtp_sender"  # 이메일 송신용
    SMTP_RECEIVER = "smtp_receiver"  # 이메일 수신용
    MONITOR = "monitor"  # 모니터링용
    BACKUP = "backup"  # 백업용
    API = "api"  # API 키용
    NOTIFICATION = "notification"  # 알림 발송용


class BaseModelPublic(BaseModel):
    __abstract__ = True
    __table_args__ = {"schema": "public"}


class SystemAdmin(BaseModelPublic):
    """시스템 어드민 (서비스 제공사 관리자) - 패스워드 해시 저장"""
    __tablename__ = "system_admin"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 관리자 이름
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 별칭
    e_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # 이메일 (Unique)
    password: Mapped[str] = mapped_column(String(64), nullable=False)  # 해싱된 패스워드 (SHA-256 hex 문자열, 64자)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 소속 부서
    contact: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 연락처
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 계정 활성화 여부
    
    def __repr__(self) -> str:
        return f"<SystemAdmin(name={self.name}, e_mail={self.e_mail}, is_active={self.is_active})>"


class ServiceAccount(BaseModelPublic):
    """서비스 계정 (SMTP 등) - 실제 패스워드 저장 (암호화 권장)"""
    __tablename__ = "service_account"
    
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=False, index=True)  # 계정 별칭
    e_mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)  # 이메일 (Unique)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # 실제 패스워드 (평문)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ServiceAccountRole enum value를 문자열로 저장
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # 용도 설명
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 계정 활성화 여부

    def __repr__(self) -> str:
        role_value = self.role.value if hasattr(self.role, 'value') else str(self.role)
        return f"<ServiceAccount(alias={self.alias}, e_mail={self.e_mail}, role={role_value}, is_active={self.is_active})>"


class Tenant(BaseModelPublic):
    __tablename__ = "tenant"
    
    country_code: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)  # 회사 소재 국가 코드
    business_no: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)  # 사업자 등록번호
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 회사명
    alias: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 별칭 (없으면 회사명)
    contact: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 대표번호
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 대표 이메일
    address: Mapped[str | None] = mapped_column(Text, nullable=True)  # 소재지
    dir_base: Mapped[str] = mapped_column(Text, nullable=False)  # 테넌트 베이스 디렉토리 경로
    schema_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # 스키마 이름
    is_db_built: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 스키마/테이블 생성 여부
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 활성화 여부
    
    def __repr__(self) -> str:
        return f"<Tenant(name={self.name}, business_no={self.business_no}, is_active={self.is_active})>"


class LLM_API_Key(BaseModelPublic):
    __tablename__ = "llm_api_key"
    
    purpose : Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # LLM 용도, 현재 OCR전용
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # LLM 제공사
    llm_model: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # LLM 모델
    api_key: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)  # API 키
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 활성화 여부
    
    def __repr__(self) -> str:
        return f"<LLM_API_Key(llm_provider={self.llm_provider}, llm_model={self.llm_model}, api_key={self.api_key}, is_active={self.is_active})>"


# ---------------------------------------------------------------------------
# PROMPT: 사용 프롬프트 이력
# 테이블 목적: 모델 관리, 사용 프롬프트 이력 관리
# Version: 2.0.0, 작성자: 윤대영
# ---------------------------------------------------------------------------
class Prompt(BaseModelPublic):
    """사용 프롬프트 이력. 프롬프트 해시로 유니크 관리."""
    __tablename__ = "prompt"

    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # 프롬프트 해시 (SHA-256)
    purpose : Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 프롬프트 목적, 현재 OCR 전용
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 프롬프트 타입, SYSTEM | USER
    prompt: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # 프롬프트
    note: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)  # 노트
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 활성화 여부
    
    def __repr__(self) -> str:
        return f"<Prompt(purpose={self.purpose}, type={self.type}, prompt={self.prompt}, note={self.note}, is_active={self.is_active})>"
       

class TestModel(BaseModelPublic):
    """테스트 모델."""
    __tablename__ = "test_model"

    a: Mapped[str] = mapped_column(String, nullable=False, unique=True) 
    b: Mapped[str] = mapped_column(String, nullable=False) 
    c: Mapped[str | None] = mapped_column(String, nullable=True)  

       