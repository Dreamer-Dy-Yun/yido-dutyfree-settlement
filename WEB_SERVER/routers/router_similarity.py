from fastapi import APIRouter, Query, Depends, Body
from fastapi.responses import RedirectResponse
from DATABASE.cruder import CRUDer
from WEB_SERVER.routers.settings import get_cruder
from WEB_SERVER.routers.settings import get_db_manager
from WEB_SERVER.routers.settings import PARENT_PATH_SPEC
from WEB_SERVER.routers.settings import PARENT_PATH_MEASURED
from WEB_SERVER.routers.settings import ffa
from WEB_SERVER.routers.settings import as_gzip_response
from WEB_SERVER.routers.settings import handle_http_error
from WEB_SERVER.routers.settings import Export
from GOOGLE_DRIVE.data_retriever_defect import sync_external_defect_data
import CUSTOMIZED.cust_parser as cp
from datetime import datetime
from async_lru import alru_cache

router = APIRouter(prefix="/api/similarity", tags=["similarity"])

# 루트 엔드포인트
@router.post("/set/defect")
@handle_http_error
async def sync_defect_data(
    body: dict = Body(..., description="요청 본문", example={"name": "시장불량"}),
    cruder: CRUDer = Depends(get_cruder),
):
    name = body.get("name", "시장불량")
    result_data = await sync_external_defect_data(cruder, name)
    return as_gzip_response(result_data)


@router.get("/get/url/google_spreadsheet/defects", response_description="Google 스프레드시트 URL")
@handle_http_error
async def get_defects_url_by_name(
    name: str = Query("시장불량", description="Google Service Account 이름", example="시장불량"),
    cruder: CRUDer = Depends(get_cruder),
) -> str:
    return await ffa.get_google_spreadsheet_url_by_name(cruder, name)


@router.post("/set/normalize_and_upsert_all_models")
@handle_http_error
async def normalize_and_upsert_all_models(cruder: CRUDer = Depends(get_cruder)):
    result_data = await ffa.normalize_and_upsert_all_models(cruder, PARENT_PATH_SPEC)
    return as_gzip_response(result_data)

@alru_cache(maxsize=1000)
@router.get("/get/trends")
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
        serial_no = (await cruder.get_latest_measured_datum())["serial_no"]

    result_data = await ffa.get_serial_similarity_hits_from_defects(
        cruder,
        instrument_name,
        serial_no,
        cp.Parser.to_float(top_n_rate, ignore_error=False),
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False),
        metric
    )   
    return as_gzip_response(result_data, numpy_serialize=True)
    

@router.get("/download/xlsx/defects_similars")
@handle_http_error
async def download_defects_similars_xlsx(
    date_from: str = Query(..., description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str = Query(..., description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    top_n_rate: float = Query(0.1, ge=0.0, le=1.0, description="상위 비율(0~1)", example=0.2),
    cruder: CRUDer = Depends(get_cruder),
):
    sheet_name = date_from + " ~ " + date_to
    result_data = await ffa.get_similars_to_defects(
        cruder,
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False),
        cp.Parser.to_float(top_n_rate, ignore_error=False)
    )

    result = {sheet_name: result_data}

    return await Export.as_excel(result, datetime.now().strftime("%Y%m%d_%H%M%S"))
    