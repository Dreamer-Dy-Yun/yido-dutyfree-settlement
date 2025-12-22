############################################
# 라우터 세팅 파일
# 여기서 임포트 된 모듈들은 모든 라우터에서 공통으로 사용되는 모듈들이므로 직접 사용되지 않는다고 해서 삭제하면 문제생김.
############################################
import os
from functools import lru_cache
from DATABASE.cruder import CRUDer
from DATABASE.db_manager import DBManager
from DATABASE.config import db_manager
from fastapi import Depends
from pathlib import Path
from WEB_SERVER.services import service as svc
from WEB_SERVER.routers.responses import as_gzip_response
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_web_helper import Export

DIR_BASE = Path(os.getenv("DIR_BASE_FOR_PARQUET", "C:/Users/user/ict_parquets"))

def set_dir_base(path: Path | str) -> None:
    global DIR_BASE
    DIR_BASE = Path(path)

@lru_cache 
def get_db_manager() -> DBManager:
    return db_manager

@lru_cache 
def get_cruder(db_mgr: DBManager = Depends(get_db_manager)) -> CRUDer:
    return CRUDer(db_mgr)

