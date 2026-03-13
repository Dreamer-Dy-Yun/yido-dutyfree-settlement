###########################################
# Module name : router_tenant.py
# Module functions : 테넌트 관리자용 API
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.02.20
# Note : 테넌트 관리자가 유저 관리, 사용량 조회, 테넌트 정보 관리
############################################

from datetime import datetime, timedelta
from typing import Any
import io
import os
import secrets
import string
import uuid
import re
from pathlib import Path
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func, and_, update as sql_update, delete as sql_delete
from sqlalchemy.sql import Select

from WEB_SERVER.auth.dependencies import get_current_tenant_admin, get_current_user
from WEB_SERVER.routers.settings import get_db_manager, get_tenant_repository
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.service_image_ocr import run_image_ocr_background
from WEB_SERVER.services.service_match_queue import enqueue_match_job
from WEB_SERVER.services.verification_token import verification_token_service
from WEB_SERVER.routers.settings import get_user_repository
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_zip_processor import ZipProcessor
from PROCESSOR_DATA.parsers.edi_lotte import EdiLotte
from PROCESSOR_DATA.parsers.edi_silla import EdiSilla
from PROCESSOR_DATA.patch import fix_invalid_datetime_in_xlsx_bytes

from DATABASE import models
from DATABASE.models.tenant_model import UserRole, MATCHED
from DATABASE.models.public_model import Tenant as PublicTenant
from DATABASE.repositories.authorities import UserRepository, TenantRepository
from DATABASE.dbms import DBManager
import pandas as pd
from PROCESSOR_MATCHING.matcher_registry import dict_matcher

router = APIRouter(prefix="/api/tenant", tags=["테넌트 관리"])


def _get_current_tenant_schema_from_user(current_user: models.User) -> str:
    """인증 의존성에서 주입된 current_user 객체에서 tenant_schema를 가져온다."""
    tenant_schema = getattr(current_user, "tenant_schema", None)
    if not tenant_schema:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유효한 테넌트 스키마를 확인할 수 없습니다.",
        )
    return tenant_schema


def _get_current_tenant_schemas(current_user: models.User) -> list[str]:
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    return [tenant_schema, "public"]


async def _fetch_verify_source(
    db: "DBManager",
    schemas: list[str],
    source: str,
    payload_id: int,
    ocr_model: type,
    verified_model: type,
    ocr_404_msg: str,
    verified_404_msg: str,
) -> tuple[Any, Any]:
    """검수 소스 조회. (ocr_row, verified_row) 반환, 둘 중 하나만 채워짐."""
    if source == "ocr":
        stmt = select(ocr_model).where(ocr_model.id == payload_id)
        result = await db.execute_query(stmt, schemas=schemas)
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ocr_404_msg)
        return (row, None)
    stmt = select(verified_model).where(verified_model.id == payload_id)
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=verified_404_msg)
    return (None, row)


def _verified_row_common(
    current_user: models.User,
    hash_img: Any,
    coordinate: Any,
    rotation: Any,
    is_corrected: bool,
    uuid_batch: str,
    uuid_record: str,
) -> dict[str, Any]:
    """Verified* upsert용 공통 필드."""
    return {
        "hash_img": hash_img,
        "coordinate": coordinate,
        "rotation": rotation,
        "is_verified": True,
        "is_corrected": is_corrected,
        "verifier_id": getattr(current_user, "id", None),
        "verifier_name": getattr(current_user, "name", None),
        "db_updated_by": str(getattr(current_user, "id", "")),
        "uuid_batch": uuid_batch or "",
        "uuid_record": uuid_record or "",
    }


async def _mark_ocr_processed_if_needed(
    db: "DBManager",
    schemas: list[str],
    ocr_row: Any,
    ocr_model: type,
    current_user: models.User,
) -> None:
    """OCR 원본이 있으면 is_processed=True 로 갱신."""
    if ocr_row is None or getattr(ocr_row, "is_processed", False):
        return
    stmt = (
        sql_update(ocr_model)
        .where(ocr_model.id == ocr_row.id)
        .values(is_processed=True, db_updated_by=str(getattr(current_user, "id", "")))
    )
    await db.execute_query(stmt, schemas=schemas)


def _is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


# 요청/응답 스키마
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


class MatchJobRequest(BaseModel):
    """매치 워커가 호출하는 내부용 매칭 작업 요청 스키마"""

    tenant_schema: str
    requested_by: int | None = None
    try_fallback: bool = True
    matcher_key: str = "lotte"


class ReceiptVerifyRequest(BaseModel):
    """영수증 검수/수정 요청 스키마"""
    source: str  # "ocr" | "verified"
    id: int
    dutyfree_company: str
    group_no: str | None = None
    receipt_no: str
    country_code: str | None = None
    passport_no: str | None = None
    purchaser: str | None = None
    coordinate: dict[str, float] | None = None
    rotation: float | None = None


class PassportVerifyRequest(BaseModel):
    """여권 검수/수정 요청 스키마"""
    source: str  # "ocr" | "verified"
    id: int
    country_code: str
    passport_no: str
    name: str | None = None
    coordinate: dict[str, float] | None = None
    rotation: float | None = None


