from CUSTOMIZED.cust_logger import logger   
import CUSTOMIZED.cust_powershell as ps
from OPEN_SSH.ssh_connector import OpenSSHConnector
from DATABASE.cruder import CRUDer
from DATABASE.config import db_manager
from pathlib import Path
from datetime import datetime, date
from typing import Any, Self
import pandas as pd
import asyncio
import json
import uuid
from CUSTOMIZED.cust_hasher import Hasher

# 1. 인스트루먼트 정보 확보 : 외부에서 주입..
# 2. 커넥션 시도(n회) : OK
#    - 실패 시 : accessible 값 False로 업데이트
#    - 성공 시 : accessible 값 True로 업데이트
# 이하는 성공한 장비 리스트 대상
# 3. 모델 리스트 확보 (신규 모델 생성 대응) : OK
# 4. DB 내의 각 장비/모델별 최종 데이터 풀링 일자 확인, 경로 확보 : OK
# 5. 각 모델의 해당 일자 이후의 폴더들을 대상으로 하여, 해당 일시 이후에 생성된 파일 조회 (생성일시 기준) : OK
# 6. 풀링 시점 변수에 저장 : OK
# 7. 풀링 대상 리스트 DB에 저장 : OK
# 8. 풀링 대상 리스트를 대상으로 하여, csv 파일 풀링 시작. : OK
# 9. DB에 성패 반영 : OK


# TODO : 리팩토링 대상. 맘이 좀 급해서 신경 많이 못씀


