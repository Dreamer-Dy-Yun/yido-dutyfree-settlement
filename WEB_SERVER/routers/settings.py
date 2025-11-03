import os
from functools import lru_cache
from DATABASE.cruder import CRUDer
from DATABASE.pg_manager import PGDBManager
from DATABASE.config import db_manager
from fastapi import Depends
from pathlib import Path
from WEB_SERVER import funcs_for_api as ffa
from WEB_SERVER.routers.responses import as_gzip_response
from CUSTOMIZED.cust_deco_error import handle_http_error
from CUSTOMIZED.cust_web_helper import Export

PARENT_PATH_SPEC = Path(os.getenv("PARENT_PATH_SPEC", "C:/Users/user/Novas_Ez"))
PARENT_PATH_MEASURED = Path(os.getenv("PARENT_PATH_MEASURED", "C:/Users/user/Novas_Ez"))

@lru_cache 
def get_db_manager() -> PGDBManager:
    return db_manager

@lru_cache 
def get_cruder(db_mgr: PGDBManager = Depends(get_db_manager)) -> CRUDer:
    return CRUDer(db_mgr)

