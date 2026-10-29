from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from cmr.models import (
    CompositionEvidence,
    EvidenceQuality,
    EvidenceType,
    Item,
    ItemCondition,
    LifecycleEvent,
    LifecycleEventType,
    Material,
    RecommendationCategory,
    RecoveryMethod,
    ValueBasis,
)
from cmr.models.material import load_usgs_critical_minerals
from cmr.recommend import (
    RULE_DISPOSE,
    RULE_INPUT_VALIDATION,
    RULE_RECLAIM,
    RULE_RECYCLE,
    RULE_RETAIN,
    RULE_UNCERTAINTY,
    recommend_item,
)
from cmr.test_cases import load_test_case_dataset

UTC = timezone.utc
REPO_ROOT = Path(__file__).resolve().parents[1]
USGS_PATH = REPO_ROOT / "data" / "static" / "usgs" / "critical_minerals_2025.csv"


def _provenance(
    record_id: str,
    quality: EvidenceQuality = EvidenceQuality.CONFIRMED,
) -> dict[str, object]:
    return {
        "source_name": "CMR unit test",
        "source_record_id": record_id,
        "generated_date": date(2026, 10, 23),
        "license_or_reuse_status": "CC0-1.0",
        "evidence_quality": quality,
        "is_synthetic": True,
    }


def _item(
    item_id: str = "TEST-ITEM-001",
    *,
    quality: EvidenceQuality = EvidenceQuality.CONFIRMED,
    characteristics: dict[str, str] | None = None,
) -> Item:
    return Item(
        public_item_id=item_id,
        name="Test item",
        category="test category",
        public_characteristics=characteristics or {"FSC": "5998", "HMIC": "N", "PMIC": "A", "CRIT_CD": "X"},
        **_provenance(item_id, quality),
    )


def _lifecycle(
    item_id: str = "TEST-ITEM-001",
    condition: ItemCondition = ItemCondition.UNSERVICEABLE,
) -> LifecycleEvent:
    return LifecycleEvent(
        event_id=f"EVT-{item_id}",
        item_id=item_id,
        event_type=LifecycleEventType.INSPECTION,
        condition=condition,
        quantity=Decimal("1"),
        quantity_unit="EA",
        timestamp=datetime(2026, 10, 23, 12, 0, tzinfo=UTC),
        generic_location_code="DEPOT-TEST-01",
        **_provenance(f"EVT-{item_id}"),
    )


def _evidence(
    item_id: str,
    material_id: str,
    *,
    quality: EvidenceQuality = EvidenceQuality.CONFIRMED,
    basis: ValueBasis = ValueBasis.SYNTHETIC,
    evidence_type: EvidenceType = EvidenceType.SYNTHETIC_BOM,
) -> CompositionEvidence:
    return CompositionEvidence(
        item_id=item_id,
        material_id=material_id,
        percentage=Decimal("10"),
        evidence_type=evidence_type,
        value_basis=basis,
        **_provenance(f"{item_id}:{material_id}", quality),
    )


def _recovery(item_material: str = "copper") -> RecoveryMethod:
    return RecoveryMethod(
        recovery_method_id="REC-TEST",
        material_id=item_material,
        process_name="Test recovery",
        expected_yield=Decimal("0.8"),
        **_provenance("REC-TEST"),
    )


def _usgs(*material_ids: str) -> dict[str, Material]:
    rows: dict[str, Material] = {}
    for index, material_id in enumerate(material_ids, start=1):
        rows[material_id] = Material(
            material_id=material_id,
            material_name=material_id.title(),
            criticality_reference="USGS 2025 critical minerals list",
            publication_year=2025,
            is_rare_earth_element=material_id == "lanthanum",
            **_provenance(f"USGS-{material_id}"),
            sort_order=index,
        )
    return rows


