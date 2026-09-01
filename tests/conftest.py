from __future__ import annotations

import importlib
import sys

import pytest
from fastapi.testclient import TestClient


def _clear_app_modules() -> None:
    module_names = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for module_name in module_names:
        sys.modules.pop(module_name, None)


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = (tmp_path / "test.db").as_posix()
    monkeypatch.setenv("MYSQL_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

    _clear_app_modules()
    importlib.invalidate_caches()

    app_main = importlib.import_module("app.main")

    with TestClient(app_main.app) as test_client:
        yield test_client
