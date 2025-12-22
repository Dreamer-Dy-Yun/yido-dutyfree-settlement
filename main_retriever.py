############################################
# Module name : main_retriever
# Module class : ICTRetrieveRunner
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.01
# Updated at : 2025.12.01
# Supported by : ChatGPT-4o
# Note :
############################################



from DATABASE.config import CRUDer, cruder
from data_retriever import FileRetriever
import asyncio
import pandas as pd
from CUSTOMIZED.cust_logger import logger
from CUSTOMIZED.cust_retrier import Retrier

class ICTRetrieveRunner:

    _DICT_FR : dict[str, FileRetriever] = {} #메모이제이션 용
    _DOWNLOAD_BATCH_SIZE : int = 10
    _FETCH_LIST_LIMIT : int = 20
    _CRUDER : CRUDer | None = None
    _MAX_ATTEMPTS : int = 5

    @classmethod
    def set_max_attempts(cls, max_attempts: int) -> None:
        cls._MAX_ATTEMPTS = max_attempts

    @classmethod
    def set_cruder(cls, cruder: CRUDer) -> None:
        cls._CRUDER = cruder

    @classmethod
    async def reset_locks(cls) -> None:
        await cls._CRUDER.reset_locks()
        logger.info("Lock reset completed successfully")

    @classmethod
    def set_download_batch_size(cls, number_of_retrieve_files: int) -> None:
        cls._DOWNLOAD_BATCH_SIZE = number_of_retrieve_files

    @classmethod
    def set_fetch_list_limit(cls, fetch_list_limit: int) -> None:
        cls._FETCH_LIST_LIMIT = fetch_list_limit

    @classmethod
    async def reset_failed_processes_for_retry(cls, max_attempts: int = 5) -> None:
        await cls._CRUDER.reset_failed_processes_for_retry(max_attempts)
    
    async def run(self):

        await ICTRetrieveRunner.reset_failed_processes_for_retry(ICTRetrieveRunner._MAX_ATTEMPTS)

        df_instrument : pd.DataFrame = pd.DataFrame(await ICTRetrieveRunner._CRUDER.get_instrument_infos())
        
        # 먼저 모든 장비에 대해 FileRetriever 생성 및 연결 태스크 준비
        connection_tasks : list[asyncio.Task] = []
        fr_dict : dict[str, FileRetriever] = {}
        
        for row in df_instrument.itertuples(index=False):
            instrument_name:str = row.name
            host:str = row.host 
            user:str = row.user
            port:int = row.port
            dir_base_source:str = row.dir_base_source
            dir_base_destination:str = row.dir_base_destination
            ssh_key_path:str = row.ssh_key_path 

            if instrument_name not in ICTRetrieveRunner._DICT_FR:
                fr = FileRetriever(ICTRetrieveRunner._CRUDER).set_instrument_infos(instrument_name, host, user, port, ssh_key_path, dir_base_source, dir_base_destination)
                fr_dict[instrument_name] = fr
                # 연결을 병렬로 처리하기 위해 태스크로 생성
                connection_tasks.append(asyncio.create_task(fr.connect_to_instrument()))
            else:
                fr_dict[instrument_name] = ICTRetrieveRunner._DICT_FR[instrument_name]

        # 모든 연결을 병렬로 실행
        if connection_tasks:
            await asyncio.gather(*connection_tasks, return_exceptions=True)
            # 연결 완료 후 딕셔너리에 저장
            for instrument_name, fr in fr_dict.items():
                if instrument_name not in ICTRetrieveRunner._DICT_FR:
                    ICTRetrieveRunner._DICT_FR[instrument_name] = fr
        
        # 연결이 완료된 후 각 장비의 run() 태스크 생성
        tasks : list[asyncio.Task] = []
        for row in df_instrument.itertuples(index=False):
            instrument_name:str = row.name
            fr = fr_dict[instrument_name]

            fr.set_download_batch_size(ICTRetrieveRunner._DOWNLOAD_BATCH_SIZE)
            fr.set_fetch_list_limit(ICTRetrieveRunner._FETCH_LIST_LIMIT)

            retrier = Retrier.retry(
                lambda fr=fr: fr.run(),
                on_retry=lambda fr=fr: fr.connect_to_instrument(),
            )
            tasks.append(asyncio.create_task(retrier))

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("리트리빙 작업 완료")


async def main():
    import os
    from dotenv import load_dotenv
    from DATABASE.setup_db import setup_db
    from DATABASE.config import db_manager
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from WEB_SERVER.routers.settings import set_dir_base
    from pathlib import Path
    
    # 환경변수 로드
    load_dotenv()
    
    # DB 설정
    base_dir = Path(os.getenv("DIR_BASE_FOR_PARQUET", "C:/Users/user/ict_parquets"))
    set_dir_base(base_dir)
    await setup_db()
    
    # 리트리버 설정
    ICTRetrieveRunner.set_cruder(cruder)
    ICTRetrieveRunner.set_download_batch_size(int(os.getenv("DOWNLOAD_BATCH_SIZE", "10")))
    ICTRetrieveRunner.set_fetch_list_limit(int(os.getenv("FETCH_LIST_LIMIT", "20")))
    ICTRetrieveRunner.set_max_attempts(int(os.getenv("MAX_ATTEMPTS", "5")))
    await ICTRetrieveRunner.reset_locks()

    max_instances_retriever: int = int(os.getenv("MAX_INSTANCES_RETRIEVER", "1"))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ICTRetrieveRunner().run, name="파일 리트리버 작업", trigger=CronTrigger(second='*/5'), max_instances=max_instances_retriever, coalesce=True)
    scheduler.start()
    
    try:
        # 무한 루프로 실행 유지
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️ 리트리버 종료 중...")
    finally:
        scheduler.shutdown()
        await db_manager.dispose_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 리트리버 종료 중...")
        from DATABASE.config import db_manager
        asyncio.run(db_manager.dispose_pool())



