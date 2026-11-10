import json
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from cmr.models import (
    CompositionEvidence,
    EvidenceQuality,
    EvidenceType,
    Item,
    ItemCondition,
    LifecycleEvent,
    LifecycleEventType,
    Recommendation,
    RecommendationCategory,
    ValueBasis,
)
from cmr.models.material import load_usgs_critical_minerals
from cmr.recommend import recommend_item
from cmr.reporting import (
    ORIGIN_PUB_LOG,
    ORIGIN_SYNTHETIC,
    DashboardSummary,
    build_dashboard_summary,
    build_recommendation_report,
)
from cmr.test_cases import DEFAULT_USGS_PATH, TestCaseRecord, load_test_case_dataset

UTC = timezone.utc


def _load_reports():
    dataset = load_test_case_dataset()
    usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(DEFAULT_USGS_PATH)}
    reports = []
    for tc in dataset.test_cases:
        result = recommend_item(
            tc.item,
            tc.lifecycle_event,
            tc.composition_evidence,
            usgs_map,
            recovery_method=tc.recovery_method,
            value_estimate=tc.value_estimate,
            analysis_id=f"ANL-{tc.test_case_id}",
        )
        reports.append(build_recommendation_report(tc, result, usgs_map))
    return dataset, usgs_map, reports


class TestRecommendationReports(unittest.TestCase):
    def test_nine_case_reports_have_required_fields(self) -> None:
        _dataset, _usgs_map, reports = _load_reports()
        self.assertEqual(len(reports), 9)

        by_id = {report.test_case_id: report for report in reports}
        for report in reports:
            rec = report.recommendation
            self.assertTrue(rec.category)
            self.assertTrue(rec.explanation)
            self.assertGreaterEqual(rec.confidence, 0)
            self.assertLessEqual(rec.confidence, 1)
            self.assertIsInstance(rec.human_review_required, bool)
            self.assertTrue(report.origin_label)
            self.assertTrue(report.audit_event.audit_id)
            self.assertTrue(report.audit_event.rules_executed)
            self.assertEqual(
                report.origin_label,
                ORIGIN_SYNTHETIC if report.item.is_synthetic else ORIGIN_PUB_LOG,
            )
            self.assertEqual(report.lifecycle_is_synthetic, report.lifecycle_event.is_synthetic)
            self.assertTrue(report.item.source_name)
            self.assertTrue(report.item.license_or_reuse_status)

        self.assertEqual(by_id["TC-09"].materials, [])
        self.assertGreater(len(by_id["TC-01"].materials), 0)
        self.assertTrue(by_id["TC-08"].item.is_synthetic)
        self.assertEqual(by_id["TC-08"].origin_label, ORIGIN_SYNTHETIC)
        self.assertFalse(by_id["TC-01"].item.is_synthetic)
        self.assertEqual(by_id["TC-01"].origin_label, ORIGIN_PUB_LOG)

        for material in by_id["TC-08"].materials:
            self.assertTrue(material.is_synthetic)
            self.assertEqual(material.value_basis, ValueBasis.SYNTHETIC)

        self.assertTrue(by_id["TC-08"].lifecycle_is_synthetic)
        self.assertIsNotNone(by_id["TC-01"].value_estimate)
        self.assertTrue(by_id["TC-01"].value_estimate.is_illustrative)
        self.assertTrue(by_id["TC-01"].value_estimate.is_synthetic)

    def test_dashboard_summary_aggregates_computed_recommendations(self) -> None:
        _dataset, _usgs_map, reports = _load_reports()
        summary = build_dashboard_summary(reports)

        expected_counts = {category.value: 0 for category in RecommendationCategory}
        expected_review = 0
        expected_public = 0
        expected_synthetic = 0
        expected_lifecycle = 0
        expected_illustrative = 0
        expected_materials: dict[str, int] = {}
        for report in reports:
            expected_counts[report.recommendation.category.value] += 1
            expected_review += int(report.recommendation.human_review_required)
            if report.item.is_synthetic:
                expected_synthetic += 1
            else:
                expected_public += 1
            expected_lifecycle += int(report.lifecycle_is_synthetic)
            if report.value_estimate is not None and report.value_estimate.is_illustrative:
                expected_illustrative += 1
            for material in report.materials:
                expected_materials[material.material_id] = (
                    expected_materials.get(material.material_id, 0) + 1
                )

        self.assertEqual(summary.items_analyzed, len(reports))
        self.assertEqual(set(summary.counts_by_category), {c.value for c in RecommendationCategory})
        self.assertEqual(summary.counts_by_category, expected_counts)
        self.assertEqual(summary.human_review_count, expected_review)
        self.assertEqual(summary.auto_verified_count, len(reports) - expected_review)
        self.assertEqual(summary.public_item_count, expected_public)
        self.assertEqual(summary.synthetic_item_count, expected_synthetic)
        self.assertEqual(summary.synthetic_lifecycle_count, expected_lifecycle)
        self.assertEqual(summary.illustrative_estimate_count, expected_illustrative)
        self.assertEqual(summary.material_assertion_counts, expected_materials)
        self.assertEqual(
            summary.human_review_count + summary.auto_verified_count,
            summary.items_analyzed,
        )
        self.assertEqual(
            summary.public_item_count + summary.synthetic_item_count,
            summary.items_analyzed,
        )

    def test_empty_reports_keep_zero_category_keys(self) -> None:
        summary = build_dashboard_summary([])
        self.assertEqual(summary.items_analyzed, 0)
        self.assertEqual(
            summary.counts_by_category,
            {category.value: 0 for category in RecommendationCategory},
        )
        self.assertEqual(summary.human_review_count, 0)
        self.assertEqual(summary.auto_verified_count, 0)
        self.assertEqual(summary.material_assertion_counts, {})

    def test_dashboard_summary_json_dump_is_serializable(self) -> None:
        _dataset, _usgs_map, reports = _load_reports()
        summary = build_dashboard_summary(reports)
        payload = summary.model_dump(mode="json")
        encoded = json.dumps(payload)
        restored = json.loads(encoded)
        self.assertEqual(restored["items_analyzed"], 9)
        self.assertEqual(
            set(restored["counts_by_category"]),
            {category.value for category in RecommendationCategory},
        )
        round_trip = DashboardSummary.model_validate(restored)
        self.assertEqual(round_trip, summary)

        case_payload = json.loads(reports[0].model_dump_json())
        self.assertEqual(case_payload["test_case_id"], reports[0].test_case_id)
        self.assertIn("is_synthetic", case_payload["item"])

    def test_tc09_empty_materials_does_not_raise(self) -> None:
        dataset = load_test_case_dataset()
        usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(DEFAULT_USGS_PATH)}
        tc = next(case for case in dataset.test_cases if case.test_case_id == "TC-09")
        self.assertEqual(tc.composition_evidence, [])
        result = recommend_item(
            tc.item,
            tc.lifecycle_event,
            tc.composition_evidence,
            usgs_map,
            analysis_id="ANL-TC-09",
        )
        report = build_recommendation_report(tc, result, usgs_map)
        self.assertEqual(report.materials, [])
        summary = build_dashboard_summary([report])
        self.assertEqual(summary.material_assertion_counts, {})


