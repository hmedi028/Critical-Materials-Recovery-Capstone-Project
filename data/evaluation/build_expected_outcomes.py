import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SOURCE = BASE / "data" / "synthetic"
OUTPUT = BASE / "data" / "evaluation" / "expected_outcomes.json"

RECOVERY_MATERIALS = {
    "lithium", "cobalt", "neodymium", "nickel", "dysprosium",
    "terbium", "praseodymium", "samarium", "yttrium", "cerium"
}

RECYCLABLE_MATERIALS = {"copper", "aluminum"}

def load_records(filename):
    return json.loads((SOURCE / filename).read_text())

items = load_records("items.json")
composition = load_records("composition_evidence.json")

evidence_by_item = {}
for record in composition:
    evidence_by_item.setdefault(record["item_id"], []).append(record)

expected = []

for item in items:
    item_id = item["public_item_id"]
    condition = item.get("public_characteristics", {}).get(
        "condition", "unknown"
    )
    evidence = evidence_by_item.get(item_id, [])

    uncertain = any(
        record.get("evidence_quality") in {"incomplete", "conflicting", "inferred"}
        or record.get("evidence_type") == "inferred"
        or record.get("value_basis") == "inferred"
        for record in evidence
    )

    materials = {record["material_id"].lower() for record in evidence}

    if condition == "unknown" or uncertain:
        category = "manual_review"
        reason = "Condition is unknown or composition evidence is uncertain."

    elif condition == "serviceable":
        category = "retain"
        reason = "Item is serviceable and has no demonstrated recovery priority."

    elif condition == "unserviceable" and materials & RECOVERY_MATERIALS:
        category = "reclaim"
        reason = "Unserviceable item contains a material identified for recovery."

    elif condition == "damaged" and materials & RECYCLABLE_MATERIALS:
        category = "recycle"
        reason = "Damaged item contains identified recyclable material."

    elif condition == "damaged":
        category = "dispose"
        reason = "Damaged item has no identified recovery-priority or recyclable material."

    else:
        category = "manual_review"
        reason = "Available condition and composition information is insufficient."

    expected.append({
        "item_id": item_id,
        "expected_category": category,
        "condition": condition,
        "materials_identified": sorted(materials),
        "composition_evidence_count": len(evidence),
        "rationale": reason,
        "is_synthetic": True
    })

if len(expected) != 100:
    raise ValueError(f"Expected 100 evaluation records; found {len(expected)}")

if len({record["item_id"] for record in expected}) != len(expected):
    raise ValueError("Duplicate item IDs found in evaluation records.")

OUTPUT.write_text(json.dumps(expected, indent=2) + "\n")

from collections import Counter

print(f"Created {OUTPUT}")
print(f"Evaluation records: {len(expected)}")
print("Expected outcome counts:")
for category, count in sorted(
    Counter(record["expected_category"] for record in expected).items()
):
    print(f"  {category}: {count}")
