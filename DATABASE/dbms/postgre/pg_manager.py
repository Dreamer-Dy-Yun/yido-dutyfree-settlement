###########################################
# Module name : pg_manager.py
# Module class : PGDBManager, DataBaseMaker
# Written by : Yun Dae-young
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.07.11
# Updated at : 2026.05.14
# Supported by : ChatGPT-4o
# Note : SQLAlchemy ORM 모델 정의
#       2025.09.23 : PGDBManager.upsert_dataframe()에 주석 추가
#       2025.10.14 : PGDBManager.truncate_table() 추가
#       2025.10.16 : 버그 수정
#                    PGDBManager.upsert_dataframe()
#                       - df에 존재하나 table에 존재하지 않는 컬럼은 무시되도록 수정
#                       - 주석 수정/추가
#       2025.10.17 : PGDBManager.execute_query() 확장
#       2025.10.20 : PGDBManager.upsert_dataframe() 반환값 변경(None → 업데이트 된 행 수(int))
#                    PGDBManager 클래스 변수를 인스턴스 변수로 변경
#       2025.11.07 : PGDBManager.upsert_dataframe() 수정(불필요한 컬럼 제거)
#                       - 롤백하면서 제거된 로직 복구.
#                       - 롤백 원인 : AI의 잘못된 대규모 코드 수정
#                                   (다른 파일의 로직을 수정요청 하였으나, 이 파일을 수정. 심지어 잘못된 방향으로.)
#       2025.11.22 : PGDBManager.initialize_engine() 수정(pool_size, max_overflow 추가)
#       2025.11.30 : DBManager 추상 클래스 추가 및 상속
#       2026.02.19 : PGDBManager.set_schema() 등 스키마 관련 메서드 추가 (멀티 테넌트 대응)
#       2026.02.20 : 컨텍스트 매니저 수정
#       2026.02.23 : PGDBManager.create_tables() 수정(스키마 명시적 지정 가능)
#                    PGDBManager.copy_tables_of_schema() 추가 (스키마 복사 기능 추가. supported by ChatGPT-5.3)
#       2026.02.24 : PGDBManager._get_most_suitable_unique_keys() 추가 및 피영향 메서드 수정
#       2026.03.02 : PGDBManager.normalize_datetime_columns() -> PGDBManager.convert_datetime_for_db()로 수정
#                    PGDBManager.convert_numeric_for_db()로 추가
#       2026.03.04 : 싱글톤 호환을 위해, 주요 메서드들에 스키마 설정 옵션 추가, 매서드 레벨에서 스키마 선택(인젝션) 가능하도록 변경
#                    PGDBManager.open_session() 추가 (세션 컨트롤 필요시 사용), 레거시 컨텍스트 매니저 삭제
#       2026.03.05 : PGDBManager.update_dataframe() 추가, PGDBManager.batch_update_dataframe() 추가
#       2026.03.08 : PGDBManager.batch_upsert_dataframe() / PGDBManager.upsert_dataframe() -> PGDBManager.upsert_batch() 로 통합/수정
#                    PGDBManager.upsert_batch() 에서 스키마 설정 옵션 추가, 매서드 레벨에서 스키마 선택(인젝션) 가능하도록 변경
#                    PGDBManager.upsert_batch() : 세션 주입 가능한 옵션 추가
#                    ※ PGDBManager.update_batch()도 동일 수정
#       2026.03.19 : PGDBManager.upsert_batch() 에서 배치 단위 에러 메시지 모음 추가
#       2026.05.14 : PGDBManager facade 유지, 내부 책임별 모듈 분리
#                    - pg_database.py: DataBaseMaker
#                    - pg_schema.py: schema/table lifecycle
#                    - pg_batch.py: batch upsert/update
#                    - pg_dataframe.py: DataFrame conversion
#                    - pg_constraints.py: metadata constraint cache
#                    - pg_identifiers.py: PostgreSQL identifier quoting
#       2026.05.15 : mixin 상속 제거, composition component 주입 구조로 변경
# TODO : Steaming용 모듈 작성 고려
# TODO : 임의의 스키마 내 테이블 일괄 변경 (퍼블릭, 테넌트 스키마(스키마 미지정) 모두 가능)
# TODO : PGDBManager.convert_df_by_model() 추가. 테스트 완료시 기존 함수 삭제 (구현 : 2026.03.19)
############################################

