"""Generate the CC0 synthetic evaluation corpus through Pydantic models.

Run: python -m cmr.generate_synthetic
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from cmr.models import (
    Component,
    CompositionEvidence,
    EvidenceQuality,
    EvidenceType,
    Item,
    ItemCondition,
    LifecycleEvent,
    LifecycleEventType,
    Recommendation,
    RecommendationCategory,
    ReviewDecision,
    ReviewerRole,
    ReviewOutcome,
    ValueBasis,
)
from cmr.synthetic import SYNTHETIC_DIR

TARGET_COUNT = 100
GENERATED_DATE = date(2026, 9, 19)
SOURCE_NAME = "CMR synthetic demonstration data"
LICENSE = "CC0 1.0 Universal"
UTC = timezone.utc

RECLAIM_MATERIALS = (
    "lithium",
    "cobalt",
    "neodymium",
    "nickel",
    "dysprosium",
    "terbium",
    "praseodymium",
    "samarium",
    "yttrium",
    "cerium",
)
REE_MATERIALS = {
    "neodymium",
    "dysprosium",
    "terbium",
    "praseodymium",
    "samarium",
    "yttrium",
    "cerium",
}


@dataclass
class Corpus:
    items: list[Item] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    composition: list[CompositionEvidence] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    reviews: list[ReviewDecision] = field(default_factory=list)
    events: list[LifecycleEvent] = field(default_factory=list)


def item_id(index: int) -> str:
    return f"SYN-ITEM-{index:03d}"


def rec_id(index: int) -> str:
    return f"REC-{index:03d}"


def provenance(
    record_id: str,
    quality: EvidenceQuality = EvidenceQuality.CONFIRMED,
) -> dict[str, object]:
    return {
        "source_name": SOURCE_NAME,
        "source_record_id": record_id,
        "generated_date": GENERATED_DATE,
        "license_or_reuse_status": LICENSE,
        "evidence_quality": quality,
        "is_synthetic": True,
    }


def add_event(
    corpus: Corpus,
    index: int,
    condition: ItemCondition,
    event_type: LifecycleEventType,
    location: str,
    day_offset: int,
) -> None:
    event_id = f"SYN-EVT-{index:03d}-{event_type.value[:3].upper()}"
    corpus.events.append(
        LifecycleEvent(
            event_id=event_id,
            item_id=item_id(index),
            event_type=event_type,
            condition=condition,
            quantity=Decimal("1"),
            quantity_unit="each",
            timestamp=datetime(2026, 9, 10, 12, 0, tzinfo=UTC) + timedelta(days=day_offset),
            generic_location_code=location,
            **provenance(event_id),
        )
    )


def add_recommendation(
    corpus: Corpus,
    index: int,
    category: RecommendationCategory,
    explanation: str,
    confidence: float,
    human_review_required: bool,
) -> None:
    corpus.recommendations.append(
        Recommendation(
            recommendation_id=rec_id(index),
            item_id=item_id(index),
            category=category,
            explanation=explanation,
            confidence=confidence,
            human_review_required=human_review_required,
        )
    )


def add_review(
    corpus: Corpus,
    index: int,
    role: ReviewerRole,
    decision: ReviewOutcome,
    reason: str,
) -> None:
    review_id = f"REV-{index:03d}"
    corpus.reviews.append(
        ReviewDecision(
            review_id=review_id,
            recommendation_id=rec_id(index),
            reviewer_role=role,
            decision=decision,
            reason=reason,
            timestamp=datetime(2026, 9, 19, 15, 0, tzinfo=UTC) + timedelta(minutes=index),
        )
    )


def build_templates() -> Corpus:
    corpus = Corpus()

    corpus.items.extend(
        [
            Item(
                public_item_id="SYN-ITEM-001",
                name="Demo field radio chassis",
                category="communications equipment",
                public_characteristics={"condition": "serviceable", "form": "metal chassis"},
                **provenance("SYN-ITEM-001"),
            ),
            Item(
                public_item_id="SYN-ITEM-002",
                name="Demo lithium battery module",
                category="energy storage",
                public_characteristics={"condition": "unserviceable", "form": "sealed module"},
                **provenance("SYN-ITEM-002"),
            ),
            Item(
                public_item_id="SYN-ITEM-003",
                name="Demo copper cable assembly",
                category="electrical cable",
                public_characteristics={"condition": "damaged", "form": "insulated cable"},
                **provenance("SYN-ITEM-003"),
            ),
            Item(
                public_item_id="SYN-ITEM-004",
                name="Demo circuit card assembly",
                category="electronics",
                public_characteristics={"condition": "unknown", "form": "printed circuit card"},
                **provenance("SYN-ITEM-004", EvidenceQuality.INCOMPLETE),
            ),
            Item(
                public_item_id="SYN-ITEM-005",
                name="Demo plastic shipping crate",
                category="packaging",
                public_characteristics={"condition": "damaged", "form": "empty crate"},
                **provenance("SYN-ITEM-005"),
            ),
            Item(
                public_item_id="SYN-ITEM-006",
                name="Demo electric motor",
                category="rotating electrical equipment",
                public_characteristics={
                    "condition": "unserviceable",
                    "form": "motor with magnet assembly",
                },
                **provenance("SYN-ITEM-006"),
            ),
            Item(
                public_item_id="SYN-ITEM-007",
                name="Demo power supply",
                category="power conversion",
                public_characteristics={"condition": "unknown", "form": "enclosed supply"},
                **provenance("SYN-ITEM-007", EvidenceQuality.CONFLICTING),
            ),
        ]
    )

    corpus.components.extend(
        [
            Component(
                component_id="SYN-CMP-002-CELL",
                name="battery cell stack",
                parent_item_id="SYN-ITEM-002",
                public_reference_number="SYN-REF-CELL",
                **provenance("SYN-CMP-002-CELL"),
            ),
            Component(
                component_id="SYN-CMP-004-CAP",
                name="surface-mount capacitor",
                parent_item_id="SYN-ITEM-004",
                public_reference_number="SYN-REF-CAP",
                **provenance("SYN-CMP-004-CAP", EvidenceQuality.INCOMPLETE),
            ),
            Component(
                component_id="SYN-CMP-006-MAG",
                name="permanent magnet assembly",
                parent_item_id="SYN-ITEM-006",
                public_reference_number="SYN-REF-MAG",
                **provenance("SYN-CMP-006-MAG"),
            ),
        ]
    )

    corpus.composition.extend(
        [
            CompositionEvidence(
                item_id="SYN-ITEM-001",
                material_id="aluminum",
                percentage=Decimal("65"),
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-001-AL"),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-002",
                component_id="SYN-CMP-002-CELL",
                material_id="lithium",
                quantity=Decimal("0.4"),
                quantity_unit="kg",
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-002-LI"),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-002",
                component_id="SYN-CMP-002-CELL",
                material_id="cobalt",
                quantity=Decimal("0.15"),
                quantity_unit="kg",
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-002-CO"),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-003",
                material_id="copper",
                quantity=Decimal("3.2"),
                quantity_unit="kg",
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-003-CU"),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-004",
                component_id="SYN-CMP-004-CAP",
                material_id="tantalum",
                percentage=Decimal("2"),
                evidence_type=EvidenceType.INFERRED,
                value_basis=ValueBasis.INFERRED,
                **provenance("SYN-COMP-004-TA", EvidenceQuality.INCOMPLETE),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-006",
                component_id="SYN-CMP-006-MAG",
                material_id="neodymium",
                quantity=Decimal("0.08"),
                quantity_unit="kg",
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-006-ND"),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-007",
                material_id="nickel",
                percentage=Decimal("8"),
                evidence_type=EvidenceType.SYNTHETIC_BOM,
                value_basis=ValueBasis.SYNTHETIC,
                **provenance("SYN-COMP-007-NI-A", EvidenceQuality.CONFLICTING),
            ),
            CompositionEvidence(
                item_id="SYN-ITEM-007",
                material_id="nickel",
                percentage=Decimal("0"),
                evidence_type=EvidenceType.INFERRED,
                value_basis=ValueBasis.INFERRED,
                **provenance("SYN-COMP-007-NI-B", EvidenceQuality.CONFLICTING),
            ),
        ]
    )

    add_recommendation(
        corpus,
        1,
        RecommendationCategory.RETAIN,
        "Serviceable chassis with no scarce-material recovery priority; retain for possible reuse.",
        0.86,
        False,
    )
    add_recommendation(
        corpus,
        2,
        RecommendationCategory.RECLAIM,
        "Synthetic bill of materials includes lithium and cobalt, both on the USGS 2025 critical-minerals list.",
        0.81,
        False,
    )
    add_recommendation(
        corpus,
        3,
        RecommendationCategory.RECYCLE,
        "Damaged copper cable has recyclable content but is not a reclaim-priority assembly.",
        0.78,
        False,
    )
    add_recommendation(
        corpus,
        4,
        RecommendationCategory.MANUAL_REVIEW,
        "Tantalum presence is inferred from an incomplete synthetic bill of materials and requires human confirmation.",
        0.41,
        True,
    )
    add_recommendation(
        corpus,
        5,
        RecommendationCategory.DISPOSE,
        "Empty plastic crate has no identified critical or recyclable material content.",
        0.9,
        False,
    )
    add_recommendation(
        corpus,
        6,
        RecommendationCategory.RECLAIM,
        "Magnet assembly includes neodymium, a rare earth element on the USGS 2025 list.",
        0.84,
        False,
    )
    add_recommendation(
        corpus,
        7,
        RecommendationCategory.MANUAL_REVIEW,
        "Two synthetic sources disagree on whether nickel is present. Send for manual review.",
        0.35,
        True,
    )

    add_review(
        corpus,
        4,
        ReviewerRole.MATERIALS_SPECIALIST,
        ReviewOutcome.REVISE,
        "Inferred tantalum is not confirmed. Keep the item in manual review until a source-backed composition is added.",
    )
    add_review(
        corpus,
        7,
        ReviewerRole.ANALYST,
        ReviewOutcome.ACCEPT,
        "Conflicting nickel evidence is correctly sent for human review.",
    )

    add_event(corpus, 1, ItemCondition.SERVICEABLE, LifecycleEventType.RECEIPT, "LOC-A", 0)
    add_event(corpus, 2, ItemCondition.UNSERVICEABLE, LifecycleEventType.INSPECTION, "LOC-B", 2)
    return corpus


def add_retain(corpus: Corpus, index: int) -> None:
    variant = index - 7
    corpus.items.append(
        Item(
            public_item_id=item_id(index),
            name=f"Demo field radio chassis {index:03d}",
            category="communications equipment",
            public_characteristics={
                "condition": "serviceable",
                "form": "metal chassis",
                "variant": str(variant),
            },
            **provenance(item_id(index)),
        )
    )
    corpus.composition.append(
        CompositionEvidence(
            item_id=item_id(index),
            material_id="aluminum",
            percentage=Decimal(50 + (variant % 20)),
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
            **provenance(f"SYN-COMP-{index:03d}-AL"),
        )
    )
    add_recommendation(
        corpus,
        index,
        RecommendationCategory.RETAIN,
        "Serviceable chassis with no scarce-material recovery priority; retain for possible reuse.",
        0.8,
        False,
    )
    add_event(
        corpus,
        index,
        ItemCondition.SERVICEABLE,
        LifecycleEventType.RECEIPT,
        "LOC-A",
        variant % 10,
    )


def add_reclaim(corpus: Corpus, index: int) -> None:
    variant = index - 7
    material = RECLAIM_MATERIALS[variant % len(RECLAIM_MATERIALS)]
    is_ree = material in REE_MATERIALS
    component_id = f"SYN-CMP-{index:03d}-{'MAG' if is_ree else 'CELL'}"
    corpus.items.append(
        Item(
            public_item_id=item_id(index),
            name=(
                f"Demo electric motor {index:03d}"
                if is_ree
                else f"Demo lithium battery module {index:03d}"
            ),
            category="rotating electrical equipment" if is_ree else "energy storage",
            public_characteristics={
                "condition": "unserviceable",
                "form": "motor with magnet assembly" if is_ree else "sealed module",
                "variant": str(variant),
            },
            **provenance(item_id(index)),
        )
    )
    corpus.components.append(
        Component(
            component_id=component_id,
            name="permanent magnet assembly" if is_ree else "battery cell stack",
            parent_item_id=item_id(index),
            public_reference_number=f"SYN-REF-{index:03d}",
            **provenance(component_id),
        )
    )
    corpus.composition.append(
        CompositionEvidence(
            item_id=item_id(index),
            component_id=component_id,
            material_id=material,
            quantity=Decimal("0.05") + Decimal(variant % 9) / Decimal("100"),
            quantity_unit="kg",
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
            **provenance(f"SYN-COMP-{index:03d}-{material[:2].upper()}"),
        )
    )
    add_recommendation(
        corpus,
        index,
        RecommendationCategory.RECLAIM,
        f"Synthetic bill of materials includes {material}, which is on the USGS 2025 critical-minerals list.",
        0.82,
        False,
    )
    add_event(
        corpus,
        index,
        ItemCondition.UNSERVICEABLE,
        LifecycleEventType.INSPECTION,
        "LOC-B",
        variant % 10,
    )


def add_recycle(corpus: Corpus, index: int) -> None:
    variant = index - 7
    material = "copper" if variant % 2 == 0 else "aluminum"
    corpus.items.append(
        Item(
            public_item_id=item_id(index),
            name=f"Demo copper cable assembly {index:03d}"
            if material == "copper"
            else f"Demo aluminum housing {index:03d}",
            category="electrical cable" if material == "copper" else "metal housing",
            public_characteristics={
                "condition": "damaged",
                "form": "insulated cable" if material == "copper" else "unserviceable housing",
                "variant": str(variant),
            },
            **provenance(item_id(index)),
        )
    )
    corpus.composition.append(
        CompositionEvidence(
            item_id=item_id(index),
            material_id=material,
            quantity=Decimal("1.5") + Decimal(variant % 8),
            quantity_unit="kg",
            evidence_type=EvidenceType.SYNTHETIC_BOM,
            value_basis=ValueBasis.SYNTHETIC,
            **provenance(f"SYN-COMP-{index:03d}-{material[:2].upper()}"),
        )
    )
    add_recommendation(
        corpus,
        index,
        RecommendationCategory.RECYCLE,
        f"Damaged {material} assembly has recyclable content but is not a reclaim-priority item.",
        0.76,
        False,
    )
    add_event(
        corpus,
        index,
        ItemCondition.DAMAGED,
        LifecycleEventType.DISPOSITION,
        "LOC-C",
        variant % 10,
    )


def add_dispose(corpus: Corpus, index: int) -> None:
    variant = index - 7
    corpus.items.append(
        Item(
            public_item_id=item_id(index),
            name=f"Demo plastic shipping crate {index:03d}",
            category="packaging",
            public_characteristics={
                "condition": "damaged",
                "form": "empty crate",
                "variant": str(variant),
            },
            **provenance(item_id(index)),
        )
    )
    add_recommendation(
        corpus,
        index,
        RecommendationCategory.DISPOSE,
        "Empty plastic crate has no identified critical or recyclable material content.",
        0.9,
        False,
    )
    add_event(
        corpus,
        index,
        ItemCondition.DAMAGED,
        LifecycleEventType.DISPOSITION,
        "LOC-C",
        variant % 10,
    )


def add_manual_review(corpus: Corpus, index: int, kind: str) -> None:
    variant = index - 7
    if kind == "inferred":
        quality = EvidenceQuality.INFERRED
        component_id = f"SYN-CMP-{index:03d}-CAP"
        corpus.items.append(
            Item(
                public_item_id=item_id(index),
                name=f"Demo circuit card assembly {index:03d}",
                category="electronics",
                public_characteristics={
                    "condition": "unknown",
                    "form": "printed circuit card",
                    "variant": str(variant),
                },
                **provenance(item_id(index), EvidenceQuality.INCOMPLETE),
            )
        )
        corpus.components.append(
            Component(
                component_id=component_id,
                name="surface-mount capacitor",
                parent_item_id=item_id(index),
                public_reference_number=f"SYN-REF-{index:03d}",
                **provenance(component_id, EvidenceQuality.INCOMPLETE),
            )
        )
        corpus.composition.append(
            CompositionEvidence(
                item_id=item_id(index),
                component_id=component_id,
                material_id="tantalum",
                percentage=Decimal("1") + Decimal(variant % 4),
                evidence_type=EvidenceType.INFERRED,
                value_basis=ValueBasis.INFERRED,
                **provenance(f"SYN-COMP-{index:03d}-TA", EvidenceQuality.INCOMPLETE),
            )
        )
        explanation = (
            "Tantalum presence is inferred from an incomplete synthetic bill of materials "
            "and requires human confirmation."
        )
        reason = "Inferred tantalum is not confirmed. Keep the item in manual review."
        role = ReviewerRole.MATERIALS_SPECIALIST
        decision = ReviewOutcome.REVISE
    elif kind == "incomplete":
        quality = EvidenceQuality.INCOMPLETE
        corpus.items.append(
            Item(
                public_item_id=item_id(index),
                name=f"Demo mixed electronics assembly {index:03d}",
                category="electronics",
                public_characteristics={
                    "condition": "unknown",
                    "form": "partial assembly",
                    "variant": str(variant),
                },
                **provenance(item_id(index), quality),
            )
        )
        corpus.composition.append(
            CompositionEvidence(
                item_id=item_id(index),
                material_id="tin",
                percentage=Decimal("3"),
                evidence_type=EvidenceType.INFERRED,
                value_basis=ValueBasis.INFERRED,
                **provenance(f"SYN-COMP-{index:03d}-SN", quality),
            )
        )
        explanation = "Composition evidence is incomplete. Send for manual review."
        reason = "Incomplete evidence correctly requires human review."
        role = ReviewerRole.SUPERVISOR
        decision = ReviewOutcome.ACCEPT
    else:
        quality = EvidenceQuality.CONFLICTING
        corpus.items.append(
            Item(
                public_item_id=item_id(index),
                name=f"Demo power supply {index:03d}",
                category="power conversion",
                public_characteristics={
                    "condition": "unknown",
                    "form": "enclosed supply",
                    "variant": str(variant),
                },
                **provenance(item_id(index), quality),
            )
        )
        corpus.composition.extend(
            [
                CompositionEvidence(
                    item_id=item_id(index),
                    material_id="nickel",
                    percentage=Decimal("8"),
                    evidence_type=EvidenceType.SYNTHETIC_BOM,
                    value_basis=ValueBasis.SYNTHETIC,
                    **provenance(f"SYN-COMP-{index:03d}-NI-A", quality),
                ),
                CompositionEvidence(
                    item_id=item_id(index),
                    material_id="nickel",
                    percentage=Decimal("0"),
                    evidence_type=EvidenceType.INFERRED,
                    value_basis=ValueBasis.INFERRED,
                    **provenance(f"SYN-COMP-{index:03d}-NI-B", quality),
                ),
            ]
        )
        explanation = "Two synthetic sources disagree on whether nickel is present. Send for manual review."
        reason = "Conflicting nickel evidence is correctly sent for human review."
        role = ReviewerRole.ANALYST
        decision = ReviewOutcome.ACCEPT

    add_recommendation(
        corpus,
        index,
        RecommendationCategory.MANUAL_REVIEW,
        explanation,
        0.38,
        True,
    )
    add_review(corpus, index, role, decision, reason)
    add_event(
        corpus,
        index,
        ItemCondition.UNKNOWN,
        LifecycleEventType.INSPECTION,
        "LOC-B",
        variant % 10,
    )


def variant_plan() -> list[tuple[int, RecommendationCategory, str | None]]:
    """Assign remaining slots after the seven templates to reach TARGET_COUNT."""
    plan: list[tuple[int, RecommendationCategory, str | None]] = []
    index = 8
    review_kinds = ("inferred", "incomplete", "conflicting")
    remaining = {
        RecommendationCategory.RETAIN: 19,
        RecommendationCategory.RECLAIM: 18,
        RecommendationCategory.RECYCLE: 19,
        RecommendationCategory.DISPOSE: 19,
        RecommendationCategory.MANUAL_REVIEW: 18,
    }
    for category, count in remaining.items():
        for offset in range(count):
            kind = None
            if category is RecommendationCategory.MANUAL_REVIEW:
                kind = review_kinds[offset % len(review_kinds)]
            plan.append((index, category, kind))
            index += 1
    if index != TARGET_COUNT + 1:
        raise RuntimeError(f"Expected {TARGET_COUNT} items, planned through {index - 1}")
    return plan


def build_corpus() -> Corpus:
    corpus = build_templates()
    builders = {
        RecommendationCategory.RETAIN: add_retain,
        RecommendationCategory.RECLAIM: add_reclaim,
        RecommendationCategory.RECYCLE: add_recycle,
        RecommendationCategory.DISPOSE: add_dispose,
        RecommendationCategory.MANUAL_REVIEW: add_manual_review,
    }
    for index, category, kind in variant_plan():
        if category is RecommendationCategory.MANUAL_REVIEW:
            add_manual_review(corpus, index, kind or "inferred")
        else:
            builders[category](corpus, index)
    return corpus


def dump_models(path: Path, models: list[object]) -> None:
    payload = [
        model.model_dump(mode="json", exclude_none=True)  # type: ignore[attr-defined]
        for model in models
    ]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_corpus(corpus: Corpus, output_dir: Path | None = None) -> None:
    dest = output_dir or SYNTHETIC_DIR
    dest.mkdir(parents=True, exist_ok=True)
    dump_models(dest / "items.json", corpus.items)
    dump_models(dest / "components.json", corpus.components)
    dump_models(dest / "composition_evidence.json", corpus.composition)
    dump_models(dest / "recommendations.json", corpus.recommendations)
    dump_models(dest / "review_decisions.json", corpus.reviews)
    dump_models(dest / "lifecycle_events.json", corpus.events)


def main() -> None:
    corpus = build_corpus()
    write_corpus(corpus)
    print(f"Wrote {len(corpus.items)} items to {SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()
