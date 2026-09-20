from datetime import date

import pytest
from pydantic import ValidationError

from cmr.models import (
    CompositionEvidence,
    EvidenceQuality,
    EvidenceType,
    Provenance,
    Recommendation,
    RecommendationCategory,
    ValueBasis,
)


def _provenance_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "source_name": "CMR synthetic demonstration data",
        "source_record_id": "rec-1",
        "generated_date": date(2026, 9, 19),
        "license_or_reuse_status": "CC0 1.0 Universal",
        "evidence_quality": EvidenceQuality.INFERRED,
        "is_synthetic": True,
    }
    values.update(overrides)
    return values


def test_provenance_rejects_missing_source_identifier() -> None:
    with pytest.raises(ValidationError, match="source_url or source_record_id"):
        Provenance(
            **_provenance_kwargs(source_record_id=None),  # type: ignore[arg-type]
        )


def test_provenance_rejects_missing_date() -> None:
    with pytest.raises(ValidationError, match="retrieved_date or generated_date"):
        Provenance(
            **_provenance_kwargs(generated_date=None),  # type: ignore[arg-type]
        )


def test_composition_requires_item_or_component() -> None:
    with pytest.raises(ValidationError, match="item_id or component_id"):
        CompositionEvidence(
            **_provenance_kwargs(),
            material_id="lithium",
            percentage=10,
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
        )


def test_composition_requires_quantity_and_unit_together() -> None:
    with pytest.raises(ValidationError, match="quantity and quantity_unit"):
        CompositionEvidence(
            **_provenance_kwargs(),
            item_id="SYN-ITEM-001",
            material_id="aluminum",
            quantity=2,
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
        )


def test_composition_requires_measured_amount() -> None:
    with pytest.raises(ValidationError, match="quantity with quantity_unit, or percentage"):
        CompositionEvidence(
            **_provenance_kwargs(),
            item_id="SYN-ITEM-001",
            material_id="aluminum",
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
        )


def test_composition_blocks_confirmed_synthetic_values() -> None:
    with pytest.raises(ValidationError, match="cannot be synthetic"):
        CompositionEvidence(
            **_provenance_kwargs(),
            item_id="SYN-ITEM-001",
            material_id="aluminum",
            percentage=40,
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.CONFIRMED,
        )


def test_recommendation_confidence_must_be_unit_interval() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            recommendation_id="REC-BAD",
            item_id="SYN-ITEM-001",
            category=RecommendationCategory.RETAIN,
            explanation="Out of range confidence",
            confidence=1.5,
            human_review_required=False,
        )


def test_recommendation_category_must_be_known() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            recommendation_id="REC-BAD",
            item_id="SYN-ITEM-001",
            category="scrap",  # type: ignore[arg-type]
            explanation="Unknown category",
            confidence=0.5,
            human_review_required=False,
        )
