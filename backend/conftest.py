import os
from pathlib import Path


INTEGRATION_TEST_PATHS = {
    "DATABASE/tests/test_pgmanager.py",
    "DATABASE/tests/test_pgmanager_integration.py",
    "DATABASE/tests/test_pgmanager_upsert_testmodel.py",
    "DATABASE/tests/test_pgmanager_update_testmodel.py",
    "PROCESSOR_MATCHING/tests/test_matching_e2e.py",
}


def pytest_addoption(parser):
    parser.addoption(
        "--run-db-tests",
        action="store_true",
        default=False,
        help="collect and run PostgreSQL/Redis integration tests",
    )


def _should_run_db_tests(config) -> bool:
    return bool(config.getoption("--run-db-tests")) or os.getenv("RUN_DB_TESTS") == "1"


def _relative_posix_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def pytest_ignore_collect(collection_path: Path, config):
    if _should_run_db_tests(config):
        return None

    test_path = _relative_posix_path(collection_path, config.rootpath)
    if test_path in INTEGRATION_TEST_PATHS:
        return True

    return None
