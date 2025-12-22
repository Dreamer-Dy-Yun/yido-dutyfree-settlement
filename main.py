import main_logger  # 코드에서 참조 안해도 자동으로 로그 세팅되므로 삭제하지 말 것
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from DATABASE.setup_db import setup_db
from WEB_SERVER.main_web import start_web_server
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from main_retriever import ICTRetrieveRunner
from main_archiver import ICTArchiveRunner
from DATABASE.config import db_manager, cruder
from WEB_SERVER.routers.settings import set_dir_base
from WEB_SERVER.services.service import normalize_and_upsert_all_models
from CUSTOMIZED.cust_deco_retry import async_retry



@async_retry(exceptions=(Exception,), backoff_factor=10)
async def main() -> None:
    # DB 설정 먼저 실행
    load_dotenv()  # .env 파일 로드

    base_dir_for_parquet = Path(os.getenv("DIR_BASE_FOR_PARQUET", "C:/Users/user/ict_parquets"))
    set_dir_base(base_dir_for_parquet)

    ICTArchiveRunner.set_dir_destination(base_dir_for_parquet)
    ICTArchiveRunner.set_sub_dir_spec("SPEC")
    ICTArchiveRunner.set_sub_dir_measured("MEASURED")

    ICTRetrieveRunner.set_cruder(cruder)
    ICTRetrieveRunner.set_download_batch_size(10)
    ICTRetrieveRunner.set_fetch_list_limit(20)
    ICTRetrieveRunner.set_max_attempts(5)
    await ICTRetrieveRunner.reset_locks()

    max_instances_archiver : int = 2
    max_instances_retriever : int = 2
    await setup_db()
    
    scheduler = AsyncIOScheduler()

    scheduler.add_job(ICTRetrieveRunner().run, name="파일 리트리버 작업", trigger=CronTrigger(second='*/10'), max_instances=max_instances_retriever, coalesce=True )
    scheduler.add_job(ICTArchiveRunner().run, name="데이터 아카이버 작업", trigger=CronTrigger(second='*/5'), max_instances=max_instances_archiver, coalesce=True )
    scheduler.add_job(normalize_and_upsert_all_models, args=[cruder, base_dir_for_parquet / "SPEC"], name="모델 정규화 및 벡터 업서트 작업", trigger=CronTrigger(hour=1, minute=0, second=0), max_instances=1, coalesce=True )
    scheduler.start()
    
    try:
        await start_web_server()
    except KeyboardInterrupt:
        print("\n⚠️ 애플리케이션 종료 중...")
    finally:
        scheduler.shutdown()
        await db_manager.dispose_pool()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 애플리케이션 종료 중...")
        asyncio.run(db_manager.dispose_pool())