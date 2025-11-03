

# 시리얼 넘버 확보
# 시리얼 넘버로 normalized 테이블에서 벡터 데이터 조회(measured와 measured_id로 조인 필요)
# 조회된 벡터 데이터를 이용하여, Normalized 테이블에서 유사도 조회.
# 유사도 결과 반환 (최종적으로, 유사도 히팅 된 데이터의 시리얼 넘버 및 유사도 순위 반환)
# 반환된 유사도를 퍼센테이지 변경 (0.000 ~ 100.000)



from DATABASE.cruder import CRUDer
from DATABASE import config
from datetime import date
import asyncio
from typing import Any
import pandas as pd
from CUSTOMIZED.cust_web_helper import export_as_excel

cruder = CRUDer(config.db_manager)

# download_xl_defects

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
        instrument_name = xrow.instrument_name    
        model_name = xrow.model_name
        serial_no = xrow.serial_no
        num_of_records = dict_model_n_num_of_records[model_name]
        records = await cruder.get_relative_similarities(model_name, serial_no, num_of_records, top_n_rate, date_from, date_to, metric, except_itself, False)

        for xvalue in records.values():
            xvalue["similarity"] = round((1 - xvalue["rank"] / num_of_records) * 100, 5)
        list_data.extend(records.values())

    return pd.DataFrame(list_data)


async def get_similars_to_defects(cruder: CRUDer, date_from: date, date_to: date) -> pd.DataFrame:

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
        top_n_rate=0.1,
        date_from=date_from,
        date_to=date_to,
        metric="cosine",
        except_itself=True
    )
    
    df.sort_values(by="measured_at", ascending=False, inplace=True)

    return df







if __name__ == "__main__":

    defective_serials = ["06DB9205606EDVNAY990193", "06DB9205606EDVNAY990999", "06DB9205606EDVNAY990076","06DB9205606EDVNAY990122", "06DB9205606EDVNAY990172"]

    df_defective = asyncio.run(get_similars_to_defects(cruder, date_from=date(2025, 1, 1), date_to=date(2025, 10, 31)))





