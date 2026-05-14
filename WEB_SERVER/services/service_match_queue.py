from datetime import datetime, timezone
import json
from typing import Any, Dict

from WEB_SERVER.auth.redis_session import session_manager


MATCH_JOB_QUEUE_KEY = "match_jobs"


def enqueue_match_job(
    tenant_schema: str,
    requested_by: int | None = None,
    try_fallback: bool = True,
) -> Dict[str, Any]:
    """
    매칭 작업을 Redis 큐에 등록한다.

    - tenant_schema: 대상 테넌트 스키마
    - requested_by: 요청자 user.id (없으면 None)
    - try_fallback: 매처의 fallback 매칭 수행 여부
    """
    job: Dict[str, Any] = {
        "tenant_schema": tenant_schema,
        "requested_by": requested_by,
        "try_fallback": bool(try_fallback),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # LPUSH 로 큐에 job JSON 등록 (간단한 FIFO 큐)
    session_manager.redis_client.lpush(MATCH_JOB_QUEUE_KEY, json.dumps(job))
    return job

