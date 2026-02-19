###########################################
# Module name : authorities_model.py
# Module class : 인증 및 권한 관리 모델 통합
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 인증 및 권한 관리 관련 모든 모델 통합
############################################

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, BigInteger
from DATABASE.models.base_model import BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenant"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 관계
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Tenant(name={self.name}, is_active={self.is_active})>"


class User(BaseModel):
    __tablename__ = "user"
    
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    
    # 관계
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users", lazy="selectin")
    roles: Mapped[list["Role"]] = relationship("Role", secondary="user_role", back_populates="users", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email}, is_active={self.is_active})>"


class Role(BaseModel):
    __tablename__ = "role"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 관계
    users: Mapped[list["User"]] = relationship("User", secondary="user_role", back_populates="roles", lazy="selectin")
    permissions: Mapped[list["Permission"]] = relationship("Permission", secondary="role_permission", back_populates="roles", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Role(name={self.name}, is_active={self.is_active})>"


class Permission(BaseModel):
    __tablename__ = "permission"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 예: "user", "role", "data"
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 예: "create", "read", "update", "delete"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 관계
    roles: Mapped[list["Role"]] = relationship("Role", secondary="role_permission", back_populates="permissions", lazy="selectin")
    
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )
    
    def __repr__(self) -> str:
        return f"<Permission(name={self.name}, resource={self.resource}, action={self.action})>"


# 다대다 관계를 위한 중간 테이블 클래스
class UserRole(BaseModel):
    __tablename__ = "user_role"
    
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(BaseModel):
    __tablename__ = "role_permission"
    
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True)
