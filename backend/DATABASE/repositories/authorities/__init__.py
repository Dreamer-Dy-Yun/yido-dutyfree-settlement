###########################################
# Module name : authorities.__init__
# Module class : Authorities 관련 Repository 통합 import
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 사용자/역할/권한 Repository 모음
############################################

from DATABASE.repositories.authorities.user_repository import UserRepository
from DATABASE.repositories.authorities.tenant_repository import TenantRepository

__all__ = [
    "UserRepository",
    "TenantRepository",
]

