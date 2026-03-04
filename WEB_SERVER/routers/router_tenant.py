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
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func, and_, update as sql_update
from sqlalchemy.sql import Select

from WEB_SERVER.auth.dependencies import get_current_tenant_admin
from WEB_SERVER.routers.settings import get_db_manager, get_tenant_repository
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.service_image_ocr import run_image_ocr_background
from WEB_SERVER.services.verification_token import verification_token_service
from WEB_SERVER.routers.settings import get_user_repository
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_zip_processor import ZipProcessor
from PROCESSOR_DATA.parsers.edi_lotte import EdiLotte
from PROCESSOR_DATA.parsers.edi_silla import EdiSilla
from PROCESSOR_DATA.patch import fix_invalid_datetime_in_xlsx_bytes

from DATABASE import models
from DATABASE.models.tenant_model import UserRole
from DATABASE.models.public_model import Tenant as PublicTenant
from DATABASE.repositories.authorities import UserRepository, TenantRepository
from DATABASE.dbms import DBManager
import pandas as pd

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
    current_user: models.User = Depends(get_current_tenant_admin),
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
        rows_upserted = await db.batch_upsert_dataframe(table, df_parsed, schemas=schemas)
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
    "/data-mapping/image-upload",
    summary="이미지 ZIP 업로드",
    description="데이터 매핑용 이미지 ZIP 파일 업로드 엔드포인트.",
)
@handle_http_error
async def upload_image_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="이미지 ZIP 파일"),
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """
    이미지 ZIP 업로드용 엔드포인트입니다.
    - 확장자가 .zip 인지 검증
    - 토큰에서 tenant_schema를 읽어 해당 테넌트의 루트 디렉터리 조회
    - .env 의 ROOT_DIR + 테넌트 전용 path_root + \"zip\" 하위에 ZIP 파일 저장
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

    # public.tenant 에서 현재 테넌트의 path_root 조회
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

    # path_root 는 테넌트별 루트 (상대/절대 여부는 설정에 따름)
    tenant_root = base_root / tenant.path_root
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
            }
        )

    if not image_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP 내에서 처리 가능한 이미지 파일을 찾지 못했습니다.",
        )

    df_images = pd.DataFrame(image_rows).drop_duplicates(subset=["hash"], keep="last")
    image_hashes = df_images["hash"].astype(str).tolist()
    try:
        rows_upserted = await db.batch_upsert_dataframe(models.Image, df_images, schemas=_get_current_tenant_schemas(current_user))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 메타데이터 저장에 실패했습니다: {e}",
        ) from e

    # OCR 비동기 백그라운드 작업 시작 (재시도 없음, 상태는 DB 컬럼으로 관리)
    background_tasks.add_task(
        run_image_ocr_background,
        tenant_schema,
        image_hashes,
    )

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
    current_user: models.User = Depends(get_current_tenant_admin),
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


@router.post("/users", summary="유저 추가", description="새로운 유저를 추가합니다.")
@handle_http_error
async def create_user(
    user_data: UserCreateRequest,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 추가"""
    schemas = _get_current_tenant_schemas(current_user)
    # TODO: 스키마 전환 로직 추가 필요
    
    # 이메일 중복 확인
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
    
    await db.upsert_dataframe(models.User, user_df, schemas=schemas)
    
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
        service_url=app_url
    ).send(log=f"인증 이메일 발송 완료: {user_data.e_mail}")
    
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


@router.delete("/users/{user_id}", summary="유저 삭제/비활성화", description="유저를 삭제하거나 비활성화합니다.")
@handle_http_error
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_tenant_admin),
    db: DBManager = Depends(get_db_manager),
):
    """유저 삭제/비활성화"""
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
    
    # 자기 자신은 삭제 불가
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )
    
    # 비활성화 처리 (실제 삭제는 하지 않음)
    stmt = sql_update(models.User).where(models.User.id == user_id).values(is_active=False)
    await db.execute_query(stmt, schemas=schemas)
    
    return {"message": "유저가 비활성화되었습니다", "user_id": user_id}


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
    stmt = select(func.count(models.Matched.id))
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
