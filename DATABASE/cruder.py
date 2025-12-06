###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.10
# Updated at : 2025.09.16
# Supported by : ChatGPT-4o
# Note : SQLAlchemy ORM 모델 정의
#   ※ 나중에 적당히 나눠야 함
#   2025.09.16 : 최신 정보 조회 방법 변경 (is_latest -> order_by(xxxx.desc()))
#                (is_latest 폐기 예정. 폐기 사유 : is_latest 사용시 데이터 입력시마다 불필요한 업데이트 필요.)
#                is_latest 예정에 따른 쿼리 변경
#                ORM 쿼리 위치 변경
#   2025.10.02 : 컬럼명 변경 및 관련부 변경(DB 설계 참조)
#   2025.10.17 : PGDBManager.execute_query() 일괄 적용
#   2025.10.20 : get_measured_after_last_normalized() 추가
#   2025.11.06 : 빌더 패턴 고려 중
############################################


from ast import stmt
from typing import Any

from sqlalchemy.util import NoneType
from DATABASE.pg_manager import PGDBManager
from sqlalchemy import select, Select, tuple_, literal, cast, distinct, text
from sqlalchemy.sql import func
from DATABASE import models
from datetime import date, timedelta, datetime
import pandas as pd
from sqlalchemy.sql.elements import BinaryExpression


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


    async def get_measured_since_last_normalized(self, model_name: str | None = None,  latest_only: bool = True,) -> list[dict]:
        """
        Measured 테이블에서 마지막 정규화된 데이터 이후의 데이터 조회
        """

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
        serial_no:str | None = None,
        get_list_measured: bool = True,
        ) -> dict[str, Any]:

        md: type[models.Measured] = models.Measured
        stmt : Select = select(md.instrument_name, md.model_name, md.serial_no, md.measured_at)

        if get_list_measured:
            stmt = stmt.add_columns(md.list_measured)
        
        if serial_no:
            stmt = stmt.where(md.serial_no == serial_no)

        if instrument_name:
            stmt = stmt.where(md.instrument_name == instrument_name)

        if model_name:
            stmt = stmt.where(md.model_name == model_name)
            
        stmt = stmt.order_by(md.measured_at.desc()).limit(1)

        result = await self.db.execute_query(stmt)
        return result.mappings().first()

###############################################
# Instrument
###############################################
    async def get_instrument_names(self) -> list[str]:
        md: type[models.Instrument] = models.Instrument
        stmt : Select = select(md.name)

        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def get_base_dir_destinations(self, instrument_name: str | None = None) -> list[dict[str, Any]]:
        md: type[models.Instrument] = models.Instrument
        stmt : Select = select(md.name, md.dir_base_destination)
        if instrument_name:
            stmt = stmt.where(md.name == instrument_name)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()


    async def get_instrument_infos(self, instrument_name: str | None = None) -> list[dict[str, Any]]:
        md: type[models.Instrument] = models.Instrument
        stmt : Select = select(md.__table__.columns)
        if instrument_name:
            stmt = stmt.where(md.name == instrument_name)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()


    async def upsert_instrument(self, df: pd.DataFrame) -> None:
        md: type[models.Instrument] = models.Instrument
        await self.db.upsert_dataframe(md, df)


############################################
# Model
############################################
    async def get_model_names(self) -> list[str]:

        md: type[models.Model] = models.Model
        stmt : Select = select(md.name)

        result = await self.db.execute_query(stmt)
        return result.scalars().all()


    async def upsert_model_names(self, model_names: pd.DataFrame) -> int:
        md: type[models.Model] = models.Model
        return await self.db.upsert_dataframe(md, model_names)


############################################
# Measured
############################################
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


############################################
# Google Service Account
############################################
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


############################################
# External Defect
############################################
    async def truncate_external_defect(self) -> None:
        await self.db.truncate_table(models.ExternalDefect)


    async def upsert_external_defect(self, df: pd.DataFrame) -> int:
        return await self.db.batch_upsert_dataframe(models.ExternalDefect, df)

############################################
# Normalized
############################################
    async def upsert_normalized (self, df: pd.DataFrame) -> int:
        return await self.db.batch_upsert_dataframe(models.Normalized, df)


    # async def get_normalized(self, measured_id: int) -> pd.DataFrame:
    #     return await self.db.get_dataframe(models.Normalized, df)

