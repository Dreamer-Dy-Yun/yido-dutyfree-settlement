from fastapi import APIRouter, Depends, Body
from CUSTOMIZED.cust_parser import Parser
from DATABASE.cruder import CRUDer
from WEB_SERVER.services import service as svc
from WEB_SERVER.routers.settings import get_cruder
import pandas as pd

router = APIRouter(prefix="", tags=["root"])


# 루트 엔드포인트
@router.get("/", summary="서버 상태 확인", description="NOVAS EZ FastAPI 서버의 기본 엔드포인트입니다.")
async def root() -> dict[str, str]:
    """서버 환영 메시지를 반환합니다."""
    return {"message": "NOVAS EZ FastAPI 서버에 오신 걸 환영합니다!"}


@router.get("/health", summary="헬스 체크", description="서버와 데이터베이스 연결 상태를 확인합니다.")
async def health_check(cruder: CRUDer = Depends(get_cruder)) -> dict[str, str]:
    """서버 및 데이터베이스 상태를 확인합니다."""
    db_status: bool = await cruder.is_db_connected()
    str_db_status: str = "connected" if db_status else "disconnected"
    return {"status": "healthy", "service": "NOVAS EZ API", "database": str_db_status}


@router.post("/upsert/instrument", summary="ICT 장비 정보 등록/수정", description="ICT 장비(인스트루먼트) 정보를 등록하거나 수정합니다.")
async def upsert_instrument(
    body: dict = Body(..., description="인스트루먼트 정보", example={
        "name": "ICT장비 이름",
        "host": "192.168.1.100",
        "user": "user",
        "port": 22,
        "dir_base_source": "D:/Report",
        "dir_base_destination": "D:/ICT_DOWNLOAD",
        "ssh_key_path": "/path/to/ssh/cilent/key/which/is/in/this/computer",
        "network_name": "network",
        "network_password": "password",
        "accessible": True
    }),
    cruder: CRUDer = Depends(get_cruder)
) -> dict[str, str]:
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
    
    await svc.upsert_instrument(cruder, pd.DataFrame([temp_dict]))
    return {"status": "success"}

