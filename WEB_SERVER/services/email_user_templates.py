###########################################
# Module name : email_user_templates.py
# Module functions : User email MIME message builders.
############################################

from email.mime.multipart import MIMEMultipart

from WEB_SERVER.services.email_message_builder import build_alternative_email_message


def build_verification_email(
    sender: str,
    receiver_email: str,
    receiver_name: str,
    verification_token: str,
    service_url: str,
    expiration_hours: int = 12,
) -> MIMEMultipart:
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

    return build_alternative_email_message(
        sender=sender,
        receiver_email=receiver_email,
        subject='[????B2C] ??? ??? ??????',
        text_body=text_body,
        html_body=html_body,
    )


def build_welcome_email(
    sender: str,
    receiver_email: str,
    receiver_name: str,
) -> MIMEMultipart:
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

    return build_alternative_email_message(
        sender=sender,
        receiver_email=receiver_email,
        subject='[????B2C] ??? ??? ???????',
        text_body=text_body,
        html_body=html_body,
    )
