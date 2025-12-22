###########################################
# Module name : service_similarity.py
# Module functions : get_defective_similarity_hits, get_serial_similarity_hits_from_defects, get_df_defects, get_similars_to_defects
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 유사도 관련 서비스 함수
############################################

from datetime import date
from DATABASE.cruder import CRUDer
import pandas as pd
from typing import Any


async def get_defective_similarity_hits(
    cruder: CRUDer, 
    model_name: str, 
    serial_no: str, 
    defective_serials: list[str], 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine",
    except_itself: bool = False
    ) -> dict[str, dict[str, Any]]:
    """
    해당 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    유사도 결과 중 대상 시리얼 넘버(defective_serials)에 해당하는 시리얼 넘버의 유사도 결과 반환
    """
    result: dict[str, dict[str, Any]] = {}

    data_size = await cruder.get_measured_data_size(model_name=model_name)

    records = await cruder.get_relative_similarities(model_name, serial_no, data_size, top_n_rate, date_from, date_to, metric, except_itself)

    for defective_serial in defective_serials :
        if defective_serial in records:
            result[defective_serial] = records[defective_serial]
            rel_sim = result[defective_serial]["vector_visual_normed"]
            result[defective_serial]["vector_visual_normed"] = rel_sim[:len(result[defective_serial]["list_measured"])]

    if not except_itself and serial_no in records:
        result[serial_no] = records[serial_no]
        rel_sim = result[serial_no]["vector_visual_normed"]
        result[serial_no]["vector_visual_normed"] = rel_sim[:len(result[serial_no]["list_measured"])]
    
    return result


async def get_serial_similarity_hits_from_defects(
    cruder: CRUDer, 
    instrument_name: str | None = None,
    serial_no: str | None = None, 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine"
    ) -> dict[str, dict[str, Any]]:
    """
    불량 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    각 불량 모델의 시리얼 넘버(defective_serial)의 유사도 결과 반환
    """
    # TODO : 최적화 대상... 제발... 시간좀..
    result: dict[str, dict[str, Any]] = {}
    serial_info : dict[str, Any] | None = None
    model_name : str | None = None
    data_size : int | None = None    # TODO : alru_cache 대상. alru_cache 적용 시, 리프레쉬 트리거 확인 필요
    df_defective : pd.DataFrame | None = None
    df_data_sizes : pd.DataFrame | None = None
    

    def _get_data_size(model_name: str, df_data_sizes: pd.DataFrame) -> int:
        if df_data_sizes.empty:
            return 0
        filtered = df_data_sizes[df_data_sizes["model_name"] == model_name]
        return int(filtered["count"].iloc[0]) if not filtered.empty else 0


    def _add_result(serial_no: str, records: dict[str, Any], model_name: str, rank: int, df_data_sizes: pd.DataFrame) -> dict[str, Any]:
        result[serial_no] = records[serial_no]
        rel_sim = result[serial_no]["vector_visual_normed"]
        result[serial_no]["vector_visual_normed"] = rel_sim[:len(result[serial_no]["list_measured"])]
        result[serial_no]["rank"] = rank
        result[serial_no]["data_size"] = _get_data_size(model_name, df_data_sizes)
        result[serial_no]["rank_percent"] = round((rank / result[serial_no]["data_size"]) * 100, 6) if result[serial_no]["data_size"] > 0 else 0
        return result[serial_no]

    serial_info : dict[str, Any] | None = await cruder.get_latest_measured_datum(instrument_name, None, serial_no)
    if serial_info is None:
        raise ValueError(f"시리얼 번호 '{serial_no}'에 해당하는 측정 데이터를 찾을 수 없습니다.")
    model_name = serial_info["model_name"]
    df_defective = await cruder.get_external_defects_info()
    df_data_sizes = await cruder.get_measured_data_sizes(date_from=date_from, date_to=date_to)
    data_size = _get_data_size(model_name, df_data_sizes)

    # 조회 시리얼
    # 대상 시리얼만 ICT 장비명 기준 조회 (본인 혹은 해당 장비의 최신 측정치는 무조건 반환)
    single_record = await cruder.get_absolute_similarities(
        instrument_name, 
        model_name, 
        serial_no, 
        top_k=1, 
        except_itself=False, 
        anchor_serial_no=serial_no
    )
    if not single_record or serial_no not in single_record:
        raise ValueError(f"시리얼 번호 '{serial_no}'에 대한 정규화된 벡터 데이터가 없습니다. 정규화 작업을 먼저 실행해주세요.")
    result[serial_no] = _add_result(serial_no, single_record, model_name, single_record[serial_no]["rank"], df_data_sizes)
    df_defective = df_defective[df_defective["model_name"] == model_name]

    if data_size > 0:
        for xrow in df_defective.itertuples():
            defective_serial = xrow.serial_no
            records = await cruder.get_relative_similarities(None, model_name, defective_serial, data_size, top_n_rate, date_from, date_to, metric, True, False, False)
            if serial_no in records:
                single_record = await cruder.get_absolute_similarities(None, model_name, serial_no, 1, date_from, date_to, metric, True, True, True, defective_serial)
                result[defective_serial] = _add_result(defective_serial, single_record, model_name, records[serial_no]["rank"], df_data_sizes)

    return result


