from OPEN_SSH.ict_data_extractor import ICTDataExtractor
from DATABASE.config import cruder, db_manager
from data_archiver import DataArchiver
import asyncio
from DATABASE.cruder import CRUDer
import pandas as pd
from pathlib import Path
from CUSTOMIZED.cust_logger import logger
import shutil
import os


class ICTArchiveRunner:


    SUB_DIR_SPEC = "SPEC"
    SUB_DIR_MEASURED = "MEASURED"
    SUB_DIR_SUCCESS = "SUCCESS"
    SUB_DIR_FAILURE = "FAILURE"

    def __init__(self) -> None:
        self.cruder: CRUDer = cruder
        self.data_archiver: DataArchiver = DataArchiver(db_manager)
        self.base_dir_sources: pd.DataFrame = pd.DataFrame()
        self.unparsed_infos: pd.DataFrame = pd.DataFrame()
        self.base_dir_destination: Path = Path("")


    def set_dir_destination(self, path_destination: Path):
        self.base_dir_destination = path_destination
        return self

    async def _get_base_dir_sources(self, instrument_name: str | None = None):
        # 리트리빙 시점의 목적지가 아카이빙 시점의 출발지.
        self.base_dir_sources = pd.DataFrame(await self.cruder.get_base_dir_destinations(instrument_name))
    
    async def _get_unparsed_infos(self, instrument_name: str | None = None, model_name: str | None = None):
        self.unparsed_infos = pd.DataFrame(await self.cruder.get_unparsed_infos(instrument_name, model_name))


    async def archive_single_file(self, instrument_name: str, source_csv_filepath: Path, base_dir_desti_for_parquet: Path, fullpath_original: Path, encoding: str = 'euc-kr'):
        path_to_move: Path = Path("")
        is_parsed: bool = False
        status: str = "PENDING"
        note: str = ""
        try:
            ict_data: ICTDataExtractor = ICTDataExtractor()
            # base_dirs_desti_for_csv : pd.DataFrame = pd.DataFrame(await self.cruder.get_base_dir_destinations(instrument_name))
            # base_dir_desti_for_csv : Path = Path(base_dirs_desti_for_csv.loc[base_dirs_desti_for_csv['name'] == instrument_name, 'dir_base_destination'].values[0])
            await asyncio.to_thread(ict_data.get,source_csv_filepath, instrument_name, encoding=encoding)
            
            # 모델 업데이트는 Retrieving 시점에 수행
            # await u.on_model(ict_data)
            await self.data_archiver.save_parquet_n_upsert(ict_data, "spec", base_dir_desti_for_parquet, self.SUB_DIR_SPEC)
            await self.data_archiver.save_parquet_n_upsert(ict_data, "measured", base_dir_desti_for_parquet, self.SUB_DIR_MEASURED)
            # path_to_move = base_dir_desti_for_csv / self.SUB_DIR_SUCCESS / Path(ict_data.data_path.name)
            is_parsed = True
            status = "ARCHIVED"
        except Exception as e:
            logger.error(f"Failed to archive {instrument_name} {source_csv_filepath}: {e}", exc_info=True)
            note = f"Failed to archive {instrument_name} {source_csv_filepath}: {e}"
            # path_to_move = base_dir_desti_for_csv / self.SUB_DIR_FAILURE / Path(ict_data.data_path.name)
            is_parsed = False
            status = "ERROR"
            raise  
        finally:
            if not path_to_move.parent.exists():
                os.makedirs(path_to_move.parent)
            # 경합 문제로 파일 이동 포기 
            # shutil.move(source_csv_filepath, path_to_move)
            path_to_move = source_csv_filepath
            await self.data_archiver.on_process_to_archive(ict_data.measured_by, ict_data.model_name, fullpath_original, path_to_move, is_parsed, status, note)


    async def run(self, encoding: str = 'euc-kr', max_concurrent: int = 8):
        await self._get_base_dir_sources()
        await self._get_unparsed_infos()

        sem = asyncio.Semaphore(max_concurrent) 
        
        async def archive_with_semaphore(row):
            async with sem:
                instrument_name: str = row.instrument_name
                model_name: str = row.model_name
                source_csv_filepath: Path = Path(row.path_full_destination)
                base_dir_destination: Path = self.base_dir_destination / instrument_name / model_name
                fullpath_original: Path = Path(row.path_full_source)
                await self.archive_single_file(instrument_name, source_csv_filepath, base_dir_destination, fullpath_original, encoding)
        
        tasks = [
            asyncio.create_task(archive_with_semaphore(row))
            for row in self.unparsed_infos.itertuples(index=False)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 에러 확인 및 로깅
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                row = list(self.unparsed_infos.itertuples(index=False))[i]
                from CUSTOMIZED.cust_logger import logger
                logger.error(f"Archive failed for {row.instrument_name}/{row.model_name}: {result}", exc_info=result)
        
        return results

    async def archive_sequential(self, encoding: str = 'euc-kr'):
        """순차 실행 버전 (테스트용)"""
        await self._get_base_dir_sources()
        await self._get_unparsed_infos()

        results = []
        for row in self.unparsed_infos.itertuples(index=False):
            # try:
                instrument_name: str = row.instrument_name
                model_name: str = row.model_name
                source_csv_filepath: Path = Path(row.path_full_destination)
                base_dir_destination: Path = self.base_dir_destination / instrument_name / model_name
                await self.archive_single_file(instrument_name, source_csv_filepath, base_dir_destination, encoding)
                results.append(None)
            # except Exception as e:
            #     from CUSTOMIZED.cust_logger import logger
            #     logger.error(f"Archive failed for {row.instrument_name}/{row.model_name}: {e}", exc_info=e)
            #     results.append(e)
        
        return results

# TEST
async def test():
    archiver = ICTArchiveRunner()
    archiver.set_dir_destination(Path("C:/Users/user/Novas_Ez"))
    await archiver.run()
    # await archiver.archive_sequential()  # 순차 실행 버전
    print("Archive completed")

if __name__ == "__main__":
    asyncio.run(test())
