###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.10
# Updated at : 2025.09.16
# Supported by : ChatGPT-4o
# Note : SQLAlchemy ORM 모델 정의
#   2025.09.16 : 최신 정보 조회 방법 변경 (is_latest -> order_by(xxxx.desc()))
#                (is_latest 폐기 예정. 폐기 사유 : is_latest 사용시 데이터 입력시마다 불필요한 업데이트 필요.)
#                is_latest 예정에 따른 쿼리 변경
#                ORM 쿼리 위치 변경
#   2025.10.02 : 컬럼명 변경 및 관련부 변경(DB 설계 참조)
#   2025.10.17 : PGDBManager.execute_query() 일괄 적용
#   2025.10.20 : get_measured_after_last_normalized() 추가
############################################


from typing import Any
from DATABASE.pg_manager import PGDBManager
from sqlalchemy import select, Select, tuple_, literal, cast
from sqlalchemy.sql import func
from DATABASE import models
from datetime import date, timedelta, datetime
import pandas as pd


class CRUDer:
    def __init__(self, db_manager: PGDBManager):
        self.db = db_manager
    
    async def get_measured_data(
        self, model_name:str, 
        date_from:date, 
        date_to:date, 
        measured_by:str | None = None, 
        ) -> list[list[float]]:

        """
        해당 모델의 기간 내의 각 시리얼 번호별, 최신 측정 데이터만 조회.
        동일 시리얼 넘버라도 복수 측정 될 수 있음을 고려.
        """

        md: type[models.Measured] = models.Measured

        sub_stmt : Select = (
            select(
                md.serial_no,
                func.max(md.measured_at).label('latest')
            )
            .where(
                md.model_name == model_name,
                md.measured_at >= date_from,
                md.measured_at < date_to + timedelta(days=1)
            )
        )

        if measured_by:
            sub_stmt = sub_stmt.where(md.instrument_name == measured_by)
        
        sub_stmt = sub_stmt.group_by(md.serial_no).subquery()

        stmt = select(md.list_measured).select_from(
            md.__table__.join(
                sub_stmt,
                (md.serial_no == sub_stmt.c.serial_no) & 
                (md.measured_at == sub_stmt.c.latest)
            )
        )
        
        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def get_measured_data_by_model_name(self, model_name: str, after: date | None = None, latest_only: bool = True) -> list[dict[str, Any]]:
        """
        안쓸 듯
        벡터화를 위한 데이터 조회
        """

        md: type[models.Measured] = models.Measured
        
        stmt = select(md).where(md.model_name == model_name)
        if after:
            stmt = stmt.where(md.measured_at > after)
        if latest_only:
            stmt = stmt.order_by(md.serial_no, md.measured_at.desc()).distinct(md.serial_no)

        result = await self.db.execute_query(stmt)
        return result.mappings().all()


    async def get_measured_after_last_normalized(self, model_name: str | None = None,  latest_only: bool = True,) -> list[dict]:

        # TODO : 동작 검증 필요
        
        md_m: type[models.Measured] = models.Measured
        md_n: type[models.Normalized] = models.Normalized

        # 0) 모델별 마지막 정규화된 Measured의 (wm_at, wm_id) 추출
        #    DISTINCT ON (model_name) → 정렬: model_name, measured_at DESC, id DESC
        last_norm = (
            select(
                md_m.model_name.label("model_name"),
                md_m.measured_at.label("wm_at"),
                md_m.id.label("wm_id"),
            )
            .join(md_n, md_n.measured_id == md_m.id)
            .order_by(md_m.model_name, md_m.measured_at.desc(), md_m.id.desc())
            .distinct(md_m.model_name)  # PostgreSQL: DISTINCT ON (model_name)
            .subquery()
        )

        # COALESCE(워터마크 없을 때): 시각은 -infinity, id는 0
        minus_inf = cast(literal("-infinity"), md_m.measured_at.type)
        wm_at = func.coalesce(last_norm.c.wm_at, minus_inf)
        wm_id = func.coalesce(last_norm.c.wm_id, literal(0))

        # 1) Measured ←(LEFT JOIN)─ last_norm(모델별 워터마크)
        stmt = select(
                md_m.id,
                md_m.instrument_name,
                md_m.model_name,
                md_m.serial_no,
                md_m.list_measured,
                md_m.measured_at,
            )
        stmt = stmt.select_from(md_m)
        stmt = stmt.join(last_norm, last_norm.c.model_name == md_m.model_name, isouter=True)
        stmt = stmt.where(tuple_(md_m.measured_at, md_m.id) > tuple_(wm_at, wm_id))
        

        if model_name: 
            stmt = stmt.where(md_m.model_name == model_name)

        # 2) 시리얼 넘버별 최신 1건(옵션): DISTINCT ON (serial_no)
        if latest_only:
            stmt = stmt.order_by(md_m.model_name, md_m.serial_no, md_m.measured_at.desc(), md_m.id.desc())
            stmt = stmt.distinct(md_m.model_name, md_m.serial_no)
        else:
            stmt = stmt.order_by(md_m.model_name, md_m.measured_at.desc(), md_m.id.desc())

        result = await self.db.execute_query(stmt)
        rows = result.mappings().all()
        return [dict(r) for r in rows]


    async def get_spec(
        self,
        model_name:str, 
        spec_id:int | None = None,
        updated_at:date | None = None
        ) -> dict[str, Any] | None:

        md: type[models.Spec] = models.Spec
        
        stmt : Select = select(md.__table__.columns).where(md.model_name == model_name)

        if spec_id:
            stmt = stmt.where(md.id == spec_id)
        if updated_at:
            stmt = stmt.where(func.date(md.updated_at) >= updated_at)  # 이거 의미 없음. 다른 기능으로 변경 예정
            
        stmt = stmt.order_by(md.updated_at.desc()).limit(1) # 최신 1건 조회

        result = await self.db.execute_query(stmt)
        return result.mappings().first()


    async def get_latest_measured_datum(
        self, 
        instrument_name:str | None = None, 
        model_name:str | None = None,
        serial_no:str | None = None
        ) -> dict[str, any]:

        md: type[models.Measured] = models.Measured
        stmt : Select = select(md.instrument_name, md.model_name, md.serial_no, md.list_measured)
        
        if serial_no:
            stmt = stmt.where(md.serial_no == serial_no)

        if instrument_name:
            stmt = stmt.where(md.instrument_name == instrument_name)

        if model_name:
            stmt = stmt.where(md.model_name == model_name)
            
        stmt = stmt.order_by(md.measured_at.desc()).limit(1)

        result = await self.db.execute_query(stmt)
        return result.mappings().first()


    async def get_instrument_names(self) -> list[str]:

        md: type[models.Instrument] = models.Instrument
        stmt : Select = select(md.name)

        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def get_latest_retrieved_time(self, instrument_name:str) -> datetime:
        """결과가 없으면 datetime.min(0001-01-01 00:00:00) 반환"""
        md: type[models.Process] = models.Process
        
        stmt = select(md.retrieved_at).where(md.instrument_name == instrument_name).order_by(md.retrieved_at.desc()).limit(1)
        
        result = await self.db.execute_query(stmt)  
        return datetime.min if result is None else result.scalars().first()


    async def get_model_names(self) -> list[str]:

        md: type[models.Model] = models.Model
        stmt : Select = select(md.name)

        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def get_serial_nos(self) -> list[str]:

        md: type[models.Measured] = models.Measured
        stmt : Select = select(md.serial_no).distinct()

        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def get_time_series_data(
        self, 
        model_name: str, 
        inspection_idx : int, 
        date_from: date, 
        date_to: date, 
        measured_by: str | None = None
        ) -> list[dict[str, Any]]:

        md: type[models.Measured] = models.Measured
        stmt : Select = select(
            md.serial_no,
            func.to_char(md.measured_at, 'YYYY-MM-DD HH24:MI:SS').label('measured_at'),
            md.list_measured[inspection_idx].label('measured_value')
        ).where(
            md.model_name == model_name,
            md.measured_at >= date_from,
            md.measured_at < date_to + timedelta(days=1)
        )
        stmt = stmt.distinct(md.serial_no).order_by(md.serial_no, md.measured_at.desc())
        if measured_by:
            stmt = stmt.where(md.instrument_name == measured_by)

        result = await self.db.execute_query(stmt)
        return result.mappings().all()


    async def get_google_service_account(self, name: str | None = None) -> dict[str, Any]:
        """
            ※ CRUD 외의 로직 포함되어 있음에 유의
            Google Service Account 정보 조회
            name: Google Service Account 이름
            return: Google Service Account 정보
            return type: dict[str, Any]
            return example:
            {
                "name": "Google Service Account",
                "path_service_account": Google Service Account JSON Path,
                "service_scopes": ["https://www.googleapis.com/auth/spreadsheets"], ,
                "spreadsheet_id": "1234567890",
                "worksheet_name": "Google Sheet Name"
            }
        """
        md: type[models.GoogleServiceAccount] = models.GoogleServiceAccount
        stmt: Select = select(md.__table__.columns)
        if name:
            stmt = stmt.where(md.name == name)
        result = await self.db.execute_query(stmt)
        return result.mappings().first()


    async def truncate_external_defect(self) -> None:
        await self.db.truncate_table(models.ExternalDefect)


    async def upsert_external_defect(self, df: pd.DataFrame) -> int:
        return await self.db.upsert_dataframe(models.ExternalDefect, df)


    async def upsert_normalized (self, df: pd.DataFrame) -> int:
        return await self.db.upsert_dataframe(models.Normalized, df)

    # async def get_normalized(self, measured_id: int) -> pd.DataFrame:
    #     return await self.db.get_dataframe(models.Normalized, df)


