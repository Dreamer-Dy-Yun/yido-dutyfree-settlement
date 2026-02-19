###########################################
# Module name : __init__.py
# Module class : 모든 모델 통합 import
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 모든 모델을 한 곳에서 import하여 하위 호환성 유지
#   2025.12.03 : models 폴더로 이동
############################################

# BaseModel
from DATABASE.models.base_model import BaseModel

# 인증 및 권한 관리 모델
from DATABASE.models.authorities_model import (
    Tenant,
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
)

# 비즈니스 모델
from DATABASE.models.bussiness_model import OcrPassport, OcrReceipt, VerifiedPassport, VerifiedReceipt, Prompt, Image, EdiSilla, EdiLotte, Matched, LlmUsage

# 하위 호환성을 위해 __all__ 정의
__all__ = [
    # Base
    "BaseModel",
    # Auth
    "Tenant",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # Business
    "OcrPassport",
    "OcrReceipt",
    "VerifiedPassport",
    "VerifiedReceipt",
    "Prompt",
    "Image",
    "EdiSilla",
    "EdiLotte",
    "Matched",
    "LlmUsage",
]
