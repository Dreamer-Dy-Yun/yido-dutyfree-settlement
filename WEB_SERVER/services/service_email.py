###########################################
# Module name : email_service.py
# Module functions : 이메일 발송 서비스
# Written by : Cursor AI 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.01.30
# Updated at : 2026.02.19
# Instructed by : Yun Dae-young
# Supported by : Cursor AI
# Note : 회원가입 이메일 인증 발송
#        2026.01.30 : 최초 생성(Cursor AI)
#        2026.02.19 : 메서드 체이닝 패턴 적용 (set_xxx_email().send())
#                     이메일 생성과 발송 로직 분리, 공통 send() 메서드 추가
############################################

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from typing import Self

from sqlalchemy import select

from CUSTOMIZED.cust_logger import logger
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import ServiceAccount, ServiceAccountRole
from WEB_SERVER.services.email_company_templates import (
    build_company_approval_email,
    build_company_deletion_email,
    build_company_registration_email,
    build_company_rejection_email,
)
from WEB_SERVER.services.email_user_account_templates import (
    build_user_deletion_email,
    build_user_temp_password_email,
)
from WEB_SERVER.services.email_user_templates import (
    build_verification_email,
    build_welcome_email,
)


class EmailService:
    """이메일 발송 서비스"""
    
    def __init__(self,server: str, port: int, user: str, password: str, sender: str):
        self._server : str = server
        self._port : int = port
        self._user : str = user
        self._password : str = password
        self._sender : str = sender
        self.mime_msg : MIMEMultipart = None

    def send(self, mime_msg: MIMEMultipart = None, log_success : str = "이메일 발송 완료", log_error : str = "이메일 발송 실패") -> bool:
        """이메일 발송"""
        if mime_msg is None:
            mime_msg = self.mime_msg
        try:
            if not self._user:
                logger.warning("SMTP 사용자 이름이 없어 이메일을 발송할 수 없습니다.")
                return False
            if not self._password:
                logger.warning("SMTP 비밀번호가 없어 이메일을 발송할 수 없습니다.")
                return False
            if not mime_msg:
                logger.warning("이메일 메시지가 없어 이메일을 발송할 수 없습니다.")
                return False    
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self._server, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.send_message(mime_msg)
            
            logger.info(log_success)
            return True
            
        except Exception as e:
            # 예외 내용을 함께 로그로 남겨 디버깅에 활용
            logger.exception(f"{log_error}: {e}")
            return False
    
    def set_verification_email(
        self, 
        receiver_email: str, 
        receiver_name: str, 
        verification_token: str, 
        service_url: str, 
        expiration_hours: int = 12
        ) -> Self:
        """Build a verification email and keep the chainable EmailService API."""
        self.mime_msg = build_verification_email(
            sender=self._sender,
            receiver_email=receiver_email,
            receiver_name=receiver_name,
            verification_token=verification_token,
            service_url=service_url,
            expiration_hours=expiration_hours,
        )
        return self


    
    def set_welcome_email(self, receiver_email: str, receiver_name: str) -> Self:
        """Build a welcome email and keep the chainable EmailService API."""
        self.mime_msg = build_welcome_email(
            sender=self._sender,
            receiver_email=receiver_email,
            receiver_name=receiver_name,
        )
        return self


    def set_company_registration_email(
        self,
        receiver_email: str,
        company_name: str,
        business_no: str | None = None,
        contact: str | None = None,
    ) -> Self:
        """Build a company registration email and keep the chainable EmailService API."""
        self.mime_msg = build_company_registration_email(
            sender=self._sender,
            receiver_email=receiver_email,
            company_name=company_name,
            business_no=business_no,
            contact=contact,
        )
        return self

    def set_company_approval_email(
        self,
        receiver_email: str,
        company_name: str,
        login_id: str,
        login_url: str,
        temp_password: str,
        business_no: str | None = None,
    ) -> Self:
        """Build a company approval email and keep the chainable EmailService API."""
        self.mime_msg = build_company_approval_email(
            sender=self._sender,
            receiver_email=receiver_email,
            company_name=company_name,
            login_id=login_id,
            login_url=login_url,
            temp_password=temp_password,
            business_no=business_no,
        )
        return self

    def set_user_temp_password_email(
        self,
        receiver_email: str,
        receiver_name: str,
        temp_password: str,
        login_url: str,
    ) -> Self:
        """Build a user temporary password email and keep the chainable API."""
        self.mime_msg = build_user_temp_password_email(
            sender=self._sender,
            receiver_email=receiver_email,
            receiver_name=receiver_name,
            temp_password=temp_password,
            login_url=login_url,
        )
        return self

    def set_user_deletion_email(
        self,
        receiver_email: str,
        receiver_name: str,
    ) -> Self:
        """Build a user deletion email and keep the chainable API."""
        self.mime_msg = build_user_deletion_email(
            sender=self._sender,
            receiver_email=receiver_email,
            receiver_name=receiver_name,
        )
        return self

    def set_company_rejection_email(
        self,
        receiver_email: str,
        company_name: str,
        reason: str,
        business_no: str | None = None,
    ) -> Self:
        """Build a company rejection email and keep the chainable API."""
        self.mime_msg = build_company_rejection_email(
            sender=self._sender,
            receiver_email=receiver_email,
            company_name=company_name,
            reason=reason,
            business_no=business_no,
        )
        return self

    def set_company_deletion_email(
        self,
        receiver_email: str,
        company_name: str,
        reason: str,
        business_no: str | None = None,
    ) -> Self:
        """Build a company deletion email and keep the chainable API."""
        self.mime_msg = build_company_deletion_email(
            sender=self._sender,
            receiver_email=receiver_email,
            company_name=company_name,
            reason=reason,
            business_no=business_no,
        )
        return self

# 전역 인스턴스 (환경변수에서 설정 읽음)
email_service = EmailService(
    server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    port=int(os.getenv("SMTP_PORT", "587")),
    user=os.getenv("SMTP_USER", ""),
    password=os.getenv("SMTP_PASSWORD", ""),
    sender=os.getenv("SMTP_SENDER", os.getenv("SMTP_USER", ""))
)


async def get_db_smtp_email_service(db: DBManager) -> EmailService | None:
    """
    DB에서 role='smtp_sender' 이고 is_active=True 인 ServiceAccount를 하나 조회해
    해당 계정 정보를 사용해 EmailService 인스턴스를 생성합니다.

    서버/포트는 환경변수(SMTP_SERVER/SMTP_PORT)를 그대로 사용하고,
    사용자/비밀번호/발신자(sender)는 ServiceAccount의 e_mail/password를 사용합니다.
    """
    try:
        schemas = ["public"]

        stmt = (
            select(ServiceAccount)
            .where(
                ServiceAccount.role == ServiceAccountRole.SMTP_SENDER.value,
                ServiceAccount.is_active == True,
            )
            .limit(1)
        )
        result = await db.execute_query(stmt, schemas=schemas)
        account: ServiceAccount | None = result.scalar_one_or_none()

        if not account:
            logger.warning("활성화된 SMTP 송신 계정(ServiceAccount, role='smtp_sender')을 찾지 못했습니다.")
            return None

        return EmailService(
            server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", "587")),
            user=account.e_mail,
            password=account.password,
            sender=account.e_mail,
        )
    except Exception as e:
        logger.exception(f"DB 기반 SMTP 송신 계정 생성 실패: {e}")
        return None
