from cmr.synthetic import load_seed_items, load_seed_recommendations

TEMPLATE_CATEGORIES = {
    "SYN-ITEM-001": "retain",
    "SYN-ITEM-002": "reclaim",
    "SYN-ITEM-003": "recycle",
    "SYN-ITEM-004": "manual_review",
    "SYN-ITEM-005": "dispose",
    "SYN-ITEM-006": "reclaim",
    "SYN-ITEM-007": "manual_review",
}


def test_original_seven_templates_keep_expected_labels() -> None:
    items = {item.public_item_id: item for item in load_seed_items()}
    recommendations = {row.item_id: row for row in load_seed_recommendations()}

    assert TEMPLATE_CATEGORIES.keys() <= items.keys()
    assert {
        item_id: recommendations[item_id].category.value
        for item_id in TEMPLATE_CATEGORIES
    } == TEMPLATE_CATEGORIES
    assert all(items[item_id].is_synthetic for item_id in TEMPLATE_CATEGORIES)
