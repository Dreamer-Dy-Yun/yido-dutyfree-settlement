###########################################
# Module name : email_service.py
# Module functions : 이메일 발송 서비스
# Written by : Yun Dae-young 
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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Self

from sqlalchemy import select

from CUSTOMIZED.cust_logger import logger
from DATABASE.dbms import DBManager
from DATABASE.models.public_model import ServiceAccount, ServiceAccountRole


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
        """인증 이메일 생성"""
        verification_url = f"{service_url}/verify-email?token={verification_token}&email={receiver_email}"
        
        # HTML 이메일 본문
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9fafb;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #6b7280;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>구매대행B2C</h1>
                </div>
                <div class="content">
                    <h2>이메일 인증</h2>
                    <p>안녕하세요, <strong>{receiver_name}</strong>님!</p>
                    <p>구매대행B2C에 가입해 주셔서 감사합니다.</p>
                    <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요:</p>
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">이메일 인증하기</a>
                    </div>
                    <p>또는 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
                    <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                    <p style="color: #dc2626; font-size: 14px;">
                        ⚠️ 이 링크는 {expiration_hours}시간 후 만료됩니다.
                    </p>
                </div>
                <div class="footer">
                    <p>이 이메일은 자동으로 발송되었습니다. 회신하지 마세요.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 텍스트 이메일 본문 (HTML을 지원하지 않는 클라이언트용)
        text_body = f"""
        구매대행B2C 이메일 인증
        
        안녕하세요, {receiver_name}님!
        
        구매대행B2C에 가입해 주셔서 감사합니다.
        아래 링크를 클릭하여 이메일 인증을 완료해주세요:
        
        {verification_url}
        
        이 링크는 {expiration_hours}시간 후 만료됩니다.
        
        이 이메일은 자동으로 발송되었습니다. 회신하지 마세요.
        """
        
        # 메시지 생성
        msg : MIMEMultipart = MIMEMultipart('alternative')
        msg['Subject'] = '[구매대행B2C] 이메일 인증을 완료해주세요'
        msg['From'] = self._sender
        msg['To'] = receiver_email
        
        # 본문 추가
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg

        return self

    
    def set_welcome_email(self, receiver_email: str, receiver_name: str) -> Self:
        """환영 이메일 생성"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9fafb;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>구매대행B2C</h1>
                </div>
                <div class="content">
                    <h2>환영합니다!</h2>
                    <p>안녕하세요, <strong>{receiver_name}</strong>님!</p>
                    <p>이메일 인증이 완료되었습니다.</p>
                    <p>이제 구매대행B2C의 모든 서비스를 이용하실 수 있습니다.</p>
                    <p>감사합니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        구매대행B2C 환영합니다!
        
        안녕하세요, {receiver_name}님!
        
        이메일 인증이 완료되었습니다.
        이제 구매대행B2C의 모든 서비스를 이용하실 수 있습니다.
        
        감사합니다.
        """
        
        # 메시지 생성
        msg : MIMEMultipart = MIMEMultipart('alternative')
        msg['Subject'] = '[구매대행B2C] 이메일 인증이 완료되었습니다'
        msg['From'] = self._sender
        msg['To'] = receiver_email
        
        # 본문 추가
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        self.mime_msg = msg
        return self

    def set_company_registration_email(
        self,
        receiver_email: str,
        company_name: str,
        business_no: str | None = None,
        contact: str | None = None,
    ) -> Self:
        """
        신규 회사 등록 접수 안내 이메일 생성
        - 수신자: 회사 대표 이메일(회사 등록 시 입력한 이메일)
        """
        html_body = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>신규 회사 등록 신청 안내</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
                    background-color: #f3f4f6;
                    color: #111827;
                    line-height: 1.6;
                    margin: 0;
                    padding: 24px 0;
                }}
                .container {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
                }}
                .header {{
                    background: radial-gradient(circle at top left, #4f46e5, #7c3aed);
                    color: #ffffff;
                    padding: 28px 32px 24px 32px;
                }}
                .header-title {{
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0 0 6px 0;
                }}
                .header-subtitle {{
                    font-size: 13px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 28px 32px 24px 32px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin: 0 0 14px 0;
                }}
                .paragraph {{
                    font-size: 14px;
                    color: #4b5563;
                    margin: 0 0 10px 0;
                }}
                .section-title {{
                    font-size: 14px;
                    font-weight: 600;
                    margin: 24px 0 10px 0;
                    color: #111827;
                }}
                .info-card {{
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #eef2ff 100%);
                    padding: 14px 16px;
                    font-size: 13px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}
                .info-label {{
                    color: #6b7280;
                    margin-right: 6px;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #111827;
                    text-align: right;
                    max-width: 65%;
                }}
                .highlight {{
                    margin-top: 12px;
                    font-size: 12px;
                    color: #4b5563;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(to right, transparent, #e5e7eb, transparent);
                    margin: 24px 0 16px 0;
                }}
                .footer {{
                    padding: 12px 32px 20px 32px;
                    font-size: 11px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                    text-align: center;
                    background-color: #f9fafb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <p class="header-title">신규 회사 등록 신청이 접수되었습니다</p>
                    <p class="header-subtitle">구매대행B2C 기업용 서비스</p>
                </div>
                <div class="content">
                    <p class="greeting">안녕하세요.</p>
                    <p class="paragraph">
                        <strong>{company_name}</strong> 회사의 구매대행B2C 서비스 이용 신청이 정상적으로 접수되었습니다.
                    </p>
                    <p class="paragraph">
                        내부 검토 및 시스템 준비가 완료되는 대로, 서비스 이용을 위한 세부 안내를 별도의 채널을 통해 전달드릴 예정입니다.
                    </p>

                    <p class="section-title">신청 정보</p>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label">회사명</span>
                            <span class="info-value">{company_name}</span>
                        </div>
                        {f'''
                        <div class="info-row">
                            <span class="info-label">사업자등록번호</span>
                            <span class="info-value">{business_no}</span>
                        </div>
                        ''' if business_no else ''}
                        {f'''
                        <div class="info-row">
                            <span class="info-label">대표 연락처</span>
                            <span class="info-value">{contact}</span>
                        </div>
                        ''' if contact else ''}
                        <p class="highlight">
                            위 정보는 회사 등록 및 초기 세팅을 위한 참고용으로만 사용되며,
                            실제 관리자 계정 정보는 이후 별도의 절차를 통해 설정하게 됩니다.
                        </p>
                    </div>

                    <div class="divider"></div>

                    <p class="paragraph" style="font-size: 12px;">
                        본 메일은 회사 등록 신청이 정상적으로 접수되었음을 알려드리기 위한 안내 메일입니다.
                        서비스 이용 시작과 관련된 상세한 일정과 안내는 추후 다시 안내드리겠습니다.
                    </p>
                </div>
                <div class="footer">
                    이 이메일은 발신 전용으로 발송되었습니다. 답장을 통해 문의하실 수 없으며,<br/>
                    별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
            [구매대행B2C] 신규 회사 등록 신청이 접수되었습니다.

            안녕하세요.

            [{company_name}] 회사의 구매대행B2C 서비스 이용 신청이 정상적으로 접수되었습니다.

            신청 정보
            - 회사명: {company_name}
            {f"- 사업자등록번호: {business_no}" if business_no else ""}
            {f"- 대표 연락처: {contact}" if contact else ""}

            위 정보는 회사 등록 및 초기 세팅을 위한 참고용으로만 사용되며,
            실제 관리자 계정 정보는 이후 별도의 절차를 통해 설정하게 됩니다.

            본 메일은 회사 등록 신청이 정상적으로 접수되었음을 알려드리기 위한 안내 메일입니다.
            서비스 이용 시작과 관련된 상세한 일정과 안내는 추후 별도 채널을 통해 안내드리겠습니다.
            """

        msg: MIMEMultipart = MIMEMultipart("alternative")
        msg["Subject"] = "[구매대행B2C] 신규 회사 등록 신청이 접수되었습니다"
        msg["From"] = self._sender
        msg["To"] = receiver_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg
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
        """
        회사 등록 승인 안내 이메일 생성
        - 수신자: 회사 대표 이메일
        - 내용: 승인 결과 + 초기 관리자 로그인 계정(ID) + 임시 비밀번호 + 로그인 페이지 안내
        """
        html_body = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>회사 등록 승인 안내</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
                    background-color: #f3f4f6;
                    color: #111827;
                    line-height: 1.6;
                    margin: 0;
                    padding: 24px 0;
                }}
                .container {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
                }}
                .header {{
                    background: radial-gradient(circle at top left, #10b981, #059669);
                    color: #ffffff;
                    padding: 28px 32px 24px 32px;
                }}
                .header-title {{
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0 0 6px 0;
                }}
                .header-subtitle {{
                    font-size: 13px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 28px 32px 24px 32px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin: 0 0 14px 0;
                }}
                .paragraph {{
                    font-size: 14px;
                    color: #4b5563;
                    margin: 0 0 10px 0;
                }}
                .section-title {{
                    font-size: 14px;
                    font-weight: 600;
                    margin: 24px 0 10px 0;
                    color: #111827;
                }}
                .info-card {{
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #ecfdf5 100%);
                    padding: 14px 16px;
                    font-size: 13px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}
                .info-label {{
                    color: #6b7280;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #111827;
                    text-align: right;
                    max-width: 65%;
                }}
                .login-button {{
                    display: inline-block;
                    margin-top: 16px;
                    padding: 10px 20px;
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 999px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                .highlight {{
                    margin-top: 12px;
                    font-size: 12px;
                    color: #4b5563;
                }}
                .footer {{
                    padding: 12px 32px 20px 32px;
                    font-size: 11px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                    text-align: center;
                    background-color: #f9fafb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <p class="header-title">회사 등록이 승인되었습니다</p>
                    <p class="header-subtitle">구매대행B2C 기업용 서비스</p>
                </div>
                <div class="content">
                    <p class="greeting">안녕하세요.</p>
                    <p class="paragraph">
                        <strong>{company_name}</strong> 회사의 구매대행B2C 서비스 이용 신청이 승인되었습니다.
                    </p>
                    <p class="paragraph">
                        이제 아래의 초기 관리자 계정으로 로그인하신 후, 프로필과 비밀번호를 설정하시면 서비스를 이용하실 수 있습니다.
                    </p>

                    <p class="section-title">회사 정보</p>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label">회사명</span>
                            <span class="info-value">{company_name}</span>
                        </div>
                        {f'''
                        <div class="info-row">
                            <span class="info-label">사업자등록번호</span>
                            <span class="info-value">{business_no}</span>
                        </div>
                        ''' if business_no else ''}
                    </div>

                    <p class="section-title">로그인 정보</p>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label">로그인 페이지</span>
                            <span class="info-value"><a href="{login_url}" target="_blank" rel="noopener noreferrer">{login_url}</a></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">초기 관리자 계정 ID</span>
                            <span class="info-value">{login_id}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">임시 비밀번호</span>
                            <span class="info-value" style="font-family: monospace; font-size: 14px; color: #dc2626; font-weight: 600;">{temp_password}</span>
                        </div>
                        <p class="highlight">
                            최초 로그인 후 반드시 비밀번호와 관리자 정보를 변경해 주시기 바랍니다.
                        </p>
                    </div>

                    <a href="{login_url}" class="login-button" target="_blank" rel="noopener noreferrer">
                        로그인 페이지로 이동
                    </a>

                    <p class="paragraph" style="font-size: 12px; margin-top: 18px;">
                        만약 본 메일이 잘못 수신되었다고 판단되면, 회신하지 마시고 별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.
                    </p>
                </div>
                <div class="footer">
                    이 이메일은 발신 전용으로 발송되었습니다. 답장을 통해 문의하실 수 없으며,<br/>
                    별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
            [구매대행B2C] 회사 등록이 승인되었습니다.

            안녕하세요.

            [{company_name}] 회사의 구매대행B2C 서비스 이용 신청이 승인되었습니다.

            회사 정보
            - 회사명: {company_name}
            {f"- 사업자등록번호: {business_no}" if business_no else ""}

            로그인 정보
            - 로그인 페이지: {login_url}
            - 초기 관리자 계정 ID: {login_id}
            - 임시 비밀번호: {temp_password}

            최초 로그인 후 반드시 비밀번호와 관리자 정보를 변경해 주시기 바랍니다.

            만약 본 메일이 잘못 수신되었다고 판단되면, 회신하지 마시고
            별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.
            """

        msg: MIMEMultipart = MIMEMultipart("alternative")
        msg["Subject"] = "[구매대행B2C] 회사 등록이 승인되었습니다"
        msg["From"] = self._sender
        msg["To"] = receiver_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg
        return self

    def set_user_temp_password_email(
        self,
        receiver_email: str,
        receiver_name: str,
        temp_password: str,
        login_url: str,
    ) -> Self:
        """
        테넌트 사용자 임시 비밀번호 발급 이메일 생성
        - 수신자: 개별 사용자 이메일
        - 내용: 임시 비밀번호 + 로그인 페이지 안내
        """
        html_body = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>임시 비밀번호 안내</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
                    background-color: #f3f4f6;
                    color: #111827;
                    line-height: 1.6;
                    margin: 0;
                    padding: 24px 0;
                }}
                .container {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
                }}
                .header {{
                    background: radial-gradient(circle at top left, #2563eb, #4f46e5);
                    color: #ffffff;
                    padding: 28px 32px 24px 32px;
                }}
                .header-title {{
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0 0 6px 0;
                }}
                .header-subtitle {{
                    font-size: 13px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 28px 32px 24px 32px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin: 0 0 14px 0;
                }}
                .paragraph {{
                    font-size: 14px;
                    color: #4b5563;
                    margin: 0 0 10px 0;
                }}
                .info-card {{
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #dbeafe 100%);
                    padding: 14px 16px;
                    font-size: 13px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}
                .info-label {{
                    color: #6b7280;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #111827;
                    text-align: right;
                    max-width: 65%;
                }}
                .temp-password {{
                    font-family: monospace;
                    font-size: 14px;
                    color: #dc2626;
                    font-weight: 600;
                }}
                .login-button {{
                    display: inline-block;
                    margin-top: 16px;
                    padding: 10px 20px;
                    background: #ffffff;
                    color: #2563eb;
                    text-decoration: none;
                    border-radius: 999px;
                    font-size: 13px;
                    font-weight: 600;
                    border: 2px solid;
                    border-image: linear-gradient(135deg, #2563eb, #4f46e5) 1;
                }}
                .footer {{
                    padding: 12px 32px 20px 32px;
                    font-size: 11px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                    text-align: center;
                    background-color: #f9fafb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <p class="header-title">임시 비밀번호가 발급되었습니다</p>
                    <p class="header-subtitle">구매대행B2C 계정 보안 안내</p>
                </div>
                <div class="content">
                    <p class="greeting">안녕하세요, {receiver_name} 님</p>
                    <p class="paragraph">
                        테넌트 관리자에 의해 비밀번호 재설정 요청이 처리되었습니다.
                        아래의 임시 비밀번호로 로그인하신 후, 반드시 새 비밀번호로 변경해 주세요.
                    </p>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label" style="margin-right: 6px; color: #6b7280;">로그인 이메일:</span>
                            <span class="info-value">{receiver_email}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label" style="margin-right: 6px; color: #6b7280;">임시 비밀번호:</span>
                            <span class="info-value temp-password">{temp_password}</span>
                        </div>
                    </div>
                    <a href="{login_url}" class="login-button" target="_blank" rel="noopener noreferrer">
                        로그인 페이지로 이동
                    </a>
                    <p class="paragraph" style="font-size: 12px; margin-top: 18px;">
                        보안을 위해 임시 비밀번호는 제3자와 공유하지 마시고,
                        로그인 후 <strong>반드시 새 비밀번호로 변경</strong>해 주세요.
                    </p>
                </div>
                <div class="footer">
                    이 이메일은 발신 전용으로 발송되었습니다. 답장을 통해 문의할 수 없습니다.
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        임시 비밀번호가 발급되었습니다.

        안녕하세요, {receiver_name} 님

        테넌트 관리자에 의해 비밀번호 재설정 요청이 처리되었습니다.
        아래의 임시 비밀번호로 로그인하신 후, 반드시 새 비밀번호로 변경해 주세요.

        로그인 이메일: {receiver_email}
        임시 비밀번호: {temp_password}
        로그인 페이지: {login_url}

        이 이메일은 발신 전용으로 발송되었습니다.
        """

        msg: MIMEMultipart = MIMEMultipart("alternative")
        msg["Subject"] = "[구매대행B2C] 임시 비밀번호가 발급되었습니다"
        msg["From"] = self._sender
        msg["To"] = receiver_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg
        return self

    def set_company_rejection_email(
        self,
        receiver_email: str,
        company_name: str,
        reason: str,
        business_no: str | None = None,
    ) -> Self:
        """
        회사 등록 거부 안내 이메일 생성
        - 수신자: 회사 대표 이메일
        - 내용: 거부 결과 + 거부 사유
        """
        html_body = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>회사 등록 거부 안내</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
                    background-color: #f3f4f6;
                    color: #111827;
                    line-height: 1.6;
                    margin: 0;
                    padding: 24px 0;
                }}
                .container {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
                }}
                .header {{
                    background: radial-gradient(circle at top left, #ef4444, #dc2626);
                    color: #ffffff;
                    padding: 28px 32px 24px 32px;
                }}
                .header-title {{
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0 0 6px 0;
                }}
                .header-subtitle {{
                    font-size: 13px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 28px 32px 24px 32px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin: 0 0 14px 0;
                }}
                .paragraph {{
                    font-size: 14px;
                    color: #4b5563;
                    margin: 0 0 10px 0;
                }}
                .section-title {{
                    font-size: 14px;
                    font-weight: 600;
                    margin: 24px 0 10px 0;
                    color: #111827;
                }}
                .info-card {{
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #fef2f2 100%);
                    padding: 14px 16px;
                    font-size: 13px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}
                .info-label {{
                    color: #6b7280;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #111827;
                    text-align: right;
                    max-width: 65%;
                }}
                .reason-box {{
                    background-color: #fef2f2;
                    border-left: 4px solid #ef4444;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 16px 0;
                    font-size: 14px;
                    color: #991b1b;
                }}
                .reason-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #dc2626;
                }}
                .reason-text {{
                    color: #7f1d1d;
                    white-space: pre-wrap;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(to right, transparent, #e5e7eb, transparent);
                    margin: 24px 0 16px 0;
                }}
                .footer {{
                    padding: 12px 32px 20px 32px;
                    background-color: #f9fafb;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-title">회사 등록 거부 안내</div>
                    <div class="header-subtitle">구매대행B2C 서비스</div>
                </div>
                <div class="content">
                    <p class="greeting">안녕하세요, {company_name} 담당자님</p>
                    <p class="paragraph">
                        신청해주신 회사 등록이 검토 결과 거부되었음을 안내드립니다.
                    </p>
                    <div class="section-title">등록 정보</div>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label">회사명</span>
                            <span class="info-value">{company_name}</span>
                        </div>
                        {f'<div class="info-row"><span class="info-label">사업자번호</span><span class="info-value">{business_no}</span></div>' if business_no else ''}
                    </div>
                    <div class="section-title">거부 사유</div>
                    <div class="reason-box">
                        <div class="reason-title">거부 사유</div>
                        <div class="reason-text">{reason}</div>
                    </div>
                    <div class="divider"></div>
                    <p class="paragraph" style="font-size: 13px; color: #6b7280;">
                        추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.
                    </p>
                </div>
                <div class="footer">
                    <p>본 메일은 자동 발송된 메일입니다.</p>
                    <p>© 2026 구매대행B2C. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        회사 등록 거부 안내

        안녕하세요, {company_name} 담당자님

        신청해주신 회사 등록이 검토 결과 거부되었음을 안내드립니다.

        등록 정보:
        - 회사명: {company_name}
        {f'- 사업자번호: {business_no}' if business_no else ''}

        거부 사유:
        {reason}

        추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.

        ---
        본 메일은 자동 발송된 메일입니다.
        © 2026 구매대행B2C. All rights reserved.
        """

        msg: MIMEMultipart = MIMEMultipart("alternative")
        msg["Subject"] = "[구매대행B2C] 회사 등록이 거부되었습니다"
        msg["From"] = self._sender
        msg["To"] = receiver_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg
        return self

    def set_company_deletion_email(
        self,
        receiver_email: str,
        company_name: str,
        reason: str,
        business_no: str | None = None,
    ) -> Self:
        """
        회사 삭제 안내 이메일 생성
        - 수신자: 회사 대표 이메일
        - 내용: 삭제 결과 + 삭제 사유 + 복구 불가 안내
        """
        html_body = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>회사 계정 삭제 안내</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
                    background-color: #f3f4f6;
                    color: #111827;
                    line-height: 1.6;
                    margin: 0;
                    padding: 24px 0;
                }}
                .container {{
                    max-width: 640px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
                }}
                .header {{
                    background: radial-gradient(circle at top left, #dc2626, #991b1b);
                    color: #ffffff;
                    padding: 28px 32px 24px 32px;
                }}
                .header-title {{
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0 0 6px 0;
                }}
                .header-subtitle {{
                    font-size: 13px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .content {{
                    padding: 28px 32px 24px 32px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin: 0 0 14px 0;
                }}
                .paragraph {{
                    font-size: 14px;
                    color: #4b5563;
                    margin: 0 0 10px 0;
                }}
                .warning-box {{
                    background-color: #fef2f2;
                    border: 2px solid #dc2626;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .warning-title {{
                    font-size: 16px;
                    font-weight: 700;
                    color: #dc2626;
                    margin-bottom: 10px;
                }}
                .warning-text {{
                    font-size: 14px;
                    color: #991b1b;
                    font-weight: 600;
                }}
                .section-title {{
                    font-size: 14px;
                    font-weight: 600;
                    margin: 24px 0 10px 0;
                    color: #111827;
                }}
                .info-card {{
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #fef2f2 100%);
                    padding: 14px 16px;
                    font-size: 13px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }}
                .info-label {{
                    color: #6b7280;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #111827;
                    text-align: right;
                    max-width: 65%;
                }}
                .reason-box {{
                    background-color: #fef2f2;
                    border-left: 4px solid #dc2626;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 16px 0;
                    font-size: 14px;
                    color: #991b1b;
                }}
                .reason-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #dc2626;
                }}
                .reason-text {{
                    color: #7f1d1d;
                    white-space: pre-wrap;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(to right, transparent, #e5e7eb, transparent);
                    margin: 24px 0 16px 0;
                }}
                .footer {{
                    padding: 12px 32px 20px 32px;
                    background-color: #f9fafb;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-title">회사 계정 삭제 안내</div>
                    <div class="header-subtitle">구매대행B2C 서비스</div>
                </div>
                <div class="content">
                    <p class="greeting">안녕하세요, {company_name} 담당자님</p>
                    <p class="paragraph">
                        안내드립니다. <strong>{company_name}</strong> 회사의 구매대행B2C 서비스 계정이 삭제되었습니다.
                    </p>
                    <div class="warning-box">
                        <div class="warning-title">⚠️ 중요 안내</div>
                        <div class="warning-text">
                            지금까지의 모든 데이터가 삭제되었으며, 복구가 불가능합니다.
                        </div>
                    </div>
                    <div class="section-title">등록 정보</div>
                    <div class="info-card">
                        <div class="info-row">
                            <span class="info-label">회사명</span>
                            <span class="info-value">{company_name}</span>
                        </div>
                        {f'<div class="info-row"><span class="info-label">사업자번호</span><span class="info-value">{business_no}</span></div>' if business_no else ''}
                    </div>
                    <div class="section-title">삭제 사유</div>
                    <div class="reason-box">
                        <div class="reason-title">삭제 사유</div>
                        <div class="reason-text">{reason}</div>
                    </div>
                    <div class="divider"></div>
                    <p class="paragraph" style="font-size: 13px; color: #6b7280;">
                        추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.
                    </p>
                </div>
                <div class="footer">
                    <p>본 메일은 자동 발송된 메일입니다.</p>
                    <p>© 2026 구매대행B2C. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        회사 계정 삭제 안내

        안녕하세요, {company_name} 담당자님

        안내드립니다. [{company_name}] 회사의 구매대행B2C 서비스 계정이 삭제되었습니다.

        ⚠️ 중요 안내
        지금까지의 모든 데이터가 삭제되었으며, 복구가 불가능합니다.

        등록 정보:
        - 회사명: {company_name}
        {f'- 사업자번호: {business_no}' if business_no else ''}

        삭제 사유:
        {reason}

        추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.

        ---
        본 메일은 자동 발송된 메일입니다.
        © 2026 구매대행B2C. All rights reserved.
        """

        msg: MIMEMultipart = MIMEMultipart("alternative")
        msg["Subject"] = "[구매대행B2C] 회사 계정이 삭제되었습니다"
        msg["From"] = self._sender
        msg["To"] = receiver_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        self.mime_msg = msg
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
        # public 스키마에서 조회
        await db.set_schemas(["public"])

        stmt = (
            select(ServiceAccount)
            .where(
                ServiceAccount.role == ServiceAccountRole.SMTP_SENDER.value,
                ServiceAccount.is_active == True,
            )
            .limit(1)
        )
        result = await db.execute_query(stmt)
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
