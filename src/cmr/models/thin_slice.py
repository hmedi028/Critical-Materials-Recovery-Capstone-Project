
from pathlib import Path

from cmr.models.material import load_usgs_critical_minerals
from cmr.models.recommendation import Recommendation, RecommendationCategory
from cmr.synthetic import load_seed_items, load_seed_composition


def main():
    item_id = "SYN-ITEM-002"

    # 1. Identify the item.
    item = next(
        item for item in load_seed_items()
        if item.public_item_id == item_id
    )

    # 2. Load the item's composition evidence.
    evidence = [
        record for record in load_seed_composition()
        if record.item_id == item_id
    ]

    # 3. Load and check the USGS critical-minerals reference.
    usgs_path = Path("data/static/usgs/critical_minerals_2025.csv")
    materials = load_usgs_critical_minerals(usgs_path)
    reference = {material.material_id.lower(): material for material in materials}

    matches = [
        record for record in evidence
        if record.material_id.lower() in reference
    ]

    # 4. Generate a recommendation from the results.
    recommendation = Recommendation(
        recommendation_id="DEMO-REC-002",
        item_id=item.public_item_id,
        category=RecommendationCategory.MANUAL_REVIEW,
        explanation=(
            "Synthetic composition evidence identifies "
            + ", ".join(record.material_id for record in matches)
            + " in the USGS critical-minerals reference. "
            "Verify the composition and assess recovery options before acting."
        ),
        confidence=0.80,
        human_review_required=True,
    )

    # 5. Display the recommendation and its provenance.
    print("=== END-TO-END THIN SLICE ===")
    print(f"Item: {item.public_item_id} — {item.name}")
    print(f"Item source: {item.source_record_id}")
    print("\nUSGS matches:")
    for record in matches:
        print(
            f"- {reference[record.material_id.lower()].material_name}"
            f" | Evidence source: {record.source_record_id}"
            f" | Synthetic: {record.is_synthetic}"
        )

    print("\nRecommendation:")
    print(recommendation.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
