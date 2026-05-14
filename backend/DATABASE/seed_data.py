###########################################
# Module name : seed_data.py
# Module functions : 초기 데이터 시드 (기본 역할 및 권한 생성)
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 데이터베이스 초기화 시 기본 역할과 권한을 생성합니다.
############################################

import pandas as pd
from DATABASE.config import db_manager, user_repository
from WEB_SERVER.auth import get_password_hash
from CUSTOMIZED.cust_logger import logger


async def seed_initial_data():
    """초기 데이터 시드 실행"""
    try:
        # 기본 사용자 생성 (선택사항)
        # await seed_default_user()
        
        logger.info("✅ 초기 데이터 시드가 완료되었습니다.")
    except Exception as e:
        logger.error(f"❌ 초기 데이터 시드 실패: {e}")
        raise


async def seed_default_user():
    """기본 관리자 사용자 생성 (선택사항)"""
    import os
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123!")
    default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    
    existing_user = await user_repository.get_by_email(default_email)
    if not existing_user:
        user_df = pd.DataFrame([{
            "username": default_username,
            "email": default_email,
            "hashed_password": get_password_hash(default_password),
            "full_name": "시스템 관리자",
            "is_active": True,
            "is_superuser": True
        }])
        await user_repository.create(user_df)
        
        logger.info(f"✅ 기본 관리자 사용자 생성: {default_email}")
        logger.warning(f"⚠️ 기본 비밀번호: {default_password} (프로덕션 환경에서는 반드시 변경하세요!)")
    else:
        logger.info(f"⏭️ 기본 관리자 사용자 이미 존재: {default_email}")


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    asyncio.run(seed_initial_data())
