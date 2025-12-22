############################################
# Module name : main_archiver
# Module class : ICTArchiveRunner
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.01
# Updated at : 2025.12.01
# Supported by : ChatGPT-4o
# Note :
############################################

from OPEN_SSH.ict_data_extractor import ICTDataExtractor
from DATABASE.config import cruder, db_manager
from data_archiver import DataArchiver
import asyncio
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
from CUSTOMIZED.cust_logger import logger
import os
from typing import Any


class ICTArchiveRunner:


    _SUB_DIR_SPEC : Path = Path("SPEC")
    _SUB_DIR_MEASURED : Path = Path("MEASURED")
    _SUB_DIR_SUCCESS : Path = Path("SUCCESS")
    _SUB_DIR_FAILURE : Path = Path("FAILURE")
    _BASE_DIR_DESTINATION : Path = Path("")

    def __init__(self) -> None:
        self.cruder: CRUDer = cruder
        self.data_archiver: DataArchiver = DataArchiver(db_manager)
        self.base_dir_sources: pd.DataFrame = pd.DataFrame()
        self.unparsed_infos: pd.DataFrame = pd.DataFrame()


    @classmethod
    def set_sub_dir_spec(cls, sub_dir_spec: Path | str) -> None:
        cls._SUB_DIR_SPEC = Path(sub_dir_spec)

    @classmethod
    def set_sub_dir_measured(cls, sub_dir_measured: Path | str) -> None:
        cls._SUB_DIR_MEASURED = Path(sub_dir_measured)

    @classmethod
    def set_sub_dir_success(cls, sub_dir_success: Path | str) -> None:
        cls._SUB_DIR_SUCCESS = Path(sub_dir_success)
        
    @classmethod
    def set_sub_dir_failure(cls, sub_dir_failure: Path | str) -> None:
        cls._SUB_DIR_FAILURE = Path(sub_dir_failure)

    @classmethod
    def set_dir_destination(cls, path_destination: Path | str) -> None:
        cls._BASE_DIR_DESTINATION = Path(path_destination)

    async def _get_base_dir_sources(self, instrument_name: str | None = None) -> pd.DataFrame:
        # 리트리빙 시점의 목적지가 아카이빙 시점의 출발지.
        self.base_dir_sources = pd.DataFrame(await self.cruder.get_base_dir_destinations(instrument_name))
    

    async def _get_unparsed_infos(self, instrument_name: str | None = None, model_name: str | None = None) -> pd.DataFrame:
        self.unparsed_infos = pd.DataFrame(await self.cruder.get_unparsed_infos(instrument_name, model_name))


    async def archive_single_file(self, instrument_name: str, source_csv_filepath: Path, base_dir_desti_for_parquet: Path, fullpath_original: Path, number_of_retries: int, encoding: str = 'euc-kr'):
        path_to_move: Path = Path("")
        is_parsed: bool = False
        status: str = "PENDING"
        note: str = ""
        try:    
            ict_data: ICTDataExtractor = ICTDataExtractor()
            # base_dirs_desti_for_csv : pd.DataFrame = pd.DataFrame(await self.cruder.get_base_dir_destinations(instrument_name))
            # base_dir_desti_for_csv : Path = Path(base_dirs_desti_for_csv.loc[base_dirs_desti_for_csv['name'] == instrument_name, 'dir_base_destination'].values[0])
            await asyncio.to_thread(ict_data.get,source_csv_filepath, instrument_name, encoding=encoding)
            
            await self.data_archiver.raise_if_points_mismatch(ict_data)

            # 모델을 먼저 등록
            # 원래는 리트리버에서 폴더명을 기반으로 등록하였으나, 폴더의 모델명과 파일 내부의 모델명이 다른 경우를 확인.(2025.12.01)
            # 따라서 아카이버에서 별도 등록. 
            await self.data_archiver.on_model(ict_data)
            await self.data_archiver.save_parquet_n_upsert(ict_data, "spec", base_dir_desti_for_parquet, self._SUB_DIR_SPEC)
            await self.data_archiver.save_parquet_n_upsert(ict_data, "measured", base_dir_desti_for_parquet, self._SUB_DIR_MEASURED)
            # path_to_move = base_dir_desti_for_csv / self.SUB_DIR_SUCCESS / Path(ict_data.data_path.name)
            is_parsed = True
            status = "ARCHIVED"
        except Exception as e:
            logger.error(f"Failed to archive {e}", exc_info=False)
            note = f"Failed to archive : {e}"
            # path_to_move = base_dir_desti_for_csv / self.SUB_DIR_FAILURE / Path(ict_data.data_path.name)
            is_parsed = False
            status = "ERROR"
            number_of_retries = number_of_retries + 1
            raise  
        finally:
            if not path_to_move.parent.exists():
                os.makedirs(path_to_move.parent)
            # 경합 문제로 파일 이동 포기 
            # shutil.move(source_csv_filepath, path_to_move)
            path_to_move = source_csv_filepath

            model_name: str = ict_data.model_name

            if not(instrument_name and model_name):
                process_info: list[dict[str, Any]] = await self.cruder.get_process_info_by_sourcepath(instrument_name, model_name, str(fullpath_original))
                instrument_name = process_info["instrument_name"]
                model_name = process_info["model_name"]
            await self.data_archiver.on_process_to_archive(instrument_name, model_name, fullpath_original, path_to_move, is_parsed, status, note, False, number_of_retries)


    async def run(self, encoding: str = 'euc-kr', max_concurrent: int = 8):
        await self._get_base_dir_sources()
        await self._get_unparsed_infos()
        
        # DataFrame을 리스트로 미리 변환 (itertuples 중복 호출 방지)
        rows_list = list(self.unparsed_infos.itertuples(index=False))
        
        if not rows_list:
            logger.info("No files to archive")
            return []
        
        sem = asyncio.Semaphore(max_concurrent) 
        
        async def archive_with_semaphore(row):
            async with sem:
                id: int = row.id
                instrument_name: str = row.instrument_name
                model_name: str = row.model_name
                source_csv_filepath: Path = Path(row.path_full_destination)
                base_dir_destination: Path = ICTArchiveRunner._BASE_DIR_DESTINATION
                fullpath_original: Path = Path(row.path_full_source)
                number_of_retries: int = row.number_of_retries
                await self.archive_single_file(instrument_name, source_csv_filepath, base_dir_destination, fullpath_original, number_of_retries,encoding)
        
        tasks = [
            asyncio.create_task(archive_with_semaphore(row))
            for row in rows_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # # 에러 확인 및 로깅
        # for i, result in enumerate(results):
        #     if isinstance(result, Exception):
        #         row = rows_list[i]  # 미리 변환한 리스트 사용
        #         from CUSTOMIZED.cust_logger import logger
        #         logger.error(f"Archive failed for {row.instrument_name}/{row.model_name}: {result}", exc_info=result)
        
        return results


async def main():
    import os
    from dotenv import load_dotenv
    from DATABASE.setup_db import setup_db
    from DATABASE.config import db_manager
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from pathlib import Path
    
    # 환경변수 로드
    load_dotenv()
    
    # DB 설정
    base_dir = Path(os.getenv("DIR_BASE_FOR_PARQUET", "C:/Users/user/ict_parquets"))
    await setup_db()
    
    # 아카이버 설정
    ICTArchiveRunner.set_dir_destination(base_dir)
    ICTArchiveRunner.set_sub_dir_spec(os.getenv("SUB_DIR_SPEC", "SPEC"))
    ICTArchiveRunner.set_sub_dir_measured(os.getenv("SUB_DIR_MEASURED", "MEASURED"))
    
    max_instances_archiver: int = int(os.getenv("MAX_INSTANCES_ARCHIVER", "5"))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ICTArchiveRunner().run, name="데이터 아카이버 작업", trigger=CronTrigger(second='*/5'), max_instances=max_instances_archiver, coalesce=True)
    scheduler.start()
    
    try:
        # 무한 루프로 실행 유지
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️ 아카이버 종료 중...")
    finally:
        scheduler.shutdown()
        await db_manager.dispose_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 아카이버 종료 중...")
        asyncio.run(db_manager.dispose_pool())
