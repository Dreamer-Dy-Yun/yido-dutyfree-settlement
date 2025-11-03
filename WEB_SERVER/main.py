import asyncio
import uvicorn
from DATABASE.pg_manager import PGDBManager
from DATABASE.config import db_manager
from WEB_SERVER import app
from DATABASE.config import apply_postgres_vector_scale_index


# 서버 실행 함수
async def _init_db():
    await db_manager.create_tables()
    await apply_postgres_vector_scale_index(db_manager)


if __name__ == "__main__":
    asyncio.run(_init_db())
    uvicorn.run(
        "WEB_SERVER.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )