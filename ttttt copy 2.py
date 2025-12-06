from pathlib import Path
from tkinter import N
import shutil
import os

from pydantic_core.core_schema import str_schema
from OPEN_SSH.ict_data_extractor import ICTDataExtractor
import pandas as pd
from DATABASE import pg_manager, models
from data_archiver import DataArchiver
import asyncio
from CUSTOMIZED.cust_logger import logger
from DATABASE.cruder import CRUDer
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# #TEST################################################################################################
DB_NAME = 'novas_ez'
DB_USER = 'admin'
DB_PASSWORD = '123!@#qwe'  
DB_HOST = 'localhost'
DB_PORT = 5432

db = pg_manager.PGDBManager(models.BaseModel, DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)

DESTINATION_PARENT_PATH = Path("C:/Users/user/Novas_Ez")



async def run_archivers():

    df_instrument : pd.DataFrame = pd.DataFrame(await cruder.get_instrument_infos())
    tasks : list[asyncio.Task] = []
    
    for row in df_instrument.itertuples(index=False):
        instrument_name:str = row.name
        host:str = row.host 
        user:str = row.user
        port:int = row.port
        dir_base_source:str = row.dir_base_source
        dir_base_destination:str = row.dir_base_destination
        ssh_key_path:str = row.ssh_key_path 

        if instrument_name not in DICT_FR:
            fr = FileRetriever(cruder).set_instrument_infos(instrument_name, host, user, port, ssh_key_path, dir_base_source, dir_base_destination)
            await fr.connect_to_instrument()
            DICT_FR[instrument_name] = fr
        else:
            fr = DICT_FR[instrument_name]

        retrier = Retrier.retry(lambda: fr.run(50), on_retry=lambda: fr.connect_to_instrument())
        tasks.append(asyncio.create_task(retrier))

        # 문제시 이걸로 백업
        # fr = FileRetriever(cruder).set_instrument_infos(instrument_name, host, user, port, ssh_key_path, dir_base_source, dir_base_destination)
        # await fr.connect_to_instrument()
        # tasks.append(asyncio.create_task(fr.run(50)))


    await asyncio.gather(*tasks, return_exceptions=True)

def schedule(
    db: pg_manager.PGDBManager, 
    source_parent_path: Path, 
    desti_parent_path: Path, 
    desti_sub_path_spec: Path, 
    desti_sub_path_measured: Path, 
    success_parent_path: Path, 
    fail_parent_path: Path, 
    extension: str = "csv", 
    encoding: str = "euc-kr", 
    semaphore_value: int = 8
    ):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        batch_process_ict_data, 
        args=[
                db, 
                source_parent_path, 
                desti_parent_path, 
                desti_sub_path_spec, 
                desti_sub_path_measured, 
                success_parent_path, 
                fail_parent_path, 
                extension,
                encoding, 
                semaphore_value
            ], 
            trigger=CronTrigger(day_of_week='mon-fri', hour='8,10,12,14,16,18,20', minute='50')
        )
    scheduler.start()


async def archive(
    db: pg_manager.PGDBManager, 
    measured_by: str, 
    source_csv_filepath: Path,
    desti_parent_path: Path,
    desti_sub_path_spec: Path,
    desti_sub_path_measured: Path,
    encoding: str = 'euc-kr'
    ):

    ict_data = ICTDataExtractor()
    await asyncio.to_thread(ict_data.get,source_csv_filepath, measured_by, encoding=encoding)

    u = DataArchiver(db)

    # TODO : backup 업데이트 및 데이터 미등록 리스트 확보

    # 모델 업데이트는 Retrieving 시점에 수행
    # await u.on_model(ict_data)

    await u.save_parquet_n_upsert(ict_data, "spec", desti_parent_path, desti_sub_path_spec)

    await u.save_parquet_n_upsert(ict_data, "measured", desti_parent_path, desti_sub_path_measured)


