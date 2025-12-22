from DATABASE.config import db_manager
from DATABASE.config import apply_postgres_vector_scale_index


# 서버 실행 함수
async def setup_db() -> None:
    await db_manager.create_tables()
    await apply_postgres_vector_scale_index(db_manager)