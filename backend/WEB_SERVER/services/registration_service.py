###########################################
# Module name : registration_service.py
# Module functions : 회원가입 및 이메일 인증 비즈니스 로직
# Written by : Cursor AI (with Yun Dae-young)
############################################

import os
from typing import Any, Dict

from fastapi import HTTPException, status
import pandas as pd

from DATABASE.dbms import DBManager
from DATABASE.repositories import UserRepository, TenantRepository
from WEB_SERVER.auth import get_password_hash
from WEB_SERVER.services.service_email import email_service, get_db_smtp_email_service
from WEB_SERVER.services.verification_token import verification_token_service


async def register_user_service(
    *,
    username: str,
    email: str,
    password: str,
    full_name: str | None,
    company_name: str,
    user_repo: UserRepository,
    tenant_repo: TenantRepository,
    db: DBManager,
) -> Dict[str, Any]:
    """
    회원가입 비즈니스 로직.
    """
    existing_email = await user_repo.get_by_email(email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다",
        )

    tenant = await tenant_repo.get_or_create(
        name=company_name,
        description=f"{company_name} 회사",
    )

    hashed_password = get_password_hash(password)

    user_df = pd.DataFrame(
        [
            {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "tenant_id": tenant.id,
                "is_active": False,
                "is_superuser": False,
            }
        ]
    )

    await user_repo.create(user_df)

    created_user = await user_repo.get_by_email(email)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 후 조회에 실패했습니다",
        )

    verification_token = verification_token_service.generate_token(email)
    verification_token_service.save_token(
        email,
        verification_token,
        created_user.id,  # type: ignore[attr-defined]
    )

    app_url = os.getenv("APP_URL", "http://localhost:5173")
    smtp_service = await get_db_smtp_email_service(db) or email_service

    smtp_service.set_verification_email(
        receiver_email=email,
        receiver_name=username,
        verification_token=verification_token,
        service_url=app_url,
    ).send(
        log_success=f"인증 이메일 발송 완료: {email}",
        log_error=f"인증 이메일 발송 실패: {email}",
    )

    return {
        "message": "회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.",
        "username": username,
        "email": email,
        "company_name": company_name,
    }


async def verify_email_service(
    *,
    token: str,
    email: str,
    user_repo: UserRepository,
    db: DBManager,
) -> Dict[str, Any]:
    """
    이메일 인증 비즈니스 로직.
    """
    token_data = verification_token_service.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 토큰이거나 만료된 토큰입니다",
        )

    if token_data["email"] != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="토큰과 이메일이 일치하지 않습니다",
        )

    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    if user.is_active:  # type: ignore[attr-defined]
        verification_token_service.delete_token(token)
        return {
            "message": "이미 인증이 완료된 계정입니다",
            "verified": True,
        }

    await user_repo.update(user.id, {"is_active": True})  # type: ignore[attr-defined]
    verification_token_service.delete_token(token)

    smtp_service = await get_db_smtp_email_service(db) or email_service

    smtp_service.set_welcome_email(
        receiver_email=email,
        receiver_name=user.username,  # type: ignore[attr-defined]
    ).send(
        log_success=f"환영 이메일 발송 완료: {email}",
        log_error=f"환영 이메일 발송 실패: {email}",
    )

    return {
        "message": "이메일 인증이 완료되었습니다",
        "verified": True,
        "email": email,
    }


