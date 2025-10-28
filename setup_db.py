#!/usr/bin/env python3
"""
기존 ORM 모델을 사용한 데이터베이스 테이블 생성
"""

import asyncio
from DATABASE import models, pg_manager

async def setup_database():
    """데이터베이스 테이블 생성"""
    try:
        # 데이터베이스 연결 정보
        db_name = 'pgvs'
        db_user = 'pgvs_user'
        db_password = 'pgvs_password'
        db_host = 'localhost'
        db_port = 5432
        
        print("=== 데이터베이스 테이블 생성 ===")
        
        # PGDBManager 초기화
        async with pg_manager.PGDBManager(models.BaseModel, db_name, db_user, db_password, db_host, db_port) as session:
            # 기존 ORM 모델로 테이블 생성
            await pg_manager.PGDBManager.create_tables()
            
            print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
            
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")

async def main():
    """메인 함수"""
    await setup_database()

if __name__ == "__main__":
    asyncio.run(main()) 