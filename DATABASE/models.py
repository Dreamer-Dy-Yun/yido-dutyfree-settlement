###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.10
# Updated at : 2025.07.16
# Supported by : ChatGPT-4o
# Note : SQLAlchemy ORM 모델 정의
#   2025.07.16 : SQLAlchemy 2.0 권고에 따라, Mapped Column으로 변경
#   2025.09.23 : Process 테이블에서 Unique Constraint 제거
#                file_hash를 Unique 컬럼으로 변경
#                fullpath_source를 fullpath_current로 변경 등.
#   2025.10.02 : 컬럼명 변경 및 관련부 변경(DB 설계 참조)
############################################

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey, UniqueConstraint, Double, LargeBinary, Index
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from alembic import op

class BaseModel(DeclarativeBase):
    """모든 모델의 기본 클래스"""
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    db_created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    db_updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, updated={self.db_updated_at})>"

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


class GoogleServiceAccount(BaseModel):
    __tablename__ = "google_service_account"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    path_account: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    spreadsheet_id: Mapped[str] = mapped_column(String(255), nullable=False)
    worksheet_name: Mapped[str] = mapped_column(String(255), nullable=False)


class Instrument(BaseModel):
    __tablename__ = "instrument"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dir_base_source : Mapped[str | None] = mapped_column(Text, nullable=True) 
    ssh_key_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    network_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    network_password: Mapped[str] = mapped_column(Text, nullable=True)  # 현재 사용예정 없으나, 사용시 암호화 정책/인터페이스 수립 할 것.
    accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ExternalDefect(BaseModel):
    __tablename__ = "external_defect"

    serial_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    occurred_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    recognized_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    recognized_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recognized_place: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Model(BaseModel):
    __tablename__ = "model"

    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)


class Spec(BaseModel):
    __tablename__ = "spec"

    instrument_name: Mapped[str | None] = mapped_column(String(50), ForeignKey("instrument.name", ondelete="SET NULL"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(20), ForeignKey("model.name", ondelete="CASCADE"), nullable=False)

    measured_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adj_val_infinity: Mapped[float | None] = mapped_column(Double, nullable=True)
    adj_val_extreme: Mapped[float | None] = mapped_column(Double, nullable=True)
    delta_spec_ratio: Mapped[float | None] = mapped_column(Double, nullable=True)

    path_sub_datafile: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_datafile: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    is_latest: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("model_name", "path_sub_datafile", name="uix_model_path"),
    )


class Measured(BaseModel):
    __tablename__ = "measured"

    instrument_name: Mapped[str | None] = mapped_column(String(50), ForeignKey("instrument.name", ondelete="SET NULL"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(20), ForeignKey("model.name", ondelete="CASCADE"), nullable=False)
    serial_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)      # 시리얼 넘버는 유니크하지 않음.

    path_sub_datafile: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_datafile: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)

    list_measured: Mapped[list[float]] = mapped_column(ARRAY(Double), nullable=False)
    measured_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_latest: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("serial_no", "path_sub_datafile", name="uix_serial_path"),
    )


class Normalized(BaseModel):
    __tablename__ = "normalized"
    # TODO : 원래는 이 테이블은 모델별로 생성하는 것이 맞으나, 시간 문제로 하나로 퉁침. 
    # TODO : 테이블을 나누게 되면, vector_visual_normed 차원을 모델별로 동적 생성/관리 할 것
    # 시리얼 넘버는 유니크 하지 않으므로, measured.id를 외래키로 사용. 
    measured_id: Mapped[int] = mapped_column(Integer, ForeignKey("measured.id", ondelete="CASCADE"), nullable=False)
    vector_visual_normed: Mapped[list[float]] = mapped_column(Vector(3000), nullable=False)
    applied_spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("spec.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        # measured_id는 1:1 관계 — 중복 방지
        UniqueConstraint("measured_id", name="uq_normalized_measured_id"),
        # applied_spec_id는 조인 시 필터링용
        Index("ix_normalized_spec_id", "applied_spec_id"),
    )


class Process(BaseModel):
    __tablename__ = "process"

    instrument_name: Mapped[str | None] = mapped_column(String(50), ForeignKey("instrument.name", ondelete="SET NULL"), nullable=True)
    path_full_source: Mapped[str] = mapped_column(Text, nullable=True)
    path_full_current: Mapped[str] = mapped_column(Text, nullable=True)
    hashed_file: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False, unique=True)
    is_retrieved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retrieved_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ShortGroup(BaseModel):
    __tablename__ = "short_groups"

    # TODO : 필요시 정의 예정
    pass
