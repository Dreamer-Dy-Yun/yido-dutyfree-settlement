"""
PGDBManager 통합 테스트

- DataBaseMaker 로 테스트용 DB 생성(없으면 생성, 있으면 통과)
- PGDBManager 로 엔진 초기화 및 테이블 생성까지 검증
"""

import pytest
import pandas as pd

from DATABASE.models import BaseModel
from DATABASE.models.public_model import Tenant
from DATABASE.dbms.postgre.pg_manager import DataBaseMaker, PGDBManager


# 테스트용 DB 접속 정보 (개발용 로컬 DB 기준)
DB_NAME = "dev"
DB_USER = "admin"
DB_PASSWORD = "123!@#qwe"
DB_HOST = "localhost"
DB_PORT = 5432


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    """
    세션 시작 시점에 테스트용 DB가 없으면 생성.
    - 실제 postgres 서버의 postgres DB에 접속해 CREATE DATABASE 실행.
    """

    print(f"\n[setup] 테스트용 DB 확인/생성: db={DB_NAME}, host={DB_HOST}, port={DB_PORT}")
    maker = DataBaseMaker(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    ok = maker.run()
    assert ok, "테스트용 DB 생성/확인에 실패했습니다."


@pytest.fixture(scope="function")
def pg_manager(ensure_test_database):
    """
    테스트용 PGDBManager 인스턴스 생성.
    - 애플리케이션과 동일하게 생성 시점에 엔진/세션 풀을 초기화.
    """

    print("[setup] PGDBManager 생성 (엔진/세션 풀 초기화)")
    mgr = PGDBManager(
        base_model=BaseModel,
        db_name=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    return mgr


@pytest.mark.asyncio
async def test_create_tables_public_schema(pg_manager: PGDBManager):
    """
    public 스키마 테이블 생성 테스트
    - 에러 없이 호출되면 통과
    - 반환값은 생성된(또는 이미 존재해서 스킵된) 테이블 개수
    """

    print("\n[test] public 스키마 테이블 생성 테스트 시작")
    count = await pg_manager.create_tables(schema="public")
    print(f"[test] public 스키마 테이블 생성 결과: {count}개")
    assert count >= 1


@pytest.mark.asyncio
async def test_schema_create_and_exists(pg_manager: PGDBManager):
    """
    신규 스키마 생성 및 존재 여부 확인 테스트
    """

    schema_name = "tenant_test_int"
    print(f"\n[test] 스키마 생성/존재 여부 테스트: {schema_name}")

    # 스키마 생성 (이미 있어도 IF NOT EXISTS 로 안전하게 처리됨)
    await pg_manager.create_schema(schema_name)
    print(f"[test] 스키마 생성 호출 완료: {schema_name}")

    # 존재 여부 확인
    exists = await pg_manager.exists_schema(schema_name)
    print(f"[test] 스키마 존재 여부: {schema_name} -> {exists}")
    assert exists is True


@pytest.mark.asyncio
async def test_set_schemas_and_get_all_schemas(pg_manager: PGDBManager):
    """
    set_schemas / get_all_schemas 기본 동작 테스트
    """

    schema_name = "tenant_test_int"
    print(f"\n[test] set_schemas / get_all_schemas 테스트, 타겟 스키마: {schema_name}")

    # 스키마 생성 보장
    await pg_manager.create_schema(schema_name)
    print(f"[test] 스키마 생성 보장: {schema_name}")

    # search_path 설정 (tenant_test_int, public 순)
    await pg_manager.set_schemas([schema_name, "public"])
    print(f"[test] search_path 설정 완료: [{schema_name}, public]")

    # 전체 스키마 목록에서 우리가 만든 스키마가 있는지 확인
    schemas = await pg_manager.get_all_schemas()
    print(f"[test] 전체 스키마 목록 (일부): {schemas[:10]}")
    assert schema_name in schemas


@pytest.mark.asyncio
async def test_upsert_tenant_and_query(pg_manager: PGDBManager):
    """
    Tenant 테이블에 대한 upsert & 조회 통합 테스트
    """

    # public 스키마 테이블이 생성되어 있다고 가정 (없으면 생성)
    print("\n[test] Tenant upsert & 조회 통합 테스트 시작")
    await pg_manager.create_tables(schema="public")
    print("[test] public 스키마 테이블 생성/검증 완료")

    # 테스트용 business_no / schema_name (다른 곳에서 쓰지 않을 값)
    biz_no = "INT-TEST-001"
    schema_name = "tenant_int_001"

    df = pd.DataFrame(
        [
            {
                "name": "통합테스트 회사",
                "business_no": biz_no,
                "schema_name": schema_name,
                "dir_root": "/test/integration",
                "is_active": True,
            }
        ]
    )

    # 1차 upsert (INSERT)
    print(f"[test] 1차 upsert (INSERT) 실행: biz_no={biz_no}, schema_name={schema_name}")
    count = await pg_manager.upsert_dataframe(Tenant, df)
    print(f"[test] 1차 upsert 처리 행 수: {count}")
    assert count == 1

    # 조회로 존재 여부 확인
    result = await pg_manager.execute_query(
        "SELECT business_no, schema_name, is_active "
        "FROM public.tenant WHERE business_no = :biz_no",
        {"biz_no": biz_no},
    )
    row = result.fetchone()
    print(f"[test] 1차 조회 결과: {row}")
    assert row is not None
    assert row.business_no == biz_no
    assert row.schema_name == schema_name
    assert row.is_active is True

    # 2차 upsert (UPDATE) - is_active False 로 변경
    df_update = pd.DataFrame(
        [
            {
                "name": "통합테스트 회사(수정)",
                "business_no": biz_no,
                "schema_name": schema_name,
                "dir_root": "/test/integration",
                "is_active": False,
            }
        ]
    )

    print(f"[test] 2차 upsert (UPDATE) 실행: biz_no={biz_no}, is_active=False")
    count2 = await pg_manager.upsert_dataframe(Tenant, df_update)
    print(f"[test] 2차 upsert 처리 행 수: {count2}")
    assert count2 == 1

    # 다시 조회해서 is_active 가 False 로 변경되었는지 확인
    result2 = await pg_manager.execute_query(
        "SELECT business_no, schema_name, is_active "
        "FROM public.tenant WHERE business_no = :biz_no",
        {"biz_no": biz_no},
    )
    row2 = result2.fetchone()
    print(f"[test] 2차 조회 결과: {row2}")
    assert row2 is not None
    assert row2.business_no == biz_no
    assert row2.schema_name == schema_name
    assert row2.is_active is False

    # 테스트 데이터 정리 (다른 테스트/환경에 영향 주지 않도록)
    print(f"[test] 테스트 데이터 정리: biz_no={biz_no}")
    await pg_manager.execute_query(
        "DELETE FROM public.tenant WHERE business_no = :biz_no",
        {"biz_no": biz_no},
    )


@pytest.mark.asyncio
async def test_dispose_pool():
    """
    연결 풀 정상 해제 테스트
    """

    print("\n[test] dispose_pool 테스트 시작")
    mgr = PGDBManager(
        base_model=BaseModel,
        db_name=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    await mgr.dispose_pool()
    print("[test] dispose_pool 호출 완료")

