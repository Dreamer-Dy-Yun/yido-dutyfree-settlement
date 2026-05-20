###########################################
# Module name : tenant_schemas.py
# Module functions : Pydantic schemas for tenant router APIs
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.05.20
# Note : Keep route request/response contracts separate from router functions.
############################################

from datetime import datetime

from pydantic import BaseModel, EmailStr

from DATABASE.models.tenant_model import UserRole


class UserCreateRequest(BaseModel):
    name: str
    e_mail: EmailStr
    password: str
    role: UserRole = UserRole.USER
    department: str | None = None
    contact: str | None = None


class UserUpdateRequest(BaseModel):
    name: str | None = None
    e_mail: EmailStr | None = None
    role: UserRole | None = None
    department: str | None = None
    contact: str | None = None
    is_active: bool | None = None


class UserActivationRequest(BaseModel):
    is_active: bool


class ResetPasswordRequest(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: int
    name: str
    e_mail: str
    role: str
    department: str | None
    contact: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UsageResponse(BaseModel):
    total_images: int
    total_ocr_passport: int
    total_ocr_receipt: int
    total_verified_passport: int
    total_verified_receipt: int
    total_matched: int
    total_llm_tokens: int
    period_start: datetime | None
    period_end: datetime | None


class TenantInfoUpdateRequest(BaseModel):
    name: str | None = None
    alias: str | None = None
    country_code: int | None = None
    contact: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class MatchJobRequest(BaseModel):
    """Match worker request schema for internal endpoints."""

    tenant_schema: str
    requested_by: int | None = None
    try_fallback: bool = True
    matcher_key: str = "LOTTE"


class EdiUnifiedJobRequest(BaseModel):
    """EDI_UNIFIED worker request schema for internal endpoints."""

    tenant_schema: str
    requested_by: int | None = None
    sources: list[str] = ["SILLA", "LOTTE"]
    max_rows: int | None = None
    fill_receipt: bool = True
    fill_passport: bool = True


class EdiUnifiedJobEnqueueRequest(BaseModel):
    """EDI_UNIFIED enqueue request schema for frontend calls."""

    sources: list[str] = ["SILLA", "LOTTE"]


class ReceiptVerifyRequest(BaseModel):
    """Receipt verification/update request schema."""

    source: str
    id: int
    dutyfree_company: str
    group_no: str | None = None
    receipt_no: str
    country_code: str | None = None
    passport_no: str | None = None
    purchaser: str | None = None
    coordinate: dict[str, float] | None = None
    rotation: float | None = None
    force_merge: bool = False


class PassportVerifyRequest(BaseModel):
    """Passport verification/update request schema."""

    source: str
    id: int
    country_code: str
    passport_no: str
    name: str | None = None
    coordinate: dict[str, float] | None = None
    rotation: float | None = None
    force_merge: bool = False


class VerifyDeleteRequest(BaseModel):
    """Verification delete request schema."""

    source: str
    id: int


class BulkVerifyReceiptsRequest(BaseModel):
    """Bulk receipt verification request schema."""

    ids: list[str]


class BulkVerifyPassportsRequest(BaseModel):
    """Bulk passport verification request schema."""

    ids: list[str]
