import asyncio
import json
import os
from typing import Any, Dict

import httpx

from CUSTOMIZED.cust_logger import logger
from DATABASE.config import db_manager
from DATABASE.dbms import DBManager
from WEB_SERVER.auth.redis_session import session_manager
from WEB_SERVER.services.service_match_queue import MATCH_JOB_QUEUE_KEY


def _create_db_manager() -> DBManager:
    """Return the configured project DB manager for tests and worker helpers."""
    return db_manager


async def _process_job(job: Dict[str, Any]) -> None:
    tenant_schema = job.get("tenant_schema")
    requested_by = job.get("requested_by")
    try_fallback = bool(job.get("try_fallback", True))
    raw_matcher_key = job.get("matcher_key")

    if not tenant_schema:
        logger.warning("[MATCH_WORKER] invalid job, missing tenant_schema: %s", job)
        return

    base_url = os.getenv("WEB_API_BASE_URL", "http://host.docker.internal:10000")
    internal_path = os.getenv("MATCH_INTERNAL_PATH", "/api/tenant/internal/match/run")
    url = f"{base_url.rstrip('/')}{internal_path}"

    matcher_keys = ["LOTTE", "SILLA"] if raw_matcher_key is None else [str(raw_matcher_key).upper()]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for matcher_key in matcher_keys:
            logger.info(
                "[MATCH_WORKER] start job via API for tenant_schema=%s, requested_by=%s, "
                "try_fallback=%s, matcher_key=%s, url=%s",
                tenant_schema,
                requested_by,
                try_fallback,
                matcher_key,
                url,
            )

            payload: Dict[str, Any] = {
                "tenant_schema": tenant_schema,
                "requested_by": requested_by,
                "try_fallback": try_fallback,
                "matcher_key": matcher_key,
            }
            response = await client.post(url, json=payload)
            if response.status_code >= 400:
                logger.error(
                    "[MATCH_WORKER] API call failed for tenant_schema=%s, matcher_key=%s, "
                    "status=%s, body=%s",
                    tenant_schema,
                    matcher_key,
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            logger.info("[MATCH_WORKER] finished job for tenant_schema=%s, matcher_key=%s", tenant_schema, matcher_key)


async def run_worker() -> None:
    redis_client = session_manager.redis_client
    logger.info("[MATCH_WORKER] started, waiting for jobs...")

    while True:
        result = redis_client.brpop(MATCH_JOB_QUEUE_KEY, timeout=5)
        if not result:
            await asyncio.sleep(1.0)
            continue

        _queue_name, payload = result
        try:
            job = json.loads(payload)
        except Exception as exc:
            logger.error("[MATCH_WORKER] failed to decode job payload=%r: %s", payload, exc)
            continue

        try:
            await _process_job(job)
        except Exception as exc:
            logger.exception("[MATCH_WORKER] job failed: %s", exc)


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("[MATCH_WORKER] stopped by KeyboardInterrupt")
