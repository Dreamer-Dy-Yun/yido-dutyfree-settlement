###########################################
# Module name : __init__.py
# Module class : Repository 통합 import
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 모든 Repository 통합 import
############################################

from DATABASE.repositories.base import BaseRepository
from DATABASE.repositories.authorities import (
    UserRepository,
    TenantRepository,
)

__all__ = [
    "BaseRepository",
    "UserRepository",
    "TenantRepository",
]