# TODO : Error 클래스 등 나누기.
"""
asyncpg 사용시 유니코드 문제로 비동기로 pg 접속이 안될 수 있음. 그 경우 아래 확인

제어판 > 국가 또는 지역 > 관리자 옵션 > 유니코드를 지원하지 않는 프로그램용 언어
> 시스템 로캘 변경(C)... > Beta: 세계 언어 지원을 위해 Unicode UTF-8 사용

체크필수!!!
"""

from __future__ import annotations

import urllib
from typing import Any, AsyncContextManager, TypeVar

from pandas import DataFrame
from sqlalchemy import Column, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.sql.elements import Executable

from CUSTOMIZED.cust_logger import logger
from DATABASE.dbms import DBManager
from DATABASE.dbms.postgre.pg_batch import BatchResult
from DATABASE.dbms.postgre.pg_components import PGManagerComponents
from DATABASE.dbms.postgre.pg_database import DataBaseMaker
from DATABASE.dbms.postgre.pg_dataframe import PGDataFrameConverter


TableModel = TypeVar("TableModel", bound=DeclarativeBase)


class PGDBManager(DBManager):
    """PostgreSQL 비동기 DB manager.

    이 클래스는 외부 공개 API를 유지하는 facade다. 세부 책임은 같은 패키지의
    schema, batch, dataframe, constraint 모듈에 둔다.
    """

    def __init__(
        self,
        base_model: type[TableModel],
        db_name: str,
        user: str,
        password: str,
        host: str,
        port: int = 5432,
        pool_size: int = 50,
        max_overflow: int = 150,
    ) -> None:
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.async_engine: AsyncEngine | None = None
        self.session_maker: sessionmaker[AsyncSession] | None = None
        self.base_model: type[DeclarativeBase] = base_model
        self.client_encoding = ""
        self.schemas: list[str] | None = None
        self._init_components()

        self.initialize_engine(
            self.db_name,
            self.user,
            self.password,
            self.host,
            self.port,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self._get_uniqueness(self.base_model)
        self.base_fields = {key: val for key, val in vars(self.base_model).items() if isinstance(val, Column)}

    def initialize_engine(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str,
        port: int = 5432,
        client_encoding: str = "utf8",
        pool_size: int = 50,
        max_overflow: int = 150,
    ) -> None:
        if self.async_engine is not None:
            return

        logger.info(f"{user}:***@{host}:{port}/{dbname}")
        encoded_password = urllib.parse.quote_plus(password)
        uri = f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{dbname}"
        self.client_encoding = client_encoding
        self.async_engine = create_async_engine(uri, echo=False, pool_size=pool_size, max_overflow=max_overflow)
        self.session_maker = sessionmaker(bind=self.async_engine, class_=AsyncSession, expire_on_commit=False)

    def _init_components(self) -> None:
        self._components: PGManagerComponents = PGManagerComponents(self)

    def _components_ref(self) -> PGManagerComponents:
        components = self.__dict__.get("_components")
        if components is None:
            components = PGManagerComponents(self)
            self._components = components
        return components

    def _engine(self) -> AsyncEngine:
        if self.async_engine is None:
            raise RuntimeError("PostgreSQL async engine is not initialized.")
        return self.async_engine

    def _session_factory(self) -> sessionmaker[AsyncSession]:
        if self.session_maker is None:
            raise RuntimeError("PostgreSQL session maker is not initialized.")
        return self.session_maker

    async def dispose_pool(self) -> None:
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Connection pool disposed.")

    async def execute_query(
        self,
        query: str | Executable,
        params: dict | list[dict] | None = None,
        schemas: list[str] | None = None,
    ) -> Any:
        async with self._session_factory()() as session:
            try:
                await self._set_session_schemas(session, schemas)
                result = await session.execute(text(query) if isinstance(query, str) else query, params or {})
                await session.commit()
                return result
            except Exception as exc:
                await session.rollback()
                logger.exception(f"Query execution error: {exc}")
                raise

    async def set_schemas(self, schemas: list[str] | None = None) -> PGDBManager:
        return await self._components_ref().schema_manager.set_schemas(schemas)

    async def exist_schemas(self, schemas: list[str], raise_error: bool = False) -> bool:
        return await self._components_ref().schema_manager.exist_schemas(schemas, raise_error)

    async def exists_schema(self, schema: str) -> bool:
        return await self._components_ref().schema_manager.exists_schema(schema)

    async def create_schema(self, schema: str) -> bool:
        return await self._components_ref().schema_manager.create_schema(schema)

    async def drop_schema(self, schema: str) -> bool:
        return await self._components_ref().schema_manager.drop_schema(schema)

    async def _set_session_schemas(self, session: AsyncSession, schemas: list[str] | None = None) -> None:
        await self._components_ref().schema_manager._set_session_schemas(session, schemas)

    async def get_all_schemas(self) -> list[str]:
        return await self._components_ref().schema_manager.get_all_schemas()

    async def copy_tables_of_schema(self, schema_to_make: str, schemas_for_fk: list[str] | None = None) -> int:
        return await self._components_ref().schema_manager.copy_tables_of_schema(schema_to_make, schemas_for_fk)

    async def truncate_table(self, table: type[DeclarativeBase], restart_identity: bool = True, cascade: bool = True) -> bool:
        return await self._components_ref().schema_manager.truncate_table(table, restart_identity, cascade)

    def __getattr__(self, name: str) -> Any:
        return self._components_ref().resolve(name)

    async def upsert_batch(
        self,
        table: type[DeclarativeBase],
        data: DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 30000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
        session: AsyncSession | None = None,
    ) -> BatchResult:
        return await self._components_ref().batch_writer.upsert_batch(
            table, data, schemas, conflict_cols, try_convert, session, params_per_chunk, allow_infinity, partial_commit
        )

    async def update_batch(
        self,
        table: type[DeclarativeBase],
        data_to_update: DataFrame | None = None,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
        session: AsyncSession | None = None,
        data: DataFrame | None = None,
    ) -> BatchResult:
        return await self._components_ref().batch_writer.update_batch(
            table, data_to_update, schemas, conflict_cols, try_convert, session, params_per_chunk, allow_infinity, partial_commit, data
        )

    @staticmethod
    def convert_datetime_for_db(df: DataFrame, deep_copy: bool = True) -> DataFrame:
        return PGDataFrameConverter.convert_datetime_for_db(df, deep_copy)

    @staticmethod
    def convert_numeric_for_db(
        df: DataFrame,
        set_none_as: float | int | None = None,
        allow_infinity: bool = True,
        deep_copy: bool = True,
    ) -> DataFrame:
        return PGDataFrameConverter.convert_numeric_for_db(df, set_none_as, allow_infinity, deep_copy)

    @staticmethod
    def convert_string_cols_by_model(df: DataFrame, model: type[DeclarativeBase]) -> DataFrame:
        return PGDataFrameConverter.convert_string_cols_by_model(df, model)

    def open_session(self, schemas: list[str] | None = None) -> AsyncContextManager[AsyncSession]:
        return self._components_ref().schema_manager.open_session(schemas)

    async def create_tables(self, schema: str | None = None) -> int:
        return await self._components_ref().schema_manager.create_tables(schema)

    async def drop_tables(self, schema: str | None = None) -> int:
        return await self._components_ref().schema_manager.drop_tables(schema)


__all__ = ["DataBaseMaker", "PGDBManager"]