############################################
# Process
############################################
    async def upsert_process (self, df: pd.DataFrame) -> int:
        return await self.db.batch_upsert_dataframe(models.Process, df, allowed_param_size=20000)


    async def get_latest_created_time(self, instrument_name:str, model_name:str | None = None) -> datetime:
        """결과가 없으면 datetime.min(0001-01-01 00:00:00) 반환"""
        md: type[models.Process] = models.Process
        
        stmt = select(md.created_at)
        stmt = stmt.where(md.instrument_name == instrument_name)
        if model_name:
            stmt = stmt.where(md.model_name == model_name)
        stmt = stmt.order_by(md.created_at.desc()).limit(1)
        
        result = await self.db.execute_query(stmt)  
        return datetime.min if result is None else result.scalars().first()


    async def get_latest_created_times(self, instrument_name:str) -> list[dict[str, Any]]:
        md: type[models.Process] = models.Process
        
        stmt = select(md.instrument_name, md.model_name, md.created_at)
        stmt = stmt.where(md.instrument_name == instrument_name)
        stmt = stmt.order_by(md.model_name, md.created_at.desc())
        stmt = stmt.distinct(md.model_name)
        
        result = await self.db.execute_query(stmt)  
        return result.mappings().all()


    async def get_unparsed_infos(self, instrument_name:str|None = None, model_name:str | None = None) -> list[dict[str, Any]]:
        md: type[models.Process] = models.Process
        stmt: Select = select(md.instrument_name, md.model_name, md.path_full_source, md.path_full_destination, md.is_parsed)
        if instrument_name:
            stmt = stmt.where(md.instrument_name == instrument_name)
        if model_name:
            stmt = stmt.where(md.model_name == model_name)
        stmt = stmt.where(md.is_parsed == False)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()


