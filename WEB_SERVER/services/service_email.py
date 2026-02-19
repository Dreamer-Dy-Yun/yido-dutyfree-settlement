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
from CUSTOMIZED.cust_logger import logger


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
            logger.error(log_error)
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


# 전역 인스턴스 (환경변수에서 설정 읽음)
email_service = EmailService(
    server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    port=int(os.getenv("SMTP_PORT", "587")),
    user=os.getenv("SMTP_USER", ""),
    password=os.getenv("SMTP_PASSWORD", ""),
    sender=os.getenv("SMTP_SENDER", os.getenv("SMTP_USER", ""))
)
