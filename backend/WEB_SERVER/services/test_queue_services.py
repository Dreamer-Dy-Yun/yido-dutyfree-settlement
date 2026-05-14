import json

from WEB_SERVER.services import service_edi_unified_queue, service_match_queue


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.lpushes = []

    def hset(self, key, mapping):
        self.hashes[key] = dict(mapping)

    def hgetall(self, key):
        return self.hashes.get(key, {})

    def lpush(self, key, value):
        self.lpushes.append((key, value))


def test_enqueue_match_job_publishes_expected_payload(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(service_match_queue.session_manager, "redis_client", fake_redis)

    job = service_match_queue.enqueue_match_job(
        tenant_schema="tenant_alpha",
        requested_by=17,
        try_fallback=0,
    )

    assert job["tenant_schema"] == "tenant_alpha"
    assert job["requested_by"] == 17
    assert job["try_fallback"] is False
    assert len(fake_redis.lpushes) == 1

    queue_key, raw_payload = fake_redis.lpushes[0]
    assert queue_key == service_match_queue.MATCH_JOB_QUEUE_KEY
    assert json.loads(raw_payload) == job


def test_enqueue_edi_unified_job_stores_status_and_payload(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(service_edi_unified_queue.session_manager, "redis_client", fake_redis)

    class FixedUuid:
        hex = "fixedjobid"

    monkeypatch.setattr(service_edi_unified_queue.uuid, "uuid4", lambda: FixedUuid())

    job = service_edi_unified_queue.enqueue_edi_unified_job(
        tenant_schema="tenant_beta",
        requested_by=9,
        sources=["SILLA"],
        max_rows=25,
        fill_receipt=False,
        fill_passport=True,
    )

    assert job == {
        "job_id": "fixedjobid",
        "tenant_schema": "tenant_beta",
        "requested_by": 9,
        "sources": ["SILLA"],
        "max_rows": 25,
        "fill_receipt": False,
        "fill_passport": True,
        "created_at": job["created_at"],
    }

    status_key = service_edi_unified_queue._job_status_key("fixedjobid")
    assert fake_redis.hashes[status_key] == {
        "job_id": "fixedjobid",
        "status": "queued",
        "tenant_schema": "tenant_beta",
        "sources": json.dumps(["SILLA"]),
        "max_rows": "25",
        "fill_receipt": "False",
        "fill_passport": "True",
        "created_at": job["created_at"],
        "started_at": "",
        "finished_at": "",
        "error": "",
    }

    assert fake_redis.lpushes == [
        (service_edi_unified_queue.EDI_UNIFIED_JOB_QUEUE_KEY, json.dumps(job))
    ]


def test_get_edi_unified_job_status_returns_none_for_missing_job(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(service_edi_unified_queue.session_manager, "redis_client", fake_redis)

    assert service_edi_unified_queue.get_edi_unified_job_status("missing") is None
