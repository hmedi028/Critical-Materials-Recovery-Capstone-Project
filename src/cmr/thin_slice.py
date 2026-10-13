from pathlib import Path
import json

from cmr.models.material import load_usgs_critical_minerals
from cmr.models.recommendation import Recommendation, RecommendationCategory
from cmr.synthetic import load_seed_items, load_seed_composition


def main():
    item_id = "SYN-ITEM-002"

    item = next(
        item for item in load_seed_items()
        if item.public_item_id == item_id
    )
    evidence = [
        record for record in load_seed_composition()
        if record.item_id == item_id
    ]

    usgs_path = Path("data/static/usgs/critical_minerals_2025.csv")
    materials = load_usgs_critical_minerals(usgs_path)
    reference = {
        material.material_id.lower(): material
        for material in materials
    }

    evidence_results = []
    matches = []

    for record in evidence:
        material = reference.get(record.material_id.lower())
        matched = material is not None

        evidence_results.append({
            "material_id": record.material_id,
            "quantity": str(record.quantity) if record.quantity is not None else None,
            "quantity_unit": record.quantity_unit,
            "evidence_source_id": record.source_record_id,
            "evidence_source_name": record.source_name,
            "evidence_quality": record.evidence_quality.value,
            "is_synthetic": record.is_synthetic,
            "usgs_match": matched,
            "usgs_material_name": material.material_name if material else None,
            "usgs_publication": material.criticality_reference if material else None,
            "usgs_publication_year": material.publication_year if material else None,
            "usgs_source_url": str(material.source_url) if material and material.source_url else None,
            "usgs_retrieved_date": str(material.retrieved_date) if material and material.retrieved_date else None,
        })

        if matched:
            matches.append(record)

    recommendation = Recommendation(
        recommendation_id="DEMO-REC-002",
        item_id=item.public_item_id,
        category=RecommendationCategory.MANUAL_REVIEW,
        explanation=(
            "Synthetic composition evidence identifies "
            + ", ".join(record.material_id for record in matches)
            + " in the USGS critical-minerals reference. "
            "Verify composition and assess recovery options before acting."
        ),
        confidence=0.80,
        human_review_required=True,
    )

    result = {
        "item": {
            "public_item_id": item.public_item_id,
            "name": item.name,
            "source_record_id": item.source_record_id,
            "source_name": item.source_name,
            "is_synthetic": item.is_synthetic,
        },
        "composition_evidence": evidence_results,
        "recommendation": recommendation.model_dump(mode="json"),
    }

    output_path = Path("thin_slice_result.json")
    output_path.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== END-TO-END THIN SLICE ===")
    print(json.dumps(result, indent=2))
    print(f"\nSaved complete result to {output_path}")


if __name__ == "__main__":
    main()
