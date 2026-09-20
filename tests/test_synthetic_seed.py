from pathlib import Path

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

EXPECTED_CATEGORIES = {
    "SYN-ITEM-001": "retain",
    "SYN-ITEM-002": "reclaim",
    "SYN-ITEM-003": "recycle",
    "SYN-ITEM-004": "manual_review",
    "SYN-ITEM-005": "dispose",
    "SYN-ITEM-006": "reclaim",
    "SYN-ITEM-007": "manual_review",
}


def test_synthetic_seed_validates_and_covers_recommendation_categories() -> None:
    items = load_seed_items()
    components = load_seed_components()
    composition = load_seed_composition()
    recommendations = load_seed_recommendations()
    reviews = load_seed_review_decisions()
    events = load_seed_lifecycle_events()
    usgs_ids = {material.material_id for material in load_usgs_critical_minerals(USGS_CSV)}

    item_ids = {item.public_item_id for item in items}
    component_ids = {component.component_id for component in components}
    recommendation_ids = {row.recommendation_id for row in recommendations}

    assert item_ids == set(EXPECTED_CATEGORIES)
    assert all(item.is_synthetic for item in items)
    assert all(component.parent_item_id in item_ids for component in components)
    assert all(
        row.item_id in item_ids
        and (row.component_id is None or row.component_id in component_ids)
        and row.material_id in usgs_ids
        and row.is_synthetic
        for row in composition
    )
    assert {row.category.value for row in recommendations} == set(EXPECTED_CATEGORIES.values())
    assert {
        row.item_id: row.category.value for row in recommendations
    } == EXPECTED_CATEGORIES
    assert all(row.recommendation_id in recommendation_ids for row in reviews)
    assert all(event.item_id in item_ids and event.is_synthetic for event in events)
    assert all(
        row.human_review_required for row in recommendations if row.category.value == "manual_review"
    )
