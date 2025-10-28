from OPEN_SSH.ict_data_extractor import ICTDataExtractor
from DATABASE import pg_manager, models
from DATABASE.pg_manager import PGDBManager
import asyncio
from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import Literal
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy import update, Update
from CUSTOMIZED.cust_hasher import Hasher
from CUSTOMIZED.cust_logger import logger

class DataArchiver:
    """
    매서드들에 딕셔너리 생성시, 
    딕셔너리 리터럴로 안넣고 전부 .update 한 것은 작성자가 마음의 병이 있어 그런 것이니 너그러이 봐 줄 것.
    """
    def __init__(self, db: PGDBManager) -> None:
        self.db: PGDBManager = db


    async def on_instrument(self, name: str, host: str, user: str, port: int, ssh_key_path: str = "") -> pd.DataFrame:
        data : dict ={}
        md : type[models.Instrument] = models.Instrument

        data.update({md.name: name})
        data.update({md.host: host})
        data.update({md.user: user})
        data.update({md.port: port})
        data.update({md.ssh_key_path: ssh_key_path})   
        data.update({md.accessible: False})  # TODO : 접근 테스트 로직 넣을 것 
        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df


    async def on_external_defect(self, serial_no:str, occurred_at:datetime, recognized_at:datetime, note:str ) -> pd.DataFrame:
        """단건 처리만 가능. 현시점 모델 자체가 없음."""
        data : dict ={}
        md = models.external_defect

        data.update({md.serial_no: serial_no})
        data.update({md.occurred_at: occurred_at})
        data.update({md.recognized_at: recognized_at})
        data.update({md.note: note})

        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df
    

    async def on_model(self, ict_data: ICTDataExtractor) -> None:
        """단건 처리만 가능"""
        data : dict ={}
        md : type[models.Model] = models.Model
        data.update({md.name.name: ict_data.model_name})

        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)


    async def on_spec(self, ict_data: ICTDataExtractor, datafile_subpath:Path, datafile_hash:bytes) -> pd.DataFrame:
        """단건 처리만 가능"""
        data : dict ={}

        md : type[models.Spec] = models.Spec

        data.update({md.instrument_name.name: ict_data.measured_by})
        data.update({md.model_name.name: ict_data.model_name})
        data.update({md.measured_points.name: ict_data.measured_points})
        data.update({md.adj_val_infinity.name: ict_data.adj_val_infinity})
        data.update({md.adj_val_extreme.name: ict_data.adj_val_extreme}) 
        data.update({md.path_sub_datafile.name: str(datafile_subpath)})
        data.update({md.hashed_datafile.name: datafile_hash})
        data.update({md.updated_at.name: ict_data.measured_at}) 
        data.update({md.is_latest.name: True}) 
        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df


    async def on_measured(self, ict_data: ICTDataExtractor, datafile_subpath:Path, datafile_hash:bytes) -> pd.DataFrame:
        """단건 처리만 가능"""
        data : dict ={}

        md : type[models.Measured] = models.Measured

        data.update({md.instrument_name.name: ict_data.measured_by})
        data.update({md.model_name.name: ict_data.model_name})
        data.update({md.serial_no.name: ict_data.serial_no}) 
        data.update({md.path_sub_datafile.name: str(datafile_subpath)})
        data.update({md.hashed_datafile.name: datafile_hash})
        data.update({md.list_measured.name: ict_data.df_measured["measured_value"].tolist()}) 
        data.update({md.measured_at.name: ict_data.measured_at}) 
        data.update({md.is_latest.name: True}) 
        data.update({md.passed.name: True}) 
        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df


    async def on_normalized(self, ict_data: ICTDataExtractor, datafile_subpath:str, datafile_hash:bytes) -> pd.DataFrame:
        """단건 처리만 가능"""
        data : dict ={}
        md : type[models.Normalized] = models.Normalized

        data.update({md.measured_id.name: ict_data.measured_by})
        data.update({md.vector_visual_normed.name: ict_data.model_name}) # TODO :  벡터화 한 값 넣어야..
        data.update({md.applied_spec_id.name: ict_data.serial_no}) 
        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df


    async def process_on_archiving(
        self, 
        instrument_name:str, 
        fullpath_current:str, 
        is_parsed:bool, 
        status:int
        ) -> pd.DataFrame:
        """단건 처리만 가능"""
        data : dict ={}
        md : type[models.Process] = models.Process

        data.update({md.instrument_name.name: instrument_name})
        # data.update({"path_full_source": ""})                  #ICT 장비 내에서의 원본 파일 위치
        data.update({md.hashed_file.name : Hasher().hash_file(fullpath_current).value}) 
        data.update({md.path_full_current.name: str(fullpath_current)})
        # data.update({"is_retrieved": ict_data.serial_no})     # ICT 장비에서 파일 확보 여부. SSH를 통한 리스트 상의 파일 내에서의 확보 여부. 애초에 리스트에 안담기면 방법 없음.
        data.update({md.is_parsed.name: is_parsed})                   # 파싱 / 이동 완료 여부(변경 예정)
        data.update({md.status.name: status}) 

        df = pd.DataFrame([data])
        await self.db.upsert_dataframe(md, df)
        return df


    async def save_parquet_n_upsert(
            self, 
            ict_data: ICTDataExtractor, 
            target_process: Literal["spec", "measured"], 
            base_folderpath: Path, 
            sub_folderpath: Path
            ):
        method_name: str = f"suggest_file_name_{target_process}"
        file_name: str = getattr(ict_data, method_name)
        fullpath: Path = Path(base_folderpath / sub_folderpath, file_name)
        df: pd.DataFrame = getattr(ict_data, f"df_{target_process}")
        df.to_parquet(fullpath)
        method_name : str = f"on_{target_process}"
        await getattr(self, method_name)(ict_data, fullpath, Hasher().hash_file(fullpath).value)
        logger.info(f"Saved {target_process} to {fullpath}")
        # TODO : 미완성
        





