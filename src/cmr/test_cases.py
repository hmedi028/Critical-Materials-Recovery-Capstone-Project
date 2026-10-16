from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cmr.models import (
    CompositionEvidence,
    Item,
    LifecycleEvent,
    Recommendation,
    RecoveryMethod,
    ValueEstimate,
)
from cmr.models.material import load_usgs_critical_minerals

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_CASES_PATH = REPO_ROOT / "data" / "synthetic" / "test_cases.json"
DEFAULT_USGS_PATH = REPO_ROOT / "data" / "static" / "usgs" / "critical_minerals_2025.csv"


class TestCaseRecord(BaseModel):
    """Single benchmark test case bundling linked Pydantic entities for an item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    test_case_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    source_notes: str = Field(min_length=1)
    item: Item
    lifecycle_event: LifecycleEvent
    composition_evidence: list[CompositionEvidence] = Field(default_factory=list)
    recovery_method: RecoveryMethod | None = None
    value_estimate: ValueEstimate | None = None
    expected_recommendation: Recommendation

    @model_validator(mode="after")
    def check_referential_integrity(self) -> "TestCaseRecord":
        item_id = self.item.public_item_id
        if self.lifecycle_event.item_id != item_id:
            raise ValueError(
                f"{self.test_case_id}: lifecycle_event.item_id ({self.lifecycle_event.item_id}) "
                f"does not match item.public_item_id ({item_id})"
            )
        if self.expected_recommendation.item_id != item_id:
            raise ValueError(
                f"{self.test_case_id}: expected_recommendation.item_id "
                f"({self.expected_recommendation.item_id}) does not match item.public_item_id ({item_id})"
            )
        for ev in self.composition_evidence:
            if ev.item_id != item_id:
                raise ValueError(
                    f"{self.test_case_id}: composition_evidence.item_id ({ev.item_id}) "
                    f"does not match item.public_item_id ({item_id})"
                )
        return self


class TestCaseDataset(BaseModel):
    """Curated collection of 5-10 test cases for initial prototype validation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dataset_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    generated_date: date
    license_or_reuse_status: str = Field(min_length=1)
    test_cases: list[TestCaseRecord] = Field(min_length=5, max_length=10)


def load_test_case_dataset(
    path: Path = DEFAULT_TEST_CASES_PATH,
    usgs_path: Path = DEFAULT_USGS_PATH,
) -> TestCaseDataset:
    raw = json.loads(path.read_text(encoding="utf-8"))
    dataset = TestCaseDataset.model_validate(raw)

    usgs_materials = {m.material_id for m in load_usgs_critical_minerals(usgs_path)}
    seen_ids: set[str] = set()
    for tc in dataset.test_cases:
        if tc.test_case_id in seen_ids:
            raise ValueError(f"Duplicate test_case_id: {tc.test_case_id}")
        seen_ids.add(tc.test_case_id)
        for ev in tc.composition_evidence:
            if ev.material_id not in usgs_materials:
                raise ValueError(
                    f"{tc.test_case_id}: unknown material_id '{ev.material_id}' "
                    "not found in USGS 2025 critical minerals reference"
                )
        if tc.recovery_method and tc.recovery_method.material_id not in usgs_materials:
            raise ValueError(
                f"{tc.test_case_id}: recovery_method.material_id "
                f"'{tc.recovery_method.material_id}' not found in USGS 2025 reference"
            )
        if tc.value_estimate and tc.value_estimate.material_id not in usgs_materials:
            raise ValueError(
                f"{tc.test_case_id}: value_estimate.material_id "
                f"'{tc.value_estimate.material_id}' not found in USGS 2025 reference"
            )

    return dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the curated test dataset against Pydantic models and USGS 2025 critical minerals."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_TEST_CASES_PATH,
        help="Path to test_cases.json",
    )
    parser.add_argument(
        "--usgs",
        type=Path,
        default=DEFAULT_USGS_PATH,
        help="Path to USGS 2025 critical minerals CSV",
    )
    args = parser.parse_args(argv)

    dataset = load_test_case_dataset(args.input, args.usgs)
    public_count = sum(not tc.item.is_synthetic for tc in dataset.test_cases)
    synthetic_count = sum(tc.item.is_synthetic for tc in dataset.test_cases)
    evidence_count = sum(len(tc.composition_evidence) for tc in dataset.test_cases)
    categories = sorted({tc.expected_recommendation.category.value for tc in dataset.test_cases})

    print(
        f"Validated {len(dataset.test_cases)} test cases "
        f"({public_count} public PUB LOG items, {synthetic_count} synthetic items; "
        f"{evidence_count} composition evidence records)."
    )
    print(f"Expected recommendation categories covered: {', '.join(categories)}")
    for tc in dataset.test_cases:
        materials = ", ".join(ev.material_id for ev in tc.composition_evidence) or "none"
        print(
            f"  {tc.test_case_id}: {tc.item.public_item_id} | {tc.item.name} | "
            f"condition={tc.lifecycle_event.condition.value} | "
            f"materials=[{materials}] -> {tc.expected_recommendation.category.value} "
            f"(human_review={tc.expected_recommendation.human_review_required})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
