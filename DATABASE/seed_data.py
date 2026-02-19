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
from DATABASE.config import db_manager, user_repository, role_repository, permission_repository
from WEB_SERVER.auth import get_password_hash
from CUSTOMIZED.cust_logger import logger


async def seed_initial_data():
    """초기 데이터 시드 실행"""
    try:
        # 기본 권한 생성
        await seed_permissions()
        
        # 기본 역할 생성
        await seed_roles()
        
        # 기본 사용자 생성 (선택사항)
        # await seed_default_user()
        
        logger.info("✅ 초기 데이터 시드가 완료되었습니다.")
    except Exception as e:
        logger.error(f"❌ 초기 데이터 시드 실패: {e}")
        raise


async def seed_permissions():
    """기본 권한 생성"""
    permissions = [
        {"name": "user:create", "resource": "user", "action": "create", "description": "사용자 생성 권한"},
        {"name": "user:read", "resource": "user", "action": "read", "description": "사용자 조회 권한"},
        {"name": "user:update", "resource": "user", "action": "update", "description": "사용자 수정 권한"},
        {"name": "user:delete", "resource": "user", "action": "delete", "description": "사용자 삭제 권한"},
        
        {"name": "role:create", "resource": "role", "action": "create", "description": "역할 생성 권한"},
        {"name": "role:read", "resource": "role", "action": "read", "description": "역할 조회 권한"},
        {"name": "role:update", "resource": "role", "action": "update", "description": "역할 수정 권한"},
        {"name": "role:delete", "resource": "role", "action": "delete", "description": "역할 삭제 권한"},
        
        {"name": "permission:create", "resource": "permission", "action": "create", "description": "권한 생성 권한"},
        {"name": "permission:read", "resource": "permission", "action": "read", "description": "권한 조회 권한"},
        {"name": "permission:update", "resource": "permission", "action": "update", "description": "권한 수정 권한"},
        {"name": "permission:delete", "resource": "permission", "action": "delete", "description": "권한 삭제 권한"},
        
        {"name": "data:read", "resource": "data", "action": "read", "description": "데이터 조회 권한"},
        {"name": "data:create", "resource": "data", "action": "create", "description": "데이터 생성 권한"},
        {"name": "data:update", "resource": "data", "action": "update", "description": "데이터 수정 권한"},
        {"name": "data:delete", "resource": "data", "action": "delete", "description": "데이터 삭제 권한"},
    ]
    
    for perm in permissions:
        existing = await permission_repository.get_by_resource_action(perm["resource"], perm["action"])
        if not existing:
            perm_df = pd.DataFrame([perm])
            await permission_repository.create(perm_df)
            logger.info(f"✅ 권한 생성: {perm['name']}")
        else:
            logger.info(f"⏭️ 권한 이미 존재: {perm['name']}")


async def seed_roles():
    """기본 역할 생성 및 권한 할당"""
    # 관리자 역할
    admin_role = await role_repository.get_by_name("admin")
    if not admin_role:
        admin_df = pd.DataFrame([{
            "name": "admin",
            "description": "시스템 관리자 역할",
            "is_active": True
        }])
        await role_repository.create(admin_df)
        admin_role = await role_repository.get_by_name("admin")
        logger.info("✅ 역할 생성: admin")
    else:
        logger.info("⏭️ 역할 이미 존재: admin")
    
    # 모든 권한을 관리자에게 할당
    permissions = await permission_repository.get_all(skip=0, limit=1000)
    for perm in permissions:
        await role_repository.assign_permission(admin_role["id"], perm["id"])
    
    # 일반 사용자 역할
    user_role = await role_repository.get_by_name("user")
    if not user_role:
        user_df = pd.DataFrame([{
            "name": "user",
            "description": "일반 사용자 역할",
            "is_active": True
        }])
        await role_repository.create(user_df)
        user_role = await role_repository.get_by_name("user")
        logger.info("✅ 역할 생성: user")
        
        # 일반 사용자에게 읽기 권한만 할당
        read_permissions = [p for p in permissions if p["action"] == "read"]
        for perm in read_permissions:
            await role_repository.assign_permission(user_role["id"], perm["id"])
    else:
        logger.info("⏭️ 역할 이미 존재: user")


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
        
        # 관리자 역할 할당
        admin_role = await role_repository.get_by_name("admin")
        if admin_role:
            user = await user_repository.get_by_email(default_email)
            await user_repository.assign_role(user["id"], admin_role["id"])
        
        logger.info(f"✅ 기본 관리자 사용자 생성: {default_email}")
        logger.warning(f"⚠️ 기본 비밀번호: {default_password} (프로덕션 환경에서는 반드시 변경하세요!)")
    else:
        logger.info(f"⏭️ 기본 관리자 사용자 이미 존재: {default_email}")


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    asyncio.run(seed_initial_data())