class TestRecommendPrecedence(unittest.TestCase):
    def test_uncertainty_gate_inferred_evidence(self) -> None:
        item = _item()
        result = recommend_item(
            item,
            _lifecycle(),
            [_evidence(item.public_item_id, "lead", quality=EvidenceQuality.CONFLICTING, basis=ValueBasis.INFERRED)],
            _usgs("lead"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.MANUAL_REVIEW)
        self.assertTrue(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_UNCERTAINTY))
        self.assertTrue(any(RULE_UNCERTAINTY in rule for rule in result.audit_event.rules_executed))

    def test_retain_when_serviceable(self) -> None:
        item = _item()
        result = recommend_item(
            item,
            _lifecycle(condition=ItemCondition.SERVICEABLE),
            [_evidence(item.public_item_id, "aluminum")],
            _usgs("aluminum"),
            recovery_method=_recovery("aluminum"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.RETAIN)
        self.assertFalse(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_RETAIN))

    def test_reclaim_when_recovery_method_present(self) -> None:
        item = _item()
        result = recommend_item(
            item,
            _lifecycle(),
            [_evidence(item.public_item_id, "copper")],
            _usgs("copper"),
            recovery_method=_recovery("copper"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.RECLAIM)
        self.assertFalse(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_RECLAIM))

    def test_recycle_without_reclamation_support(self) -> None:
        item = _item()
        result = recommend_item(
            item,
            _lifecycle(),
            [_evidence(item.public_item_id, "aluminum"), _evidence(item.public_item_id, "magnesium")],
            _usgs("aluminum", "magnesium"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.RECYCLE)
        self.assertFalse(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_RECYCLE))

    def test_dispose_when_no_composition(self) -> None:
        item = _item()
        result = recommend_item(item, _lifecycle(condition=ItemCondition.DAMAGED), [], _usgs("copper"))
        self.assertEqual(result.recommendation.category, RecommendationCategory.DISPOSE)
        self.assertFalse(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_DISPOSE))


class TestRecommendSafety(unittest.TestCase):
    def test_unknown_material_id_is_manual_review(self) -> None:
        item = _item()
        result = recommend_item(
            item,
            _lifecycle(),
            [_evidence(item.public_item_id, "unobtanium")],
            _usgs("copper"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.MANUAL_REVIEW)
        self.assertTrue(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_INPUT_VALIDATION))

    def test_missing_lifecycle_is_manual_review(self) -> None:
        item = _item()
        result = recommend_item(item, None, [_evidence(item.public_item_id, "copper")], _usgs("copper"))
        self.assertEqual(result.recommendation.category, RecommendationCategory.MANUAL_REVIEW)
        self.assertTrue(result.recommendation.human_review_required)

    def test_lifecycle_item_mismatch_is_manual_review(self) -> None:
        item = _item("ITEM-A")
        result = recommend_item(
            item,
            _lifecycle("ITEM-B"),
            [_evidence("ITEM-A", "copper")],
            _usgs("copper"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.MANUAL_REVIEW)
        self.assertTrue(result.recommendation.human_review_required)

    def test_unmatched_inc_is_manual_review(self) -> None:
        item = _item(characteristics={"INC": "77777", "INC_STATUS": "UNMATCHED_IN_V_H6_NAME_INC", "HMIC": "N"})
        result = recommend_item(
            item,
            _lifecycle(),
            [_evidence(item.public_item_id, "lead")],
            _usgs("lead"),
        )
        self.assertEqual(result.recommendation.category, RecommendationCategory.MANUAL_REVIEW)
        self.assertTrue(result.recommendation.human_review_required)
        self.assertTrue(result.recommendation.explanation.startswith(RULE_UNCERTAINTY))

    def test_empty_evidence_does_not_raise(self) -> None:
        item = _item()
        result = recommend_item(item, _lifecycle(condition=ItemCondition.DAMAGED), [], {})
        self.assertEqual(result.recommendation.category, RecommendationCategory.DISPOSE)


class TestRecommendBenchmarkOracle(unittest.TestCase):
    def test_all_nine_cases_match_expected_category_and_review_flag(self) -> None:
        dataset = load_test_case_dataset()
        usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(USGS_PATH)}
        for tc in dataset.test_cases:
            with self.subTest(tc.test_case_id):
                result = recommend_item(
                    tc.item,
                    tc.lifecycle_event,
                    tc.composition_evidence,
                    usgs_map,
                    recovery_method=tc.recovery_method,
                    value_estimate=tc.value_estimate,
                    analysis_id=f"ANL-{tc.test_case_id}",
                )
                expected = tc.expected_recommendation
                self.assertEqual(result.recommendation.category, expected.category)
                self.assertEqual(
                    result.recommendation.human_review_required,
                    expected.human_review_required,
                )
                self.assertTrue(result.audit_event.rules_executed)
                winning_rule = result.recommendation.explanation.split(":", 1)[0]
                self.assertTrue(winning_rule in result.recommendation.explanation)
                self.assertTrue(
                    any(winning_rule in rule for rule in result.audit_event.rules_executed)
                )


if __name__ == "__main__":
    unittest.main()
