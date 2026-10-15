"""Load committed synthetic demonstration records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from cmr.models import (
    Component,
    CompositionEvidence,
    Item,
    LifecycleEvent,
    Recommendation,
    ReviewDecision,
)

T = TypeVar("T", bound=BaseModel)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = REPO_ROOT / "data" / "synthetic"


def load_json_models(path: Path, model: type[T]) -> list[T]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    return [model.model_validate(row) for row in payload]


def load_seed_items(path: Path | None = None) -> list[Item]:
    return load_json_models(path or SYNTHETIC_DIR / "items.json", Item)


def load_seed_components(path: Path | None = None) -> list[Component]:
    return load_json_models(path or SYNTHETIC_DIR / "components.json", Component)


def load_seed_composition(path: Path | None = None) -> list[CompositionEvidence]:
    return load_json_models(
        path or SYNTHETIC_DIR / "composition_evidence.json",
        CompositionEvidence,
    )


def load_seed_recommendations(path: Path | None = None) -> list[Recommendation]:
    return load_json_models(
        path or SYNTHETIC_DIR / "recommendations.json",
        Recommendation,
    )


def load_seed_review_decisions(path: Path | None = None) -> list[ReviewDecision]:
    return load_json_models(
        path or SYNTHETIC_DIR / "review_decisions.json",
        ReviewDecision,
    )


def load_seed_lifecycle_events(path: Path | None = None) -> list[LifecycleEvent]:
    return load_json_models(
        path or SYNTHETIC_DIR / "lifecycle_events.json",
        LifecycleEvent,
    )
