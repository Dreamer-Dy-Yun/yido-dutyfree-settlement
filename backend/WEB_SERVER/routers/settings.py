############################################
# 라우터 세팅 파일
# 여기서 임포트 된 모듈들은 모든 라우터에서 공통으로 사용되는 모듈들이므로 직접 사용되지 않는다고 해서 삭제하면 문제생김.
############################################
from functools import lru_cache
from DATABASE.repositories.authorities import UserRepository, TenantRepository
from DATABASE.dbms import DBManager
from DATABASE.config import db_manager, user_repository, tenant_repository

@lru_cache 
def get_db_manager() -> DBManager:
    return db_manager

@lru_cache 
def get_user_repository() -> UserRepository:
    return user_repository

@lru_cache 
def get_tenant_repository() -> TenantRepository:
    return tenant_repository
