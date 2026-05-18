"""Smoke test: the MCP entrypoint imports cleanly.

Catches regressions where a dep update or transport rename breaks
``apps/mcp/app/main.py`` at import time.

We load the module by file path rather than by name because both
``apps/api`` and ``apps/mcp`` install themselves as the top-level
``app`` Python package; sys.path resolution otherwise picks the api's
``app.main`` and the assertion never reaches the MCP code. A proper
fix (renaming one of the packages) is tracked as a separate cleanup.
"""

import importlib.util
from pathlib import Path


def _load(module_name: str, relative: str):
    file_path = Path(__file__).resolve().parents[2] / "app" / relative
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None, f"could not load {file_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_module_imports() -> None:
    main = _load("mcp_app_main_smoke", "main.py")
    assert callable(main.main)


def test_config_loads_without_error() -> None:
    config = _load("mcp_app_config_smoke", "core/config.py")
    settings = config.settings
    assert settings.MCP_TRANSPORT in {"stdio", "sse"}