# 유저 관리 API
@router.get("/users", summary="유저 목록 조회", description="테넌트의 모든 유저 목록을 조회합니다.")
@handle_http_error
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool | None = Query(None),
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 목록 조회"""
    schemas = _get_current_tenant_schemas(current_user)
    stmt: Select = select(models.User)
    if is_active is not None:
        stmt = stmt.where(models.User.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit).order_by(models.User.db_created_at.desc())
    
    result = await db.execute_query(stmt, schemas=schemas)
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "e_mail": user.e_mail,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "department": user.department,
            "contact": user.contact,
            "is_active": user.is_active,
            "created_at": user.db_created_at,
            "updated_at": user.db_updated_at,
        }
        for user in users
    ]


# ============================================================================
# 데이터 매핑 / EDI 업로드
# ============================================================================

@router.post(
    "/data-mapping/edi-upload",
    summary="EDI 데이터 업로드",
    description="면세점(롯데/신라) 구분과 엑셀 파일을 받아 파서로 파싱 후 해당 테이블에 업서트합니다.",
)
@handle_http_error
async def upload_edi_data(
    file: UploadFile = File(..., description="EDI/엑셀 파일"),
    edi_source: str = Form(..., description="면세점 구분: lotte | silla"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    """
    EDI/엑셀 파일 업로드 → PROCESSOR_DATA 파서로 파싱 → 테넌트 스키마 EDI 테이블에 업서트.
    """
    filename = file.filename or ""
    edi_source_lower = edi_source.strip().lower()
    if edi_source_lower not in ("lotte", "silla"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="edi_source는 lotte 또는 silla만 가능합니다.",
        )
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EDI 업로드는 엑셀(.xlsx, .xls)만 지원합니다.",
        )

    contents = await file.read()
    if edi_source_lower == "silla":
        contents = fix_invalid_datetime_in_xlsx_bytes(contents)

    # EDI 파서가 엑셀 로딩/플랫헤더/타입 변환을 모두 담당하도록 위임
    try:
        buffer = io.BytesIO(contents)
        if edi_source_lower == "lotte":
            parser = EdiLotte()
            table = models.EdiLotte
        elif edi_source_lower == "silla":
            parser = EdiSilla()
            table = models.EdiSilla
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 데이터 소스입니다.")

        df_parsed = parser.set_data(buffer).parse()
    except HTTPException:
        # 위에서 명시적으로 만든 HTTPException은 그대로 전달
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="엑셀을 읽는 중 오류가 발생했습니다.",
        )

    if df_parsed.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="파싱 결과가 비어 있습니다.")

    try:
        upsert_result = await db.upsert_batch(table=table, data=df_parsed, schemas=schemas)
        rows_upserted = int(upsert_result["cnt_success_rows"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장에 실패했습니다.",
        )

    return {
        "message": "파일이 업로드되어 반영되었습니다.",
        "filename": filename,
        "edi_source": edi_source_lower,
        "rows_upserted": rows_upserted,
    }


@router.post(
    "/data-mapping/match-attempt",
    summary="영수증-여권 매칭 작업 요청",
    description="현재 테넌트에 대해 백그라운드 매칭 작업을 Redis 큐에 등록합니다.",
)
@handle_http_error
async def request_match_attempt(
    try_fallback: bool = Form(True, description="fallback 매칭 수행 여부 (기본값: True)"),
    current_user: models.User = Depends(get_current_user),
):
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    job = enqueue_match_job(
        tenant_schema=tenant_schema,
        requested_by=getattr(current_user, "id", None),
        try_fallback=try_fallback,
    )
    return {
        "message": "매칭 작업이 큐에 등록되었습니다.",
        "job": job,
    }


@router.post(
    "/internal/match/run",
    summary="내부용 매칭 작업 실행",
    description="매치 워커가 호출하는 내부 전용 엔드포인트로, 지정된 테넌트에 대해 매칭 로직을 실행합니다.",
)
@handle_http_error
async def internal_run_match_job(
    payload: MatchJobRequest,
    db: DBManager = Depends(get_db_manager),
):
    import uuid

    matcher_key = (payload.matcher_key or "lotte").lower()
    matcher_cls = dict_matcher.get(matcher_key)
    if matcher_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 matcher_key 입니다: {matcher_key}",
        )

    matcher = matcher_cls(
        db=db,
        public_schema="public",
        tenant_schema=payload.tenant_schema,
    )

    locked_by = uuid.uuid4().hex
    await matcher.run(locked_by=locked_by, try_fallback=payload.try_fallback)

    return {
        "message": "매칭 작업이 완료되었습니다.",
        "tenant_schema": payload.tenant_schema,
        "matcher_key": matcher_key,
    }


@router.post(
    "/data-mapping/image-upload",
    summary="이미지 ZIP 업로드",
    description="데이터 매핑용 이미지 ZIP 파일 업로드 엔드포인트.",
)
@handle_http_error
async def upload_image_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="이미지 ZIP 파일"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    이미지 ZIP 업로드용 엔드포인트입니다.
    - 확장자가 .zip 인지 검증
    - 토큰에서 tenant_schema를 읽어 해당 테넌트의 루트 디렉터리 조회
    - .env 의 ROOT_DIR + 테넌트 전용 dir_base + \"zip\" 하위에 ZIP 파일 저장
    - 같은 루트의 \"img\" 하위에 ZipProcessor로 이미지 파일들만 풀어놓음
    실제 이미지 처리/DB 반영은 추후 구현.
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 업로드는 ZIP(.zip) 파일만 지원합니다.",
        )

    tenant_schema = _get_current_tenant_schema_from_user(current_user)

    # public.tenant 에서 현재 테넌트의 dir_base 조회
    stmt = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    result = await db.execute_query(stmt, schemas=["public"])
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트 정보를 찾을 수 없습니다.",
        )

    # ROOT_DIR + 테넌트 전용 디렉토리 + 하위(zip/img 폴더명은 .env) 구성
    root_dir = os.getenv("ROOT_DIR", "D:\\")
    zip_dir_name = os.getenv("ZIP_ROOT", "zip")
    img_dir_name = os.getenv("IMG_ROOT", "img")
    base_root = Path(root_dir)

    # dir_base 는 테넌트별 베이스 경로 (상대/절대 여부는 설정에 따름)
    tenant_root = base_root / tenant.dir_base
    zip_root = tenant_root / zip_dir_name
    img_root = tenant_root / img_dir_name

    zip_root.mkdir(parents=True, exist_ok=True)
    img_root.mkdir(parents=True, exist_ok=True)

    # ZIP 파일 저장 경로 (업로드 ID + 원본 파일명 조합)
    upload_id = uuid.uuid4().hex
    safe_name = Path(filename).name
    zip_path = zip_root / f"{upload_id}_{safe_name}"

    # 업로드된 파일 내용을 청크 단위로 디스크에 저장
    upload_chunk_size = 1024 * 1024  # 1MB
    try:
        with zip_path.open("wb") as dst:
            while True:
                chunk = await file.read(upload_chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ZIP 파일 저장에 실패했습니다: {e}",
        ) from e

    # ZIP 내용을 이미지 폴더로 풀기 (이미지 확장자만 대상으로 처리)
    try:
        zip_processor = ZipProcessor(zip_path).to_files(
            dir_dest_root=tenant_root,
            dir_dest_sub=Path(img_dir_name),
            allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
            ignore_inner_directory=True,
            set_hash_as_file_name=True,
        )
    except Exception as e:
        # 압축 해제 실패 시 ZIP 파일은 남겨두고 에러만 반환
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 압축 해제에 실패했습니다: {e}",
        ) from e

    # 생성된 이미지 파일 메타를 테넌트 image 테이블에 업서트
    image_rows: list[dict[str, Any]] = []
    for _full_path, meta in zip_processor.saved_meta.items():
        relative_path = meta.get("relative_path")
        file_hash = meta.get("hash")
        if not relative_path or not file_hash:
            continue
        image_rows.append(
            {
                "hash": str(file_hash),
                "path": str(relative_path).replace("\\", "/"),
                "exists": True,
                "is_processed": False,
                "uuid_batch": upload_id,
            }
        )

    if not image_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP 내에서 처리 가능한 이미지 파일을 찾지 못했습니다.",
        )

    df_images = pd.DataFrame(image_rows).drop_duplicates(subset=["hash"], keep="last")
    try:
        upsert_result = await db.upsert_batch(
            table=models.Image,
            data=df_images,
            schemas=_get_current_tenant_schemas(current_user),
        )
        rows_upserted = int(upsert_result["cnt_success_rows"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 메타데이터 저장에 실패했습니다: {e}",
        ) from e

    # OCR 비동기 백그라운드 작업 시작 (재시도 없음, 상태는 DB 컬럼으로 관리)
    background_tasks.add_task(run_image_ocr_background, tenant_schema, "public")

    return {
        "message": "이미지 ZIP 업로드/압축 해제 및 image 테이블 업서트가 완료되었습니다. OCR 백그라운드 처리를 시작했습니다.",
        "filename": filename,
        "upload_id": upload_id,
        "rows_upserted": rows_upserted,
    }


@router.get(
    "/data-mapping/image-ocr-progress",
    summary="이미지 OCR 진행도 조회",
    description="현재 테넌트 이미지 OCR 진행 현황을 조회합니다.",
)
@handle_http_error
async def get_image_ocr_progress(
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)

    # OCR 대상: exists=True 인 이미지 기준
    stmt_total = select(func.count(models.Image.id)).where(models.Image.exists == True)
    total = (await db.execute_query(stmt_total, schemas=schemas)).scalar() or 0

    stmt_processing = select(func.count(models.Image.id)).where(
        and_(models.Image.exists == True, models.Image.is_processing == True)
    )
    processing = (await db.execute_query(stmt_processing, schemas=schemas)).scalar() or 0

    stmt_done = select(func.count(models.Image.id)).where(
        and_(models.Image.exists == True, models.Image.is_processed == True)
    )
    done = (await db.execute_query(stmt_done, schemas=schemas)).scalar() or 0

    pending = max(total - processing - done, 0)
    progress_percent = round((done / total) * 100, 2) if total > 0 else 0.0

    return {
        "total": int(total),
        "processing": int(processing),
        "done": int(done),
        "pending": int(pending),
        "progress_percent": progress_percent,
    }


@router.get(
    "/data-mapping/match-status",
    summary="영수증-여권 매칭 상태 조회",
    description="현재 테넌트의 영수증 매칭 진행 현황을 조회합니다.",
)
@handle_http_error
async def get_match_status(
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    매칭 상태 요약:
    - total_count: is_verified=True 인 VerifiedReceipt 전체 건수
    - unmatched_count: is_verified=True 이면서 is_processed=False 인 건수 (아직 매칭 시도 대상)
    - matched_count: total_count - unmatched_count
    """
    schemas = _get_current_tenant_schemas(current_user)

    stmt_total = select(func.count(models.VerifiedReceipt.id)).where(
        models.VerifiedReceipt.is_verified.is_(True)
    )
    total_count = (await db.execute_query(stmt_total, schemas=schemas)).scalar() or 0

    stmt_unmatched = select(func.count(models.VerifiedReceipt.id)).where(
        and_(
            models.VerifiedReceipt.is_verified.is_(True),
            models.VerifiedReceipt.is_processed.is_(False),
        )
    )
    unmatched_count = (await db.execute_query(stmt_unmatched, schemas=schemas)).scalar() or 0

    matched_count = max(int(total_count) - int(unmatched_count), 0)

    return {
        "total_count": int(total_count),
        "matched_count": matched_count,
        "unmatched_count": int(unmatched_count),
    }


