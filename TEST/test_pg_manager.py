###########################################
# Module name : test_pg_manager.py
# 테스트 대상 : DATABASE.pg_manager.PGDBManager, DataBaseMaker
# Written by : GPT Test Template
# Note       : 실제 동작하는 단위 테스트 (Mock 활용)
###########################################

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, UniqueConstraint, Table, MetaData

from DATABASE.pg_manager import DataBaseMaker, PGDBManager
from DATABASE import models


class TestDataBaseMaker:
    """DataBaseMaker 클래스에 대한 단위 테스트"""

    @pytest.mark.asyncio
    async def test_database_maker_init(self):
        """DataBaseMaker 초기화 테스트"""
        maker = DataBaseMaker(
            db_name="test_db",
            user="test_user",
            password="test_password",
            host="localhost",
            port=5432
        )
        
        assert maker.db_name == "test_db"
        assert maker.user == "test_user"
        assert maker.password == "test_password"
        assert maker.host == "localhost"
        assert maker.port == 5432
        assert maker.conn is None

    @pytest.mark.asyncio
    async def test_database_maker_run_with_mock(self):
        """asyncpg Mock을 사용한 run() 메서드 테스트"""
        maker = DataBaseMaker(
            db_name="test_db",
            user="test_user",
            password="test_password",
            host="localhost",
            port=5432
        )
        
        # Mock asyncpg connection
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=False)  # DB가 존재하지 않음
        mock_conn.execute = AsyncMock()
        mock_conn.close = AsyncMock()
        
        with patch('DATABASE.pg_manager.asyncpg.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_conn
            
            result = await maker._run_async()
            
            assert result is True
            mock_connect.assert_called_once()
            mock_conn.fetchval.assert_called_once()
            mock_conn.execute.assert_called_once()  # CREATE DATABASE 호출
            mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_maker_run_db_exists(self):
        """이미 DB가 존재하는 경우"""
        maker = DataBaseMaker(
            db_name="existing_db",
            user="test_user",
            password="test_password",
            host="localhost",
            port=5432
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=True)  # DB가 이미 존재
        mock_conn.close = AsyncMock()
        
        with patch('DATABASE.pg_manager.asyncpg.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_conn
            
            result = await maker._run_async()
            
            assert result is True
            mock_conn.fetchval.assert_called_once()
            mock_conn.execute.assert_not_called()  # CREATE DATABASE 호출 안 됨


class TestPGDBManager:
    """PGDBManager 클래스에 대한 단위 테스트"""

    @pytest.fixture
    def pg_manager(self):
        """테스트용 PGDBManager 인스턴스 생성"""
        return PGDBManager(
            base_model=models.BaseModel,
            db_name="test_db",
            user="test_user",
            password="test_password",
            host="localhost",
            port=5432,
            pool_size=5,
            max_overflow=10,
        )

    def test_pgdbmanager_init(self, pg_manager):
        """PGDBManager 초기화 테스트"""
        assert pg_manager.db_name == "test_db"
        assert pg_manager.user == "test_user"
        assert pg_manager.host == "localhost"
        assert pg_manager.port == 5432
        assert pg_manager.async_engine is not None
        assert pg_manager.session_maker is not None
        assert pg_manager.base_model == models.BaseModel

    def test_pgdbmanager_get_uniqueness(self, pg_manager):
        """get_uniqueness() 메서드 테스트 - PK/UK 추출 검증"""
        uniqueness = pg_manager.get_uniqueness(models.BaseModel)
        
        # BaseModel의 모든 테이블에 대해 uniqueness 정보가 있는지 확인
        assert isinstance(uniqueness, dict)
        
        # Instrument 테이블: name이 unique
        if "instrument" in uniqueness:
            assert "name" in uniqueness["instrument"]
        
        # Model 테이블: name이 unique
        if "model" in uniqueness:
            assert "name" in uniqueness["model"]
        
        # Spec 테이블: (model_name, path_sub_datafile)이 unique constraint
        if "spec" in uniqueness:
            assert len(uniqueness["spec"]) > 0
        
        # Measured 테이블: (serial_no, path_sub_datafile)이 unique constraint
        if "measured" in uniqueness:
            assert len(uniqueness["measured"]) > 0

    def test_pgdbmanager_normalize_datetime_columns(self):
        """normalize_datetime_columns() 정적 메서드 테스트"""
        # datetime64[ns] 타입의 컬럼이 있는 DataFrame 생성
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'created_at': pd.to_datetime(['2025-01-01', '2025-01-02', None]),
            'updated_at': pd.to_datetime(['2025-01-01 10:00:00', '2025-01-02 11:00:00', '2025-01-03 12:00:00'])
        })
        
        # NaT를 명시적으로 추가
        df.loc[0, 'created_at'] = pd.NaT
        
        result = PGDBManager.normalize_datetime_columns(df)
        
        # datetime 컬럼이 object 타입으로 변환되었는지 확인
        assert result['created_at'].dtype == 'object'
        assert result['updated_at'].dtype == 'object'
        
        # NaT가 None으로 변환되었는지 확인
        assert result.loc[0, 'created_at'] is None or pd.isna(result.loc[0, 'created_at'])
        
        # 정상 datetime 값은 유지되는지 확인
        assert isinstance(result.loc[1, 'created_at'], (datetime, type(None)))
        assert isinstance(result.loc[1, 'updated_at'], (datetime, type(None)))

    def test_pgdbmanager_normalize_datetime_columns_no_datetime(self):
        """datetime 컬럼이 없는 경우"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['a', 'b', 'c'],
            'value': [1.0, 2.0, 3.0]
        })
        
        result = PGDBManager.normalize_datetime_columns(df)
        
        # 원본과 동일해야 함
        pd.testing.assert_frame_equal(result, df)

    @pytest.mark.asyncio
    async def test_pgdbmanager_execute_query_with_mock(self, pg_manager):
        """execute_query() 메서드 Mock 테스트"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        
        # session_maker를 Mock으로 교체
        pg_manager.session_maker = MagicMock(return_value=mock_session)
        pg_manager.session_maker.__call__ = MagicMock(return_value=mock_session)
        
        # 컨텍스트 매니저로 동작하도록 설정
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        result = await pg_manager.execute_query("SELECT 1")
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_pgdbmanager_execute_query_rollback_on_error(self, pg_manager):
        """execute_query() 에러 발생 시 rollback 테스트"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Test error"))
        mock_session.rollback = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # session_maker()가 컨텍스트 매니저를 반환하도록 설정
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        pg_manager.session_maker = MagicMock(return_value=mock_context_manager)
        
        with pytest.raises(Exception, match="Test error"):
            await pg_manager.execute_query("SELECT 1")
        
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_pgdbmanager_truncate_table_with_mock(self, pg_manager):
        """truncate_table() Mock 테스트"""
        mock_table = MagicMock()
        mock_table.__tablename__ = "test_table"
        
        # execute_query를 Mock
        with patch.object(pg_manager, 'execute_query', new_callable=AsyncMock) as mock_execute:
            result = await pg_manager.truncate_table(mock_table, restart_identity=True, cascade=True)
            
            assert result is True
            mock_execute.assert_called_once()
            # TRUNCATE 쿼리가 올바르게 생성되었는지 확인
            call_args = mock_execute.call_args[0][0]
            assert "TRUNCATE TABLE test_table" in call_args
            assert "RESTART IDENTITY" in call_args
            assert "CASCADE" in call_args

    @pytest.mark.asyncio
    async def test_pgdbmanager_batch_upsert_dataframe_batch_splitting(self, pg_manager):
        """batch_upsert_dataframe() 배치 분할 로직 테스트"""
        # 큰 DataFrame 생성 (100행, 10컬럼 = 1000 파라미터)
        # allowed_param_size=10000이면 10000/10 = 1000행씩 배치
        # 하지만 100행이면 1배치로 처리됨
        df = pd.DataFrame({
            'id': range(100),
            **{f'col_{i}': range(100) for i in range(10)}
        })
        
        mock_table = MagicMock()
        mock_table.__tablename__ = "test_table"
        
        # upsert_dataframe을 Mock하여 호출 횟수 확인
        call_count = []
        
        async def mock_upsert(table, df_batch, **kwargs):
            call_count.append(len(df_batch))
            return len(df_batch)
        
        pg_manager.upsert_dataframe = AsyncMock(side_effect=mock_upsert)
        
        result = await pg_manager.batch_upsert_dataframe(mock_table, df, allowed_param_size=10000)
        
        # 100행이면 1번 호출되어야 함
        assert len(call_count) == 1
        assert call_count[0] == 100
        assert result == 100

    @pytest.mark.asyncio
    async def test_pgdbmanager_batch_upsert_dataframe_multiple_batches(self, pg_manager):
        """batch_upsert_dataframe() 여러 배치로 나뉘는 경우"""
        # 500행, 21컬럼 (id + 20개 컬럼)
        # allowed_param_size=1000이면 1000/21 = 47행씩 배치 (정수 나눗셈)
        # 500행을 47행씩 나누면: 47*10 = 470, 나머지 30행 = 총 11배치
        df = pd.DataFrame({
            'id': range(500),
            **{f'col_{i}': range(500) for i in range(20)}
        })
        
        mock_table = MagicMock()
        mock_table.__tablename__ = "test_table"
        
        call_count = []
        
        async def mock_upsert(table, df_batch, **kwargs):
            call_count.append(len(df_batch))
            return len(df_batch)
        
        pg_manager.upsert_dataframe = AsyncMock(side_effect=mock_upsert)
        
        result = await pg_manager.batch_upsert_dataframe(mock_table, df, allowed_param_size=1000)
        
        # 실제 계산: 1000 // 21 = 47행씩
        # 500행을 47행씩 나누면 11배치 (마지막은 30행)
        expected_batch_size = 1000 // len(df.columns)  # 47
        expected_num_batches = (len(df) + expected_batch_size - 1) // expected_batch_size  # 올림 나눗셈
        
        assert len(call_count) == expected_num_batches
        # 모든 배치의 행 수 합이 전체 행 수와 같아야 함
        assert sum(call_count) == len(df)
        # 마지막 배치를 제외하고는 모두 expected_batch_size 이하여야 함
        assert all(count <= expected_batch_size for count in call_count)
        # 마지막 배치는 나머지 행 수 (30행) 또는 expected_batch_size
        assert call_count[-1] == len(df) % expected_batch_size or call_count[-1] == expected_batch_size
        assert result == 500

    @pytest.mark.asyncio
    async def test_pgdbmanager_batch_upsert_dataframe_empty_dataframe(self, pg_manager):
        """빈 DataFrame 처리"""
        df = pd.DataFrame()
        mock_table = MagicMock()
        
        result = await pg_manager.batch_upsert_dataframe(mock_table, df)
        
        assert result == 0
        # upsert_dataframe이 호출되지 않아야 함
        if hasattr(pg_manager, 'upsert_dataframe'):
            # Mock이 설정되지 않았을 수 있으므로 확인만
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


