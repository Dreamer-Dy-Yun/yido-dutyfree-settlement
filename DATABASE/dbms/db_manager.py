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
# TODO : Steaming용 모듈 작성 고려
############################################
from abc import ABC, abstractmethod
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from typing import TypeVar, Type, Any
import pandas as pd

TableModel = TypeVar('TableModel', bound=DeclarativeBase)


class DBManager(ABC):
    """
    데이터베이스 관리자 추상 클래스
    
    모든 데이터베이스 구현체(PGDBManager, MySQLManager 등)가 상속받아야 하는
    기본 인터페이스를 정의합니다.
    
    Attributes:
        None (추상 클래스이므로 인스턴스 변수는 구현체에서 정의)
    
    Methods:
        upsert_dataframe: DataFrame을 데이터베이스에 업데이트합니다.
        execute_query: SQL 쿼리 실행
        create_tables: 테이블 생성
        drop_tables: 테이블 삭제
        get_uniqueness: 테이블의 유니크 키/프라이머리 키 정보 추출
        _get_unique_columns: 테이블의 유니크 컬럼 추출 (내부 메서드)
        _get_primary_columns: 테이블의 프라이머리 키 컬럼 추출 (내부 메서드)
    """


    @abstractmethod
    async def batch_upsert_dataframe(self, table: DeclarativeBase, df: pd.DataFrame, allowed_param_size: int = 10000) -> int:
        """
        DataFrame을 데이터베이스에 업데이트합니다.
        
        Args:
            table: SQLAlchemy DeclarativeBase 모델 클래스
            df: pandas DataFrame
            allowed_param_size: 파라미터 개수
        
        Returns:
            업데이트 된 행 수
        """
        pass

    @abstractmethod
    async def upsert_dataframe(self, table: DeclarativeBase, df: pd.DataFrame, try_normalize: bool = True) -> int:
        """
        DataFrame을 데이터베이스에 업데이트합니다.
        
        Args:
            table: SQLAlchemy DeclarativeBase 모델 클래스
            df: pandas DataFrame
            try_normalize: 날짜 형식 정규화 여부
        
        Returns:
            업데이트 된 행 수
        """
        pass

    @abstractmethod
    async def execute_query(self, query: str | Any, params: dict | list[dict] | None = None) -> Any:
        """
        SQL 쿼리를 실행합니다.
        
        Args:
            query: 실행할 SQL 쿼리 문자열 또는 Executable 객체
            params: 쿼리 파라미터 (딕셔너리 또는 딕셔너리 리스트)
        
        Returns:
            쿼리 실행 결과 (DB별로 다를 수 있음, 일반적으로 SQLAlchemy Result 객체)
        
        Raises:
            DB별 예외 (예: PostgreSQL의 경우 asyncpg 예외)
        """
        pass

    @abstractmethod
    async def create_tables(self) -> None:
        """
        데이터베이스에 모든 테이블을 생성합니다.
        
        Raises:
            DB별 예외
        """
        pass

    @abstractmethod
    async def drop_tables(self) -> None:
        """
        데이터베이스의 모든 테이블을 삭제합니다.
        
        Raises:
            DB별 예외
        """
        pass


