###########################################
# Module name : service.py
# Module functions : 모든 서비스 함수를 re-export하는 stub 모듈
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
#        - IDE 인식을 위한 stub 모듈
#        - 실제 구현은 각 service_*.py 파일에 있음
#        - from WEB_SERVER.services.service import 함수명 형태로 사용 가능
############################################

# 모든 서비스 함수 import 및 re-export
from .service_email import EmailService

__all__ = [
    # email
    "EmailService",
]