############################################
# Vector
############################################
    async def get_vector_data(self, serial_no: str) -> tuple[str, str, list[float]]:
        """
        해당 시리얼 넘버의 최신 벡터 데이터 조회
        """
        md_n: type[models.Normalized] = models.Normalized
        md_m: type[models.Measured] = models.Measured

        stmt : Select = select(md_m.model_name, md_m.serial_no, md_n.vector_visual_normed)
        stmt = stmt.join(md_m, md_m.id == md_n.measured_id)
        stmt = stmt.where(md_m.serial_no == serial_no)
        stmt = stmt.order_by(md_m.measured_at.desc()).limit(1)
        result = await self.db.execute_query(stmt)
        row = result.mappings().first()
        if not row:
            return ("", "", [])
        return (row[md_m.model_name.name], row[md_m.serial_no.name], row[md_n.vector_visual_normed.name])


    async def get_relative_similarities(
        self, 
        instrument_name: str | None,
        model_name: str | None,
        serial_no: str, 
        num_of_records: int, 
        top_k_rate: float = 0.01, 
        date_from: date | None = None,
        date_to: date | None = None,
        metric: str = "cosine", 
        except_itself: bool = True,
        return_vector: bool = True,
        return_measured_values: bool = True,
        anchor_serial_no: str | None = None
        ) -> dict[str, dict[str, Any]]:
        """
        해당 모델의 시리얼 넘버의 유사도를 조회
        target_data_size : 대상 데이터 건수 
            ※ await cruder.get_measured_data_size(model_name=model_name) 호출 후 전달
        top_k_rate : 상위 몇 건의 데이터를 대상으로 유사도 조회할 것인지 비율
        """

        if top_k_rate < 0.0 or top_k_rate > 1.0:
            raise ValueError("top_k_rate must be between 0.0 and 1.0")
        
        top_k = int(num_of_records * top_k_rate)

        if except_itself:
            top_k += 1

        return await self.get_absolute_similarities(instrument_name, model_name, serial_no, top_k, date_from, date_to, metric, except_itself, return_vector, return_measured_values,anchor_serial_no)


    async def get_absolute_similarities(
        self, 
        instrument_name: str | None,
        model_name: str | None,
        serial_no: str, 
        top_k: int = 100, 
        date_from: date | None = None,
        date_to: date | None = None,
        metric: str = "cosine", 
        except_itself: bool = True,
        return_vector: bool = True,
        return_measured_values: bool = True,
        anchor_serial_no: str | None = None
        ) -> dict[str, dict[str, Any]]:        
        """
        해당 모델의 시리얼 넘버의 유사도를 조회
        k : 상위 몇 건의 데이터를 대상으로 유사도 조회할 것인지
        metric : 유사도 계산 방법
        except_itself : 자기 자신을 제외할 것인지
        시리얼 넘버는 유일하지만, 모든 모델이 같은 벡터 DB에 존재하므로, 모델명 정보
        """

        _, _, query_vector = await self.get_vector_data(serial_no)

        if query_vector is None or len(query_vector) == 0:
            return {}

        match metric:
            case "cosine":
                # 코사인 거리 (1- cosθ)
                return await self._get_cosine_distance(instrument_name, model_name, serial_no, query_vector, top_k, date_from, date_to, except_itself, return_vector, return_measured_values, anchor_serial_no)
            # case "Euclidean":
            #     # 유클리드 거리
            #     return
            # case "Dot Product":
            #     # 내적 유사도 : 
            #     # Dot Product는 원래 유사할 수록 큰 값을 가지나, 
            #     # PostgreSQL에서는 유사할수록 작은값을 가지도록 부호 반전함.
            #     return
            case _:
                raise ValueError(f"Invalid metric: {metric}")


    async def _get_cosine_distance(
        self, 
        instrument_name: str | None,
        model_name: str | None, 
        serial_no: str, 
        query_vector: list[float], 
        k: int = 100, 
        date_from: date | None = None, 
        date_to: date | None = None, 
        except_itself: bool = True,
        return_vector: bool = True,
        return_measured_values: bool = True,
        anchor_serial_no: str | None = None
        ) -> dict[str, dict[str, Any]]:
        md_n: type[models.Normalized] = models.Normalized
        md_m: type[models.Measured] = models.Measured

        dist : BinaryExpression[float] = md_n.vector_visual_normed.cosine_distance(query_vector)

        stmt_sub = select(md_m.instrument_name, md_m.id, md_m.model_name, md_m.serial_no, md_m.measured_at,)
        if return_measured_values:
            stmt_sub = stmt_sub.add_columns(md_m.list_measured)
        if instrument_name:
            stmt_sub = stmt_sub.where(md_m.instrument_name == instrument_name)
        if model_name:
            stmt_sub = stmt_sub.where(md_m.model_name == model_name) 
        if anchor_serial_no:
            stmt_sub = stmt_sub.where(md_m.serial_no == anchor_serial_no)
        if date_from:
            stmt_sub = stmt_sub.where(md_m.measured_at >= date_from)
        if date_to:
            stmt_sub = stmt_sub.where(md_m.measured_at <= date_to + timedelta(days=1))
        if except_itself:
            stmt_sub = stmt_sub.where(md_m.serial_no != serial_no)
        stmt_sub = stmt_sub.distinct(md_m.serial_no) 
        stmt_sub = stmt_sub.order_by(md_m.serial_no, md_m.measured_at.desc())
        stmt_sub = stmt_sub.subquery()

        stmt : Select = select(
                stmt_sub.c.instrument_name.label(md_m.instrument_name.name),
                stmt_sub.c.model_name.label(md_m.model_name.name),
                stmt_sub.c.serial_no.label(md_m.serial_no.name),
                stmt_sub.c.measured_at.label(md_m.measured_at.name),
                md_n.measured_id.label(md_n.measured_id.name),
                dist.label("dist")
            )
        if return_vector:
            stmt = stmt.add_columns(md_n.vector_visual_normed.label(md_n.vector_visual_normed.name))
        if return_measured_values:
            stmt = stmt.add_columns(stmt_sub.c.list_measured.label(stmt_sub.c.list_measured.name))
        stmt = stmt.select_from(md_n)
        stmt = stmt.join(stmt_sub, stmt_sub.c.id == md_n.measured_id)
        stmt = stmt.order_by(dist, md_n.id)
        stmt = stmt.limit(k)
      

        res = await self.db.execute_query(stmt)
        rows = res.mappings().all()

        result: dict[str, dict[str, Any]] = {}    # serial_no: {measured_id: int, rank: int, distance: float, vector_visual_normed: list[float]}
        for rank, row in enumerate(rows, start=1):
            result[row["serial_no"]] = {
                "serial_query": serial_no,
                "measured_id": row["measured_id"],
                "instrument_name": row["instrument_name"],
                "model_name": row["model_name"],
                "serial_result": row["serial_no"],
                "measured_at": row["measured_at"],
                "rank": rank,
                "distance": float(row["dist"]),
            }  
            if return_vector:
                result[row["serial_no"]][str(md_n.vector_visual_normed.name)] = row[md_n.vector_visual_normed.name]
            if return_measured_values:
                result[row["serial_no"]][str(stmt_sub.c.list_measured.name)] = row[stmt_sub.c.list_measured.name]
        return result


    async def get_measured_data_size(
        self, 
        instrument_name: str | None = None, 
        model_name: str | None = None, 
        distinct_serial: bool = True
        ) -> int:
        """
        해당 모델의 측정 데이터 건수 조회
        distinct = True 일 경우 시리얼 넘버수 조회, False 일 경우 측정 데이터 건수 전체 조회
        """
        md_m: type[models.Measured] = models.Measured

        if distinct_serial:
            stmt = select(func.count(distinct(md_m.serial_no)))
        else:
            stmt = select(func.count(md_m.id))

        if model_name:
            stmt = stmt.where(md_m.model_name == model_name)
        if instrument_name:
            stmt = stmt.where(md_m.instrument_name == instrument_name)
        stmt = stmt.group_by(md_m.model_name)

        result = await self.db.execute_query(stmt)
        return result.scalar_one()


    async def get_measured_data_sizes(self, date_from: date | None = None, date_to: date | None = None, distinct_serial: bool = True) -> pd.DataFrame:
        """
        해당 모델의 측정 데이터 건수 조회
        distinct = True 일 경우 시리얼 넘버수 조회, False 일 경우 측정 데이터 건수 전체 조회
        """
        md_m: type[models.Measured] = models.Measured

        if distinct_serial:
            stmt = select(md_m.model_name, func.count(distinct(md_m.serial_no)).label("count"))
        else:
            stmt = select(md_m.model_name, func.count(md_m.id).label("count"))
        if date_from:
            stmt = stmt.where(md_m.measured_at >= date_from)
        if date_to:
            stmt = stmt.where(md_m.measured_at <= date_to + timedelta(days=1))
        stmt = stmt.group_by(md_m.model_name)

        result = await self.db.execute_query(stmt)

        return pd.DataFrame(result.mappings().all())


    async def get_external_defects_info(
        self, 
        occurred_date_from: date|None = None, 
        occurred_date_to: date|None = None, 
        recognized_date_from: date|None = None,
        recognized_date_to: date|None = None,
        latest_only: bool = True
        ) -> pd.DataFrame:
        md_e: type[models.ExternalDefect] = models.ExternalDefect
        md_m: type[models.Measured] = models.Measured

        stmt: Select = select(md_m.instrument_name, md_m.model_name, md_e.serial_no, md_e.occurred_at, md_m.measured_at)
        stmt = stmt.select_from(md_e)
        stmt = stmt.join(md_m, md_m.serial_no == md_e.serial_no)
        if occurred_date_from:
            stmt = stmt.where(md_e.occurred_at >= occurred_date_from)
        if occurred_date_to:
            stmt = stmt.where(md_e.occurred_at <= occurred_date_to)
        if recognized_date_from:
            stmt = stmt.where(md_e.recognized_at >= recognized_date_from)
        if recognized_date_to:
            stmt = stmt.where(md_e.recognized_at <= recognized_date_to)
        if latest_only:
            stmt = stmt.distinct(md_m.model_name, md_e.serial_no)
        stmt = stmt.order_by(md_m.model_name, md_e.serial_no, md_e.occurred_at.desc())
        result = await self.db.execute_query(stmt)
        return pd.DataFrame(result.mappings().all()) 


    async def get_unretrieved_files(self, instrument_name:str | None = None, model_name:str | None = None) -> list[dict[str, Any]]:
        md: type[models.Process] = models.Process
        stmt: Select = select(md.instrument_name, md.model_name, md.path_full_source, md.path_full_destination)
        stmt = stmt.where(md.is_retrieved == False)
        if instrument_name:
            stmt = stmt.where(md.instrument_name == instrument_name)
        if model_name:
            stmt = stmt.where(md.model_name == model_name)
        result = await self.db.execute_query(stmt)
        return result.mappings().all()


    async def is_db_connected(self) -> bool:
        try:
            status: bool = True
            result = await self.db.execute_query(text("SELECT 1"))
            return result.scalars().all()
        except Exception as e:
            status: bool = False
        finally:
            pass
        return status

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