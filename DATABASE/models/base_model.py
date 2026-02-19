###########################################
# Module name : base.py
# Module class : BaseModel (기본 모델 클래스)
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 모든 모델의 기본 클래스
#   2025.12.03 : models.py에서 분리 후 models 폴더로 이동
############################################

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from sqlalchemy.types import BigInteger, String  # UUID 와 동일. DBMS 독립 범용 데이터 타입.
from sqlalchemy.sql import func
from typing import Self
import uuid


class BaseModel(DeclarativeBase):
    """모든 모델의 기본 클래스"""
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 감사 필드
    db_created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    db_updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    db_created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    db_updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, updated={self.db_updated_at})>"

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
