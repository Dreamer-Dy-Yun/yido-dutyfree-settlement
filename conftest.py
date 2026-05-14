import os

import pytest


INTEGRATION_TEST_PATTERNS = (
    "DATABASE/tests/test_pgmanager.py",
    "DATABASE/tests/test_pgmanager_integration.py",
    "DATABASE/tests/test_pgmanager_upsert_testmodel.py",
    "DATABASE/tests/test_pgmanager_update_testmodel.py",
    "PROCESSOR_MATCHING/tests/test_matching_e2e.py",
)


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_DB_TESTS") == "1":
        return

    skip_integration = pytest.mark.skip(
        reason="requires RUN_DB_TESTS=1 and a local PostgreSQL/Redis/schema environment"
    )
    for item in items:
        test_path = str(item.path).replace("\\", "/")
        if any(pattern in test_path for pattern in INTEGRATION_TEST_PATTERNS):
            item.add_marker(skip_integration)
