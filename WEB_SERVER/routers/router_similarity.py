###########################################
# Module name : router_similarity.py
# Module functions : sync_defect_data, 
#                   get_defects_url_by_name, 
#                   normalize_and_upsert_all_models, 
#                   get_serial_similarity_hits_from_defects, 
#                   download_defects_similars_xlsx
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.??.??
# Updated at : 2025.12.03
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
############################################

from fastapi import APIRouter, Query, Depends, Body
from DATABASE.cruder import CRUDer
from WEB_SERVER.routers.settings import get_cruder
from WEB_SERVER.routers.settings import DIR_BASE
from WEB_SERVER.routers.settings import svc
from WEB_SERVER.routers.settings import as_gzip_response
from WEB_SERVER.routers.settings import handle_http_error
from WEB_SERVER.routers.settings import Export
from GOOGLE_DRIVE.data_retriever_defect import sync_external_defect_data
import CUSTOMIZED.cust_parser as cp
from datetime import datetime
from async_lru import alru_cache

router = APIRouter(prefix="/api/similarity", tags=["similarity"])

# 루트 엔드포인트
@router.post("/set/defect", summary="불량 데이터 동기화", description="Google 스프레드시트에서 외부 불량 데이터를 동기화합니다.")
@handle_http_error
async def sync_defect_data(
    body: dict = Body(..., description="요청 본문", example={"name": "시장불량"}),
    cruder: CRUDer = Depends(get_cruder),
):
    name = body.get("name", "시장불량")
    result_data = await sync_external_defect_data(cruder, name)
    return as_gzip_response(result_data)


@router.get("/get/url/google_spreadsheet/defects", summary="Google 스프레드시트 URL 조회", description="불량 데이터가 저장된 Google 스프레드시트의 URL을 조회합니다.", response_description="Google 스프레드시트 URL")
@handle_http_error
async def get_defects_url_by_name(
    name: str = Query("시장불량", description="Google Service Account 이름", example="시장불량"),
    cruder: CRUDer = Depends(get_cruder),
) -> str:
    return await svc.get_google_spreadsheet_url_by_name(cruder, name)


@router.post("/set/normalize_and_upsert_all_models", summary="모델 정규화 및 벡터 업서트", description="모든 모델의 측정 데이터를 정규화하고 벡터 데이터로 변환하여 저장합니다.")
@handle_http_error
async def normalize_and_upsert_all_models(cruder: CRUDer = Depends(get_cruder)):
    result_data = await svc.normalize_and_upsert_all_models(cruder, DIR_BASE)
    return as_gzip_response(result_data)


@router.get("/get/trends", summary="불량 유사도 트렌드 조회", description="불량 데이터와 유사한 시리얼의 트렌드 데이터를 조회합니다.")
@handle_http_error
async def get_serial_similarity_hits_from_defects(
    instrument_name: str | None = Query(None, description="ICT 기기명", example="1호기"),
    serial_no: str | None = Query(None, description="기준 시리얼", example="06DB9205606EDVNAY9A0003"),
    top_n_rate: float = Query(0.01, ge=0.0, le=1.0, description="상위 비율(0~1)", example=0.2),
    date_from: str | None = Query(None, description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str | None = Query(None, description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    metric: str = Query("cosine", description="유사도 지표", example="cosine"),
    cruder: CRUDer = Depends(get_cruder),
):

    if not cp.Parser.to_string(serial_no):
        latest_datum = await cruder.get_latest_measured_datum()
        if latest_datum is None:
            raise ValueError("측정 데이터가 없습니다. serial_no를 명시적으로 제공해주세요.")
        serial_no = latest_datum["serial_no"]

    await svc.normalize_and_upsert_all_models(cruder, DIR_BASE)

    result_data = await svc.get_serial_similarity_hits_from_defects(
        cruder,
        instrument_name,
        serial_no,
        cp.Parser.to_float(top_n_rate, ignore_error=False),
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False),
        metric
    )   
    return as_gzip_response(result_data, numpy_serialize=True)
    

@router.get("/download/xlsx/defects_similars", summary="불량 유사도 Excel 다운로드", description="불량 데이터와 유사한 시리얼 데이터를 Excel 파일로 다운로드합니다.")
@handle_http_error
async def download_defects_similars_xlsx(
    date_from: str = Query(..., description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str = Query(..., description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    top_n_rate: float = Query(0.1, ge=0.0, le=1.0, description="상위 비율(0~1)", example=0.2),
    cruder: CRUDer = Depends(get_cruder),
):
    sheet_name = date_from + " ~ " + date_to
    result_data = await svc.get_similars_to_defects(
        cruder,
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False),
        cp.Parser.to_float(top_n_rate, ignore_error=False)
    )

    result = {sheet_name: result_data}

    return await Export.as_excel(result, datetime.now().strftime("%Y%m%d_%H%M%S"))
    