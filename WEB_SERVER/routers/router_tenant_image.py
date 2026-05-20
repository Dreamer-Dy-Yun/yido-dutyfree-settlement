from typing import Any
import mimetypes
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, select

from WEB_SERVER.auth.dependencies import get_current_user
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.tenant_helpers import (
    _get_current_tenant_schema_from_user,
    _get_current_tenant_schemas,
)
from WEB_SERVER.services.service_image_ocr import run_image_ocr_background
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_zip_processor import ZipProcessor

from DATABASE import models
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import Tenant as PublicTenant
import pandas as pd

router = APIRouter()


async def _get_public_tenant(tenant_schema: str, db: DBManager) -> PublicTenant:
    stmt = select(PublicTenant).where(PublicTenant.schema_name == tenant_schema)
    result = await db.execute_query(stmt, schemas=["public"])
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant information was not found.",
        )
    return tenant


def _get_tenant_root(tenant: PublicTenant) -> Path:
    root_dir = os.getenv("ROOT_DIR", "D:\\")
    return Path(root_dir) / tenant.dir_base


@router.post("/data-mapping/image-upload")
@handle_http_error
async def upload_image_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image ZIP file"),
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image upload only accepts ZIP(.zip) files.",
        )

    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    tenant = await _get_public_tenant(tenant_schema, db)

    zip_dir_name = os.getenv("ZIP_ROOT", "zip")
    img_dir_name = os.getenv("IMG_ROOT", "img")
    tenant_root = _get_tenant_root(tenant)
    zip_root = tenant_root / zip_dir_name
    img_root = tenant_root / img_dir_name

    zip_root.mkdir(parents=True, exist_ok=True)
    img_root.mkdir(parents=True, exist_ok=True)

    upload_id = uuid.uuid4().hex
    safe_name = Path(filename).name
    zip_path = zip_root / f"{upload_id}_{safe_name}"

    try:
        with zip_path.open("wb") as dst:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save ZIP file: {exc}",
        ) from exc

    try:
        zip_processor = ZipProcessor(zip_path).to_files(
            dir_dest_root=tenant_root,
            dir_dest_sub=Path(img_dir_name),
            allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
            ignore_inner_directory=True,
            set_hash_as_file_name=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract image files: {exc}",
        ) from exc

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
            detail="No supported image files were found in the ZIP.",
        )

    try:
        upsert_result = await db.upsert_batch(
            table=models.Image,
            data=pd.DataFrame(image_rows).drop_duplicates(subset=["hash"], keep="last"),
            schemas=_get_current_tenant_schemas(current_user),
        )
        rows_upserted = int(upsert_result["cnt_success_rows"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image metadata: {exc}",
        ) from exc

    background_tasks.add_task(run_image_ocr_background, tenant_schema, "public")
    return {
        "message": "Image ZIP upload, extraction, metadata upsert, and OCR background start completed.",
        "filename": filename,
        "upload_id": upload_id,
        "rows_upserted": rows_upserted,
    }


@router.get("/data-mapping/image-ocr-progress")
@handle_http_error
async def get_image_ocr_progress(
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)

    total_stmt = select(func.count(models.Image.id)).where(models.Image.exists == True)
    total = (await db.execute_query(total_stmt, schemas=schemas)).scalar() or 0

    processing_stmt = select(func.count(models.Image.id)).where(
        and_(models.Image.exists == True, models.Image.is_processing == True)
    )
    processing = (await db.execute_query(processing_stmt, schemas=schemas)).scalar() or 0

    done_stmt = select(func.count(models.Image.id)).where(
        and_(models.Image.exists == True, models.Image.is_processed == True)
    )
    done = (await db.execute_query(done_stmt, schemas=schemas)).scalar() or 0

    pending = max(total - processing - done, 0)
    return {
        "total": int(total),
        "processing": int(processing),
        "done": int(done),
        "pending": int(pending),
        "progress_percent": round((done / total) * 100, 2) if total > 0 else 0.0,
    }


@router.get("/data-mapping/image/{hash_img}")
@handle_http_error
async def get_data_mapping_image(
    hash_img: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    tenant_schema = _get_current_tenant_schema_from_user(current_user)
    tenant = await _get_public_tenant(tenant_schema, db)

    image_stmt = select(models.Image).where(models.Image.hash == hash_img)
    image_result = await db.execute_query(image_stmt, schemas=[tenant_schema, "public"])
    image_row = image_result.scalar_one_or_none()
    if image_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image metadata was not found.",
        )

    file_path = _get_tenant_root(tenant) / Path(getattr(image_row, "path", ""))
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file was not found.",
        )

    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return FileResponse(path=str(file_path), media_type=mime_type)


