# import main_logger  # 코드에서 참조 안해도 자동으로 로그 세팅되므로 삭제하지 말 것
import asyncio
from dotenv import load_dotenv
from DATABASE.setup_db import setup_db
from WEB_SERVER.main_web import start_web_server
from DATABASE.config import db_manager
from CUSTOMIZED.cust_deco_retry import async_retry



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