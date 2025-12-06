from CUSTOMIZED.cust_retrier import Retrier   
from OPEN_SSH.ssh_connector import OpenSSHConnector
from DATABASE.cruder import CRUDer
from pathlib import Path
from datetime import datetime
import pandas as pd

# TODO : 리팩토링 대상. 맘이 좀 급해서 신경 많이 못씀

class FileRetriever:
    """

    ※ 데이터 리스트 확보는 하였으나, 파일 복사 중간에 에러 발생 가능하므로, DB에서 이력 관리.
    
    ※ 애초에 리스트도 가져오지 못하는 경우는 방법이 없으므로 해당 경우에는 재시도 할 것

    ※ 현 시점 아직 ICT내의 폴더 구조 파악 안됨. 아래와 같다고 추정 중

        모델 > YYYY > MM > DD >(CSV등의 파일들)
    """

    retrier : Retrier = Retrier()
    def __init__(
        self,
        cruder: CRUDer,
        instrument_name: str,
        hostname: str,
        username: str,
        port: int,
        dir_source_base: str,
        ssh_key_path: str,
        accessible: bool
    ) -> None:
        self.cruder: CRUDer = cruder
        self.instrument_name: str = instrument_name
        self.hostname: str = hostname
        self.username: str = username
        self.port: int = port
        self.dir_source_base: str = dir_source_base
        self.ssh_key_path: str = ssh_key_path
        self.accessible: bool = accessible
        self._unretrieved_files:list[str] = []

    async def run(self, dir_base_desti:Path, dir_sub_desti:Path):
        await self.set_status(self.instrument_name, self.dir_source_base, dir_base_desti, dir_sub_desti)
        await self.retrieve_files(dir_base_desti / dir_sub_desti)


    async def set_status(self, measured_by:str, dir_source_base:Path, dir_desti_base:Path, dir_desti_sub:Path):
        """ICT 장비에서 확보한 csv 파일 리스트를 DB의 process 테이블에 업서트"""

        model_names: list[str] = await self.cruder.get_model_names()  # TODO : 여기서 모델명 받으면 안됨. 추가 모델 못받게 됨. 폴더 리스트 가져와서 받는 방법으로.
        from_datetime: datetime = await self.cruder.get_latest_retrieved_time(measured_by)
        to_datetime: datetime = datetime.now()
        dir_sources: list[Path] = []

        for model_name in model_names:
            target_dirs = FileRetriever.make_sub_dirs_for_source(model_name, from_datetime, to_datetime)
            dir_sources.append(dir_source_base / target_dirs)

        target_files: set = await self._get_targetfiles_from_ict(dir_sources, from_datetime, to_datetime)

        data: list =[]
        for fullpath_source in target_files:
            file_name: str = Path(fullpath_source).name
            fullpath_desti: Path = dir_desti_base / dir_desti_sub / file_name
            is_retrieved: bool = False
            if fullpath_desti.exists() :
                is_retrieved = True

            record: dict ={}
            record.update({"instrument_name": self.instrument_name})
            record.update({"path_full_source": fullpath_source})
            # record.update({"file_hash": ""}) 
            record.update({"path_full_current": fullpath_desti})
            record.update({"is_retrieved": is_retrieved}) 
            data.append(record)

        await self.cruder.upsert_process(pd.DataFrame(data))


    async def retrieve_files(self,dir_destination:Path):
        """
        ICT 파일 확보 및 결과 기재
        path_destination : 해당 폴더 이하의 폴더 물색. 대상 파일은 CSV
        """
        file_list = await self.cruder.get_unretrieved_files()

        # ICT 에서 데이터 Pulling
        async with OpenSSHConnector(self.hostname, self.username) as ssh:
            results:dict[str:bool] = await FileRetriever.retrier.retry(
                lambda: ssh.download_files(dir_destination, file_list), 
                lambda: ssh.connect_with_private_key()
            )
        
        # 풀링한 결과를 DB에 업서트하기 위해 변환
        result_lists: list[dict[str, str | bool]] = [{'fullpath_source': path, 'is_retrieved' : result} for path, result in results.items()]

        # DB 업서트
        await self.cruder.upsert_process(pd.DataFrame(result_lists))


    async def _get_targetfiles_from_ict(
        self, 
        path_sources: list[Path], 
        from_datetime: datetime | None = None, 
        to_datetime: datetime | None = None, 
        extensions: str = "csv"
        ) -> set:
        """ICT 기기에서 데이터 리스트 확보"""
        async with OpenSSHConnector(self.hostname, self.username) as ssh:
            await FileRetriever.retrier.retry(
                lambda: ssh.get_sourcefile_list_from_multiple_dirs(path_sources, after=from_datetime, before=to_datetime), 
                lambda: ssh.connect_with_private_key()
                )
            return await ssh.filter_sourcefiles_by_ext(extensions)


    @staticmethod
    def make_sub_dirs_for_source(model_name : str, from_date: datetime | None = None, to_date: datetime | None = None) -> list[Path]:
        # 폴더 형태
        # \DB92-05165A\2025\09\02\OK
        # \DB92-05165A\2025\09\02\NG 
        path_list : list[path] = []
        for date in range(from_date, to_date):
            path = Path(model_name) / date.year.zfill(4) / date.month.zfill(2) / date.day.zfill(2)
            path_list.append(path)
        return path_list



# #TEST#############################################################

# import asyncio    
# 접속 정보 설정
# DB_NAME = 'postgres'
# DB_USER = 'postgres'
# DB_PASSWORD = '123!@#qwe'  
# DB_HOST = 'localhost'
# DB_PORT = '5432'

# db = pg_manager.PGDBManager(models.BaseModel, DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)