class FileRetriever:
    """

    ※ 데이터 리스트 확보는 하였으나, 파일 복사 중간에 에러 발생 가능하므로, DB에서 이력 관리.
    
    ※ 애초에 리스트도 가져오지 못하는 경우는 방법이 없으므로 해당 경우에는 재시도 할 것

    ※ 현 시점 아직 ICT내의 폴더 구조 파악 안됨. 아래와 같다고 추정 중   

        모델 > YYYY > MM > DD >(CSV등의 파일들)
    """

    def __init__(self, cruder: CRUDer) -> None:
        self.ssh: OpenSSHConnector | None = None
        self.cruder: CRUDer = cruder
        self.instrument_name: str | None = None
        self.hostname: str | None = None
        self.username: str | None = None
        self.port: int | None = None
        self.dir_source_base: Path | None = None
        self.dir_destination_base: Path | None = None
        self.ssh_key_path: Path | None = None
        self.accessible: bool = True
        self._unretrieved_files:list[str] = []
        self.is_instrument_info_set: bool = False
        self._download_batch_size: int = 20
        self._fetch_list_limit: int = 20


    def set_download_batch_size(self, num: int) -> Self:
        self._download_batch_size = num
        return self

    def set_fetch_list_limit(self, num: int) -> Self:
        self._fetch_list_limit = num
        return self

    def set_instrument_infos(self, instrument_name: str, host: str, user: str, port: int, ssh_key_path: str, dir_base_source: str, dir_destination_base: str) -> Self:
        self.instrument_name = instrument_name
        self.hostname = host
        self.username = user
        self.port = port
        self.ssh_key_path = None if ssh_key_path is None else Path(ssh_key_path)
        self.dir_base_source = dir_base_source
        self.dir_destination_base = dir_destination_base
        self.is_instrument_info_set = True
        return self


    async def run(self) -> None:
        log_msg :str = ""
        model_name : str = ""
        instrument_name : str = ""
        color_set : str = "\033[31m"
        color_reset : str = "\033[0m"
        instrument_name_for_log : str = color_set + (self.instrument_name or "Unknown") + color_reset

        try:
            if not self.is_instrument_info_set:
                logger.error("Instrument information is not set")
                return

            instrument_name = self.instrument_name
            dir_base_source : Path = Path(self.dir_base_source)
            dir_destination_base : Path = Path(self.dir_destination_base)

            if self.ssh is None or not await self.ssh.is_connected():
                raise ConnectionError(f"SSH connection not available for {instrument_name_for_log}. Reconnection will be attempted.")
            
            ssh = self.ssh

            logger.info(f"Accessing FileRetriever for {instrument_name_for_log}")

            model_names : pd.DataFrame = await self.get_model_names_from_ict(ssh, Path(dir_base_source))

            if model_names.empty:
                raise ValueError(f"No model names found for {instrument_name_for_log}")

            await self.upsert_model_names(model_names) #모델 추가는 자주 없을텐데 이렇게 매번 하는게 맞는건지... 그렇다고 안하거나 매번 비교해서 쓰기도 그렇고..

            df_target : pd.DataFrame = self.create_initial_target_dataframe(instrument_name, model_names)
 
            df_lps : pd.DataFrame = await self.get_latest_path_full_sources(instrument_name)

            if not df_lps.empty:
                df_target = self.apply_result_to_target_dataframe(df_target, df_lps)

            for xrow in df_target.itertuples(index=False):
                instrument_name = xrow.instrument_name
                model_name = xrow.model_name
                exclusive_file_names = xrow.path_full_sources
                latest_retrieved_time = xrow.created_at
                await self._process_single_model(ssh, instrument_name, model_name, dir_base_source, dir_destination_base, latest_retrieved_time, self._fetch_list_limit, exclusive_file_names)
            if df_target.empty:
                log_msg = f" - {instrument_name_for_log} has no target data to retrieve."
            else:
                log_msg = f" - {instrument_name_for_log} completed successfully."
        except Exception as e:
            log_msg = f" - {instrument_name_for_log} : {model_name} Error in run: {e}"
            raise
        finally:
            # 연결 안끊고 있는 연결 계속 사용.
            # await self.ssh.close() 
            if log_msg:
                logger.info(log_msg)

    def create_initial_target_dataframe(self, instrument_name: str, model_names: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
                    "instrument_name": [instrument_name] * len(model_names),
                    "model_name": model_names["name"].to_list(),
                    "path_full_sources": [[] for _ in range(len(model_names))],  # 각 행마다 독립적인 빈 리스트
                    "created_at": [datetime.min] * len(model_names)
                })

    def apply_result_to_target_dataframe(self, df_target: pd.DataFrame, result: pd.DataFrame) -> pd.DataFrame:
        df = df_target.copy()
        # result를 model_name을 인덱스로 하는 딕셔너리로 변환 (빠른 조회)
        result_dict = result.set_index("model_name").to_dict("index")
        
        for idx, row in df.iterrows():
            model_name = row["model_name"]
            if model_name in result_dict:
                df.loc[idx, "path_full_sources"] = result_dict[model_name]["path_full_sources"]
                df.loc[idx, "created_at"] = result_dict[model_name]["created_at"]
        return df

    async def _process_single_model(
        self, 
        ssh: OpenSSHConnector,
        instrument_name: str,
        model_name: str,
        dir_base_source: Path,
        dir_destination_base: Path,
        latest_retrieved_time: datetime,
        retrieve_count_of_each_model: int,
        exclusive_fullpathes: list[Path] = []
        ):
        # logger.info(f" - Getting data from {instrument_name} : {model_name}")
        df_target_dir : pd.DataFrame = await self.get_target_dirs_from_ict(ssh, Path(dir_base_source) / model_name)
        df_target_dir : pd.DataFrame = df_target_dir[df_target_dir["date"] >= latest_retrieved_time.date()]
        if df_target_dir.empty:
            return
        target_file_list : pd.DataFrame = await self.get_target_file_list_from_ict(ssh, df_target_dir["FullName"].to_list(), latest_retrieved_time, exclusive_fullpathes, retrieve_count_of_each_model)
        
        if not target_file_list.empty:
            # TODO : 별도 함수 분리 할 것
            df : pd.DataFrame = self.make_void_dataframe_for_process()

            subdir_destination = dir_destination_base / instrument_name / model_name
            series_fullpath_destination = pd.Series([str(subdir_destination / Path(path).name) for path in target_file_list["FullName"]])
            series_created_at = pd.Series([datetime.fromtimestamp(int(time.strip('/Date()')) / 1000.0) for time in target_file_list["CreationTime"]])
            
            df["path_full_destination"] = series_fullpath_destination
            df["created_at"] = series_created_at
            df["hashed"] = None
            df["instrument_name"] = instrument_name
            df["model_name"] = model_name
            df["path_full_source"] = target_file_list["FullName"]
            df["is_retrieved"] = False
            df["retrieved_at"] = None
            await self.cruder.upsert_process(df)

        # DB에서 다운로드 대상 리스트 확보 (방급 업데이트한 리스트 + 모종의 이유로 다운로드 되지 않은 리스트)
        df_to_download : pd.DataFrame = await self.get_unretrieved_files(instrument_name, model_name, limit=self._download_batch_size)
        await self.retrieve_files(ssh, df_to_download)


    def make_void_dataframe_for_process(self) -> pd.DataFrame:
        return pd.DataFrame(columns=['instrument_name', 'model_name', 'path_full_source', 'path_full_destination', 'is_retrieved', 'retrieved_at', 'created_at', 'hashed'])


    async def get_target_file_list_from_ict(self, ssh: OpenSSHConnector, dir_source: Path, since_datetime: datetime, exclusive_fullpathes: list[Path] = [], max_count: int = 20) -> pd.DataFrame:
        cmd_source = ps.Get_ChildItem(dir_source).recursive(True).build()
        cmd_selection = ps.Select().full_name().creation_time(with_milliseconds=True).first(max_count).build()
        cmd_condition = ps.Filter.container("file") & ps.Filter.by_extension("csv") & ps.Filter.since(since_datetime) 
        for fullpath in exclusive_fullpathes:
            cmd_condition = cmd_condition & ~ ps.Filter.by_full_name(fullpath)
        cmd_sort = ps.Sort().by_creation_time().build()
        cmd_consumer = ps.ToJson().compress().build()
        ps_cmd = (
            ps.PSCommand()
            .set_source(cmd_source)
            .set_condition(cmd_condition)
            .set_selection(cmd_selection)
            .set_sort(cmd_sort)
            .set_consumer(cmd_consumer)
            .build()
        )
        result = await ssh.run_command(ps_cmd)

        if not result.stdout or not result.stdout.strip():
            return pd.DataFrame(columns=['FullName', 'CreationTime'])
        json_result = self.powershell_reponse_to_json(result.stdout)
        df = pd.DataFrame(json_result)
        return df


    async def get_target_dirs_from_ict(self, ssh: OpenSSHConnector, dir_source_base: Path) -> pd.DataFrame:
        cmd_source = ps.Get_ChildItem(dir_source_base).recursive(True).build()
        cmd_condition = ps.Filter.container("directory")
        cmd_selection = ps.Select().full_name().build()
        cmd_consumer = ps.ToJson().compress().build()
        ps_cmd = ps.PSCommand().set_source(cmd_source).set_condition(cmd_condition).set_selection(cmd_selection).set_consumer(cmd_consumer).build()
        result = await ssh.run_command(ps_cmd)
        json_result = self.powershell_reponse_to_json(result.stdout)
        df = pd.DataFrame(json_result)
        df_empty = pd.DataFrame(columns=["FullName", "date"])
        
        # 빈 DataFrame이거나 FullName 컬럼이 없으면 빈 DataFrame 반환 (date 컬럼 포함)
        if df.empty or "FullName" not in df.columns:
            return df_empty
        
        for fullname in df["FullName"]:
            is_date_structured, date = self.is_date_structured_path(Path(fullname))
            if is_date_structured:
                df.loc[df["FullName"] == fullname, "date"] = date
        
        # 'date' 컬럼이 있으면 필터링, 없으면 빈 DataFrame 반환
        if "date" in df.columns:
            return df[df["date"].notna()]
        else:
            return df_empty
        

    @staticmethod
    def is_date_structured_path(
        directory: Path, 
        start_index: int | None = -3, 
        end_index: int | None= None, 
        format: str = "%Y/%m/%d"
        ) -> tuple[bool, date | None]:
        extracted_date : date | None = None
        try:
            parts = directory.parts[start_index:end_index]
            str_ymd = "/".join(parts)
            extracted_date = datetime.strptime(str_ymd, format).date()
            return True, extracted_date
        except (ValueError, IndexError):
            return False, None


    @staticmethod
    def powershell_reponse_to_json(json_str: str) -> list[dict[str, Any]]:
        try:
            if not json_str or not json_str.strip():
                return []
            json_result = json.loads(json_str)
            if isinstance(json_result, dict):
                json_result = [json_result]
            return json_result
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from PowerShell: {json_str}")


    async def get_model_names_from_ict(self, ssh: OpenSSHConnector, dir_source_base : Path) -> pd.DataFrame:
        """dir_source_base 직하가 모델 명으로 이루어진 폴더임을 가정"""
        cmd_source = ps.Get_ChildItem(dir_source_base).build() # 5.0 이상 대상.
        cmd_condition = ps.Filter.container("directory")
        cmd_selection = ps.Select().name().build()
        cmd_consumer = ps.ToJson().compress().build()
        cmd = ps.PSCommand().set_source(cmd_source).set_condition(cmd_condition).set_selection(cmd_selection).set_consumer(cmd_consumer).build()
        result = await ssh.run_command(cmd)
        if result.exit_status is None:
            # 나중에..
            pass

        json_result = self.powershell_reponse_to_json(result.stdout)
        df = pd.DataFrame(json_result)
        df.rename(columns={"Name": "name"}, inplace=True)
        return df   

    async def upsert_model_names(self, model_names: pd.DataFrame) -> None:
        """dir_source_base 직하가 모델 명으로 이루어진 폴더임을 가정"""
        await self.cruder.upsert_model_names(model_names)


    async def get_latest_created_times(self, instrument_name: str) -> pd.DataFrame:
        return pd.DataFrame(await self.cruder.get_latest_created_times(instrument_name))

    async def get_latest_path_full_sources(self, instrument_name: str) -> pd.DataFrame:
        return pd.DataFrame(await self.cruder.get_latest_path_full_sources(instrument_name))


    async def get_latest_created_time(self, measured_by: str, model_name: str | None = None) -> datetime:
        return await self.cruder.get_latest_created_time(measured_by, model_name)


    async def get_unretrieved_files(self, instrument_name:str, model_name:str, limit: int | None = None) -> pd.DataFrame:
        return pd.DataFrame(await self.cruder.get_list_unretrieved(instrument_name, model_name, limit))


    async def connect_to_instrument(self) -> None:
        ssh = None 
        try:
            logger.info(f"Connecting to {self.hostname} as {self.username} on port {self.port}")
            ssh = await OpenSSHConnector(self.hostname, self.username, self.port, self.ssh_key_path).connect_with_private_key()
            accessible = True
        except Exception as e:
            logger.error(f"Error connecting to {self.hostname} as {self.username} on port {self.port}: {e}")
            accessible = False
            ssh = None
        finally :
            self.ssh = ssh
            df : pd.DataFrame = pd.DataFrame([{
                "name": self.instrument_name,
                "accessible": accessible
            }])
            await self.cruder.upsert_instrument(df)
        return ssh


    async def retrieve_files(self, ssh: OpenSSHConnector, df: pd.DataFrame):
        """
        ICT 파일 확보 및 결과 기재
        path_destination : 해당 폴더 이하의 폴더 물색. 대상 파일은 CSV
        """
        for _, row in df.iterrows():
            dir_destination: Path = Path(row["path_full_destination"])

            if not dir_destination.exists():
                dir_destination.parent.mkdir(parents=True, exist_ok=True)
    
        task_no: int = 0
        results : pd.DataFrame = await ssh.download_files(df, "path_full_source", "path_full_destination", "is_retrieved", task_no)

        # is_retrieved가 True일 때 retrieved_at을 설정하고, 다운로드된 파일의 해시 계산
        results["retrieved_at"] = results["is_retrieved"].apply(lambda x: datetime.now() if x else None)
        results["status"] = results["is_retrieved"].apply(lambda x: "RETRIEVED" if x else "ERROR")
        results["is_locked"] = False
        # results["hash"] =  # 필요 한가..?

        await self.cruder.upsert_process(results)


# #TEST#############################################################

# import asyncio    
# 접속 정보 설정
async def test():
    hostname = "172.30.1.72"
    username = "admin"
    dir_source = Path(f"C:/Users/{username}/Desktop/Report")

    cruder = CRUDer(db_manager)
    fr = FileRetriever(cruder)
    ssh = await OpenSSHConnector(hostname, username).connect_with_private_key()
    model_names = await fr.get_model_names_from_ict(ssh, dir_source)
    print(model_names)

    target_dirs = await fr.get_target_dirs_from_ict(ssh, dir_source)
    print(target_dirs)

    target_file_list = await fr.get_target_file_list_from_ict(ssh, dir_source, max_count=2)
    print(target_file_list)

if __name__ == "__main__":
    asyncio.run(test())





# db = pg_manager.PGDBManager(models.BaseModel, DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)
