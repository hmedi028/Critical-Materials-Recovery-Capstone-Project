"""Deterministic item-to-recommendation engine.

Evaluates Item + LifecycleEvent + CompositionEvidence against the USGS 2025
critical-minerals reference and optional recovery/value records. Never reads
expected_recommendation; explanation and AuditEvent.rules_executed share one
evaluation trace.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from cmr.models import (
    AuditEvent,
    CompositionEvidence,
    EvidenceQuality,
    Item,
    ItemCondition,
    LifecycleEvent,
    Material,
    Recommendation,
    RecommendationCategory,
    RecoveryMethod,
    ValueBasis,
    ValueEstimate,
)
from cmr.models.material import load_usgs_critical_minerals
from cmr.test_cases import DEFAULT_TEST_CASES_PATH, DEFAULT_USGS_PATH, load_test_case_dataset

RULE_INPUT_VALIDATION = "RULE-00"
RULE_UNCERTAINTY = "RULE-01"
RULE_RETAIN = "RULE-02"
RULE_RECLAIM = "RULE-03"
RULE_RECYCLE = "RULE-04"
RULE_DISPOSE = "RULE-05"

UNCERTAIN_QUALITY = {
    EvidenceQuality.INFERRED,
    EvidenceQuality.INCOMPLETE,
    EvidenceQuality.CONFLICTING,
}
NICKEL_COBALT_FAMILY = frozenset({"nickel", "cobalt", "chromium"})
PRECIOUS_PMIC = frozenset({"S", "G", "C", "P"})


@dataclass
class _Trace:
    rules: list[str] = field(default_factory=list)
    winning_rule: str = RULE_INPUT_VALIDATION
    notes: list[str] = field(default_factory=list)

    def add(self, rule_id: str, message: str) -> None:
        self.rules.append(f"{rule_id}: {message}")

    def win(self, rule_id: str, message: str) -> None:
        self.winning_rule = rule_id
        self.add(rule_id, message)
        self.notes.append(message)


@dataclass(frozen=True)
class RecommendationResult:
    recommendation: Recommendation
    audit_event: AuditEvent


# Compute the recommendation
def recommend_item(
    item: Item,
    lifecycle_event: LifecycleEvent | None,
    composition_evidence: list[CompositionEvidence],
    usgs_materials: dict[str, Material],
    *,
    recovery_method: RecoveryMethod | None = None,
    value_estimate: ValueEstimate | None = None,
    analysis_id: str | None = None,
) -> RecommendationResult:
    """Compute a Recommendation and AuditEvent from item inputs only."""
    trace = _Trace()
    item_id = (item.public_item_id or "").strip()
    analysis = analysis_id or f"ANL-{item_id or 'UNKNOWN'}"

    if not item_id:
        return _finish(
            item_id="UNKNOWN",
            analysis_id=analysis,
            category=RecommendationCategory.MANUAL_REVIEW,
            human_review=True,
            confidence=0.30,
            trace=trace,
            rule_id=RULE_INPUT_VALIDATION,
            message="Missing public_item_id; route to manual review",
        )

    if lifecycle_event is not None and lifecycle_event.item_id != item_id:
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.MANUAL_REVIEW,
            human_review=True,
            confidence=0.30,
            trace=trace,
            rule_id=RULE_INPUT_VALIDATION,
            message=(
                f"Lifecycle event item_id ({lifecycle_event.item_id}) does not match "
                f"item.public_item_id ({item_id})"
            ),
        )

    unknown_materials = sorted(
        {
            ev.material_id
            for ev in composition_evidence
            if ev.material_id not in usgs_materials
        }
    )
    if unknown_materials:
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.MANUAL_REVIEW,
            human_review=True,
            confidence=0.30,
            trace=trace,
            rule_id=RULE_INPUT_VALIDATION,
            message=(
                "Unknown material_id not in USGS 2025 reference: "
                + ", ".join(unknown_materials)
            ),
        )

    chars = item.public_characteristics
    review_reasons, review_confidence = _uncertainty_reasons(item, composition_evidence, chars)
    if review_reasons:
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.MANUAL_REVIEW,
            human_review=True,
            confidence=review_confidence,
            trace=trace,
            rule_id=RULE_UNCERTAINTY,
            message="; ".join(review_reasons),
        )
    trace.add(RULE_UNCERTAINTY, "No uncertainty or safety gate triggered")

    if lifecycle_event is None:
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.MANUAL_REVIEW,
            human_review=True,
            confidence=0.35,
            trace=trace,
            rule_id=RULE_INPUT_VALIDATION,
            message="Missing lifecycle event; cannot evaluate operational state",
        )

    if lifecycle_event.condition is ItemCondition.SERVICEABLE:
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.RETAIN,
            human_review=False,
            confidence=0.95,
            trace=trace,
            rule_id=RULE_RETAIN,
            message=(
                f"Item condition is {lifecycle_event.condition.value}; "
                "retain in inventory rather than recovering materials"
            ),
        )
    trace.add(
        RULE_RETAIN,
        f"Condition is {lifecycle_event.condition.value}; not retained",
    )

    confirmed_usgs = _confirmed_usgs_materials(composition_evidence, usgs_materials)
    if confirmed_usgs and _has_reclamation_support(
        chars, confirmed_usgs, usgs_materials, recovery_method
    ):
        signals = _reclamation_signals(chars, confirmed_usgs, usgs_materials, recovery_method)
        materials = ", ".join(sorted(confirmed_usgs))
        extra = ""
        if value_estimate is not None:
            extra = f" Illustrative value estimate {value_estimate.estimate_id} recorded."
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.RECLAIM,
            human_review=False,
            confidence=0.92,
            trace=trace,
            rule_id=RULE_RECLAIM,
            message=(
                f"Unserviceable or damaged item has confirmed USGS 2025 critical minerals "
                f"({materials}) with supporting reclamation signal ({signals}).{extra}"
            ),
        )
    if confirmed_usgs:
        trace.add(
            RULE_RECLAIM,
            "Confirmed USGS materials present but no supporting reclamation signal",
        )
        materials = ", ".join(sorted(confirmed_usgs))
        return _finish(
            item_id=item_id,
            analysis_id=analysis,
            category=RecommendationCategory.RECYCLE,
            human_review=False,
            confidence=0.91,
            trace=trace,
            rule_id=RULE_RECYCLE,
            message=(
                f"Unserviceable or damaged item has confirmed USGS 2025 materials "
                f"({materials}) suited to standard recycling, without a specialized "
                "reclamation pathway"
            ),
        )

    materials_note = (
        "no composition assertions"
        if not composition_evidence
        else "no confirmed USGS 2025 critical-mineral matches"
    )
    return _finish(
        item_id=item_id,
        analysis_id=analysis,
        category=RecommendationCategory.DISPOSE,
        human_review=False,
        confidence=0.96,
        trace=trace,
        rule_id=RULE_DISPOSE,
        message=(
            f"Damaged or unserviceable item has {materials_note}; "
            "route to ordinary disposal"
        ),
    )

# Identify the uncertainty reasons
def _uncertainty_reasons(
    item: Item,
    composition_evidence: list[CompositionEvidence],
    chars: dict[str, str],
) -> tuple[list[str], float]:
    # Initialize the reasons and confidence
    reasons: list[str] = []
    confidence = 0.80

    if item.evidence_quality in UNCERTAIN_QUALITY:
        reasons.append(f"item evidence_quality is {item.evidence_quality.value}")
        confidence = min(confidence, 0.45 if item.evidence_quality is EvidenceQuality.INCOMPLETE else 0.40)

    for ev in composition_evidence:
        if ev.evidence_quality in UNCERTAIN_QUALITY:
            reasons.append(
                f"composition {ev.material_id} evidence_quality is {ev.evidence_quality.value}"
            )
            if ev.evidence_quality is EvidenceQuality.CONFLICTING:
                confidence = min(confidence, 0.25)
            elif ev.evidence_quality is EvidenceQuality.INFERRED:
                confidence = min(confidence, 0.55)
            else:
                confidence = min(confidence, 0.45)
        if ev.value_basis is ValueBasis.INFERRED:
            reasons.append(f"composition {ev.material_id} value_basis is inferred")
            confidence = min(confidence, 0.55)

    inc = chars.get("INC", "")
    inc_status = chars.get("INC_STATUS", "")
    if inc_status == "UNMATCHED_IN_V_H6_NAME_INC" or inc == "77777":
        reasons.append(f"unmatched catalog INC ({inc or inc_status})")
        confidence = min(confidence, 0.40)

    if chars.get("HMIC") == "P":
        reasons.append("hazardous material indicator HMIC=P")
        confidence = min(confidence, 0.75)

    return reasons, confidence

# Identify the confirmed USGS materials
def _confirmed_usgs_materials(
    composition_evidence: list[CompositionEvidence],
    usgs_materials: dict[str, Material],
) -> set[str]:
    matched: set[str] = set()
    for ev in composition_evidence:
        if ev.material_id not in usgs_materials:
            continue
        if ev.evidence_quality is not EvidenceQuality.CONFIRMED:
            continue
        if ev.value_basis is ValueBasis.INFERRED:
            continue
        matched.add(ev.material_id)
    return matched

# Check if the item has reclamation support
def _has_reclamation_support(
    chars: dict[str, str],
    confirmed_usgs: set[str],
    usgs_materials: dict[str, Material],
    recovery_method: RecoveryMethod | None,
) -> bool:
    return bool(_reclamation_signals(chars, confirmed_usgs, usgs_materials, recovery_method))


# Identify the reclamation signals
def _reclamation_signals(
    chars: dict[str, str],
    confirmed_usgs: set[str],
    usgs_materials: dict[str, Material],
    recovery_method: RecoveryMethod | None,
) -> str:
    signals: list[str] = []
    if recovery_method is not None:
        signals.append(f"recovery_method={recovery_method.recovery_method_id}")
    pmic = chars.get("PMIC", "")
    if pmic in PRECIOUS_PMIC:
        signals.append(f"PMIC={pmic}")
    ree = sorted(
        mid
        for mid in confirmed_usgs
        if usgs_materials[mid].is_rare_earth_element
    )
    if ree:
        signals.append("rare_earth=" + ",".join(ree))
    if chars.get("CRIT_CD") == "Y" and confirmed_usgs & NICKEL_COBALT_FAMILY:
        family = ",".join(sorted(confirmed_usgs & NICKEL_COBALT_FAMILY))
        signals.append(f"CRIT_CD=Y with nickel/cobalt-family alloys ({family})")
    return "; ".join(signals)

# Finalize the recommendation and audit event
def _finish(
    *,
    item_id: str,
    analysis_id: str,
    category: RecommendationCategory,
    human_review: bool,
    confidence: float,
    trace: _Trace,
    rule_id: str,
    message: str,
) -> RecommendationResult:
    trace.win(rule_id, message)
    explanation = f"{rule_id}: {message}"
    recommendation = Recommendation(
        recommendation_id=f"REC-{item_id}",
        item_id=item_id,
        category=category,
        explanation=explanation,
        confidence=confidence,
        human_review_required=human_review,
    )
    audit_event = AuditEvent(
        audit_id=f"AUD-{item_id}",
        analysis_id=analysis_id,
        action="evaluate_item_disposition",
        rules_executed=list(trace.rules),
        timestamp=datetime.now(timezone.utc),
        result=(
            f"category={category.value}; human_review_required={human_review}; "
            f"winning_rule={rule_id}"
        ),
    )
    return RecommendationResult(recommendation=recommendation, audit_event=audit_event)

# Execution entry point
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute recommendations for the curated benchmark test cases."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_TEST_CASES_PATH)
    parser.add_argument("--usgs", type=Path, default=DEFAULT_USGS_PATH)
    args = parser.parse_args(argv)

    dataset = load_test_case_dataset(args.input, args.usgs)
    usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(args.usgs)}

    matches = 0
    for tc in dataset.test_cases:
        # Compute the recommendation
        result = recommend_item(
            tc.item,
            tc.lifecycle_event,
            tc.composition_evidence,
            usgs_map,
            recovery_method=tc.recovery_method,
            value_estimate=tc.value_estimate,
            analysis_id=f"ANL-{tc.test_case_id}",
        )
        rec = result.recommendation
        expected = tc.expected_recommendation
        matched = (
            rec.category == expected.category
            and rec.human_review_required == expected.human_review_required
        )
        matches += int(matched)
        status = "MATCH" if matched else "MISMATCH"
        print(
            f"{tc.test_case_id}: computed={rec.category.value} "
            f"review={rec.human_review_required} expected={expected.category.value} "
            f"[{status}]"
        )
        print(f"  {rec.explanation}")
        for rule in result.audit_event.rules_executed:
            print(f"  - {rule}")
    print(f"Oracle match: {matches}/{len(dataset.test_cases)}")
    return 0 if matches == len(dataset.test_cases) else 1

# System entry point
if __name__ == "__main__":
    raise SystemExit(main())
