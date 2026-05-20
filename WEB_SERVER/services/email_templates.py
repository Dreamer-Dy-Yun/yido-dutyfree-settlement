###########################################
# Module name : email_templates.py
# Module functions : Compatibility imports for email MIME message builders.
############################################

from WEB_SERVER.services.email_company_templates import (
    build_company_approval_email,
    build_company_registration_email,
)
from WEB_SERVER.services.email_user_templates import (
    build_verification_email,
    build_welcome_email,
)

__all__ = [
    "build_company_approval_email",
    "build_company_registration_email",
    "build_verification_email",
    "build_welcome_email",
]
