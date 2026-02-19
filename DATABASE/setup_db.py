from DATABASE.config import db_manager
from DATABASE.seed_data import seed_initial_data


# 서버 실행 함수
async def setup_db() -> None:
    print("DB 설정 중...")
    await db_manager.create_tables()
    print("DB 설정 완료")
    # 초기 데이터 시드 실행 (역할 및 권한 생성)
    # await seed_initial_data()
    # print("초기 데이터 시드 완료")