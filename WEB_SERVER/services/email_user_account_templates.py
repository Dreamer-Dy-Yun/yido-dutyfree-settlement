###########################################
# Module name : email_user_account_templates.py
# Module functions : Tenant user account email MIME message builders.
############################################

from email.mime.multipart import MIMEMultipart

from WEB_SERVER.services.email_message_builder import build_alternative_email_message


def build_user_temp_password_email(
    sender: str,
    receiver_email: str,
    receiver_name: str,
    temp_password: str,
    login_url: str,
) -> MIMEMultipart:
    """Build a tenant user temporary password email."""
    html_body = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>임시 비밀번호 안내</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; background-color: #f3f4f6; color: #111827; line-height: 1.6; margin: 0; padding: 24px 0; }}
            .container {{ max-width: 640px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16); }}
            .header {{ background: radial-gradient(circle at top left, #2563eb, #4f46e5); color: #ffffff; padding: 28px 32px 24px 32px; }}
            .header-title {{ font-size: 22px; font-weight: 700; margin: 0 0 6px 0; }}
            .header-subtitle {{ font-size: 13px; opacity: 0.9; margin: 0; }}
            .content {{ padding: 28px 32px 24px 32px; }}
            .greeting {{ font-size: 16px; margin: 0 0 14px 0; }}
            .paragraph {{ font-size: 14px; color: #4b5563; margin: 0 0 10px 0; }}
            .info-card {{ border-radius: 12px; border: 1px solid #e5e7eb; background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, #dbeafe 100%); padding: 14px 16px; font-size: 13px; }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
            .info-label {{ color: #6b7280; }}
            .info-value {{ font-weight: 500; color: #111827; text-align: right; max-width: 65%; }}
            .temp-password {{ font-family: monospace; font-size: 14px; color: #dc2626; font-weight: 600; }}
            .login-button {{ display: inline-block; margin-top: 16px; padding: 10px 20px; background: #ffffff; color: #2563eb; text-decoration: none; border-radius: 999px; font-size: 13px; font-weight: 600; border: 2px solid; border-image: linear-gradient(135deg, #2563eb, #4f46e5) 1; }}
            .footer {{ padding: 12px 32px 20px 32px; font-size: 11px; color: #9ca3af; border-top: 1px solid #f3f4f6; text-align: center; background-color: #f9fafb; }}
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
                <p class="paragraph">테넌트 관리자에 의해 비밀번호 재설정 요청이 처리되었습니다. 아래의 임시 비밀번호로 로그인하신 후, 반드시 새 비밀번호로 변경해 주세요.</p>
                <div class="info-card">
                    <div class="info-row"><span class="info-label" style="margin-right: 6px; color: #6b7280;">로그인 이메일:</span><span class="info-value">{receiver_email}</span></div>
                    <div class="info-row"><span class="info-label" style="margin-right: 6px; color: #6b7280;">임시 비밀번호:</span><span class="info-value temp-password" style="-webkit-user-select: all; user-select: all; cursor: text; display: inline-block; padding: 2px 4px;" title="클릭 후 Ctrl+C로 복사">{temp_password}</span></div>
                </div>
                <a href="{login_url}" class="login-button" target="_blank" rel="noopener noreferrer">로그인 페이지로 이동</a>
                <p class="paragraph" style="font-size: 12px; margin-top: 18px;">보안을 위해 임시 비밀번호는 제3자와 공유하지 마시고, 로그인 후 <strong>반드시 새 비밀번호로 변경</strong>해 주세요.</p>
            </div>
            <div class="footer">이 이메일은 발신 전용으로 발송되었습니다. 답장을 통해 문의할 수 없습니다.</div>
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
    return build_alternative_email_message(
        sender=sender,
        receiver_email=receiver_email,
        subject="[구매대행B2C] 임시 비밀번호가 발급되었습니다",
        text_body=text_body,
        html_body=html_body,
    )


def build_user_deletion_email(
    sender: str,
    receiver_email: str,
    receiver_name: str,
) -> MIMEMultipart:
    """Build a tenant user deletion email."""
    html_body = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>계정 삭제 안내</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; background-color: #f3f4f6; color: #111827; line-height: 1.6; margin: 0; padding: 24px 0; }}
            .container {{ max-width: 640px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16); }}
            .header {{ background: radial-gradient(circle at top left, #ef4444, #dc2626); color: #ffffff; padding: 28px 32px 24px 32px; }}
            .header-title {{ font-size: 22px; font-weight: 700; margin: 0 0 6px 0; }}
            .content {{ padding: 28px 32px 24px 32px; }}
            .paragraph {{ font-size: 14px; color: #4b5563; margin: 0 0 12px 0; }}
            .footer {{ padding: 12px 32px 20px 32px; font-size: 11px; color: #9ca3af; border-top: 1px solid #f3f4f6; text-align: center; background-color: #f9fafb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><p class="header-title">계정 삭제가 완료되었습니다</p></div>
            <div class="content">
                <p class="paragraph">안녕하세요, {receiver_name} 님.</p>
                <p class="paragraph">요청하신 계정 삭제가 정상적으로 처리되었습니다.</p>
                <p class="paragraph">본 메일은 안내용 자동 발송 메일이며, 문의가 필요한 경우 관리자에게 연락해 주세요.</p>
            </div>
            <div class="footer">본 메일은 발신 전용입니다.</div>
        </div>
    </body>
    </html>
    """
    text_body = f"""
    계정 삭제가 완료되었습니다.

    안녕하세요, {receiver_name} 님.
    요청하신 계정 삭제가 정상적으로 처리되었습니다.

    본 메일은 안내용 자동 발송 메일입니다.
    """
    return build_alternative_email_message(
        sender=sender,
        receiver_email=receiver_email,
        subject="[구매대행B2C] 계정 삭제가 완료되었습니다",
        text_body=text_body,
        html_body=html_body,
    )
