from fastapi import APIRouter, Query, Depends
from typing import Any
from DATABASE.cruder import CRUDer
from pathlib import Path
import CUSTOMIZED.cust_parser as cp
from WEB_SERVER.routers.settings import get_cruder
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.settings import ffa
from WEB_SERVER.routers.settings import PARENT_PATH_SPEC
from WEB_SERVER.routers.settings import PARENT_PATH_MEASURED
from WEB_SERVER.routers.settings import as_gzip_response
from WEB_SERVER.routers.settings import handle_http_error


router = APIRouter(prefix="", tags=["pmf"])


# PMF 데이터 조회 (기본 바이올린 데이터)
@router.get("/api/pmf")
@handle_http_error
async def get_pmf_data(
        model_name: str = Query(..., description="모델명", example="DB92-05606E"),
        left_date_from: str = Query(..., description="시작일자 (왼쪽)", example="2025-01-01"),
        left_date_to: str = Query(..., description="종료일자 (왼쪽)", example="2025-10-31"),
        left_measured_by: str | None = Query(None, description="ICT 장비명(왼쪽)", example="1호기"),
        right_date_from: str | None = Query(None, description="시작일자 (오른쪽)", example="2025-01-01"),
        right_date_to: str | None = Query(None, description="종료일자 (오른쪽)", example="2025-10-31"),
        right_measured_by: str | None = Query(None, description="ICT 장비명(오른쪽)", example="2호기"),
        resolution: int = Query(200, ge=10, le=400, description="해상도", example=200),
        cruder: CRUDer = Depends(get_cruder)
    ):
    result_data : list[dict[str, Any]] = await ffa.get_dual_pmf_chart_data(
        cruder, 
        PARENT_PATH_SPEC, 
        model_name, 
        cp.Parser.to_date(left_date_from, ignore_error=False), 
        cp.Parser.to_date(left_date_to, ignore_error=False), 
        cp.Parser.to_string(left_measured_by, ignore_error=False), 
        cp.Parser.to_date(right_date_from, ignore_error=False), 
        cp.Parser.to_date(right_date_to, ignore_error=False), 
        cp.Parser.to_string(right_measured_by, ignore_error=False), 
        cp.Parser.to_integer(resolution, ignore_error=False)
        )
    return as_gzip_response(result_data)


@router.get("/api/single_item_trend")
@handle_http_error
async def get_single_item_trend(
    measured_by: str | None = Query(None, description="ICT 장비명", example="1호기"),
    model_name: str | None = Query(None, description="모델명", example="DB92-05606E"),
    serial_no: str | None = Query(None, description="시리얼번호", example="06DB9205606EDVNAY9A0003"),
    resolution: int = Query(400, ge=10, le=400, description="해상도", example=400),
    cruder: CRUDer = Depends(get_cruder)
    ):
    result_data = await ffa.get_single_item_trend(
        cruder, 
        PARENT_PATH_SPEC, 
        cp.Parser.to_string(measured_by, ignore_error=False), 
        cp.Parser.to_string(model_name, ignore_error=False), 
        cp.Parser.to_string(serial_no, ignore_error=False), 
        resolution
        )
    return as_gzip_response(result_data)


@router.get("/api/instruments")
@handle_http_error
async def get_instrument_names(cruder: CRUDer = Depends(get_cruder)):
    result_data = await ffa.get_instrument_names(cruder)
    return as_gzip_response(result_data)



@router.get("/api/models")
@handle_http_error
async def get_model_names(cruder: CRUDer = Depends(get_cruder)):
    result_data = await ffa.get_model_names(cruder)
    return as_gzip_response(result_data)


@router.get("/api/time_series")
@handle_http_error
async def get_time_series_data(
    model_name: str = Query(..., description="모델명", example="DB92-05606E"),
    inspection_idx: int = Query(..., description="대상 인덱스", example=1),
    date_from: str = Query(..., description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str = Query(..., description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    measured_by: str | None = Query(None, description="ICT 장비명", example="1호기"),
    cruder: CRUDer = Depends(get_cruder)):
    result_data = await ffa.get_time_series_data(
        cruder, 
        model_name, 
        inspection_idx, 
        cp.Parser.to_date(date_from, ignore_error=False), 
        cp.Parser.to_date(date_to, ignore_error=False), 
        cp.Parser.to_string(measured_by, ignore_error=False)
        )
    return as_gzip_response(result_data)

