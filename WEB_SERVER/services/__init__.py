###########################################
# Module name : __init__.py
# Module functions : service 모듈 export
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
#        - service 모듈을 import하여 from WEB_SERVER.services import service 형태 지원
#        - service 모듈을 통해 from WEB_SERVER.services.service import 함수명 형태도 지원
#        - 모든 서비스 함수는 service.py에서 관리
############################################

# service 모듈 import (모든 서비스 함수는 service.py에서 관리)
from . import service

__all__ = ["service"]
