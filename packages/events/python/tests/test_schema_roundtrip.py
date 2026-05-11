"""Round-trip every fixture through the generated pydantic models.

Source of truth: packages/events/src/schema.ts. If this test fails after a
schema change, run ``pnpm -F @lockin/events gen`` to regenerate
``lockin_events.generated``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lockin_events import generated as gen

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"


def _model_for(event_type: str) -> type:
    """Map an event_type string to its generated pydantic class.

    Names follow the codegen convention: dots removed, segments title-cased.
    e.g. ``task.created`` -> ``TaskCreated``.
    """

    class_name = "".join(part.title() for part in event_type.split("."))
    if not hasattr(gen, class_name):
        raise AssertionError(
            f"generated module has no class {class_name} for event_type {event_type}. "
            "Did you forget to run `pnpm -F @lockin/events gen`?"
        )
    return getattr(gen, class_name)


@pytest.mark.parametrize("fixture_path", sorted(FIXTURE_DIR.glob("*.json")))
def test_fixture_roundtrips(fixture_path: Path) -> None:
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    model_cls = _model_for(raw["event_type"])
    obj = model_cls.model_validate(raw)
    reserialized = obj.model_dump(mode="json", exclude_none=False)
    reparsed = model_cls.model_validate(reserialized)
    assert reparsed == obj


def test_every_event_type_has_a_fixture() -> None:
    expected = {
        "task.created",
        "task.scheduled",
        "task.accepted",
        "task.rejected",
        "task.modified",
        "task.completed",
        "mood.logged",
        "energy.logged",
        "schedule.explained",
    }
    actual = {p.stem.replace("_", ".") for p in FIXTURE_DIR.glob("*.json")}
    assert expected == actual