class TestReportingBuildersOnMinimalInputs(unittest.TestCase):
    def test_unmatched_material_is_still_summarized(self) -> None:
        item = Item(
            public_item_id="TEST-REP-001",
            name="Minimal item",
            category="test",
            public_characteristics={"FSC": "5998"},
            source_name="unit test",
            source_record_id="TEST-REP-001",
            generated_date=date(2026, 11, 6),
            license_or_reuse_status="CC0-1.0",
            evidence_quality=EvidenceQuality.CONFIRMED,
            is_synthetic=True,
        )
        lifecycle = LifecycleEvent(
            event_id="EVT-TEST-REP-001",
            item_id=item.public_item_id,
            event_type=LifecycleEventType.INSPECTION,
            condition=ItemCondition.UNSERVICEABLE,
            quantity=Decimal("1"),
            quantity_unit="EA",
            timestamp=datetime(2026, 11, 6, 12, 0, tzinfo=UTC),
            generic_location_code="DEPOT-TEST",
            source_name="unit test",
            source_record_id="EVT-TEST-REP-001",
            generated_date=date(2026, 11, 6),
            license_or_reuse_status="CC0-1.0",
            evidence_quality=EvidenceQuality.CONFIRMED,
            is_synthetic=True,
        )
        evidence = CompositionEvidence(
            item_id=item.public_item_id,
            material_id="not-a-usgs-mineral",
            percentage=Decimal("10"),
            evidence_type=EvidenceType.INFERRED,
            value_basis=ValueBasis.INFERRED,
            source_name="unit test",
            source_record_id="EV-TEST-REP-001",
            generated_date=date(2026, 11, 6),
            license_or_reuse_status="CC0-1.0",
            evidence_quality=EvidenceQuality.INFERRED,
            is_synthetic=True,
        )
        expected = Recommendation(
            recommendation_id="REC-TEST-REP-001",
            item_id=item.public_item_id,
            category=RecommendationCategory.MANUAL_REVIEW,
            explanation="placeholder oracle",
            confidence=0.5,
            human_review_required=True,
        )
        tc = TestCaseRecord(
            test_case_id="TC-TEST",
            scenario="unmatched material",
            source_notes="unit test",
            item=item,
            lifecycle_event=lifecycle,
            composition_evidence=[evidence],
            expected_recommendation=expected,
        )
        result = recommend_item(item, lifecycle, [evidence], {}, analysis_id="ANL-TC-TEST")
        report = build_recommendation_report(tc, result, {})
        self.assertEqual(len(report.materials), 1)
        self.assertFalse(report.materials[0].usgs_match)
        self.assertFalse(report.materials[0].is_rare_earth_element)
        self.assertEqual(report.materials[0].measured_amount, "10%")


if __name__ == "__main__":
    unittest.main()
