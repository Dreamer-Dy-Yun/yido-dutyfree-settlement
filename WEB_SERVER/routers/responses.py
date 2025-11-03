###########################################
# Module name : responses.py
# Module functions : Response Helper Functions
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.10.31
# Note : API 응답 관련 헬퍼 함수
############################################

from fastapi import Response
from typing import Any
import orjson
import gzip


def as_gzip_response(
    data: Any, 
    numpy_serialize: bool = False,
    compresslevel: int = 9
) -> Response:
    """
    데이터를 JSON으로 직렬화하고 GZIP 압축하여 Response 객체 반환
    
    Args:
        data: 응답할 데이터
        numpy_serialize: NumPy 배열 직렬화 옵션 사용 여부
        compresslevel: GZIP 압축 레벨 (1-9, 기본값: 9)
    
    Returns:
        GZIP 압축된 Response 객체
    """
    options = orjson.OPT_SERIALIZE_NUMPY if numpy_serialize else None
    json_bytes = orjson.dumps(data, option=options)
    compressed = gzip.compress(json_bytes, compresslevel=compresslevel)
    
    return Response(
        content=compressed,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )

