import os
from DATABASE import pg_manager, models
from DATABASE.repositories.authorities import (
    UserRepository,
    TenantRepository,
)

db_manager = pg_manager.PGDBManager(
    models.BaseModel,
    db_name=os.getenv("DB_NAME", "db"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "123!@#qwe"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")), 
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "50"))  
)

# Repository 인스턴스 생성
user_repository = UserRepository(db_manager)
tenant_repository = TenantRepository(db_manager)

