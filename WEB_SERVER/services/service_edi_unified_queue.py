from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Literal

from WEB_SERVER.auth.redis_session import session_manager


EDI_UNIFIED_JOB_QUEUE_KEY = "edi_unified_jobs"
EDI_UNIFIED_JOB_STATUS_PREFIX = "edi_unified_job:"


def _job_status_key(job_id: str) -> str:
    return f"{EDI_UNIFIED_JOB_STATUS_PREFIX}{job_id}"


def enqueue_edi_unified_job(
    tenant_schema: str,
    requested_by: int | None = None,
    sources: List[Literal["SILLA", "LOTTE"]] | None = None,
    max_rows: int | None = None,
    fill_receipt: bool = True,
    fill_passport: bool = True,
) -> Dict[str, Any]:
    """
    EDI_UNIFIED 동기화/매핑 작업을 Redis 큐에 등록한다.

    - tenant_schema: 대상 테넌트 스키마
    - requested_by: 요청자 user.id (없으면 None)
    - sources: ["SILLA","LOTTE"] 중 선택 (None이면 둘 다)
    - max_rows: None이면 무제한, 정수면 제한
    - fill_receipt: uuid_receipt 채우기 수행 여부
    - fill_passport: uuid_passport 채우기 수행 여부
    """
    job_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    src = sources or ["SILLA", "LOTTE"]

    job: Dict[str, Any] = {
        "job_id": job_id,
        "tenant_schema": tenant_schema,
        "requested_by": requested_by,
        "sources": src,
        "max_rows": max_rows,
        "fill_receipt": bool(fill_receipt),
        "fill_passport": bool(fill_passport),
        "created_at": created_at,
    }

    # 상태 저장(초기)
    status: Dict[str, Any] = {
        "job_id": job_id,
        "status": "queued",
        "tenant_schema": tenant_schema,
        "sources": json.dumps(src),
        "max_rows": "" if max_rows is None else str(max_rows),
        "fill_receipt": str(bool(fill_receipt)),
        "fill_passport": str(bool(fill_passport)),
        "created_at": created_at,
        "started_at": "",
        "finished_at": "",
        "error": "",
    }
    session_manager.redis_client.hset(_job_status_key(job_id), mapping=status)

    # 큐 등록
    session_manager.redis_client.lpush(EDI_UNIFIED_JOB_QUEUE_KEY, json.dumps(job))
    return job


def get_edi_unified_job_status(job_id: str) -> Dict[str, Any] | None:
    data = session_manager.redis_client.hgetall(_job_status_key(job_id))
    return data or None