# 현재 불필요. 나중에 쓸 수도 있으니 남겨둠.
# 불필요 사실상 확정(is_latest 컬럼 실사용 중단)(2025.09.23)
class LatestUnsetter:
    """최신 여부 초기화 클래스"""
    
    def __init__(self, db: PGDBManager):
        self.db = db

    async def on_spec(self, model_name: str | None = None):
        """
            해당 model_name의 spec에서 is_latest = true인 것들을 false로 변경
            ※ model_name은 제품의 모델명을 의미
        """

        set_all_false : bool = False
        if model_name is None or model_name == "":
            set_all_false = True

        md: type[DeclarativeMeta] = models.Spec
        async with self.db.session_maker() as session:
            stmt : Update = update(md)
            stmt = stmt.where(md.is_latest == True)

            if set_all_false:
                stmt = stmt.where(md.model_name == model_name)
            
            stmt = stmt.values(is_latest = False)
                
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def on_measured(self, serial_no: str | None = None):
        """해당 serial_no의 measured에서 is_latest = true인 것들을 false로 변경"""

        set_all_false : bool = False
        if serial_no is None or serial_no == "":
            set_all_false = True

        md: type[DeclarativeMeta] = models.Measured
        async with self.db.session_maker() as session:
            stmt : Update = update(md)
            stmt = stmt.where(md.is_latest == True)

            if set_all_false:
                stmt = stmt.where(md.serial_no == serial_no)

            stmt = stmt.values(is_latest = False)
                
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount




# #TEST################################################################################################


async def test():
    ict_data = ICTDataExtractor()
    path = Path(r"TEST\testdata_ICT\06DB9205685ADVNAY3A0001_20250310080803.csv")

    ict_data.get(path,"test_name","utf-8")
    df: pd.DataFrame = ict_data.get_parquet_spec()

    DB_NAME = 'novas_ez'
    DB_USER = 'admin'
    DB_PASSWORD = '123!@#qwe'  
    DB_HOST = 'localhost'
    DB_PORT = 5432

    db = pg_manager.PGDBManager(models.BaseModel, DB_NAME,DB_USER,DB_PASSWORD,DB_HOST,DB_PORT)

    PARENT_PATH = Path("C:/Users/user/Novas_Ez")
    # 테이블이 없으면 자동으로 생성됨
    await db.drop_tables()
    await db.create_tables()

    u = DataArchiver(db)
    # 맨 처음 수기 등록(혹은 ICT 장비 등록 페이지 만들어서 ICT 정보 등록/변경)
    await u.on_instrument(ict_data.measured_by,db.host,db.user,db.port,"")

    # TODO : backup 업데이트 및 데이터 미등록 리스트 확보

    await u.on_model(ict_data)

    # Spec 업서트 관련

    await u.save_parquet_n_upsert(ict_data, "spec", PARENT_PATH, Path(".", "TEST", "SPEC"))

    await u.save_parquet_n_upsert(ict_data, "measured", PARENT_PATH, Path(".", "TEST", "MEASURED"))

    # path = Path(".", "TEST", "SPEC", ict_data.suggest_file_name_spec)
    # print(path.resolve()) 
    # ict_data.df_spec.to_parquet(path)
    # hs_spec = Hasher().hash_file(path).value.hex()
    # await u.spec(ict_data,path, Hasher().hash_file(path).value)
    # # TODO : parquet 저장

    # # Measured 업서트 관련
    # path = Path(".", "TEST", "MEASURED", ict_data.suggest_file_name_measured)
    # ict_data.df_measured.to_parquet(path)
    # hs_meas = Hasher().hash_file(path).value.hex()
    # await u.measured(ict_data,path, Hasher().hash_file(path).value)
    # # TODO : measured 업서트


    # print(hs_spec)

    # print(hs_meas)
if __name__ == "__main__":
    asyncio.run(test())



