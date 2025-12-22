###########################################
# Module name : service.py
# Module functions : 모든 서비스 함수를 re-export하는 stub 모듈
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.XX
# Updated at : 2025.12.XX
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
#        - IDE 인식을 위한 stub 모듈
#        - 실제 구현은 각 service_*.py 파일에 있음
#        - from WEB_SERVER.services.service import 함수명 형태로 사용 가능
############################################

# 모든 서비스 함수 import 및 re-export
from .service_spec import get_spec_parquet
from .service_yield import get_daily_yield
from .service_chart import get_statistics, get_dual_pmf_chart_data, get_single_item_trend
from .service_normalize import normalize_and_upsert_all_models, process_and_upsert_vector_data, uniformize_length
from .service_similarity import (
    get_defective_similarity_hits,
    get_serial_similarity_hits_from_defects,
    get_df_defects,
    get_similars_to_defects
)
from .service_common import (
    get_instrument_names,
    get_model_names
)
from .service_instrument import upsert_instrument
from .service_time_series import get_time_series_data
from .service_google import get_google_spreadsheet_url_by_name

__all__ = [
    # spec
    "get_spec_parquet",
    # yield
    "get_daily_yield",
    # chart
    "get_statistics",
    "get_dual_pmf_chart_data",
    "get_single_item_trend",
    # normalize
    "normalize_and_upsert_all_models",
    "process_and_upsert_vector_data",
    "uniformize_length",
    # similarity
    "get_defective_similarity_hits",
    "get_serial_similarity_hits_from_defects",
    "get_df_defects",
    "get_similars_to_defects",
    # common
    "get_instrument_names",
    "get_model_names",
    # instrument
    "upsert_instrument",
    # time_series
    "get_time_series_data",
    # google
    "get_google_spreadsheet_url_by_name",
]
