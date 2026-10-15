"""Write JSON Schema contracts from the Pydantic models into data/schemas/."""

from __future__ import annotations

import json
from pathlib import Path

# Import all 12 entities
from cmr.models import (
    AuditEvent,
    Component,
    CompositionEvidence,
    CriticalityReference,
    Item,
    LifecycleEvent,
    Material,
    Provenance,
    Recommendation,
    RecoveryMethod,
    ReviewDecision,
    ValueEstimate,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "data" / "schemas"

# JSON Schema definitions for all 12 PDF entities
MODELS = {
    "provenance": Provenance,
    "material": Material,
    "criticality_reference": CriticalityReference,
    "item": Item,
    "component": Component,
    "composition_evidence": CompositionEvidence,
    "lifecycle_event": LifecycleEvent,
    "recovery_method": RecoveryMethod,
    "value_estimate": ValueEstimate,
    "recommendation": Recommendation,
    "review_decision": ReviewDecision,
    "audit_event": AuditEvent,
}

# Export all 12 JSON Schema definitions to data/schemas/
def export_schemas(output_dir: Path | None = None) -> list[Path]:
    dest = output_dir or SCHEMA_DIR
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in MODELS.items():
        path = dest / f"{name}.json"
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def main() -> None:
    for path in export_schemas():
        print(path)


if __name__ == "__main__":
    main()
