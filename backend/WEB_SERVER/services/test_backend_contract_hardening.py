from datetime import datetime

import pytest

from DATABASE.config import DEFAULT_DB_PASSWORD, _resolve_db_password
from DATABASE.models.public_model import LLM_API_Key, Tenant as PublicTenant
from WEB_SERVER.auth.config import DEFAULT_JWT_SECRET_KEY, _resolve_secret_key
from WEB_SERVER.routers import router_tenant


def test_llm_api_key_serialization_masks_secret():
    raw_key = "sk-test-secret-value-1234"
    row = LLM_API_Key(
        purpose="OCR",
        llm_provider="openai",
        llm_model="gpt-test",
        api_key=raw_key,
        is_active=True,
    )

    assert raw_key not in repr(row)
    assert row.to_dict()["api_key"] == "sk-test-******...******1234"
    assert LLM_API_Key.mask_api_key("short") == "******"


def test_production_requires_non_default_secrets():
    with pytest.raises(RuntimeError):
        _resolve_secret_key({"ENVIRONMENT": "production", "JWT_SECRET_KEY": DEFAULT_JWT_SECRET_KEY})

    with pytest.raises(RuntimeError):
        _resolve_db_password({"APP_ENV": "prod", "DB_PASSWORD": DEFAULT_DB_PASSWORD})

    assert _resolve_secret_key({"ENVIRONMENT": "development"}) == DEFAULT_JWT_SECRET_KEY
    assert _resolve_db_password({"APP_ENV": "local"}) == DEFAULT_DB_PASSWORD


@pytest.mark.asyncio
async def test_usage_queries_count_matched_model_not_missing_edi_info():
    class Result:
        def __init__(self, value):
            self.value = value

        def scalar(self):
            return self.value

    class FakeDB:
        def __init__(self):
            self.queries = []

        async def execute_query(self, query, schemas=None):
            self.queries.append(query)
            return Result(len(self.queries))

    current_user = type("User", (), {"tenant_schema": "tenant_alpha"})()
    db = FakeDB()

    response = await router_tenant.get_usage(
        start_date=datetime(2026, 5, 1),
        end_date=datetime(2026, 5, 14),
        current_user=current_user,
        db=db,
    )

    assert response["total_matched"] == 6
    matched_query = str(db.queries[5]).lower()
    assert "matched" in matched_query
    assert "edi_info" not in matched_query
    assert "image.db_created_at" not in matched_query


def test_tenant_info_response_excludes_internal_filesystem_fields():
    tenant = PublicTenant(
        name="YIDO",
        alias="YIDO",
        country_code=82,
        business_no="123-45-67890",
        contact="02-0000-0000",
        email="admin@example.test",
        address="Seoul",
        dir_base="tenants/company_internal",
        schema_name="company_internal",
        is_db_built=True,
        is_active=True,
    )

    payload = router_tenant._tenant_info_response(tenant)

    assert payload["schema_name"] == "company_internal"
    assert "dir_base" not in payload
    assert "is_db_built" not in payload
