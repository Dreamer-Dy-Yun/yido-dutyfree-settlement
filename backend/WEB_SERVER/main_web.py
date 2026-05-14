import asyncio
import os
from dotenv import load_dotenv
from uvicorn import Config, Server
from DATABASE.setup_db import setup_db
from DATABASE.config import db_manager

async def start_web_server() -> None:
    config = Config(
        "WEB_SERVER.app:app",
        host=os.getenv("WEB_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("WEB_SERVER_PORT", "10000")),
        reload=os.getenv("WEB_SERVER_RELOAD", "false").lower() == "true", # 한글 경로 때문에 사용
        # reload=os.getenv("WEB_SERVER_RELOAD", "true").lower() == "true",
        log_level=os.getenv("WEB_SERVER_LOG_LEVEL", "info")
    )
    server = Server(config)
    print("Server started")
    await server.serve()

async def main() -> None:
    # 환경변수 로드
    load_dotenv()

    await setup_db()
    
    try:
        await start_web_server()
    except KeyboardInterrupt:
        print("\n⚠️ 웹 서버 종료 중...")
    finally:
        await db_manager.dispose_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 웹 서버 종료 중...")
        asyncio.run(db_manager.dispose_pool())