@router.get("/data-mapping/image-details")
@handle_http_error
async def get_data_mapping_details_by_image(
    hash_img: str,
    current_user: models.User = Depends(get_current_user),
    db: DBManager = Depends(get_db_manager),
):
    schemas = _get_current_tenant_schemas(current_user)
    receipt_data: dict[str, Any] | None = None
    passport_data: dict[str, Any] | None = None

    verified_receipt_stmt = (
        select(models.VerifiedReceipt)
        .where(models.VerifiedReceipt.hash_img == hash_img, models.VerifiedReceipt.is_verified.is_(True))
        .order_by(models.VerifiedReceipt.db_updated_at.desc())
        .limit(1)
    )
    verified_receipt = (await db.execute_query(verified_receipt_stmt, schemas=schemas)).scalar_one_or_none()

    if verified_receipt is not None:
        receipt_data = {
            "source": "verified",
            "id": verified_receipt.id,
            "dutyfree_company": verified_receipt.dutyfree_company,
            "group_no": verified_receipt.group_no,
            "receipt_no": verified_receipt.receipt_no,
            "country_code": getattr(verified_receipt, "country_code", None),
            "passport_no": verified_receipt.passport_no,
            "purchaser": verified_receipt.name,
            "coordinate": verified_receipt.coordinate,
            "rotation": getattr(verified_receipt, "rotation", None),
        }
    else:
        ocr_receipt_stmt = (
            select(models.OcrReceipt)
            .where(models.OcrReceipt.hash_img == hash_img)
            .order_by(models.OcrReceipt.db_created_at.asc())
            .limit(1)
        )
        ocr_receipt = (await db.execute_query(ocr_receipt_stmt, schemas=schemas)).scalar_one_or_none()
        if ocr_receipt is not None:
            receipt_data = {
                "source": "ocr",
                "id": ocr_receipt.id,
                "dutyfree_company": ocr_receipt.dutyfree_company,
                "group_no": ocr_receipt.group_no,
                "receipt_no": ocr_receipt.receipt_no,
                "country_code": ocr_receipt.country_code,
                "passport_no": ocr_receipt.passport_no,
                "purchaser": ocr_receipt.purchaser,
                "coordinate": ocr_receipt.coordinate,
                "rotation": None,
            }

    verified_passport_stmt = (
        select(models.VerifiedPassport)
        .where(models.VerifiedPassport.hash_img == hash_img, models.VerifiedPassport.is_verified.is_(True))
        .order_by(models.VerifiedPassport.db_updated_at.desc())
        .limit(1)
    )
    verified_passport = (await db.execute_query(verified_passport_stmt, schemas=schemas)).scalar_one_or_none()

    if verified_passport is not None:
        passport_data = {
            "source": "verified",
            "id": verified_passport.id,
            "country_code": verified_passport.country_code,
            "passport_no": verified_passport.passport_no,
            "name": verified_passport.name,
            "coordinate": verified_passport.coordinate,
            "rotation": getattr(verified_passport, "rotation", None),
        }
    else:
        ocr_passport_stmt = (
            select(models.OcrPassport)
            .where(models.OcrPassport.hash_img == hash_img)
            .order_by(models.OcrPassport.db_created_at.asc())
            .limit(1)
        )
        ocr_passport = (await db.execute_query(ocr_passport_stmt, schemas=schemas)).scalar_one_or_none()
        if ocr_passport is not None:
            passport_data = {
                "source": "ocr",
                "id": ocr_passport.id,
                "country_code": ocr_passport.country_code,
                "passport_no": ocr_passport.passport_no,
                "name": ocr_passport.name,
                "coordinate": ocr_passport.coordinate,
                "rotation": None,
            }

    return {"receipt": receipt_data, "passport": passport_data}