async def get_df_defects(
    cruder: CRUDer, 
    df_defective: pd.DataFrame, 
    top_n_rate: float = 0.01, 
    date_from: date | None = None,
    date_to: date | None = None,
    metric: str = "cosine",
    except_itself: bool = False
    ) -> pd.DataFrame:

    """
    df_defective : serial_no, model_name, instrument_name 컬럼을 가진 데이터프레임
    해당 모델(model_name)의 시리얼 넘버(serial_no)의 유사도를 조회하고, 
    유사도 결과 중 대상 시리얼 넘버(defective_serials)에 해당하는 시리얼 넘버의 유사도 결과 반환
    """
    # TODO : Pydantic의 BaseModel 사용하여 DTO 정의(리팩토링시)
    instrument_name : str | None = None
    model_name : str | None = None
    serial_no : str | None = None
    num_of_records : int | None = None

    target_models : list[str] = df_defective["model_name"].unique()
    dict_model_n_num_of_records: dict[str, int] = {}
    for model_name in target_models:
        num_of_records = await cruder.get_measured_data_size(model_name=model_name)
        dict_model_n_num_of_records[model_name] = num_of_records

    list_data : list[dict[str, Any]] = []
    for xrow in df_defective.itertuples():
        instrument_name = xrow.instrument_name    # 안 씀
        model_name = xrow.model_name
        serial_no = xrow.serial_no
        num_of_records = dict_model_n_num_of_records[model_name]
        records = await cruder.get_relative_similarities(None, model_name, serial_no, num_of_records, top_n_rate, date_from, date_to, metric, except_itself, False, False)

        for xvalue in records.values():
            xvalue["relative_similarity"] = round((1 - xvalue["rank"] / num_of_records) * 100, 5)
        list_data.extend(records.values())

    return pd.DataFrame(list_data)


async def get_similars_to_defects(cruder: CRUDer, date_from: date, date_to: date, top_n_rate : float = 0.1) -> pd.DataFrame:

    """
    불량 시리얼 넘버 조회 (DB)
    불량 시리얼 넘버와 유사한 측정치 조회 (DB)

    최적화는 안된 상태
    """
    # TODO : 여러번 조회하는데, 추후 한번으로 바꿀 것.

    df_defective = await cruder.get_external_defects_info()

    df = await get_df_defects(
        cruder, 
        df_defective=df_defective, 
        top_n_rate=top_n_rate,
        date_from=date_from,
        date_to=date_to,
        metric="cosine",
        except_itself=True
    )
    
    if df.empty :
        return pd.DataFrame({"message": ["요청 기간에 해당 데이터가 없습니다."]})
    else:
        df.sort_values(by="measured_at", ascending=False, inplace=True)
        df = df.rename(columns={'serial_query': '시장불량'})
        df = df.rename(columns={'serial_result': '유사제품'})
        df = df.rename(columns={'rank': '유사도순위'})
        df = df.rename(columns={'relative_similarity': '상대 유사도(%)'})
        df = df.rename(columns={'measured_at': '측정일시'})
        df = df.rename(columns={'distance': '유사도 거리(1-cosθ)'})

    return df
