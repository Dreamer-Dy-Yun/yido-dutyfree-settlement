###########################################
# Module name : models
# Module class : SQLAlchemy ORM Models
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.11.30
# Updated at : 2025.11.30
# Supported by : ChatGPT-4o
# Note : 
#       2026.02.24 : 이하의 추상 매서드 삭제(보다 깊어진 DB 제약조건 이해로 인한 변경)
#                    _get_unique_columns
#                    _get_primary_columns
#                    get_uniqueness
#       2026.02.26 : PGDBManager 와 시그니처 통일
# TODO : Steaming용 모듈 작성 고려
############################################
from abc import ABC, abstractmethod
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import Executable
from typing import TypeVar, Any, AsyncContextManager
import pandas as pd

TableModel = TypeVar('TableModel', bound=DeclarativeBase)


class DBManager(ABC):
    """
    데이터베이스 관리자 추상 클래스
    
    모든 데이터베이스 구현체(PGDBManager, MySQLManager 등)가 상속받아야 하는
    기본 인터페이스를 정의합니다.
    
    Attributes:
        None (추상 클래스이므로 인스턴스 변수는 구현체에서 정의)
    
    Methods (구현체에서 공통 제공해야 하는 인터페이스):
        upsert_batch: DataFrame 배치 업서트
        update_batch: DataFrame 배치 업데이트
        execute_query: SQL 쿼리 실행
        create_tables: 테이블 생성 (옵션: 특정 스키마만)
        drop_tables: 테이블 삭제 (옵션: 특정 스키마만)
    """


    @abstractmethod
    async def upsert_batch(
        self,
        table: DeclarativeBase,
        data: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
        session: AsyncSession | None = None,
    ) -> dict[str, int | pd.DataFrame]:
        """
        DataFrame을 배치 업서트합니다.
        
        Args:
            table: SQLAlchemy DeclarativeBase 모델 클래스
            data: pandas DataFrame
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])
            conflict_cols: upsert 충돌 기준 컬럼 (None이면 자동 선택)
            try_convert: 날짜/숫자 정규화 수행 여부
            params_per_chunk: 청크 단위 파라미터 개수 기준
            allow_infinity: numeric 변환시 무한대 허용 여부
            partial_commit: True면 배치별 커밋, False면 전체 커밋
            session: 외부 주입 세션 (주입 시 커밋/롤백은 호출부에서 관리)
        
        Returns:
            처리 결과 요약 딕셔너리
        """
        ...

    @abstractmethod
    async def update_batch(
        self,
        table: DeclarativeBase,
        data_to_update: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
        params_per_chunk: int = 10000,
        allow_infinity: bool = True,
        partial_commit: bool = True,
        session: AsyncSession | None = None,
    ) -> dict[str, int | pd.DataFrame]:
        """
        DataFrame을 배치 업데이트합니다. (UPDATE only)

        Args:
            table: SQLAlchemy DeclarativeBase 모델 클래스
            data_to_update: pandas DataFrame
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])
            conflict_cols: 업데이트 매칭 기준 컬럼 (None이면 자동 선택)
            try_convert: 날짜/숫자 정규화 수행 여부
            params_per_chunk: 청크 단위 파라미터 개수 기준
            allow_infinity: numeric 변환시 무한대 허용 여부
            partial_commit: True면 배치별 커밋, False면 전체 커밋
            session: 외부 주입 세션 (주입 시 커밋/롤백은 호출부에서 관리)

        Returns:
            처리 결과 요약 딕셔너리
        """
        ...

    # -------------------------------------------------------------------------
    # Backward-compatible wrappers
    # -------------------------------------------------------------------------
    async def upsert_dataframe(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
    ) -> int:
        result = await self.upsert_batch(
            table=table,
            data=df,
            schemas=schemas,
            conflict_cols=conflict_cols,
            try_convert=try_convert,
        )
        return int(result["cnt_success_rows"])

    async def update_dataframe(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        schemas: list[str] | None = None,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
    ) -> int:
        result = await self.update_batch(
            table=table,
            data_to_update=df,
            schemas=schemas,
            conflict_cols=conflict_cols,
            try_convert=try_convert,
        )
        return int(result["cnt_success_rows"])

    async def batch_upsert_dataframe(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        schemas: list[str] | None = None,
        allowed_param_size: int = 10000,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
    ) -> int:
        result = await self.upsert_batch(
            table=table,
            data=df,
            schemas=schemas,
            conflict_cols=conflict_cols,
            try_convert=try_convert,
            params_per_chunk=allowed_param_size,
        )
        return int(result["cnt_success_rows"])

    async def batch_update_dataframe(
        self,
        table: DeclarativeBase,
        df: pd.DataFrame,
        schemas: list[str] | None = None,
        allowed_param_size: int = 10000,
        conflict_cols: list[str] | None = None,
        try_convert: bool = True,
    ) -> int:
        result = await self.update_batch(
            table=table,
            data_to_update=df,
            schemas=schemas,
            conflict_cols=conflict_cols,
            try_convert=try_convert,
            params_per_chunk=allowed_param_size,
        )
        return int(result["cnt_success_rows"])

    @abstractmethod
    async def execute_query(
        self,
        query: str | Executable,
        params: dict | list[dict] | None = None,
        schemas: list[str] | None = None,
    ) -> Any:
        """
        SQL 쿼리를 실행합니다.
        
        Args:
            query: 실행할 SQL 쿼리 문자열 또는 Executable 객체
            params: 쿼리 파라미터 (딕셔너리 또는 딕셔너리 리스트)
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])
        
        Returns:
            쿼리 실행 결과 (DB별로 다를 수 있음, 일반적으로 SQLAlchemy Result 객체)
        
        Raises:
            DB별 예외 (예: PostgreSQL의 경우 asyncpg 예외)
        """
        pass

    @abstractmethod
    def open_session(
        self,
        schemas: list[str] | None = None,
    ) -> AsyncContextManager[AsyncSession]:
        """
        스키마 컨텍스트가 적용된 AsyncSession 컨텍스트를 엽니다.

        Args:
            schemas: search_path로 설정할 스키마 리스트 (예: ["tenant_xxx", "public"])

        Returns:
            AsyncSession을 제공하는 비동기 컨텍스트 매니저
        """
        pass

    @abstractmethod
    async def create_tables(self, schema: str | None = None) -> int:
        """
        데이터베이스에 테이블을 생성합니다.

        Args:
            schema: 특정 스키마의 테이블만 생성 (None이면 모든 테이블 대상)

        Returns:
            생성된(또는 대상이 된) 테이블 개수
        """
        pass

    @abstractmethod
    async def drop_tables(self, schema: str | None = None) -> int:
        """
        데이터베이스의 테이블을 삭제합니다.

        Args:
            schema: 특정 스키마의 테이블만 삭제 (None이면 모든 테이블 대상)

        Returns:
            삭제된 테이블 개수
        """
        pass

    @staticmethod
    @abstractmethod
    def convert_datetime_for_db(df: pd.DataFrame) -> pd.DataFrame:
        """datetime 컬럼만 NaT → None 변환 (DB insert 직전용)."""
        ...

    @staticmethod
    @abstractmethod
    def convert_numeric_for_db(
        df: pd.DataFrame,
        set_none_as: float | int | None = None,
        allow_infinity: bool = True,
        deep_copy: bool = True,
    ) -> pd.DataFrame:
        """numeric 컬럼만 NaN/None 처리 (DB insert 직전용)."""
        ...

