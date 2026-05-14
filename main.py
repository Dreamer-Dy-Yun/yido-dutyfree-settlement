# import main_logger  # 코드에서 참조 안해도 자동으로 로그 세팅되므로 삭제하지 말 것
import argparse
import asyncio
import os
from dotenv import load_dotenv
from DATABASE.setup_db import setup_db
from WEB_SERVER.main_web import start_web_server
from DATABASE.config import db_manager
from CUSTOMIZED.cust_deco_retry import async_retry

# 개발 중
# 백엔드 기준 경로: D:\DEV\YIDO\backend
# 루트 compose 기준 경로: D:\DEV\YIDO
# 프론트 작업트리: D:\DEV\YIDO\frontend
# 패키지 설치
# py -m venv .venv
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# .venv\Scripts\activate
# pip install -r requirements.txt  
# uvicorn WEB_SERVER.app:app --reload
# cd ..\frontend ;; pnpm dev


# @async_retry(exceptions=(Exception,), backoff_factor=10)
async def main() -> None:
    try:
        load_dotenv()

        await setup_db()

        await start_web_server()

    except KeyboardInterrupt:
        print("\n⚠️ 애플리케이션 종료 중...")
    finally:
        await db_manager.dispose_pool()


if __name__ == "__main__":
    asyncio.run(main())


# d:/DEV/YIDO/venv/Scripts/Activate.ps1
# cd .. ;; docker compose up -d
# cd ..\frontend ;; pnpm dev
# uvicorn WEB_SERVER.app:app --reload --port 10000
