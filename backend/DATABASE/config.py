import os
from collections.abc import Mapping
from DATABASE import pg_manager, models
from DATABASE.repositories.authorities import (
    UserRepository,
    TenantRepository,
)

DEFAULT_DB_PASSWORD = "123!@#qwe"


def _is_production_env(env: Mapping[str, str] | None = None) -> bool:
    env_source = os.environ if env is None else env
    return any(
        str(env_source.get(key, "")).lower() in {"prod", "production"}
        for key in ("APP_ENV", "ENV", "ENVIRONMENT")
    )


def _resolve_db_password(env: Mapping[str, str] | None = None) -> str:
    env_source = os.environ if env is None else env
    password = env_source.get("DB_PASSWORD", DEFAULT_DB_PASSWORD)
    if _is_production_env(env_source) and password in {"", DEFAULT_DB_PASSWORD}:
        raise RuntimeError("DB_PASSWORD must be set to a non-default value in production.")
    return password


db_manager = pg_manager.PGDBManager(
    models.BaseModel,
    db_name=os.getenv("DB_NAME", "db"),
    user=os.getenv("DB_USER", "admin"),
    password=_resolve_db_password(),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "50"))
)

# Repository 인스턴스 생성
user_repository = UserRepository(db_manager)
tenant_repository = TenantRepository(db_manager)
