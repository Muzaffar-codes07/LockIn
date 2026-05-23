"""Asserts every migration in the chain can downgrade and re-upgrade cleanly."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=API_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_alembic_chain_is_reversible() -> None:
    head = _alembic("upgrade", "head")
    assert head.returncode == 0, head.stderr
    base = _alembic("downgrade", "base")
    assert base.returncode == 0, base.stderr
    head2 = _alembic("upgrade", "head")
    assert head2.returncode == 0, head2.stderr
