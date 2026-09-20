from collections import Counter
from pathlib import Path

from cmr.models import EvidenceQuality, ValueBasis
from cmr.models.material import load_usgs_critical_minerals
from cmr.synthetic import (
    load_seed_components,
    load_seed_composition,
    load_seed_items,
    load_seed_lifecycle_events,
    load_seed_recommendations,
    load_seed_review_decisions,
)

USGS_CSV = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "static"
    / "usgs"
    / "critical_minerals_2025.csv"
)

TEMPLATE_CATEGORIES = {
    "SYN-ITEM-001": "retain",
    "SYN-ITEM-002": "reclaim",
    "SYN-ITEM-003": "recycle",
    "SYN-ITEM-004": "manual_review",
    "SYN-ITEM-005": "dispose",
    "SYN-ITEM-006": "reclaim",
    "SYN-ITEM-007": "manual_review",
}

UNCERTAIN_QUALITY = {
    EvidenceQuality.INFERRED,
    EvidenceQuality.INCOMPLETE,
    EvidenceQuality.CONFLICTING,
}


def test_synthetic_eval_corpus_has_at_least_100_labeled_items() -> None:
    items = load_seed_items()
    components = load_seed_components()
    composition = load_seed_composition()
    recommendations = load_seed_recommendations()
    reviews = load_seed_review_decisions()
    events = load_seed_lifecycle_events()
    usgs_ids = {material.material_id for material in load_usgs_critical_minerals(USGS_CSV)}

    item_ids = {item.public_item_id for item in items}
    component_ids = {component.component_id for component in components}
    recommendation_by_item = {row.item_id: row for row in recommendations}
    counts = Counter(row.category.value for row in recommendations)

    assert len(items) >= 100
    assert len(item_ids) == len(items)
    assert len(recommendations) == len(items)
    assert item_ids == set(recommendation_by_item)
    assert all(item.is_synthetic for item in items)
    assert all(item.license_or_reuse_status.startswith("CC0") for item in items)
    assert all(item.generated_date is not None and item.source_record_id for item in items)
    assert all(component.parent_item_id in item_ids for component in components)
    assert all(
        row.item_id in item_ids
        and (row.component_id is None or row.component_id in component_ids)
        and row.material_id in usgs_ids
        and row.is_synthetic
        for row in composition
    )
    assert set(counts) == {
        "retain",
        "reclaim",
        "recycle",
        "manual_review",
        "dispose",
    }
    assert all(count >= 20 for count in counts.values())
    assert all(
        recommendation_by_item[item_id].category.value == category
        for item_id, category in TEMPLATE_CATEGORIES.items()
    )
    assert all(event.item_id in item_ids and event.is_synthetic for event in events)
    assert all(
        row.human_review_required
        for row in recommendations
        if row.category.value == "manual_review"
    )
    uncertain_item_ids = {
        row.item_id
        for row in composition
        if row.item_id
        and (
            row.evidence_quality in UNCERTAIN_QUALITY
            or row.value_basis is ValueBasis.INFERRED
        )
    }
    assert uncertain_item_ids
    assert all(
        recommendation_by_item[item_id].human_review_required
        and recommendation_by_item[item_id].category.value == "manual_review"
        for item_id in uncertain_item_ids
    )
    review_rec_ids = {row.recommendation_id for row in reviews}
    assert {
        recommendation_by_item[item_id].recommendation_id
        for item_id in uncertain_item_ids
    } <= review_rec_ids
