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

# Public 스키마 모델 (인증 및 권한 관리)
from DATABASE.models.public_model import (
    SystemAdmin,
    ServiceAccount,
    ServiceAccountRole,
    Tenant,
    LLM_API_Key,
    Prompt_path,
)

# Tenant 스키마 모델
from DATABASE.models.tenant_model import User, OcrPassport, OcrReceipt, VerifiedPassport, VerifiedReceipt, Prompt, Image, EdiSilla, EdiLotte, Matched, LlmUsage

# 하위 호환성을 위해 __all__ 정의
__all__ = [
    # Base
    "BaseModel",
    # Public
    "SystemAdmin",
    "ServiceAccount",
    "ServiceAccountRole",
    "Tenant",
    "LLM_API_Key",
    "Prompt_path",
    # Tenant
    "User",
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
