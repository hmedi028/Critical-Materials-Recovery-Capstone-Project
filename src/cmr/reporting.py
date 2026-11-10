"""Presentation DTOs for recommendation reports and dashboard summaries.

Composes existing domain models for display and JSON download. Not a 13th PDF
entity and not registered with export_schemas.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from cmr.models import (
    AuditEvent,
    CompositionEvidence,
    EvidenceQuality,
    Item,
    LifecycleEvent,
    Material,
    Recommendation,
    RecommendationCategory,
    RecoveryMethod,
    ValueBasis,
    ValueEstimate,
)
from cmr.recommend import RecommendationResult
from cmr.test_cases import TestCaseRecord

ORIGIN_PUB_LOG = "PUB LOG"
ORIGIN_SYNTHETIC = "Synthetic (CC0)"


def format_measured_amount(
    quantity: Decimal | None,
    unit: str | None,
    percentage: Decimal | None,
) -> str:
    if quantity is not None and unit is not None:
        return f"{quantity} {unit}"
    if percentage is not None:
        return f"{percentage}%"
    return "N/A"


def origin_label_for(item: Item) -> str:
    return ORIGIN_SYNTHETIC if item.is_synthetic else ORIGIN_PUB_LOG


class MaterialSummary(BaseModel):
    """Flattened composition assertion for a recommendation report."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    material_id: str = Field(min_length=1)
    material_name: str = Field(min_length=1)
    usgs_match: bool
    is_rare_earth_element: bool
    measured_amount: str = Field(min_length=1)
    evidence_quality: EvidenceQuality
    value_basis: ValueBasis
    is_synthetic: bool
    source_name: str = Field(min_length=1)
    source_record_id: str | None = None


class RecommendationReport(BaseModel):
    """Item-level presentation object assembled from engine output and test inputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    test_case_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    source_notes: str = Field(min_length=1)
    item: Item
    lifecycle_event: LifecycleEvent
    recommendation: Recommendation
    expected_recommendation: Recommendation
    audit_event: AuditEvent
    lifecycle_is_synthetic: bool
    origin_label: str = Field(min_length=1)
    materials: list[MaterialSummary] = Field(default_factory=list)
    recovery_method: RecoveryMethod | None = None
    value_estimate: ValueEstimate | None = None


class DashboardSummary(BaseModel):
    """Fleet-level aggregates used by Summary charts and JSON export."""

    model_config = ConfigDict(extra="forbid")

    items_analyzed: int = Field(ge=0)
    counts_by_category: dict[str, int]
    human_review_count: int = Field(ge=0)
    auto_verified_count: int = Field(ge=0)
    public_item_count: int = Field(ge=0)
    synthetic_item_count: int = Field(ge=0)
    material_assertion_counts: dict[str, int] = Field(default_factory=dict)
    synthetic_lifecycle_count: int = Field(ge=0)
    illustrative_estimate_count: int = Field(ge=0)


def _material_summary(
    evidence: CompositionEvidence,
    usgs_map: dict[str, Material],
) -> MaterialSummary:
    material = usgs_map.get(evidence.material_id)
    return MaterialSummary(
        material_id=evidence.material_id,
        material_name=material.material_name if material else evidence.material_id.title(),
        usgs_match=material is not None,
        is_rare_earth_element=bool(material and material.is_rare_earth_element),
        measured_amount=format_measured_amount(
            evidence.quantity,
            evidence.quantity_unit,
            evidence.percentage,
        ),
        evidence_quality=evidence.evidence_quality,
        value_basis=evidence.value_basis,
        is_synthetic=evidence.is_synthetic,
        source_name=evidence.source_name,
        source_record_id=evidence.source_record_id,
    )


def build_recommendation_report(
    tc: TestCaseRecord,
    result: RecommendationResult,
    usgs_map: dict[str, Material],
) -> RecommendationReport:
    return RecommendationReport(
        test_case_id=tc.test_case_id,
        scenario=tc.scenario,
        source_notes=tc.source_notes,
        item=tc.item,
        lifecycle_event=tc.lifecycle_event,
        recommendation=result.recommendation,
        expected_recommendation=tc.expected_recommendation,
        audit_event=result.audit_event,
        lifecycle_is_synthetic=tc.lifecycle_event.is_synthetic,
        origin_label=origin_label_for(tc.item),
        materials=[_material_summary(ev, usgs_map) for ev in tc.composition_evidence],
        recovery_method=tc.recovery_method,
        value_estimate=tc.value_estimate,
    )


def build_dashboard_summary(reports: list[RecommendationReport]) -> DashboardSummary:
    counts_by_category = {category.value: 0 for category in RecommendationCategory}
    material_assertion_counts: dict[str, int] = {}
    human_review_count = 0
    public_item_count = 0
    synthetic_item_count = 0
    synthetic_lifecycle_count = 0
    illustrative_estimate_count = 0

    for report in reports:
        counts_by_category[report.recommendation.category.value] += 1
        if report.recommendation.human_review_required:
            human_review_count += 1
        if report.item.is_synthetic:
            synthetic_item_count += 1
        else:
            public_item_count += 1
        if report.lifecycle_is_synthetic:
            synthetic_lifecycle_count += 1
        if report.value_estimate is not None and report.value_estimate.is_illustrative:
            illustrative_estimate_count += 1
        for material in report.materials:
            material_assertion_counts[material.material_id] = (
                material_assertion_counts.get(material.material_id, 0) + 1
            )

    items_analyzed = len(reports)
    return DashboardSummary(
        items_analyzed=items_analyzed,
        counts_by_category=counts_by_category,
        human_review_count=human_review_count,
        auto_verified_count=items_analyzed - human_review_count,
        public_item_count=public_item_count,
        synthetic_item_count=synthetic_item_count,
        material_assertion_counts=material_assertion_counts,
        synthetic_lifecycle_count=synthetic_lifecycle_count,
        illustrative_estimate_count=illustrative_estimate_count,
    )
