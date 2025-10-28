
from fastapi import FastAPI, HTTPException
from fastapi import Depends 
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import gzip
from fastapi.responses import Response
from DATABASE.cruder import CRUDer
from DATABASE.pg_manager import PGDBManager
from DATABASE.config import db_manager

from pathlib import Path
import funcs_for_api as ffa
import orjson
import CUSTOMIZED.cust_parser as cp
import asyncio
from GOOGLE_DRIVE.data_retriever_defect import sync_external_defect_data



# FastAPI 앱 생성
app = FastAPI(
    title="NOVAS EZ API",
    description="NOVAS EZ 프로젝트 FastAPI 예제",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # React 앱 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.sessions = {}
# 하기 패스들은 임시 패스. 나중에 변경해야..
PARENT_PATH_SPEC = Path("C:/Users/user/Novas_Ez")
PARENT_PATH_MEASURED = Path("C:/Users/user/Novas_Ez")


def get_db_manager() -> PGDBManager:
    return db_manager

def get_cruder(db_mgr: PGDBManager = Depends(get_db_manager)) -> CRUDer:
    return CRUDer(db_mgr)


# PMF 데이터 조회 (기본 바이올린 데이터)
@app.get("/api/pmf")
async def get_pmf_data(
        model_name: str, 
        left_date_from: str, 
        left_date_to: str, 
        left_measured_by: str | None = None, 
        right_measured_by: str | None = None, 
        right_date_from: str | None = None, 
        right_date_to: str | None = None, 
        resolution: int = 200, 
        cruder: CRUDer = Depends(get_cruder)
    ):
    try:
        result_data : list[dict[str, any]] = await ffa.get_dual_pmf_chart_data(
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

        json_bytes = orjson.dumps(result_data)

        # 압축 (1-9. 1 : 속도↑, 압축률↓. 9 : 속도↓, 압축률↑.)
        # 데이터 전송 속도 최적화를 위해 고압축률 선택
        compressed = gzip.compress(json_bytes, compresslevel=9)  
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    # TODO : 전용 예외 클래스 설계
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/single_item_trend")
async def get_single_item_trend(
    measured_by: str | None = None,
    model_name: str | None = None, 
    serial_no: str | None = None, 
    resolution: int = 400, 
    cruder: CRUDer = Depends(get_cruder)
    ):
    try:
        result_data = await ffa.get_single_item_trend(
            cruder, 
            PARENT_PATH_SPEC, 
            cp.Parser.to_string(measured_by, ignore_error=False), 
            cp.Parser.to_string(model_name, ignore_error=False), 
            cp.Parser.to_string(serial_no, ignore_error=False), 
            resolution
            )
        # GZIP 압축 추가
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
            
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    # TODO : 전용 예외 클래스 설계
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/instruments")
async def get_instrument_names(cruder: CRUDer = Depends(get_cruder)):
    try:
        result_data = await ffa.get_instrument_names(cruder)
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    # TODO : 전용 예외 클래스 설계
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/models")
async def get_model_names(cruder: CRUDer = Depends(get_cruder)):
    try:
        result_data = await ffa.get_model_names(cruder)
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    # TODO : 전용 예외 클래스 설계
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/time_series")
async def get_time_series_data(
    model_name: str, 
    inspection_idx: int, 
    date_from: str, 
    date_to: str, 
    measured_by: str | None = None, 
    cruder: CRUDer = Depends(get_cruder)):

    try:
        print(f"model_name: {model_name}, inspection_idx: {inspection_idx}, date_from: {date_from}, date_to: {date_to}, measured_by: {measured_by}")
        result_data = await ffa.get_time_series_data(
            cruder, 
            model_name, 
            inspection_idx, 
            cp.Parser.to_date(date_from, ignore_error=False), 
            cp.Parser.to_date(date_to, ignore_error=False), 
            cp.Parser.to_string(measured_by, ignore_error=False)
            )
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    # TODO : 전용 예외 클래스 설계
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 루트 엔드포인트
@app.post("/api/defect")
async def sync_defect_data():
    try:
        msg : str = ""
        result_data = await sync_external_defect_data("시장불량")
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 업서트 만들어야..

@app.post("/api/normalize_and_upsert_all_models")
async def normalize_and_upsert_all_models(cruder: CRUDer = Depends(get_cruder)):
    try:
        result_data = await ffa.normalize_and_upsert_all_models(cruder, PARENT_PATH_SPEC)
        json_bytes = orjson.dumps(result_data)
        compressed = gzip.compress(json_bytes, compresslevel=9)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "NOVAS EZ FastAPI 서버에 오신 걸 환영합니다!"}


# 서버 실행 함수
if __name__ == "__main__":
    asyncio.run(db_manager.create_tables())
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )