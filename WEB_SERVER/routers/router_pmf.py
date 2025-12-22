from fastapi import APIRouter, Query, Depends
from typing import Any
from DATABASE.cruder import CRUDer
import CUSTOMIZED.cust_parser as cp
from WEB_SERVER.routers.settings import get_cruder
from WEB_SERVER.routers.settings import svc
from WEB_SERVER.routers.settings import DIR_BASE
from WEB_SERVER.routers.settings import as_gzip_response
from WEB_SERVER.routers.settings import handle_http_error 
import pandas as pd
from WEB_SERVER.routers.settings import Export
from datetime import datetime


router = APIRouter(prefix="/api/pmf", tags=["pmf"])

# 통계 데이터 조회
@router.get("/get/daily_yield", summary="일별 수율 데이터 조회", description="일별 수율 데이터를 조회합니다.")
@handle_http_error
async def get_daily_yield(
        measured_by: str | None = Query(None, description="ICT 장비명", example="MI_01"),
        model_name: str | None = Query(None, description="모델명", example="DB92-05606E"),
        date_from: str | None = Query(None, description="시작일자", example="2025-01-01"),
        date_to: str | None = Query(None, description="종료일자", example="2025-11-30"),
        latest_only: bool = Query(False, description="최신 데이터만 필터링", example=False),
        cruder: CRUDer = Depends(get_cruder)
    ):
    result_data : pd.DataFrame = await svc.get_daily_yield(
        cruder, 
        cp.Parser.to_string(model_name, ignore_error=False), 
        cp.Parser.to_date(date_from, ignore_error=False), 
        cp.Parser.to_date(date_to, ignore_error=False), 
        cp.Parser.to_string(measured_by, ignore_error=False),
        cp.Parser.to_boolean(latest_only, ignore_error=False)
        )

    df_info = pd.DataFrame({
        "장비명": [measured_by if measured_by else "전체"],
        "모델명": [model_name if model_name else "전체"],
        "시작일자": [date_from if date_from else "시작일 없음"],
        "종료일자": [date_to if date_to else "종료일 없음"],
        "보고일자": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    }).T
    df_info.reset_index(inplace=True)
    df_info.columns = ["항목", "값"]

    result = {"info": df_info, "일별 수율 데이터": result_data}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return await Export.as_excel(result, f"Daily_Yield_{measured_by}_{model_name}_{timestamp}")


# 통계 데이터 조회
@router.get("/get/statistics", summary="통계 데이터 조회", description="스펙 정보와 측정 데이터의 통계(중앙값, 평균값, 분산)를 조회합니다.")
@handle_http_error
async def get_statistics(
        model_name: str = Query(..., description="모델명", example="DB92-05606E"),
        date_from: str = Query(..., description="시작일자", example="2025-01-01"),
        date_to: str = Query(..., description="종료일자", example="2025-11-30"),
        measured_by: str | None = Query(None, description="ICT 장비명", example="MI_01"),
        cruder: CRUDer = Depends(get_cruder)
    ):
    result_data : pd.DataFrame = await svc.get_statistics(
        cruder, 
        DIR_BASE, 
        model_name, 
        cp.Parser.to_date(date_from, ignore_error=False), 
        cp.Parser.to_date(date_to, ignore_error=False), 
        cp.Parser.to_string(measured_by, ignore_error=False), 
        )

    df_info = pd.DataFrame({
        "장비명": [measured_by if measured_by else "전체"],
        "모델명": [model_name],
        "시작일자": [date_from],
        "종료일자": [date_to],
        "보고일자": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    }).T
    df_info.reset_index(inplace=True)
    df_info.columns = ["항목", "값"]

    result = {"info": df_info, "statistics": result_data}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return await Export.as_excel(result, f"{model_name}_{timestamp}")


# PMF 데이터 조회 (기본 바이올린 데이터)
@router.get("/get/pmf_data", summary="PMF 데이터 조회", description="두 개의 데이터셋을 비교하는 PMF(Probability Mass Function) 차트 데이터를 조회합니다.")
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
    result_data : list[dict[str, Any]] = await svc.get_dual_pmf_chart_data(
        cruder, 
        DIR_BASE, 
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


@router.get("/get/single_item_trend", summary="단일 항목 트렌드 조회", description="특정 시리얼번호의 단일 항목 트렌드 데이터를 조회합니다.")
@handle_http_error
async def get_single_item_trend(
    measured_by: str | None = Query(None, description="ICT 장비명", example="1호기"),
    model_name: str | None = Query(None, description="모델명", example="DB92-05606E"),
    serial_no: str | None = Query(None, description="시리얼번호", example="06DB9205606EDVNAY9A0003"),
    resolution: int = Query(400, ge=10, le=400, description="해상도", example=400),
    cruder: CRUDer = Depends(get_cruder)
    ):
    result_data = await svc.get_single_item_trend(
        cruder, 
        DIR_BASE, 
        cp.Parser.to_string(measured_by, ignore_error=False), 
        cp.Parser.to_string(model_name, ignore_error=False), 
        cp.Parser.to_string(serial_no, ignore_error=False), 
        resolution
        )
    return as_gzip_response(result_data)


@router.get("/get/instruments", summary="ICT 장비 목록 조회", description="등록된 모든 ICT 장비명 목록을 반환합니다.")
@handle_http_error
async def get_instrument_names(cruder: CRUDer = Depends(get_cruder)):
    result_data = await svc.get_instrument_names(cruder)
    return as_gzip_response(result_data)



@router.get("/get/models", summary="모델 목록 조회", description="등록된 모든 모델명 목록을 반환합니다.")
@handle_http_error
async def get_model_names(cruder: CRUDer = Depends(get_cruder)):
    result_data = await svc.get_model_names(cruder)
    return as_gzip_response(result_data)


@router.get("/get/time_series", summary="시계열 데이터 조회", description="특정 모델의 인덱스별 시계열 데이터를 조회합니다.")
@handle_http_error
async def get_time_series_data(
    model_name: str = Query(..., description="모델명", example="DB92-05606E"),
    inspection_idx: int = Query(..., description="대상 인덱스", example=1),
    date_from: str = Query(..., description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str = Query(..., description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    measured_by: str | None = Query(None, description="ICT 장비명", example="1호기"),
    cruder: CRUDer = Depends(get_cruder)):
    result_data = await svc.get_time_series_data(
        cruder, 
        model_name, 
        inspection_idx, 
        cp.Parser.to_date(date_from, ignore_error=False), 
        cp.Parser.to_date(date_to, ignore_error=False), 
        cp.Parser.to_string(measured_by, ignore_error=False)
        )
    return as_gzip_response(result_data)

