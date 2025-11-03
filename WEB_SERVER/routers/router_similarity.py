from fastapi import APIRouter, Query, Depends
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

router = APIRouter(prefix="/api/similarity", tags=["similarity"])

# 루트 엔드포인트
@router.post("/defect")
@handle_http_error
async def sync_defect_data():
    result_data = await sync_external_defect_data("시장불량")
    return as_gzip_response(result_data)


@router.post("/normalize_and_upsert_all_models")
@handle_http_error
async def normalize_and_upsert_all_models(cruder: CRUDer = Depends(get_cruder)):
    result_data = await ffa.normalize_and_upsert_all_models(cruder, PARENT_PATH_SPEC)
    return as_gzip_response(result_data)


@router.get("/get_serial_similarity_hits_from_defects")
@handle_http_error
async def get_serial_similarity_hits_from_defects(
    model_name: str = Query(..., description="모델명", example="DB92-05606E"),
    serial_no: str = Query(..., description="기준 시리얼", example="06DB9205606EDVNAY9A0003"),
    defective_serials: list[str] = Query(..., description="불량 시리얼 목록", example=["06DB9205606EDVNAY990193", "06DB9205606EDVNAY990999", "06DB9205606EDVNAY990076"]),
    top_n_rate: float = Query(0.01, ge=0.0, le=1.0, description="상위 비율(0~1)", example=0.2),
    date_from: str | None = Query(None, description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str | None = Query(None, description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    metric: str = Query("cosine", description="유사도 지표", example="cosine"),
    cruder: CRUDer = Depends(get_cruder),
):
    result_data = await ffa.get_serial_similarity_hits_from_defects(
        cruder,
        model_name,
        serial_no,
        defective_serials,
        cp.Parser.to_float(top_n_rate, ignore_error=False),
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False),
        metric,
        False
    )   
    return as_gzip_response(result_data, numpy_serialize=True)


@router.get("/get_similars_to_defects")
@handle_http_error
async def get_similars_to_defects(
    date_from: str = Query(..., description="시작일자 YYYY-MM-DD", example="2025-01-01"),
    date_to: str = Query(..., description="종료일자 YYYY-MM-DD", example="2025-10-31"),
    cruder: CRUDer = Depends(get_cruder),
):
    result_data = await ffa.get_similars_to_defects(
        cruder,
        cp.Parser.to_date(date_from, ignore_error=False),
        cp.Parser.to_date(date_to, ignore_error=False)
    )

    return await Export.as_excel(result_data, datetime.now().strftime("%Y%m%d_%H%M%S"))
    