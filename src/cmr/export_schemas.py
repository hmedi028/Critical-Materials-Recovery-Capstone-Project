"""Write JSON Schema contracts from the Pydantic models into data/schemas/."""

from __future__ import annotations

import json
from pathlib import Path

from cmr.models import (
    CompositionEvidence,
    CriticalityReference,
    Item,
    Material,
    Provenance,
    Recommendation,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "data" / "schemas"

MODELS = {
    "provenance": Provenance,
    "material": Material,
    "criticality_reference": CriticalityReference,
    "item": Item,
    "composition_evidence": CompositionEvidence,
    "recommendation": Recommendation,
}


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
