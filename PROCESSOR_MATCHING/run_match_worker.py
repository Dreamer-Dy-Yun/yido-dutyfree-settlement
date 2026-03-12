import asyncio
import json
import os
from typing import Any, Dict

import httpx

from CUSTOMIZED.cust_logger import logger
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.services.service_match_queue import MATCH_JOB_QUEUE_KEY


async def _process_job(job: Dict[str, Any]) -> None:
    tenant_schema = job.get("tenant_schema")
    requested_by = job.get("requested_by")
    try_fallback = bool(job.get("try_fallback", True))

    if not tenant_schema:
        logger.warning(f"[MATCH_WORKER] invalid job, missing tenant_schema: {job}")
        return

    base_url = os.getenv("WEB_API_BASE_URL", "http://host.docker.internal:10000")
    internal_path = os.getenv("MATCH_INTERNAL_PATH", "/api/tenant/internal/match/run")
    url = f"{base_url.rstrip('/')}{internal_path}"

    logger.info(
        f"[MATCH_WORKER] start job via API for tenant_schema={tenant_schema}, "
        f"requested_by={requested_by}, try_fallback={try_fallback}, url={url}"
    )

    payload: Dict[str, Any] = {
        "tenant_schema": tenant_schema,
        "requested_by": requested_by,
        "try_fallback": try_fallback,
        "matcher_key": job.get("matcher_key", "lotte"),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)

    if response.status_code >= 400:
        logger.error(
            f"[MATCH_WORKER] API call failed for tenant_schema={tenant_schema}, "
            f"status={response.status_code}, body={response.text}"
        )
        response.raise_for_status()

    logger.info(f"[MATCH_WORKER] finished job for tenant_schema={tenant_schema}")


async def run_worker() -> None:
    redis_client = session_manager.redis_client

    logger.info("[MATCH_WORKER] started, waiting for jobs...")

    while True:
        # BRPOP 으로 블록 대기; (queue, timeout)
        result = redis_client.brpop(MATCH_JOB_QUEUE_KEY, timeout=5)
        if not result:
            await asyncio.sleep(1.0)
            continue

        _queue_name, payload = result
        try:
            job = json.loads(payload)
        except Exception as e:
            logger.error(f"[MATCH_WORKER] failed to decode job payload={payload!r}: {e}")
            continue

        try:
            await _process_job(job)
        except Exception as e:
            logger.exception(f"[MATCH_WORKER] job failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("[MATCH_WORKER] stopped by KeyboardInterrupt")

import asyncio
import json
import os
from typing import Any, Dict

import httpx

from CUSTOMIZED.cust_logger import logger
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.services.service_match_queue import MATCH_JOB_QUEUE_KEY


async def _process_job(job: Dict[str, Any]) -> None:
    tenant_schema = job.get("tenant_schema")
    requested_by = job.get("requested_by")
    try_fallback = bool(job.get("try_fallback", True))

    if not tenant_schema:
        logger.warning(f"[MATCH_WORKER] invalid job, missing tenant_schema: {job}")
        return

    base_url = os.getenv("WEB_API_BASE_URL", "http://host.docker.internal:8000")
    internal_path = os.getenv("MATCH_INTERNAL_PATH", "/api/tenant/internal/match/run")
    url = f"{base_url.rstrip('/')}{internal_path}"

    logger.info(
        f"[MATCH_WORKER] start job via API for tenant_schema={tenant_schema}, "
        f"requested_by={requested_by}, try_fallback={try_fallback}, url={url}"
    )

    payload: Dict[str, Any] = {
        "tenant_schema": tenant_schema,
        "requested_by": requested_by,
        "try_fallback": try_fallback,
        "matcher_key": job.get("matcher_key", "lotte"),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)

    if response.status_code >= 400:
        logger.error(
            f"[MATCH_WORKER] API call failed for tenant_schema={tenant_schema}, "
            f"status={response.status_code}, body={response.text}"
        )
        response.raise_for_status()

    logger.info(f"[MATCH_WORKER] finished job for tenant_schema={tenant_schema}")


async def run_worker() -> None:
    redis_client = session_manager.redis_client

    logger.info("[MATCH_WORKER] started, waiting for jobs...")

    while True:
        # BRPOP 으로 블록 대기; (queue, timeout)
        result = redis_client.brpop(MATCH_JOB_QUEUE_KEY, timeout=5)
        if not result:
            await asyncio.sleep(1.0)
            continue

        _queue_name, payload = result
        try:
            job = json.loads(payload)
        except Exception as e:
            logger.error(f"[MATCH_WORKER] failed to decode job payload={payload!r}: {e}")
            continue

        try:
            await _process_job(job)
        except Exception as e:
            logger.exception(f"[MATCH_WORKER] job failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("[MATCH_WORKER] stopped by KeyboardInterrupt")

