import asyncio
from DATABASE.setup_db import setup_db
from WEB_SERVER.main import start_web_server
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from main_retriever import ICTRetrieveRunner
from main_archiver import ICTArchiveRunner
from pathlib import Path


async def main():
    # DB 설정 먼저 실행
    await setup_db()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ICTRetrieveRunner().run, name="파일 리트리버 작업", trigger=CronTrigger(second='*/5'), max_instances=1, coalesce=True )
    scheduler.add_job(ICTArchiveRunner().set_dir_destination(Path("C:/Users/user/Novas_Ez")).run, name="데이터 아카이버 작업", trigger=CronTrigger(second='*/5'), max_instances=1, coalesce=True )
    scheduler.start()
    # 웹 서버와 다른 작업들을 병렬로 실행
    await start_web_server()


if __name__ == "__main__":
    asyncio.run(main())