@router.get(
    "/data-mapping/matches",
    summary="영수증-여권 매칭 결과 리스트 조회",
    description="MATCHED 테이블 기준으로 매핑/미매핑/전체 리스트를 조회합니다.",
)
@handle_http_error
async def list_matches(
    status_filter: str = Query(
        "all",
        alias="status",
        description="'all' | 'matched' | 'unmatched' 중 하나",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    MATCHED + VerifiedReceipt 조인 결과를 기반으로 리스트를 반환한다.
    - status='matched'   : MATCHED.uuid_passport IS NOT NULL
    - status='unmatched' : MATCHED.uuid_passport IS NULL
    - status='all'       : 필터 없음
    """
    schemas = _get_current_tenant_schemas(current_user)

    base_stmt = (
        select(
            MATCHED.uuid_receipt.label("uuid_receipt"),
            MATCHED.uuid_passport.label("uuid_passport"),
            models.VerifiedReceipt.dutyfree_company.label("dutyfree_company"),
            models.VerifiedReceipt.receipt_no.label("receipt_no"),
            models.VerifiedReceipt.name.label("name"),
        )
        .select_from(MATCHED)
        .join(
            models.VerifiedReceipt,
            models.VerifiedReceipt.uuid_record == MATCHED.uuid_receipt,
        )
    )

    if status_filter == "matched":
        base_stmt = base_stmt.where(MATCHED.uuid_passport.is_not(None))
    elif status_filter == "unmatched":
        base_stmt = base_stmt.where(MATCHED.uuid_passport.is_(None))

    # total_count 계산
    count_stmt = base_stmt.with_only_columns(func.count()).order_by(None)
    total_result = await db.execute_query(count_stmt, schemas=schemas)
    total_count = total_result.scalar() or 0

    # 페이지네이션 적용
    stmt = (
        base_stmt.order_by(models.VerifiedReceipt.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute_query(stmt, schemas=schemas)
    items = result.mappings().all() if result.mappings() else []

    return {
        "items": [dict(row) for row in items],
        "total_count": int(total_count),
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/data-mapping/matches/{uuid_receipt}",
    summary="영수증-여권 매핑 상세 조회",
    description="MATCHED 기준으로 영수증/여권 상세 및 매핑 후보 리스트를 조회합니다.",
)
@handle_http_error
async def get_match_detail(
    uuid_receipt: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)

    # MATCHED + VerifiedReceipt 를 한 번에 조인해서 list_matches 와 동일 기준으로 조회
    stmt_base = (
        select(
            MATCHED,
            models.VerifiedReceipt,
            models.Image.path.label("image_path"),
        )
        .select_from(MATCHED)
        .join(
            models.VerifiedReceipt,
            models.VerifiedReceipt.uuid_record == MATCHED.uuid_receipt,
        )
        .join(
            models.Image,
            models.Image.hash == models.VerifiedReceipt.hash_img,
            isouter=True,
        )
        .where(MATCHED.uuid_receipt == uuid_receipt)
    )
    result_base = await db.execute_query(stmt_base, schemas=schemas)
    row_base = result_base.mappings().first() if result_base.mappings() else None
    if not row_base:
        raise HTTPException(status_code=404, detail="해당 영수증에 대한 매칭 결과가 없습니다.")

    matched = row_base.get("MATCHED", row_base)
    vr = row_base.get("VerifiedReceipt") or row_base.get("verified_receipt") or None
    if vr is None:
        raise HTTPException(status_code=404, detail="해당 영수증을 찾을 수 없습니다.")

    receipt = {
        "uuid_record": vr.uuid_record,
        "dutyfree_company": vr.dutyfree_company,
        "group_no": vr.group_no,
        "receipt_no": vr.receipt_no,
        "country_code": vr.country_code,
        "passport_no": vr.passport_no,
        "name": vr.name,
        "coordinate_verified": vr.coordinate,
        "hash_img": vr.hash_img,
        "image_path": row_base.get("image_path"),
    }

    possible_passports = getattr(matched, "possible_passports", None) or []
    ranks = getattr(matched, "ranks", None) or [float(i) for i in range(len(possible_passports))]

    candidates: list[dict] = []
    if possible_passports:
        stmt_candidates = (
            select(
                models.VerifiedPassport.uuid_record.label("uuid_record"),
                models.VerifiedPassport.country_code,
                models.VerifiedPassport.passport_no,
                models.VerifiedPassport.name,
                models.VerifiedPassport.coordinate,
                models.VerifiedPassport.hash_img,
                models.Image.path.label("image_path"),
            )
            .select_from(models.VerifiedPassport)
            .join(
                models.Image,
                models.Image.hash == models.VerifiedPassport.hash_img,
                isouter=True,
            )
            .where(models.VerifiedPassport.uuid_record.in_(possible_passports))
        )
        result_candidates = await db.execute_query(stmt_candidates, schemas=schemas)
        rows_candidates = result_candidates.mappings().all() if result_candidates.mappings() else []

        dict_candidates = {str(r["uuid_record"]): dict(r) for r in rows_candidates}

        tmp: list[dict] = []
        for idx, uuid_p in enumerate(possible_passports):
            row = dict_candidates.get(str(uuid_p))
            if not row:
                continue
            rank_value = ranks[idx] if idx < len(ranks) else float(idx)
            row_out = dict(row)
            row_out["rank"] = rank_value
            tmp.append(row_out)

        candidates = sorted(tmp, key=lambda x: (x.get("rank", 0), x.get("uuid_record", "")))

    current_uuid_passport = getattr(matched, "uuid_passport", None)
    current_match = None
    if current_uuid_passport:
        for c in candidates:
            if str(c.get("uuid_record")) == str(current_uuid_passport):
                current_match = c
                break

        if current_match is None:
            stmt_current = (
                select(
                    models.VerifiedPassport.uuid_record.label("uuid_record"),
                    models.VerifiedPassport.country_code,
                    models.VerifiedPassport.passport_no,
                    models.VerifiedPassport.name,
                    models.VerifiedPassport.coordinate,
                    models.VerifiedPassport.hash_img,
                    models.Image.path.label("image_path"),
                )
                .select_from(models.VerifiedPassport)
                .join(
                    models.Image,
                    models.Image.hash == models.VerifiedPassport.hash_img,
                    isouter=True,
                )
                .where(models.VerifiedPassport.uuid_record == current_uuid_passport)
            )
            result_current = await db.execute_query(stmt_current, schemas=schemas)
            row_current = result_current.mappings().first() if result_current.mappings() else None
            if row_current:
                current_match = dict(row_current)
                current_match["rank"] = 0.0

    return {
        "receipt": receipt,
        "current_match": current_match,
        "candidates": candidates,
    }


# ============================================================================
# 데이터 매핑 / 이미지 확인용 리스트 API
# ============================================================================


@router.get(
    "/data-mapping/receipts",
    summary="영수증 OCR/검증 리스트 조회",
    description="이미지 기반 영수증 OCR/검증 데이터를 조회합니다. 기본은 미완료(OCR 원본, is_processed=False)만 반환합니다.",
)
@handle_http_error
async def list_receipts_for_review(
    is_completed: bool = Query(
        False,
        description="작업 완료 여부. false=OCR 미처리(OcrReceipt.is_processed=False), true=검증 완료(VerifiedReceipt.is_verified=True)",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    이미지 기반 영수증 OCR/검증 리스트를 조회한다.
    - is_completed=False: OcrReceipt 기준, is_processed=False 인 행만 반환
    - is_completed=True: VerifiedReceipt 기준, is_verified=True 인 행만 반환
    """
    schemas = _get_current_tenant_schemas(current_user)

    if not is_completed:
        # 미완료: OCR 원본 기준 (is_processed=False)
        stmt = (
            select(
                models.OcrReceipt.id.label("id"),
                models.OcrReceipt.dutyfree_company.label("dutyfree_company"),
                models.OcrReceipt.group_no.label("group_no"),
                models.OcrReceipt.receipt_no.label("receipt_no"),
                models.OcrReceipt.country_code.label("country_code"),
                models.OcrReceipt.passport_no.label("passport_no"),
                models.OcrReceipt.purchaser.label("purchaser"),
                models.OcrReceipt.coordinate.label("coordinate_ocr"),
                models.OcrReceipt.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
            )
            .join(
                models.Image,
                models.Image.hash == models.OcrReceipt.hash_img,
                isouter=True,
            )
            .where(models.OcrReceipt.is_processed.is_(False))
            .order_by(models.OcrReceipt.id.desc())
            .offset(skip)
            .limit(limit)
        )
    else:
        # 완료: 검증 결과 기준
        stmt = (
            select(
                models.VerifiedReceipt.id.label("id"),
                models.VerifiedReceipt.dutyfree_company.label("dutyfree_company"),
                models.VerifiedReceipt.group_no.label("group_no"),
                models.VerifiedReceipt.receipt_no.label("receipt_no"),
                # 검증 테이블에는 국적 필드가 없으므로, 필요 시 확장 고려
                models.VerifiedReceipt.passport_no.label("passport_no"),
                models.VerifiedReceipt.name.label("purchaser"),
                models.VerifiedReceipt.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
                models.VerifiedReceipt.coordinate.label("coordinate_verified"),
                models.OcrReceipt.coordinate.label("coordinate_ocr"),
            )
            .join(
                models.Image,
                models.Image.hash == models.VerifiedReceipt.hash_img,
                isouter=True,
            )
            .join(
                models.OcrReceipt,
                models.OcrReceipt.hash_img == models.VerifiedReceipt.hash_img,
                isouter=True,
            )
            .where(models.VerifiedReceipt.is_verified.is_(True))
            .order_by(models.VerifiedReceipt.id.desc())
            .offset(skip)
            .limit(limit)
        )

    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.mappings().all()

    items: list[dict[str, Any]] = []
    for row in rows:
        coord = row.get("coordinate_verified") or row.get("coordinate_ocr") or {}
        image = {
            "hash_img": row.get("hash_img"),
            "path": row.get("image_path"),
            "coordinate": {
                "top": coord.get("top", 0),
                "bottom": coord.get("bottom", 0),
                "left": coord.get("left", 0),
                "right": coord.get("right", 0),
            }
            if isinstance(coord, dict)
            else None,
        }
        items.append(
            {
                "id": row.get("id"),
                "source": "verified" if is_completed else "ocr",
                "dutyfree_company": row.get("dutyfree_company"),
                "group_no": row.get("group_no"),
                "receipt_no": row.get("receipt_no"),
                "country_code": row.get("country_code"),
                "passport_no": row.get("passport_no"),
                "purchaser": row.get("purchaser"),
                "is_completed": is_completed,
                "image": image,
            }
        )

    return items


@router.get(
    "/data-mapping/passports",
    summary="여권 OCR/검증 리스트 조회",
    description="이미지 기반 여권 OCR/검증 데이터를 조회합니다. 기본은 미완료(OcrPassport.is_processed=False)만 반환합니다.",
)
@handle_http_error
async def list_passports_for_review(
    is_completed: bool = Query(
        False,
        description="작업 완료 여부. false=OCR 미처리(OcrPassport.is_processed=False), true=검증 완료(VerifiedPassport.is_verified=True)",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    이미지 기반 여권 OCR/검증 리스트를 조회한다.
    - is_completed=False: OcrPassport 기준, is_processed=False 인 행만 반환
    - is_completed=True: VerifiedPassport 기준, is_verified=True 인 행만 반환
    """
    schemas = _get_current_tenant_schemas(current_user)

    if not is_completed:
        # 미완료: OCR 원본 기준 (is_processed=False)
        stmt = (
            select(
                models.OcrPassport.id.label("id"),
                models.OcrPassport.country_code.label("country_code"),
                models.OcrPassport.passport_no.label("passport_no"),
                models.OcrPassport.name.label("name"),
                models.OcrPassport.coordinate.label("coordinate_ocr"),
                models.OcrPassport.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
            )
            .join(
                models.Image,
                models.Image.hash == models.OcrPassport.hash_img,
                isouter=True,
            )
            .where(models.OcrPassport.is_processed.is_(False))
            .order_by(models.OcrPassport.id.desc())
            .offset(skip)
            .limit(limit)
        )
    else:
        # 완료: 검증 결과 기준
        stmt = (
            select(
                models.VerifiedPassport.id.label("id"),
                models.VerifiedPassport.country_code.label("country_code"),
                models.VerifiedPassport.passport_no.label("passport_no"),
                models.VerifiedPassport.name.label("name"),
                models.VerifiedPassport.hash_img.label("hash_img"),
                models.Image.path.label("image_path"),
                models.VerifiedPassport.coordinate.label("coordinate_verified"),
                models.OcrPassport.coordinate.label("coordinate_ocr"),
            )
            .join(
                models.Image,
                models.Image.hash == models.VerifiedPassport.hash_img,
                isouter=True,
            )
            .join(
                models.OcrPassport,
                models.OcrPassport.hash_img == models.VerifiedPassport.hash_img,
                isouter=True,
            )
            .where(models.VerifiedPassport.is_verified.is_(True))
            .order_by(models.VerifiedPassport.id.desc())
            .offset(skip)
            .limit(limit)
        )

    result = await db.execute_query(stmt, schemas=schemas)
    rows = result.mappings().all()

    items: list[dict[str, Any]] = []
    for row in rows:
        coord = row.get("coordinate_verified") or row.get("coordinate_ocr") or {}
        image = {
            "hash_img": row.get("hash_img"),
            "path": row.get("image_path"),
            "coordinate": {
                "top": coord.get("top", 0),
                "bottom": coord.get("bottom", 0),
                "left": coord.get("left", 0),
                "right": coord.get("right", 0),
            }
            if isinstance(coord, dict)
            else None,
        }
        items.append(
            {
                "id": row.get("id"),
                "source": "verified" if is_completed else "ocr",
                "country_code": row.get("country_code"),
                "passport_no": row.get("passport_no"),
                "name": row.get("name"),
                "is_completed": is_completed,
                "image": image,
            }
        )

    return items


@router.get(
    "/data-mapping/image/{hash_img}",
    summary="데이터 매핑용 이미지 다운로드",
    description="현재 테넌트의 image 테이블과 테넌트 디렉터리를 기준으로 실제 이미지 파일을 찾아 반환합니다.",
)
@handle_http_error
async def get_data_mapping_image(
    hash_img: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    이미지 해시(hash_img)를 기준으로 테넌트 전용 이미지 파일을 찾아 반환한다.
    - 인증/테넌트 스키마는 get_current_tenant_admin 에서 보장
    - 파일 경로 구성:
      ROOT_DIR + tenant.dir_base + image.path
    """
    tenant_schema = _get_current_tenant_schema_from_user(current_user)

    # public.tenant 에서 현재 테넌트의 dir_base 조회
    stmt_tenant = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    result_tenant = await db.execute_query(stmt_tenant, schemas=["public"])
    tenant = result_tenant.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트 정보를 찾을 수 없습니다.",
        )

    # 테넌트 스키마에서 이미지 메타 조회
    schemas = [tenant_schema, "public"]
    stmt_image = select(models.Image).where(models.Image.hash == hash_img)
    result_image = await db.execute_query(stmt_image, schemas=schemas)
    image_row = result_image.scalar_one_or_none()
    if image_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지 메타데이터를 찾을 수 없습니다.",
        )

    root_dir = os.getenv("ROOT_DIR", "D:\\")
    base_root = Path(root_dir)
    tenant_root = base_root / tenant.dir_base

    relative_path = Path(getattr(image_row, "path", ""))
    file_path = tenant_root / relative_path

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지 파일을 찾을 수 없습니다.",
        )

    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return FileResponse(path=str(file_path), media_type=mime_type)


@router.get(
    "/data-mapping/image-details",
    summary="이미지 기반 영수증/여권 상세 조회",
    description="hash_img 를 기준으로 OCR/검증 영수증/여권 데이터를 조회합니다.",
)
@handle_http_error
async def get_data_mapping_details_by_image(
    hash_img: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    """
    하나의 이미지(hash_img)에 연결된 영수증/여권 OCR 및 검증 데이터를 조회한다.
    - receipt: VerifiedReceipt 가 있으면 우선, 없으면 OcrReceipt
    - passport: VerifiedPassport 가 있으면 우선, 없으면 OcrPassport
    """
    schemas = _get_current_tenant_schemas(current_user)

    # Receipt 쪽
    receipt_data: dict[str, Any] | None = None

    stmt_vr = (
        select(models.VerifiedReceipt)
        .where(
            models.VerifiedReceipt.hash_img == hash_img,
            models.VerifiedReceipt.is_verified.is_(True),
        )
        .order_by(models.VerifiedReceipt.db_updated_at.desc())
        .limit(1)
    )
    result_vr = await db.execute_query(stmt_vr, schemas=schemas)
    vr = result_vr.scalar_one_or_none()

    if vr is not None:
        receipt_data = {
            "source": "verified",
            "id": vr.id,
            "dutyfree_company": vr.dutyfree_company,
            "group_no": vr.group_no,
            "receipt_no": vr.receipt_no,
            "country_code": getattr(vr, "country_code", None),
            "passport_no": vr.passport_no,
            "purchaser": vr.name,
            "coordinate": vr.coordinate,
            "rotation": getattr(vr, "rotation", None),
        }
    else:
        stmt_or = (
            select(models.OcrReceipt)
            .where(models.OcrReceipt.hash_img == hash_img)
            .order_by(models.OcrReceipt.db_created_at.asc())
            .limit(1)
        )
        result_or = await db.execute_query(stmt_or, schemas=schemas)
        orow = result_or.scalar_one_or_none()
        if orow is not None:
            receipt_data = {
                "source": "ocr",
                "id": orow.id,
                "dutyfree_company": orow.dutyfree_company,
                "group_no": orow.group_no,
                "receipt_no": orow.receipt_no,
                "country_code": orow.country_code,
                "passport_no": orow.passport_no,
                "purchaser": orow.purchaser,
                "coordinate": orow.coordinate,
                "rotation": None,
            }

    # Passport 쪽
    passport_data: dict[str, Any] | None = None

    stmt_vp = (
        select(models.VerifiedPassport)
        .where(
            models.VerifiedPassport.hash_img == hash_img,
            models.VerifiedPassport.is_verified.is_(True),
        )
        .order_by(models.VerifiedPassport.db_updated_at.desc())
        .limit(1)
    )
    result_vp = await db.execute_query(stmt_vp, schemas=schemas)
    vp = result_vp.scalar_one_or_none()

    if vp is not None:
        passport_data = {
            "source": "verified",
            "id": vp.id,
            "country_code": vp.country_code,
            "passport_no": vp.passport_no,
            "name": vp.name,
            "coordinate": vp.coordinate,
            "rotation": getattr(vp, "rotation", None),
        }
    else:
        stmt_op = (
            select(models.OcrPassport)
            .where(models.OcrPassport.hash_img == hash_img)
            .order_by(models.OcrPassport.db_created_at.asc())
            .limit(1)
        )
        result_op = await db.execute_query(stmt_op, schemas=schemas)
        op = result_op.scalar_one_or_none()
        if op is not None:
            passport_data = {
                "source": "ocr",
                "id": op.id,
                "country_code": op.country_code,
                "passport_no": op.passport_no,
                "name": op.name,
                "coordinate": op.coordinate,
                "rotation": None,
            }

    return {
        "receipt": receipt_data,
        "passport": passport_data,
    }


@router.post("/users", summary="유저 추가", description="새로운 유저를 추가합니다.")
@handle_http_error
async def create_user(
    user_data: UserCreateRequest,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 추가"""
    # 유저 생성/조회는 현재 테넌트 스키마에서만 수행
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    schemas = [tenant_schema]

    # 이메일 중복 확인 (테넌트 스키마 한정)
    stmt = select(models.User).where(models.User.e_mail == user_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 유저 생성
    user_df = pd.DataFrame([{
        "name": user_data.name,
        "e_mail": user_data.e_mail,
        "password": hashed_password,
        "role": user_data.role.value,
        "department": user_data.department,
        "contact": user_data.contact,
        "is_active": False,  # 이메일 인증 전까지 비활성화
    }])
    
    await db.upsert_batch(table=models.User, data=user_df, schemas=schemas)
    
    # 생성된 유저 조회
    stmt = select(models.User).where(models.User.e_mail == user_data.e_mail)
    result = await db.execute_query(stmt, schemas=schemas)
    created_user = result.scalar_one_or_none()
    
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유저 생성 후 조회에 실패했습니다"
        )
    
    # 인증 토큰 생성 및 저장
    verification_token = verification_token_service.generate_token(user_data.e_mail)
    verification_token_service.save_token(
        user_data.e_mail,
        verification_token,
        created_user.id
    )
    
    # 인증 이메일 발송
    app_url = os.getenv("APP_URL", "http://localhost:5173")
    email_service.set_verification_email(
        receiver_email=user_data.e_mail,
        receiver_name=user_data.name,
        verification_token=verification_token,
        service_url=app_url,
    ).send(
        log_success=f"인증 이메일 발송 완료: {user_data.e_mail}",
        log_error=f"인증 이메일 발송 실패: {user_data.e_mail}",
    )
    
    return {
        "message": "유저가 추가되었습니다. 이메일을 확인하여 인증을 완료해주세요.",
        "user_id": created_user.id,
        "e_mail": user_data.e_mail
    }


@router.get("/users/{user_id}", summary="유저 상세 조회", description="특정 유저의 상세 정보를 조회합니다.")
@handle_http_error
async def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 상세 조회"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요
    
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )
    
    return {
        "id": user.id,
        "name": user.name,
        "e_mail": user.e_mail,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "department": user.department,
        "contact": user.contact,
        "is_active": user.is_active,
        "created_at": user.db_created_at,
        "updated_at": user.db_updated_at,
    }


@router.put("/users/{user_id}", summary="유저 수정", description="유저 정보를 수정합니다.")
@handle_http_error
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 수정"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요
    
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )
    
    # 업데이트할 데이터 준비
    update_data = {}
    if user_data.name is not None:
        update_data["name"] = user_data.name
    if user_data.e_mail is not None:
        update_data["e_mail"] = user_data.e_mail
    if user_data.role is not None:
        update_data["role"] = user_data.role.value
    if user_data.department is not None:
        update_data["department"] = user_data.department
    if user_data.contact is not None:
        update_data["contact"] = user_data.contact
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )
    
    # 업데이트 실행
    stmt = sql_update(models.User).where(models.User.id == user_id).values(**update_data)
    await db.execute_query(stmt, schemas=schemas)
    
    return {"message": "유저 정보가 수정되었습니다", "user_id": user_id}


@router.patch("/users/{user_id}/activation", summary="유저 활성 상태 변경", description="유저의 활성 상태를 설정합니다.")
@handle_http_error
async def user_activate(
    user_id: int,
    activation_data: UserActivationRequest,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 활성 상태 변경"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요
    
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )
    
    # 자기 자신 비활성화는 불가
    if user.id == current_user.id and not activation_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 비활성화할 수 없습니다"
        )

    stmt = sql_update(models.User).where(models.User.id == user_id).values(is_active=activation_data.is_active)
    await db.execute_query(stmt, schemas=schemas)
    
    return {
        "message": "유저가 활성화되었습니다" if activation_data.is_active else "유저가 비활성화되었습니다",
        "user_id": user_id,
        "is_active": activation_data.is_active,
    }


@router.delete("/users/{user_id}", summary="유저 삭제", description="유저를 물리적으로 삭제합니다.")
@handle_http_error
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 물리 삭제"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요

    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )

    receiver_email = (getattr(user, "e_mail", "") or "").strip()
    receiver_name = (getattr(user, "name", "") or "").strip() or receiver_email

    stmt = sql_delete(models.User).where(models.User.id == user_id)
    await db.execute_query(stmt, schemas=schemas)

    smtp_service = await get_db_smtp_email_service(db) or email_service
    sender_email = (getattr(smtp_service, "_sender", "") or "").strip()
    smtp_user = (getattr(smtp_service, "_user", "") or "").strip()
    smtp_password = (getattr(smtp_service, "_password", "") or "").strip()

    mail_sent = False
    if not sender_email or not smtp_user or not smtp_password or not _is_valid_email(sender_email):
        mail_notice = "유저 삭제는 완료되었지만 송신자 메일 계정이 유효하지 않아 확인 메일을 발송하지 못했습니다. 시스템 관리자에게 문의해 주세요."
    elif not _is_valid_email(receiver_email):
        mail_notice = "유저 삭제는 완료되었지만 수신자 메일 주소가 유효하지 않아 확인 메일을 발송하지 못했습니다."
    else:
        mail_sent = smtp_service.set_user_deletion_email(
            receiver_email=receiver_email,
            receiver_name=receiver_name,
        ).send(
            log_success=f"유저 삭제 확인 이메일 발송 완료: {receiver_email}",
            log_error=f"유저 삭제 확인 이메일 발송 실패: {receiver_email}",
        )
        if mail_sent:
            mail_notice = "유저 삭제가 완료되었고 삭제 확인 메일을 발송했습니다."
        else:
            mail_notice = "유저 삭제는 완료되었지만 확인 메일 발송에 실패했습니다."

    return {
        "message": "유저가 삭제되었습니다",
        "user_id": user_id,
        "mail_sent": mail_sent,
        "mail_notice": mail_notice,
    }


@router.post("/users/{user_id}/reset-password", summary="비밀번호 재설정", description="유저의 비밀번호를 재설정합니다.")
@handle_http_error
async def reset_password(
    user_id: int,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """비밀번호 재설정"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요
    
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )

    # 임시 비밀번호 생성 (영문 대/소문자 + 숫자 조합, 12자리)
    alphabet = string.ascii_letters + string.digits
    temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

    # 비밀번호 해싱
    hashed_password = get_password_hash(temp_password)
    
    # 비밀번호 업데이트
    stmt = sql_update(models.User).where(models.User.id == user_id).values(password=hashed_password)
    await db.execute_query(stmt, schemas=schemas)

    # 임시 비밀번호를 이메일로 발송
    # 우선 DB 기반 SMTP 계정 사용, 없으면 기본 email_service 사용
    smtp_service = await get_db_smtp_email_service(db) or email_service
    app_url = os.getenv("APP_URL", "http://localhost:5173")
    login_url = f"{app_url}/login"

    receiver_name = getattr(user, "name", None) or user.e_mail
    smtp_service.set_user_temp_password_email(
        receiver_email=user.e_mail,
        receiver_name=receiver_name,
        temp_password=temp_password,
        login_url=login_url,
    ).send(
        log_success=f"임시 비밀번호 이메일 발송 완료: {user.e_mail}",
        log_error=f"임시 비밀번호 이메일 발송 실패: {user.e_mail}",
    )
    
    return {"message": "임시 비밀번호가 등록된 이메일로 발송되었습니다", "user_id": user_id}


# 사용량 조회 API
@router.get("/usage", summary="전체 사용량 조회", description="테넌트의 전체 사용량을 조회합니다.")
@handle_http_error
async def get_usage(
    start_date: datetime | None = Query(None, description="시작 날짜"),
    end_date: datetime | None = Query(None, description="종료 날짜"),
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """전체 사용량 조회"""
    schemas = _get_current_tenant_schemas(current_user)
    # JWT에서 테넌트 스키마 정보는 이미 get_current_user에서 설정됨
    
    # 기본 기간 설정 (최근 30일)
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 각 테이블별 카운트 조회
    conditions = []
    if start_date:
        conditions.append(models.Image.db_created_at >= start_date)
    if end_date:
        conditions.append(models.Image.db_created_at <= end_date)
    
    # Image 카운트
    stmt = select(func.count(models.Image.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_images = result.scalar() or 0
    
    # OCR Passport 카운트
    stmt = select(func.count(models.OcrPassport.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_ocr_passport = result.scalar() or 0
    
    # OCR Receipt 카운트
    stmt = select(func.count(models.OcrReceipt.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_ocr_receipt = result.scalar() or 0
    
    # Verified Passport 카운트
    stmt = select(func.count(models.VerifiedPassport.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_verified_passport = result.scalar() or 0
    
    # Verified Receipt 카운트
    stmt = select(func.count(models.VerifiedReceipt.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_verified_receipt = result.scalar() or 0
    
    # Matched 카운트
    stmt = select(func.count(models.EDI_INFO.id))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_matched = result.scalar() or 0
    
    # LLM 토큰 합계
    stmt = select(func.sum(models.LlmUsage.token_total))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await db.execute_query(stmt, schemas=schemas)
    total_llm_tokens = result.scalar() or 0
    
    return {
        "total_images": total_images,
        "total_ocr_passport": total_ocr_passport,
        "total_ocr_receipt": total_ocr_receipt,
        "total_verified_passport": total_verified_passport,
        "total_verified_receipt": total_verified_receipt,
        "total_matched": total_matched,
        "total_llm_tokens": int(total_llm_tokens) if total_llm_tokens else 0,
        "period_start": start_date,
        "period_end": end_date,
    }


@router.post(
    "/data-mapping/receipts/verify",
    summary="영수증 검수/수정",
    description="OCR 또는 검증 데이터를 기반으로 영수증 정보를 검수/수정하고 VerifiedReceipt/OcrReceipt 상태를 반영합니다.",
)
@handle_http_error
async def verify_receipt(
    payload: ReceiptVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    source = (payload.source or "").lower()
    if source not in ("ocr", "verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source는 'ocr' 또는 'verified'만 가능합니다.",
        )

    ocr_row, verified_row = await _fetch_verify_source(
        db, schemas, source, payload.id,
        models.OcrReceipt, models.VerifiedReceipt,
        "지정된 OCR 영수증을 찾을 수 없습니다.",
        "지정된 검증 영수증을 찾을 수 없습니다.",
    )
    source_row = ocr_row or verified_row
    original_duty = getattr(source_row, "dutyfree_company", None)
    original_receipt_no = getattr(source_row, "receipt_no", None)
    original_country_code = getattr(source_row, "country_code", None)
    original_passport_no = getattr(source_row, "passport_no", None)
    original_name = getattr(source_row, "purchaser", None) or getattr(source_row, "name", None)

    dutyfree_company = (payload.dutyfree_company or "").strip()
    group_no = (payload.group_no or "").strip() or None
    receipt_no = (payload.receipt_no or "").strip()
    country_code = (payload.country_code or "").strip() or None
    passport_no = (payload.passport_no or "").strip() or None
    purchaser = (payload.purchaser or "").strip() or None

    is_corrected = any([
        dutyfree_company != (original_duty or ""),
        receipt_no != (original_receipt_no or ""),
        country_code != (original_country_code or ""),
        (passport_no or "") != (original_passport_no or ""),
        (purchaser or "") != (original_name or ""),
    ])

    common = _verified_row_common(
        current_user,
        getattr(source_row, "hash_img", None),
        payload.coordinate,
        payload.rotation,
        is_corrected,
        getattr(source_row, "uuid_batch", None) or "",
        getattr(source_row, "uuid_record", None) or "",
    )
    row = {
        "dutyfree_company": dutyfree_company,
        "group_no": group_no,
        "receipt_no": receipt_no,
        "country_code": country_code,
        "passport_no": passport_no,
        "name": purchaser,
        **common,
    }
    await db.upsert_batch(table=models.VerifiedReceipt, data=pd.DataFrame([row]), schemas=schemas)
    await _mark_ocr_processed_if_needed(db, schemas, ocr_row, models.OcrReceipt, current_user)

    return {
        "message": "영수증 정보가 검수/저장되었습니다.",
        "dutyfree_company": payload.dutyfree_company,
        "receipt_no": payload.receipt_no,
        "is_corrected": is_corrected,
    }


@router.post(
    "/data-mapping/passports/verify",
    summary="여권 검수/수정",
    description="OCR 또는 검증 데이터를 기반으로 여권 정보를 검수/수정하고 VerifiedPassport/OcrPassport 상태를 반영합니다.",
)
@handle_http_error
async def verify_passport(
    payload: PassportVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    source = (payload.source or "").lower()
    if source not in ("ocr", "verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source는 'ocr' 또는 'verified'만 가능합니다.",
        )
    if payload.passport_no and len(payload.passport_no) > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="여권 번호는 9자리 이하여야 합니다.",
        )

    ocr_row, verified_row = await _fetch_verify_source(
        db, schemas, source, payload.id,
        models.OcrPassport, models.VerifiedPassport,
        "지정된 OCR 여권 정보를 찾을 수 없습니다.",
        "지정된 검증 여권 정보를 찾을 수 없습니다.",
    )
    source_row = ocr_row or verified_row
    original_country = getattr(source_row, "country_code", None)
    original_passport_no = getattr(source_row, "passport_no", None)
    original_name = getattr(source_row, "name", None)

    country_code = (payload.country_code or "").strip()
    passport_no = (payload.passport_no or "").strip()
    name = (payload.name or "").strip() or None

    is_corrected = any([
        country_code != (original_country or ""),
        passport_no != (original_passport_no or ""),
        (name or "") != (original_name or ""),
    ])

    common = _verified_row_common(
        current_user,
        getattr(source_row, "hash_img", None),
        payload.coordinate,
        payload.rotation,
        is_corrected,
        getattr(source_row, "uuid_batch", None) or "",
        getattr(source_row, "uuid_record", None) or "",
    )
    row = {
        "country_code": country_code,
        "passport_no": passport_no,
        "name": name,
        **common,
    }
    await db.upsert_batch(table=models.VerifiedPassport, data=pd.DataFrame([row]), schemas=schemas)
    await _mark_ocr_processed_if_needed(db, schemas, ocr_row, models.OcrPassport, current_user)

    return {
        "message": "여권 정보가 검수/저장되었습니다.",
        "country_code": payload.country_code,
        "passport_no": payload.passport_no,
        "is_corrected": is_corrected,
    }


@router.get("/usage/users/{user_id}/tokens", summary="사용자별 토큰 사용량 조회", description="특정 사용자의 LLM 토큰 사용량을 조회합니다.")
@handle_http_error
async def get_user_token_usage(
    user_id: int,
    start_date: datetime | None = Query(None, description="시작 날짜"),
    end_date: datetime | None = Query(None, description="종료 날짜"),
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """사용자별 토큰 사용량 조회"""
    schemas = _get_current_tenant_schemas(current_user)
    # 사용자 존재 확인
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute_query(stmt, schemas=schemas)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 기본 기간 설정 (최근 30일)
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # LLM 사용량 조회 (hash_img로 사용자 추적은 어려우므로, 전체 사용량만 조회)
    # 실제로는 LlmUsage에 user_id 필드가 없으므로, 전체 사용량만 반환
    conditions = []
    if start_date:
        conditions.append(models.LlmUsage.db_created_at >= start_date)
    if end_date:
        conditions.append(models.LlmUsage.db_created_at <= end_date)
    
    stmt = select(
        func.sum(models.LlmUsage.token_input).label("token_input"),
        func.sum(models.LlmUsage.token_output).label("token_output"),
        func.sum(models.LlmUsage.token_total).label("token_total"),
        func.count(models.LlmUsage.id).label("usage_count")
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    result = await db.execute_query(stmt, schemas=schemas)
    row = result.first()
    
    return {
        "user_id": user_id,
        "user_name": user.name,
        "user_email": user.e_mail,
        "token_input": int(row.token_input) if row.token_input else 0,
        "token_output": int(row.token_output) if row.token_output else 0,
        "token_total": int(row.token_total) if row.token_total else 0,
        "usage_count": row.usage_count or 0,
        "period_start": start_date,
        "period_end": end_date,
    }


# 테넌트 정보 관리 API
@router.get("/info", summary="테넌트 정보 조회", description="테넌트 정보를 조회합니다.")
@handle_http_error
async def get_tenant_info(
    current_user: models.User = Depends(get_current_tenant_admin),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 정보 조회"""
    # TODO: current_user에서 tenant_id 가져오기
    # tenant = await tenant_repo.get_by_id(tenant_id)
    # return tenant 정보
    return {"message": "구현 예정"}


@router.put("/info", summary="테넌트 정보 수정", description="테넌트 정보를 수정합니다.")
@handle_http_error
async def update_tenant_info(
    current_user: models.User = Depends(get_current_tenant_admin),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """테넌트 정보 수정"""
    # TODO: 구현 예정
    return {"message": "구현 예정"}
