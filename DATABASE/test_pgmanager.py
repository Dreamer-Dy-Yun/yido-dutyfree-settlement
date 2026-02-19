from DATABASE.models import BaseModel
from DATABASE.dbms.postgre.pg_manager import DataBaseMaker, PGDBManager
import asyncio


# 접속 정보 설정
DB_NAME = 'novas_ez'
DB_USER = 'admin'
DB_PASSWORD = '123!@#qwe'  # ← 이스케이프 제거
DB_HOST = 'localhost'
DB_PORT = '5432'

dm = DataBaseMaker(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
dm.run()

db = PGDBManager(BaseModel, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)


async def main():
    await db.create_tables()
    # await db.drop_tables()

asyncio.run(main())