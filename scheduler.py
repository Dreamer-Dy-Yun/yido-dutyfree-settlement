from typing import Any


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import time
import logging
from sqlalchemy import select
from DATABASE import models, pg_manager
from data_retriever import FileRetriever
import pandas as pd
from pathlib import Path


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_instrument_infos(db_name:str, db_user:str, db_password:str, db_host:str, db_port:int) -> pd.DataFrame:
    async with pg_manager.PGDBManager(models.BaseModel, db_name, db_user, db_password, db_host, db_port) as session:
        result = await session.execute(select(models.Instrument))
        rows = result.fetchall()
        return pd.DataFrame([dict[Any, Any](row._mapping) for row in rows])


async def scheduled_task(name:str):
    """예약된 작업 실행"""
    try:
        logger.info(f"✅{name} 작업 실행됨: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        # 여기에 실제 작업 로직 추가
    except Exception as e:
        logger.error(f"{name} 작업 실행 중 오류 발생: {e}")


async def main():
    db_name = 'postgres'
    db_user = 'postgres'
    db_password = '123!@#qwe'  
    db_host = 'localhost'
    db_port = 5432

    base_path:Path =Path[""]
    sub_path:Path =Path[""]

    df_instrument:pd.DataFrame = get_instrument_infos(db_name, db_user, db_password, db_host, db_port)

    for row in df_instrument.itertuples(index=False):
        name:str = row.name
        host:str = row.host 
        user:str = row.user
        port:int = row.port
        base_path_source:str = row.base_path_source
        ssh_key_path:str = row.ssh_key_path 
        accessible:bool = row.accessible 
        # network_name:str = row.network_name
        # network_password:str = row.network_password
        async with pg_manager.PGDBManager(models.BaseModel, db_name, db_user, db_password, db_host, db_port) as db:
            fr = FileRetriever(db,name,host,user,port,base_path_source,ssh_key_path,accessible)
            await fr.set_status(base_path, sub_path)
            # await fr.retrieve_files(base_path / sub_path)





    try:
        scheduler = AsyncIOScheduler()
        
        # 평일 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00에 실행
        scheduler.add_job(scheduled_task, args= ["홍길동"],trigger = CronTrigger(day_of_week='mon-fri', hour='8,10,12,14,16,18,20', minute='50'))
        scheduler.add_job(scheduled_task, args= ["윤대영"],trigger = CronTrigger(day_of_week='mon-fri', hour='8,10,12,14,16,18,20', minute='50'))
        scheduler.start()
        logger.info("📌 스케줄러 시작됨 (평일 08,10,12,14,16,18,20시)")
        
        # 무한 루프 (조용히 대기)
        while True:
            await asyncio.sleep(3600)  # 1시간마다 체크
            
    except KeyboardInterrupt:
        logger.info("스케줄러 종료 중...")
        scheduler.shutdown()
        logger.info("스케줄러 종료됨")
    except Exception as e:
        logger.error(f"스케줄러 오류: {e}")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
