from CUSTOMIZED.cust_logger import logger   
import CUSTOMIZED.cust_powershell as ps
from OPEN_SSH.ssh_connector import OpenSSHConnector
from DATABASE.cruder import CRUDer
from DATABASE.config import db_manager
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import asyncio
import json   
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


    def set_instrument_infos(self, instrument_name: str, host: str, user: str, port: int, ssh_key_path: str, dir_base_source: str, dir_destination_base: str):
        self.instrument_name = instrument_name
        self.hostname = host
        self.username = user
        self.port = port
        self.ssh_key_path = None if ssh_key_path is None else Path(ssh_key_path)
        self.dir_base_source = dir_base_source
        self.dir_destination_base = dir_destination_base
        self.is_instrument_info_set = True
        return self


    async def run(self, retrieve_count_of_each_model: int = 20) -> None:
        try:
            log_msg :str = ""
            if not self.is_instrument_info_set:
                logger.error("Instrument information is not set")
                return

            instrument_name : str = self.instrument_name
            dir_base_source : Path = Path(self.dir_base_source)
            dir_destination_base : Path = Path(self.dir_destination_base)

            if self.ssh is None:
                return
            else:
                ssh = self.ssh

            logger.info(f"Accessing FileRetriever for {self.instrument_name}")

            model_names : pd.DataFrame = await self.get_model_names_from_ict(ssh, Path(dir_base_source))

            await self.upsert_model_names(model_names) #모델 추가는 자주 없을텐데 이렇게 매번 하는게 맞는건지... 그렇다고 안하거나 매번 비교해서 쓰기도 그렇고..

            # latest_retrieved_time : datetime = await self.get_latest_retrieved_time(self.instrument_name)
            # # 모델별로 하자니 네트워크 통신이 많아지고, 한번에 하자니 최초 가지고 올 때 상위 N개 확정하기가 어려워지고..
            # # 장비별로 한번에 가져오면, 리스트 수가 너무 많아지거나, 기준을 세우기가 애매해짐..
            # # 모델별로 해야 하나...

            instrument_name : str = self.instrument_name
            df_lct : pd.DataFrame = await self.get_latest_created_times(instrument_name)  

            for model_name in model_names["name"]:
                # logger.info(f" - Getting data from {instrument_name} : {model_name}")
                target_dirs : pd.DataFrame = await self.get_target_dirs_from_ict(ssh, Path(dir_base_source) / model_name)
                latest_retrieved_time : datetime = self.get_latest_created_time_from_model(df_lct, model_name)
                target_dirs : pd.DataFrame = target_dirs[target_dirs["date"] >= latest_retrieved_time.date()]
                target_file_list : pd.DataFrame = await self.get_target_file_list_from_ict(ssh, Path(dir_base_source) / model_name, latest_retrieved_time, retrieve_count_of_each_model)
                
                if target_file_list.empty:
                    # logger.info(f" - {instrument_name} : {model_name} - No data to retrieve")
                    continue

                df : pd.DataFrame = self.make_void_dataframe_for_process()

                subdir_destination = dir_destination_base / instrument_name / model_name
                series_fullpath_destination = pd.Series([str(subdir_destination / Path(path).name) for path in target_file_list["FullName"]])
                series_created_at = pd.Series([datetime.fromtimestamp(int(time.strip('/Date()')) / 1000.0) for time in target_file_list["CreationTime"]])
                series_hashed = pd.Series([Hasher().hash_file(Path(path)).value for path in series_fullpath_destination])
                
                df["path_full_destination"] = series_fullpath_destination
                df["created_at"] = series_created_at
                df["hashed"] = series_hashed
                df["instrument_name"] = instrument_name
                df["model_name"] = model_name
                df["path_full_source"] = target_file_list["FullName"]
                df["is_retrieved"] = False
                df["retrieved_at"] = None
                await self.cruder.upsert_process(df)

                # DB에서 다운로드 대상 리스트 확보 (방급 업데이트한 리스트 + 모종의 이유로 다운로드 되지 않은 리스트)
                df_to_download : pd.DataFrame = await self.get_unretrieved_files(instrument_name, model_name)

                # 파일 다운로드
                await self.retrieve_files(ssh, df_to_download)

            # log_msg = f" - {instrument_name} completed successfully"
        except Exception as e:
            log_msg = f" - {instrument_name} : {model_name} Error in run: {e}"
        finally:
            # 연결 안끊고 있는 연결 계속 사용.
            # await self.ssh.close() 
            if log_msg:
                logger.info(log_msg)


    def get_latest_created_time_from_model(self, df: pd.DataFrame, model_name: str) -> datetime:
        if df.empty or df[df["model_name"] == model_name]["created_at"].empty:
            return datetime.min
        result = df.loc[df["model_name"] == model_name, "created_at"].iloc[0]
        if isinstance(result, datetime):
            return result 
        else:
            return datetime.min

    def make_void_dataframe_for_process(self) -> pd.DataFrame:
        return pd.DataFrame(columns=['instrument_name', 'model_name', 'path_full_source', 'path_full_destination', 'is_retrieved', 'retrieved_at', 'created_at', 'hashed'])

    async def get_target_file_list_from_ict(self, ssh: OpenSSHConnector, dir_source: Path, since_datetime: datetime, max_count: int = 20) -> pd.DataFrame:
        cmd_source = ps.Get_ChildItem(dir_source).entry("file").recursive(True).build()
        cmd_selection = ps.Select().full_name().creation_time(with_milliseconds=True).first(max_count).build()
        cmd_condition_extension = ps.Filter.by_extension("csv").build()
        cmd_condition_time = ps.Filter.since(since_datetime).build()
        cmd_condition = cmd_condition_extension & cmd_condition_time
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

        if not result.stdout:
            return pd.DataFrame(columns=['FullName', 'CreationTime'])
        json_result = json.loads(result.stdout)
        # 단일 딕셔너리인 경우 리스트로 감싸기
        if isinstance(json_result, dict):
            json_result = [json_result]
        df = pd.DataFrame(json_result)
        return df


    async def get_target_dirs_from_ict(self, ssh: OpenSSHConnector, dir_source_base: Path) -> pd.DataFrame:
        cmd_source = ps.Get_ChildItem(dir_source_base).entry("directory").recursive(True).build()
        cmd_selection = ps.Select().full_name().build()
        cmd_consumer = ps.ToJson().compress().build()
        ps_cmd = ps.PSCommand().set_source(cmd_source).set_selection(cmd_selection).set_consumer(cmd_consumer).build()
        result = await ssh.run_command(ps_cmd)
        json_result = json.loads(result.stdout)
        # 단일 딕셔너리인 경우 리스트로 감싸기
        if isinstance(json_result, dict):
            json_result = [json_result]
        df = pd.DataFrame(json_result)
        for fullname in df["FullName"]:
            is_date_structured, date = self.is_date_structured_path(Path(fullname))
            if is_date_structured:
                df["date"] = date
        return df[df["date"].notna()]
        

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


    async def get_model_names_from_ict(self, ssh: OpenSSHConnector, dir_source_base : Path) -> pd.DataFrame:
        """dir_source_base 직하가 모델 명으로 이루어진 폴더임을 가정"""
        cmd_source = ps.Get_ChildItem(dir_source_base).entry("directory").build()
        cmd_selection = ps.Select().name().build()
        cmd_consumer = ps.ToJson().compress().build()
        cmd = ps.PSCommand().set_source(cmd_source).set_selection(cmd_selection).set_consumer(cmd_consumer).build()
        result = await ssh.run_command(cmd)
        json_result = json.loads(result.stdout)
        # 단일 딕셔너리인 경우 리스트로 감싸기
        if isinstance(json_result, dict):
            json_result = [json_result]
        df = pd.DataFrame(json_result)
        df.rename(columns={"Name": "name"}, inplace=True)
        return df


    async def upsert_model_names(self, model_names: pd.DataFrame) -> None:
        """dir_source_base 직하가 모델 명으로 이루어진 폴더임을 가정"""
        await self.cruder.upsert_model_names(model_names)


    async def get_latest_created_times(self, instrument_name: str) -> pd.DataFrame:
        return pd.DataFrame(await self.cruder.get_latest_created_times(instrument_name))


    async def get_latest_created_time(self, measured_by: str, model_name: str | None = None) -> datetime:
        return await self.cruder.get_latest_created_time(measured_by, model_name)


    async def get_unretrieved_files(self, instrument_name:str, model_name:str) -> pd.DataFrame:
        return pd.DataFrame(await self.cruder.get_unretrieved_files(instrument_name, model_name))


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

        results : pd.DataFrame = await ssh.download_files(df, "path_full_source", "path_full_destination", "is_retrieved")

        results["retrieved_at"] = results["is_retrieved"].apply(lambda x: datetime.now() if not x else None)
        results["status"] = results["is_retrieved"].apply(lambda x: "RETRIEVED" if x else "ERROR")
        # results["hash"] =  # 필요 한가..?

        await self.cruder.upsert_process(results)


# #TEST#############################################################

# import asyncio    
# 접속 정보 설정
async def test():
    hostname = "172.30.1.72"
    username = "admin"
    dir_source = Path(f"C:/Users/{username}/Desktop/Report")
    dir_destination = Path(r"C:\TEST")

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
