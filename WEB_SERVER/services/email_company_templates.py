###########################################
# Module name : email_company_templates.py
# Module functions : Company email MIME message builders.
############################################

from email.mime.multipart import MIMEMultipart

from WEB_SERVER.services.email_message_builder import build_alternative_email_message


_COMPANY_STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; background-color: #f3f4f6; color: #111827; line-height: 1.6; margin: 0; padding: 24px 0; }
.container { max-width: 640px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16); }
.header { color: #ffffff; padding: 28px 32px 24px 32px; }
.header-title { font-size: 22px; font-weight: 700; margin: 0 0 6px 0; }
.header-subtitle { font-size: 13px; opacity: 0.9; margin: 0; }
.content { padding: 28px 32px 24px 32px; }
.greeting { font-size: 16px; margin: 0 0 14px 0; }
.paragraph { font-size: 14px; color: #4b5563; margin: 0 0 10px 0; }
.section-title { font-size: 14px; font-weight: 600; margin: 24px 0 10px 0; color: #111827; }
.info-card { border-radius: 12px; border: 1px solid #e5e7eb; padding: 14px 16px; font-size: 13px; }
.info-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.info-label { color: #6b7280; margin-right: 6px; }
.info-value { font-weight: 500; color: #111827; text-align: right; max-width: 65%; }
.highlight { margin-top: 12px; font-size: 12px; color: #4b5563; }
.login-button { display: inline-block; margin-top: 16px; padding: 10px 20px; background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; text-decoration: none; border-radius: 999px; font-size: 13px; font-weight: 600; }
.reason-box { background-color: #fef2f2; border-left: 4px solid #dc2626; border-radius: 8px; padding: 16px; margin: 16px 0; font-size: 14px; color: #991b1b; }
.reason-title { font-weight: 600; margin-bottom: 8px; color: #dc2626; }
.reason-text { color: #7f1d1d; white-space: pre-wrap; }
.warning-box { background-color: #fef2f2; border: 2px solid #dc2626; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; }
.warning-title { font-size: 16px; font-weight: 700; color: #dc2626; margin-bottom: 10px; }
.warning-text { font-size: 14px; color: #991b1b; font-weight: 600; }
.divider { height: 1px; background: linear-gradient(to right, transparent, #e5e7eb, transparent); margin: 24px 0 16px 0; }
.footer { padding: 12px 32px 20px 32px; font-size: 11px; color: #9ca3af; border-top: 1px solid #f3f4f6; text-align: center; background-color: #f9fafb; }
""".strip()


def _info_row(label: str, value: str | None) -> str:
    if not value:
        return ""
    return f'<div class="info-row"><span class="info-label">{label}</span><span class="info-value">{value}</span></div>'


def _info_card(rows: list[str], tone: str) -> str:
    return f'<div class="info-card" style="background: linear-gradient(145deg, #f9fafb 0%, #ffffff 60%, {tone} 100%);">{"".join(rows)}</div>'


def _page(title: str, subtitle: str, gradient: str, content_html: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"><title>{title}</title><style>{_COMPANY_STYLE}</style></head>
    <body><div class="container"><div class="header" style="background: {gradient};"><p class="header-title">{title}</p><p class="header-subtitle">{subtitle}</p></div><div class="content">{content_html}</div><div class="footer">이 이메일은 발신 전용으로 발송되었습니다. 답장을 통해 문의하실 수 없으며,<br/>별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.</div></div></body>
    </html>
    """


def _business_no_text(business_no: str | None, label: str = "사업자등록번호") -> str:
    return f"\n- {label}: {business_no}" if business_no else ""


def build_company_registration_email(
    sender: str,
    receiver_email: str,
    company_name: str,
    business_no: str | None = None,
    contact: str | None = None,
) -> MIMEMultipart:
    """신규 회사 등록 접수 안내 이메일 생성."""
    info_rows = [_info_row("회사명", company_name), _info_row("사업자등록번호", business_no), _info_row("대표 연락처", contact)]
    html_body = _page(
        title="신규 회사 등록 신청이 접수되었습니다",
        subtitle="구매대행B2C 기업용 서비스",
        gradient="radial-gradient(circle at top left, #4f46e5, #7c3aed)",
        content_html=f"""
        <p class="greeting">안녕하세요.</p>
        <p class="paragraph"><strong>{company_name}</strong> 회사의 구매대행B2C 서비스 이용 신청이 정상적으로 접수되었습니다.</p>
        <p class="paragraph">내부 검토 및 시스템 준비가 완료되는 대로, 서비스 이용을 위한 세부 안내를 별도의 채널을 통해 전달드릴 예정입니다.</p>
        <p class="section-title">신청 정보</p>{_info_card(info_rows, "#eef2ff")}
        <p class="highlight">위 정보는 회사 등록 및 초기 세팅을 위한 참고용으로만 사용되며, 실제 관리자 계정 정보는 이후 별도의 절차를 통해 설정하게 됩니다.</p>
        <div class="divider"></div><p class="paragraph" style="font-size: 12px;">본 메일은 회사 등록 신청이 정상적으로 접수되었음을 알려드리기 위한 안내 메일입니다. 서비스 이용 시작과 관련된 상세한 일정과 안내는 추후 다시 안내드리겠습니다.</p>
        """,
    )
    text_body = f"""[구매대행B2C] 신규 회사 등록 신청이 접수되었습니다.

안녕하세요.

[{company_name}] 회사의 구매대행B2C 서비스 이용 신청이 정상적으로 접수되었습니다.

신청 정보
- 회사명: {company_name}{_business_no_text(business_no)}{f"\n- 대표 연락처: {contact}" if contact else ""}

위 정보는 회사 등록 및 초기 세팅을 위한 참고용으로만 사용되며, 실제 관리자 계정 정보는 이후 별도의 절차를 통해 설정하게 됩니다.

본 메일은 회사 등록 신청이 정상적으로 접수되었음을 알려드리기 위한 안내 메일입니다. 서비스 이용 시작과 관련된 상세한 일정과 안내는 추후 별도 채널을 통해 안내드리겠습니다."""
    return build_alternative_email_message(sender=sender, receiver_email=receiver_email, subject='[????B2C] ?? ?? ?? ??? ???????', text_body=text_body, html_body=html_body)


def build_company_approval_email(
    sender: str,
    receiver_email: str,
    company_name: str,
    login_id: str,
    login_url: str,
    temp_password: str,
    business_no: str | None = None,
) -> MIMEMultipart:
    """회사 등록 승인 안내 이메일 생성."""
    company_card = _info_card([_info_row("회사명", company_name), _info_row("사업자등록번호", business_no)], "#ecfdf5")
    login_card = _info_card([
        _info_row("로그인 페이지", f'<a href="{login_url}" target="_blank" rel="noopener noreferrer">{login_url}</a>'),
        _info_row("초기 관리자 계정 ID", login_id),
        _info_row("임시 비밀번호", f'<span style="font-family: monospace; font-size: 14px; color: #dc2626; font-weight: 600; -webkit-user-select: all; user-select: all; cursor: text; display: inline-block; padding: 2px 4px;" title="클릭 후 Ctrl+C로 복사">{temp_password}</span>'),
    ], "#ecfdf5")
    html_body = _page(
        title="회사 등록이 승인되었습니다",
        subtitle="구매대행B2C 기업용 서비스",
        gradient="radial-gradient(circle at top left, #10b981, #059669)",
        content_html=f"""
        <p class="greeting">안녕하세요.</p>
        <p class="paragraph"><strong>{company_name}</strong> 회사의 구매대행B2C 서비스 이용 신청이 승인되었습니다.</p>
        <p class="paragraph">이제 아래의 초기 관리자 계정으로 로그인하신 후, 프로필과 비밀번호를 설정하시면 서비스를 이용하실 수 있습니다.</p>
        <p class="section-title">회사 정보</p>{company_card}
        <p class="section-title">로그인 정보</p>{login_card}
        <p class="highlight">최초 로그인 후 반드시 비밀번호와 관리자 정보를 변경해 주시기 바랍니다.</p>
        <a href="{login_url}" class="login-button" target="_blank" rel="noopener noreferrer">로그인 페이지로 이동</a>
        <p class="paragraph" style="font-size: 12px; margin-top: 18px;">만약 본 메일이 잘못 수신되었다고 판단되면, 회신하지 마시고 별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다.</p>
        """,
    )
    text_body = f"""[구매대행B2C] 회사 등록이 승인되었습니다.

안녕하세요.

[{company_name}] 회사의 구매대행B2C 서비스 이용 신청이 승인되었습니다.

회사 정보
- 회사명: {company_name}{_business_no_text(business_no)}

로그인 정보
- 로그인 페이지: {login_url}
- 초기 관리자 계정 ID: {login_id}
- 임시 비밀번호: {temp_password}

최초 로그인 후 반드시 비밀번호와 관리자 정보를 변경해 주시기 바랍니다.

만약 본 메일이 잘못 수신되었다고 판단되면, 회신하지 마시고 별도의 고객센터 또는 담당자를 통해 문의해 주시기 바랍니다."""
    return build_alternative_email_message(sender=sender, receiver_email=receiver_email, subject='[????B2C] ?? ??? ???????', text_body=text_body, html_body=html_body)


def build_company_rejection_email(
    sender: str,
    receiver_email: str,
    company_name: str,
    reason: str,
    business_no: str | None = None,
) -> MIMEMultipart:
    """회사 등록 거부 안내 이메일 생성."""
    html_body = _page(
        title="회사 등록 거부 안내",
        subtitle="구매대행B2C 서비스",
        gradient="radial-gradient(circle at top left, #ef4444, #dc2626)",
        content_html=f"""
        <p class="greeting">안녕하세요, {company_name} 담당자님</p>
        <p class="paragraph">신청해주신 회사 등록이 검토 결과 거부되었음을 안내드립니다.</p>
        <p class="section-title">등록 정보</p>{_info_card([_info_row("회사명", company_name), _info_row("사업자번호", business_no)], "#fef2f2")}
        <p class="section-title">거부 사유</p><div class="reason-box"><div class="reason-title">거부 사유</div><div class="reason-text">{reason}</div></div>
        <div class="divider"></div><p class="paragraph" style="font-size: 13px; color: #6b7280;">추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.</p>
        """,
    )
    text_body = f"""회사 등록 거부 안내

안녕하세요, {company_name} 담당자님

신청해주신 회사 등록이 검토 결과 거부되었음을 안내드립니다.

등록 정보:
- 회사명: {company_name}{_business_no_text(business_no, "사업자번호")}

거부 사유:
{reason}

추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.

---
본 메일은 자동 발송된 메일입니다.
© 2026 구매대행B2C. All rights reserved."""
    return build_alternative_email_message(sender=sender, receiver_email=receiver_email, subject="[구매대행B2C] 회사 등록이 거부되었습니다", text_body=text_body, html_body=html_body)


def build_company_deletion_email(
    sender: str,
    receiver_email: str,
    company_name: str,
    reason: str,
    business_no: str | None = None,
) -> MIMEMultipart:
    """회사 삭제 안내 이메일 생성."""
    html_body = _page(
        title="회사 계정 삭제 안내",
        subtitle="구매대행B2C 서비스",
        gradient="radial-gradient(circle at top left, #dc2626, #991b1b)",
        content_html=f"""
        <p class="greeting">안녕하세요, {company_name} 담당자님</p>
        <p class="paragraph">안내드립니다. <strong>{company_name}</strong> 회사의 구매대행B2C 서비스 계정이 삭제되었습니다.</p>
        <div class="warning-box"><div class="warning-title">중요 안내</div><div class="warning-text">지금까지의 모든 데이터가 삭제되었으며, 복구가 불가능합니다.</div></div>
        <p class="section-title">등록 정보</p>{_info_card([_info_row("회사명", company_name), _info_row("사업자번호", business_no)], "#fef2f2")}
        <p class="section-title">삭제 사유</p><div class="reason-box"><div class="reason-title">삭제 사유</div><div class="reason-text">{reason}</div></div>
        <div class="divider"></div><p class="paragraph" style="font-size: 13px; color: #6b7280;">추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.</p>
        """,
    )
    text_body = f"""회사 계정 삭제 안내

안녕하세요, {company_name} 담당자님

안내드립니다. [{company_name}] 회사의 구매대행B2C 서비스 계정이 삭제되었습니다.

중요 안내
지금까지의 모든 데이터가 삭제되었으며, 복구가 불가능합니다.

등록 정보:
- 회사명: {company_name}{_business_no_text(business_no, "사업자번호")}

삭제 사유:
{reason}

추가 문의사항이 있으시면 고객센터로 연락 주시기 바랍니다.

---
본 메일은 자동 발송된 메일입니다.
© 2026 구매대행B2C. All rights reserved."""
    return build_alternative_email_message(sender=sender, receiver_email=receiver_email, subject="[구매대행B2C] 회사 계정이 삭제되었습니다", text_body=text_body, html_body=html_body)
