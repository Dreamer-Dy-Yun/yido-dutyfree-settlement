import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict

import httpx

from CUSTOMIZED.cust_logger import logger
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.services.service_edi_unified_queue import (
    EDI_UNIFIED_JOB_QUEUE_KEY,
    EDI_UNIFIED_JOB_STATUS_PREFIX,
)


def _status_key(job_id: str) -> str:
    return f"{EDI_UNIFIED_JOB_STATUS_PREFIX}{job_id}"


async def _process_job(job: Dict[str, Any]) -> None:
    job_id = job.get("job_id")
    tenant_schema = job.get("tenant_schema")

    if not job_id or not tenant_schema:
        logger.warning(f"[EDI_UNIFIED_WORKER] invalid job: {job}")
        return

    # 기본값은 로컬 개발 서버(uvicorn) 기준.
    # Docker/운영 환경에서는 WEB_API_BASE_URL 로 오버라이드.
    base_url = os.getenv("WEB_API_BASE_URL", "http://localhost:10000")
    internal_path = os.getenv("EDI_UNIFIED_INTERNAL_PATH", "/api/tenant/internal/edi-unified/run")
    url = f"{base_url.rstrip('/')}{internal_path}"

    # 상태 업데이트: running
    session_manager.redis_client.hset(
        _status_key(job_id),
        mapping={"status": "running", "started_at": datetime.utcnow().isoformat()},
    )

    payload: Dict[str, Any] = {
        "tenant_schema": tenant_schema,
        "requested_by": job.get("requested_by"),
        "sources": job.get("sources", ["silla", "lotte"]),
        "max_rows": job.get("max_rows"),
        "fill_receipt": bool(job.get("fill_receipt", True)),
        "fill_passport": bool(job.get("fill_passport", True)),
    }

    logger.info(f"[EDI_UNIFIED_WORKER] start job_id={job_id} tenant_schema={tenant_schema} url={url}")

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(url, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"API failed status={resp.status_code} body={resp.text}")

        session_manager.redis_client.hset(
            _status_key(job_id),
            mapping={"status": "finished", "finished_at": datetime.utcnow().isoformat()},
        )
        logger.info(f"[EDI_UNIFIED_WORKER] finished job_id={job_id}")
    except Exception as e:
        session_manager.redis_client.hset(
            _status_key(job_id),
            mapping={
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(e),
            },
        )
        raise


async def run_worker() -> None:
    redis_client = session_manager.redis_client
    logger.info("[EDI_UNIFIED_WORKER] started, waiting for jobs...")

    while True:
        result = redis_client.brpop(EDI_UNIFIED_JOB_QUEUE_KEY, timeout=5)
        if not result:
            await asyncio.sleep(1.0)
            continue

        _queue_name, payload = result
        try:
            job = json.loads(payload)
        except Exception as e:
            logger.error(f"[EDI_UNIFIED_WORKER] failed to decode payload={payload!r}: {e}")
            continue

        try:
            await _process_job(job)
        except Exception as e:
            logger.exception(f"[EDI_UNIFIED_WORKER] job failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("[EDI_UNIFIED_WORKER] stopped by KeyboardInterrupt")

