import unittest

from cmr.models.recommendation import RecommendationCategory
from cmr.test_cases import load_test_case_dataset


class TestCuratedTestCases(unittest.TestCase):
    def test_dataset_validates_and_covers_requirements(self) -> None:
        dataset = load_test_case_dataset()
        self.assertGreaterEqual(len(dataset.test_cases), 5)
        self.assertLessEqual(len(dataset.test_cases), 10)

        categories = {tc.expected_recommendation.category for tc in dataset.test_cases}
        self.assertEqual(categories, set(RecommendationCategory))

        review_flags = {tc.expected_recommendation.human_review_required for tc in dataset.test_cases}
        self.assertEqual(review_flags, {True, False})

        by_id = {tc.test_case_id: tc for tc in dataset.test_cases}
        self.assertTrue(by_id["TC-02"].expected_recommendation.human_review_required)
        self.assertEqual(
            by_id["TC-02"].expected_recommendation.category,
            RecommendationCategory.MANUAL_REVIEW,
        )


if __name__ == "__main__":
    unittest.main()