async def process_archive(
    db: pg_manager.PGDBManager,
    measured_by: str,
    source_csv_filepath: Path,
    desti_parent_path: Path,
    desti_sub_path_spec: Path,
    desti_sub_path_measured: Path,
    success_parent_path: Path = None,
    fail_parent_path: Path = None,
    encoding: str = 'euc-kr'
    ):
    try:

        if not source_csv_filepath.exists():
            raise FileNotFoundError(f"소스 파일이 존재하지 않습니다: {source_csv_filepath}")

        if not desti_parent_path.exists():
            raise FileNotFoundError(f"목적지의 폴더가 존재하지 않습니다: {desti_parent_path}")

        success_parent_path = desti_parent_path / "SUCCESS" if success_parent_path is None else success_parent_path
        fail_parent_path = desti_parent_path / "FAILURE" if fail_parent_path is None else fail_parent_path

        u = DataArchiver(db)

        status = 1
        is_parsed : bool = True
        path_to_move : Path = success_parent_path / source_csv_filepath.name
        success_parent_path.mkdir(parents=True, exist_ok=True)

        await archive(db, measured_by, source_csv_filepath, desti_parent_path, desti_sub_path_spec, desti_sub_path_measured, encoding)

        if path_to_move.exists():
            raise FileExistsError(f"파일이 이미 존재합니다: {path_to_move}")

    except Exception as e:
        status = -1
        is_parsed = False
        path_to_move = fail_parent_path / source_csv_filepath.name

        fail_parent_path.mkdir(parents=True, exist_ok=True)
        
        if path_to_move.exists():
            os.remove(path_to_move)
    
    finally:
        shutil.move(source_csv_filepath, path_to_move)

        try:
            # 여기서 에러나면 크래시. 진행하면 안됨. 그냥 크래시.
            await u.on_process_to_archive(measured_by,path_to_move, is_parsed, status)
        except Exception as e:
            logger.error(f"아카이빙 프로세스 에러: {e}", exc_info=True)
            # 로그만 남기고 크래시
            raise
        
        return is_parsed


#  
async def batch_process_ict_data(
    db: pg_manager.PGDBManager,
    source_parent_path: Path, 
    desti_parent_path: Path, 
    desti_sub_path_spec: Path, 
    desti_sub_path_measured: Path,
    success_parent_path: Path,
    fail_parent_path: Path,
    extension: str = "csv",
    encoding: str = "euc-kr",
    semaphore_value: int = 8
    ):
    ict_name : str = ""
    sem = asyncio.Semaphore(semaphore_value)  # 동시 실행 제한

    async def run_with_semaphore(
        db: pg_manager.PGDBManager,
        ict_name: str,
        file_path: Path,
        desti_parent_path: Path,
        desti_sub_path_spec: Path,
        desti_sub_path_measured: Path,
        success_parent_path: Path,
        fail_parent_path: Path,
        encoding: str,
    ):
        async with sem:
            return await process_archive(
                db,
                ict_name,
                file_path,
                desti_parent_path,
                desti_sub_path_spec,
                desti_sub_path_measured,
                success_parent_path,
                fail_parent_path,
                encoding,
            )

    cruder = CRUDer(db)
    instruments : list[str] = await cruder.get_instrument_names()    

    main_tasks : list[asyncio.Task] = []
    for source_path in source_parent_path.iterdir():
        ict_name : str = source_path.name
        if ict_name not in instruments:
            logger.warning(f"ICT 이름이 존재하지 않습니다: {ict_name}")
            continue

        sub_tasks : list[asyncio.Task] = []
        for file_path in list(source_path.rglob(f"*.{extension}")):
            # 서브에서 크래시 나면 에외 처리 없이 크래시 낼 것. 여기에서 크래시 나는 것은 아카이빙 크래시임.
            sub_task = asyncio.create_task(
                run_with_semaphore(
                    db,
                    ict_name,
                    file_path,
                    desti_parent_path,
                    desti_sub_path_spec,
                    desti_sub_path_measured,
                    success_parent_path,
                    fail_parent_path,
                    encoding,
                )
            )
            sub_tasks.append(sub_task)
        main_tasks.append(asyncio.gather(*sub_tasks))
    await asyncio.gather(*main_tasks)


# TEST################################################################################################
async def test():
    source_parent_path = Path(r"D:\csv")
    file_pathes : list[Path] = list(source_parent_path.rglob("*.csv"))
    desti_sub_path_spec = Path(".", "TEST", "SPEC")
    desti_sub_path_measured = Path(".", "TEST", "MEASURED")

    for file_path in file_pathes:
        print(file_path)
        await archive(db, "test_name", file_path, DESTINATION_PARENT_PATH, desti_sub_path_spec, desti_sub_path_measured)


if __name__ == "__main__":
    asyncio.run(test())