'''
# id 기반 CRUD. 만들고 보니 쓸데 없음.


class CRUDHandler:
    def __init__(self, db_manager: PGDBManager, model_class: type[DeclarativeMeta]):
        self.db = db_manager
        self.model = model_class

    async def get_by_id(self, row_id: Any) -> Optional[Any]:
        async with self.db.session_maker() as session:
            stmt = select(self.model).where(self.model.id == row_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update(self, row_id: Any, update_dict: dict) -> int:
        async with self.db.session_maker() as session:
            stmt = (
                update(self.model)
                .where(self.model.id == row_id)
                .values(**update_dict)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def insert(self, row_dict: dict) -> Any:
        async with self.db.session_maker() as session:
            obj = self.model(**row_dict)
            session.add(obj)
            await session.commit()
            return obj

    async def delete(self, row_id: Any) -> int:
        async with self.db.session_maker() as session:
            stmt = self.model.__table__.delete().where(self.model.id == row_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount


class Instrument(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.Instrument)

class ExternalDefect(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.ExternalDefect)

class Model(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.Model)

class Spec(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.Spec)

class Measured(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.Measured)

class Normalized(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.Normalized)

class Process(CRUDHandler):
    def __init__(self, db_manager: PGDBManager):
        super().__init__(db_manager, models.BackUp)
'''