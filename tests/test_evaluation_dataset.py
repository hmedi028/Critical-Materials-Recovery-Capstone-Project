import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EVALUATION_FILE = BASE / "data" / "evaluation" / "expected_outcomes.json"

VALID_CATEGORIES = {
    "retain",
    "reclaim",
    "recycle",
    "manual_review",
    "dispose",
}


class EvaluationDatasetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.records = json.loads(EVALUATION_FILE.read_text())

    def test_contains_100_records(self):
        self.assertEqual(len(self.records), 100)

    def test_item_ids_are_unique(self):
        item_ids = [record["item_id"] for record in self.records]
        self.assertEqual(len(item_ids), len(set(item_ids)))

    def test_all_five_categories_are_present(self):
        categories = {
            record["expected_category"] for record in self.records
        }
        self.assertEqual(categories, VALID_CATEGORIES)

    def test_all_records_are_synthetic(self):
        self.assertTrue(
            all(record["is_synthetic"] for record in self.records)
        )

    def test_all_categories_are_valid(self):
        for record in self.records:
            self.assertIn(record["expected_category"], VALID_CATEGORIES)

    def test_each_record_has_a_rationale(self):
        for record in self.records:
            self.assertTrue(record["rationale"].strip())


if __name__ == "__main__":
    unittest.main()
