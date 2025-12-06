from fastapi import APIRouter, HTTPException, Depends, Body
from CUSTOMIZED.cust_parser import Parser
from WEB_SERVER.routers.settings import get_db_manager
from DATABASE.cruder import CRUDer
from WEB_SERVER import funcs_for_api as ffa
from sqlalchemy import text
from WEB_SERVER.routers.settings import get_cruder
import pandas as pd

router = APIRouter(prefix="", tags=["root"])


# 루트 엔드포인트
@router.get("/")
async def root():
    return {"message": "NOVAS EZ FastAPI 서버에 오신 걸 환영합니다!"}


@router.get("/health")
async def health_check(cruder: CRUDer = Depends(get_cruder)):
    db_status: bool = await cruder.is_db_connected()
    str_db_status: str = "connected" if db_status else "disconnected"
    return {"status": "healthy", "service": "NOVAS EZ API", "database": str_db_status}


@router.post("/upsert/instrument")
async def upsert_instrument(
    body: dict = Body(..., description="인스트루먼트 정보", example={
        "name": "ICT장비 이름",
        "host": "192.168.1.100",
        "user": "user",
        "port": 22,
        "dir_base_source": "/path/to/source",
        "dir_base_destination": "/path/to/destination",
        "ssh_key_path": "/path/to/key",
        "network_name": "network",
        "network_password": "password",
        "accessible": True
    }),
    cruder: CRUDer = Depends(get_cruder)
):
    """인스트루먼트 정보 업데이트"""
    none_values : list[str] = ['None', ""]
    temp_dict : dict = {
        "name": body.get("name"),
        "host": Parser.to_string(body.get("host"), none_values=none_values, ignore_case=False),
        "user": Parser.to_string(body.get("user"), none_values=none_values, ignore_case=False),
        "port": Parser.to_integer(body.get("port"), none_values=none_values, ignore_error=True),
        "dir_base_source": Parser.to_string(body.get("dir_base_source"), none_values=none_values, ignore_case=False),
        "dir_base_destination": Parser.to_string(body.get("dir_base_destination"), none_values=none_values, ignore_case=False),
        "ssh_key_path": Parser.to_string(body.get("ssh_key_path"), none_values=none_values, ignore_case=False),
    }
    
    await ffa.upsert_instrument(cruder, pd.DataFrame([temp_dict]))
    return {"status": "success"}

