from pathlib import Path

from pydantic_core.core_schema import str_schema
from OPEN_SSH.ict_data_extractor import ICTDataExtractor
from DATABASE import pg_manager, models
from data_archiver import DataArchiver
import asyncio
from CUSTOMIZED.cust_logger import logger
from DATABASE.cruder import CRUDer
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger 
import os
import shutil

class ICTArchiveRunner:
    # 이하는 상수. 
    STR_SUCCESS = "SUCCESS"
    STR_FAILURE = "FAILURE"
    STR_SPEC = "SPEC"
    STR_MEASURED = "MEASURED"

    def __init__(self, db: pg_manager.PGDBManager):
        self.db = db
        self.data_archiver = DataArchiver(self.db)
        self.cruder = CRUDer(self.db)
        self.dir_success = None
        self.dir_failure = None
        self.dir_desti_sub_spec = None
        self.dir_desti_sub_measured = None


    async def archive(self, measured_by: str, dir_desti_base: Path, fullpath_source_csv: Path, encoding: str = "euc-kr"):
        try:
            if not fullpath_source_csv.exists():
                raise FileNotFoundError(f"소스 파일이 존재하지 않습니다: {fullpath_source_csv}")

            if not dir_desti_base.exists():
                raise FileNotFoundError(f"목적지의 폴더가 존재하지 않습니다: {dir_desti_base}")

            status = 1
            is_parsed : bool = True
            path_to_move : Path = self.dir_success / fullpath_source_csv.name

            ict_data = ICTDataExtractor()

            await asyncio.to_thread(ict_data.get, fullpath_source_csv, measured_by, encoding=encoding)

            await self.data_archiver.on_model(ict_data)

            await self.data_archiver.save_parquet_n_upsert(ict_data, "spec", dir_desti_base, self.dir_desti_sub_spec)
            await self.data_archiver.save_parquet_n_upsert(ict_data, "measured", dir_desti_base, self.dir_desti_sub_measured)

            print(path_to_move)
            if path_to_move.exists():
                raise FileExistsError(f"파일이 이미 존재합니다: {path_to_move}")

        except Exception as e:
            status = -1
            is_parsed = False
            path_to_move = self.dir_failure / fullpath_source_csv.name

            self.dir_failure.mkdir(parents=True, exist_ok=True)
            
            if path_to_move.exists():
                os.remove(path_to_move)
        
        finally:
            shutil.move(fullpath_source_csv, path_to_move)

            try:
                # 여기서 에러나면 크래시. 진행하면 안됨. 그냥 크래시.
                await self.data_archiver.on_process_to_archive(measured_by, path_to_move, is_parsed, status)
            except Exception as e:
                logger.error(f"아카이빙 프로세스 에러: {e}", exc_info=True)
                # 로그만 남기고 크래시
                raise
            
            return is_parsed


    async def batch_process_ict_data(self, dir_source_base: Path, dir_desti_base: Path, semaphore_value: int = 8, extension: str = "csv", encoding: str = "euc-kr"):
        """
        source 디렉토리 구조
        - [dir_source_base]
            - [ict_name] : 반드시 DB에 등록되어 있는 ICT 이름이어야만 함.
                - [file_name].csv : 반드시 CSV 파일이어야만 함.
        """
        
        ict_name : str = ""

        self.dir_desti_base = dir_desti_base
        self.dir_success = dir_desti_base / self.STR_SUCCESS if self.dir_success is None else self.dir_success
        self.dir_failure = dir_desti_base / self.STR_FAILURE if self.dir_failure is None else self.dir_failure
        self.dir_desti_sub_spec = dir_desti_base / self.STR_SPEC if self.dir_desti_sub_spec is None else self.dir_desti_sub_spec
        self.dir_desti_sub_measured = dir_desti_base / self.STR_MEASURED if self.dir_desti_sub_measured is None else self.dir_desti_sub_measured

        sem = asyncio.Semaphore(semaphore_value)  # 동시 실행 제한

        self.dir_success.mkdir(parents=True, exist_ok=True)
        self.dir_failure.mkdir(parents=True, exist_ok=True)
        self.dir_desti_sub_spec.mkdir(parents=True, exist_ok=True)
        self.dir_desti_sub_measured.mkdir(parents=True, exist_ok=True)

        async def run_with_semaphore(measured_by: str, dir_desti_base: Path, fullpath_source: Path, encoding: str = "euc-kr"):
            async with sem:
                return await self.archive(measured_by, dir_desti_base, fullpath_source, encoding)

        instruments : list[str] = await self.cruder.get_instrument_names()    

        main_tasks : list[asyncio.Task] = []
        for dir_source_sub in dir_source_base.iterdir():
            ict_name = dir_source_sub.name
            if ict_name not in instruments:
                logger.warning(f"ICT 이름이 존재하지 않습니다: {ict_name}")
                continue

            sub_tasks : list[asyncio.Task] = []
            for fullpath_source in list(dir_source_sub.rglob(f"*.{extension}")):
                # 서브에서 크래시 나면 예외 처리 없이 크래시 낼 것. 여기에서 크래시 나는 것은 아카이빙 크래시임.
                sub_task = asyncio.create_task(run_with_semaphore(ict_name, dir_desti_base, fullpath_source, encoding))
                sub_tasks.append(sub_task)
            main_tasks.append(asyncio.gather(*sub_tasks))
        await asyncio.gather(*main_tasks)


# ###################################################################################

async def schedule(
    db: pg_manager.PGDBManager, 
    dir_source_base: Path, 
    dir_desti_parent: Path, 
    cron_trigger: CronTrigger,
    dir_desti_sub_spec: Path|None, 
    dir_desti_sub_measured: Path|None, 
    dir_success: Path|None, 
    dir_failure: Path|None, 
    extension: str = "csv", 
    encoding: str = "euc-kr", 
    semaphore_value: int = 8
    ):

    ict_archive_runner = ICTArchiveRunner(db)
    ict_archive_runner.dir_success = dir_success 
    ict_archive_runner.dir_failure = dir_failure 
    ict_archive_runner.dir_desti_sub_spec = dir_desti_sub_spec 
    ict_archive_runner.dir_desti_sub_measured = dir_desti_sub_measured 

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        ict_archive_runner.batch_process_ict_data, 
        args=[dir_source_base, dir_desti_parent, semaphore_value, extension, encoding], trigger=cron_trigger
        )
    scheduler.start()


# TEST################################################################################################
async def test():

    DB_NAME = 'novas_ez'
    DB_USER = 'admin'
    DB_PASSWORD = '123!@#qwe'  
    DB_HOST = 'localhost'
    DB_PORT = 5432

    db = pg_manager.PGDBManager(models.BaseModel, DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)

    DESTINATION_PARENT_PATH = Path("C:/Users/user/Novas_Ez")

    ict_archive_runner = ICTArchiveRunner(db)
    await ict_archive_runner.batch_process_ict_data(Path(r"D:\ICT_TEST"), Path(r"D:\ICT_TEST_ARCHIVE"))

if __name__ == "__main__":
    asyncio.run(test())