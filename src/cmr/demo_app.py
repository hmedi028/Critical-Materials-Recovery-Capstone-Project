from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from cmr.models import (
    AuditEvent,
    Material,
    RecommendationCategory,
    ReviewDecision,
    ReviewerRole,
    ReviewOutcome,
)
from cmr.models.material import load_usgs_critical_minerals
from cmr.test_cases import (
    DEFAULT_TEST_CASES_PATH,
    DEFAULT_USGS_PATH,
    TestCaseDataset,
    TestCaseRecord,
    load_test_case_dataset,
)

CATEGORY_LABELS: dict[RecommendationCategory, str] = {
    RecommendationCategory.RECLAIM: "RECLAIM",
    RecommendationCategory.MANUAL_REVIEW: "MANUAL REVIEW",
    RecommendationCategory.RETAIN: "RETAIN",
    RecommendationCategory.RECYCLE: "RECYCLE",
    RecommendationCategory.DISPOSE: "DISPOSE",
}


@st.cache_data
def get_loaded_data() -> tuple[TestCaseDataset, dict[str, Material]]:
    dataset = load_test_case_dataset(DEFAULT_TEST_CASES_PATH, DEFAULT_USGS_PATH)
    usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(DEFAULT_USGS_PATH)}
    return dataset, usgs_map


def format_measured_amount(quantity: Decimal | None, unit: str | None, percentage: Decimal | None) -> str:
    if quantity is not None and unit is not None:
        return f"{quantity} {unit}"
    if percentage is not None:
        return f"{percentage}%"
    return "N/A"


def extract_mrc_summary(chars: dict[str, str]) -> tuple[str, str]:
    mrc_keys = [k for k in chars if k.startswith("MRC_") or k == "SYNTHETIC_SPEC"]
    if not mrc_keys:
        return "None", "No characteristic text recorded"
    labels = ", ".join(mrc_keys)
    values = " | ".join(f"{k}: {chars[k]}" for k in mrc_keys)
    return labels, values


def derive_rules_executed(tc: TestCaseRecord, usgs_map: dict[str, Material]) -> list[str]:
    rules: list[str] = ["RULE-01: Normalize Item & Provenance Contract"]
    cond = tc.lifecycle_event.condition.value
    rules.append(f"RULE-02: Evaluate Lifecycle Condition ({cond})")

    if any(ev.material_id in usgs_map for ev in tc.composition_evidence):
        matched = ", ".join(sorted({ev.material_id for ev in tc.composition_evidence if ev.material_id in usgs_map}))
        rules.append(f"RULE-03: Match USGS 2025 Critical Minerals ({matched})")
    else:
        rules.append("RULE-03: No USGS 2025 Critical Minerals Matched")

    chars = tc.item.public_characteristics
    if chars.get("INC_STATUS") == "UNMATCHED_IN_V_H6_NAME_INC":
        rules.append("RULE-04A: Flag Unmatched Catalog INC (77777 -> Human Review)")
    if any(ev.evidence_quality.value in {"inferred", "incomplete", "conflicting"} for ev in tc.composition_evidence):
        rules.append("RULE-04B: Non-Confirmed Composition Evidence -> Require Human Review")
    if chars.get("HMIC") == "P":
        rules.append("RULE-04C: Hazardous Material Indicator (HMIC=P) -> Require Specialist Review")

    rules.append(
        f"RULE-05: Emit Recommendation ({tc.expected_recommendation.category.value.upper()}, "
        f"human_review_required={tc.expected_recommendation.human_review_required})"
    )
    return rules


def build_overview_dataframe(
    cases: list[TestCaseRecord],
    usgs_map: dict[str, Material],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for tc in cases:
        materials = [ev.material_id for ev in tc.composition_evidence]
        ree_present = any(
            usgs_map[m].is_rare_earth_element for m in materials if m in usgs_map
        )
        rows.append(
            {
                "Test Case": tc.test_case_id,
                "Public Item ID / NSN": tc.item.public_item_id,
                "Item Name": tc.item.name,
                "FSC": tc.item.public_characteristics.get("FSC", ""),
                "Origin": "Synthetic (CC0)" if tc.item.is_synthetic else "PUB LOG",
                "Condition": tc.lifecycle_event.condition.value,
                "Lot Qty": f"{tc.lifecycle_event.quantity} {tc.lifecycle_event.quantity_unit}",
                "USGS 2025 Minerals": ", ".join(materials) if materials else "none (non-metallic)",
                "REE": "Yes" if ree_present else "No",
                "Expected Outcome": tc.expected_recommendation.category.value.upper(),
                "Confidence": f"{tc.expected_recommendation.confidence:.0%}",
                "Human Review": "REQUIRED" if tc.expected_recommendation.human_review_required else "No",
            }
        )
    return pd.DataFrame(rows)


def render_recommendation_banner(tc: TestCaseRecord) -> None:
    rec = tc.expected_recommendation
    cat_label = CATEGORY_LABELS[rec.category]
    review_badge = (
        "HUMAN REVIEW REQUIRED" if rec.human_review_required else "AUTO-VERIFIED (NO HUMAN REVIEW REQUIRED)"
    )
    header_text = (
        f"**Recommendation: `{cat_label}`** &nbsp;|&nbsp; "
        f"**Confidence:** `{rec.confidence:.0%}` &nbsp;|&nbsp; "
        f"**Gate:** `{review_badge}`\n\n"
        f"{rec.explanation}\n\n"
        f"*Scenario:* {tc.scenario}"
    )
    if rec.human_review_required:
        st.warning(header_text)
    elif rec.category == RecommendationCategory.RECLAIM:
        st.success(header_text)
    elif rec.category == RecommendationCategory.DISPOSE:
        st.error(header_text)
    else:
        st.info(header_text)


def render_item_inspector(tc: TestCaseRecord, usgs_map: dict[str, Material]) -> None:
    render_recommendation_banner(tc)

    col_item, col_life = st.columns(2)
    chars = tc.item.public_characteristics

    with col_item:
        with st.container(border=True):
            origin_tag = "Synthetic Seed (CC0-1.0)" if tc.item.is_synthetic else "Public DLA PUB LOG"
            st.subheader(f"Item & Classification (`Item` — {origin_tag})")
            meta_rows = [
                ("Public Item ID / NSN", tc.item.public_item_id),
                ("NIIN", chars.get("NIIN", "Synthetic")),
                ("Item Name", tc.item.name),
                ("End Item Application", chars.get("END_ITEM_NAME", "Not specified in PUB LOG")),
                ("FSG", f"{chars.get('FSG', '')} — {chars.get('FSG_TITLE', '')}"),
                ("FSC", f"{chars.get('FSC', '')} — {chars.get('FSC_TITLE', '')}"),
                (
                    "INC",
                    f"{chars.get('INC', 'N/A')} "
                    f"({'UNMATCHED in V_H6_NAME_INC.CSV' if chars.get('INC_STATUS') else 'Matched in H6'})",
                ),
                ("CRIT_CD / PMIC", f"CRIT_CD={chars.get('CRIT_CD', 'N/A')} | PMIC={chars.get('PMIC', 'N/A')}"),
                ("DMIL / HMIC", f"DMIL={chars.get('DMIL', 'N/A')} | HMIC={chars.get('HMIC', 'N/A')}"),
                ("Item Evidence Quality", tc.item.evidence_quality.value),
                ("Source Record ID", tc.item.source_record_id or str(tc.item.source_url)),
                ("License / Reuse Status", tc.item.license_or_reuse_status),
            ]
            st.dataframe(
                pd.DataFrame(meta_rows, columns=["Attribute", "Value"]),
                hide_index=True,
                use_container_width=True,
            )

    with col_life:
        with st.container(border=True):
            st.subheader("Warehouse Lifecycle & Characteristic Reply (`LifecycleEvent`)")
            le = tc.lifecycle_event
            life_rows = [
                ("Lifecycle Event ID", le.event_id),
                ("Event Type", le.event_type.value),
                ("Warehouse Condition", le.condition.value.upper()),
                ("Quantity", f"{le.quantity} {le.quantity_unit}"),
                ("Generic Location Code", le.generic_location_code),
                ("Timestamp (UTC)", le.timestamp.isoformat()),
                ("Provenance Source", f"{le.source_name} ({le.source_record_id})"),
                ("Synthetic Flag", f"is_synthetic={le.is_synthetic} ({le.license_or_reuse_status})"),
            ]
            st.dataframe(
                pd.DataFrame(life_rows, columns=["Attribute", "Value"]),
                hide_index=True,
                use_container_width=True,
            )
            mrc_label, mrc_text = extract_mrc_summary(chars)
            st.caption(f"Raw Characteristic Reply ({mrc_label})")
            st.code(mrc_text, language="text")
            st.caption(tc.source_notes)

    st.markdown("#### Material Composition Evidence & USGS 2025 Criticality Match (`CompositionEvidence`)")
    if tc.composition_evidence:
        ev_rows: list[dict[str, Any]] = []
        for ev in tc.composition_evidence:
            mat = usgs_map.get(ev.material_id)
            ev_rows.append(
                {
                    "Material ID": ev.material_id,
                    "Material Name": mat.material_name if mat else ev.material_id.title(),
                    "USGS 2025 Critical Mineral": "Yes (2025)" if mat else "No",
                    "Rare Earth (REE)": "Yes (REE)" if (mat and mat.is_rare_earth_element) else "No",
                    "Measured Amount": format_measured_amount(ev.quantity, ev.quantity_unit, ev.percentage),
                    "Evidence Type": ev.evidence_type.value,
                    "Value Basis": ev.value_basis.value,
                    "Evidence Quality": ev.evidence_quality.value,
                    "Synthetic": ev.is_synthetic,
                    "Source Record ID": ev.source_record_id or "",
                    "Source Name": ev.source_name,
                }
            )
        st.dataframe(pd.DataFrame(ev_rows), hide_index=True, use_container_width=True)
    else:
        st.info(
            "No critical, strategic, or precious material assertions (`composition_evidence = []`). "
            "This item serves as a non-metallic negative control and routes to `DISPOSE`."
        )

    if tc.recovery_method or tc.value_estimate:
        col_rec, col_val = st.columns(2)
        with col_rec:
            if tc.recovery_method:
                rm = tc.recovery_method
                with st.container(border=True):
                    st.subheader("Documented Recovery Method (`RecoveryMethod`)")
                    st.markdown(
                        f"- **Method ID:** `{rm.recovery_method_id}` (Target Material: `{rm.material_id}`)\n"
                        f"- **Process:** {rm.process_name}\n"
                        f"- **Expected Yield:** `{rm.expected_yield:.0%}`\n"
                        f"- **Handling Notes:** {rm.handling_notes or 'None'}\n"
                        f"- **Provenance:** {rm.source_name} (`{rm.source_record_id}`, `{rm.license_or_reuse_status}`)"
                    )
        with col_val:
            if tc.value_estimate:
                ve = tc.value_estimate
                net_val = ve.reference_value - ve.recovery_cost
                with st.container(border=True):
                    st.subheader("Illustrative Value Estimate (`ValueEstimate`)")
                    st.markdown(
                        f"- **Estimate ID:** `{ve.estimate_id}` (`is_illustrative={ve.is_illustrative}`)\n"
                        f"- **Material & Quantity:** `{ve.quantity} {ve.quantity_unit}` of `{ve.material_id}`\n"
                        f"- **Gross Reference Value:** `${ve.reference_value} {ve.currency}`\n"
                        f"- **Estimated Recovery Cost:** `${ve.recovery_cost} {ve.currency}`\n"
                        f"- **Net Illustrative Margin:** `${net_val:+.2f} {ve.currency}` (Calc Date: `{ve.calculation_date}`)"
                    )

    with st.expander("View Executed Rules, Audit Trail & Raw Pydantic JSON"):
        rules = derive_rules_executed(tc, usgs_map)
        audit_event = AuditEvent(
            audit_id=f"AUD-{tc.test_case_id}-001",
            analysis_id=f"ANL-{tc.item.public_item_id}",
            action="evaluate_item_disposition",
            rules_executed=rules,
            timestamp=datetime.now(timezone.utc),
            result=(
                f"category={tc.expected_recommendation.category.value}; "
                f"human_review_required={tc.expected_recommendation.human_review_required}"
            ),
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Generated `AuditEvent` (Pydantic validated)**")
            st.json(audit_event.model_dump(mode="json"))
        with c2:
            st.markdown("**Full `TestCaseRecord` Payload (Pydantic validated)**")
            st.json(tc.model_dump(mode="json"))


def render_human_review_simulator(tc: TestCaseRecord, usgs_map: dict[str, Material]) -> None:
    st.subheader(f"Interactive Human Review & Audit Simulator — {tc.test_case_id} ({tc.item.name})")
    if tc.expected_recommendation.human_review_required:
        st.warning(
            f"`{tc.test_case_id}` (`{tc.item.public_item_id}`) triggered a mandatory **Human Review Gate** "
            f"(`human_review_required=True`). Reason: {tc.expected_recommendation.explanation}"
        )
    else:
        st.info(
            f"`{tc.test_case_id}` (`{tc.item.public_item_id}`) did not require mandatory human review "
            "(`human_review_required=False`), but you can still simulate a supervisor or specialist override below."
        )

    default_reason = (
        "Confirmed '16.750 IN. APPROX. LG OF LEAD' refers to electrical wire length, not elemental lead; "
        "INC 77777 logged for catalog follow-up."
        if tc.test_case_id == "TC-02"
        else (
            "Hazardous Material Indicator HMIC=P (Copper Alloy 170/172 beryllium hazard) verified; "
            "route to certified beryllium-safe reclamation handler."
            if tc.test_case_id == "TC-03"
            else f"Reviewed supporting evidence and approved {tc.expected_recommendation.category.value} disposition."
        )
    )

    with st.form(key=f"review_form_{tc.test_case_id}"):
        col_a, col_b = st.columns(2)
        with col_a:
            role_choice = st.selectbox(
                "Reviewer Role (`ReviewerRole`)",
                options=[r.value for r in ReviewerRole],
                index=2 if tc.test_case_id == "TC-03" else 0,
            )
        with col_b:
            outcome_choice = st.selectbox(
                "Review Decision Outcome (`ReviewOutcome`)",
                options=[o.value for o in ReviewOutcome],
                index=2 if tc.test_case_id in {"TC-02", "TC-03"} else 0,
            )
        reason_text = st.text_area(
            "Review Justification (`reason`)",
            value=default_reason,
        )
        submitted = st.form_submit_button("Validate & Record ReviewDecision + AuditEvent")

    if submitted or tc.expected_recommendation.human_review_required:
        now = datetime.now(timezone.utc)
        review_record = ReviewDecision(
            review_id=f"REV-{tc.test_case_id}-001",
            recommendation_id=tc.expected_recommendation.recommendation_id,
            reviewer_role=ReviewerRole(role_choice),
            decision=ReviewOutcome(outcome_choice),
            reason=reason_text.strip() or "Reviewed by human operator.",
            timestamp=now,
        )
        audit_record = AuditEvent(
            audit_id=f"AUD-REV-{tc.test_case_id}-001",
            analysis_id=f"ANL-{tc.item.public_item_id}",
            action=f"human_review_{review_record.decision.value}",
            rules_executed=derive_rules_executed(tc, usgs_map)
            + [f"HUMAN-REVIEW: role={review_record.reviewer_role.value} decision={review_record.decision.value}"],
            timestamp=now,
            result=f"Review {review_record.review_id} recorded ({review_record.decision.value})",
        )
        if submitted:
            st.success("Validated `ReviewDecision` and `AuditEvent` against Pydantic v2 contracts.")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("**Validated `ReviewDecision` (`data/schemas/review_decision.json`)**")
            st.json(review_record.model_dump(mode="json"))
        with col_r2:
            st.markdown("**Validated `AuditEvent` (`data/schemas/audit_event.json`)**")
            st.json(audit_record.model_dump(mode="json"))


def main() -> None:
    st.set_page_config(
        page_title="CMR Decision-Support Prototype",
        layout="wide",
    )

    dataset, usgs_map = get_loaded_data()
    all_cases = dataset.test_cases

    st.title("Critical Materials Recovery — Decision-Support Prototype")
    st.caption(
        "Explainable decision-support demonstration linking public DLA PUB LOG catalog items, "
        "synthetic operational states, and the USGS 2025 Critical Minerals List."
    )

    # Top KPI & Pipeline Reduction Strip
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("PUB LOG Scan", "38.9M rows", "Stage 2 V_CHARACTERISTICS")
    k2.metric("Classified Slice", "19 NIINs", "Stages 1–3 + Priority 4")
    k3.metric("Curated Test Cases", f"{len(all_cases)} items", "7 PUB LOG · 2 Synthetic")
    k4.metric("USGS 2025 Minerals", "11 matched", "60 total in static table")
    k5.metric("Human-Review Gates", "2 items", "TC-02 & TC-03")

    # Sidebar Filters & Selector
    st.sidebar.header("Benchmark Controls")
    category_filter = st.sidebar.selectbox(
        "Filter by Expected Recommendation",
        options=["All"] + [c.value for c in RecommendationCategory],
        index=0,
    )
    origin_filter = st.sidebar.radio(
        "Item Origin",
        options=["All", "Public PUB LOG", "Synthetic (CC0)"],
        index=0,
    )
    only_review = st.sidebar.checkbox("Only items requiring Human Review", value=False)
    search_query = st.sidebar.text_input("Search by NSN, NIIN, Name, or Material", value="").strip().lower()

    filtered_cases: list[TestCaseRecord] = []
    for tc in all_cases:
        if category_filter != "All" and tc.expected_recommendation.category.value != category_filter:
            continue
        if origin_filter == "Public PUB LOG" and tc.item.is_synthetic:
            continue
        if origin_filter == "Synthetic (CC0)" and not tc.item.is_synthetic:
            continue
        if only_review and not tc.expected_recommendation.human_review_required:
            continue
        if search_query:
            haystack = " ".join(
                [
                    tc.test_case_id,
                    tc.item.public_item_id,
                    tc.item.name,
                    tc.scenario,
                    " ".join(tc.item.public_characteristics.values()),
                    " ".join(ev.material_id for ev in tc.composition_evidence),
                ]
            ).lower()
            if search_query not in haystack:
                continue
        filtered_cases.append(tc)

    active_pool = filtered_cases if filtered_cases else all_cases
    case_options = {
        f"{tc.test_case_id} | {tc.item.public_item_id} — {tc.item.name} "
        f"[{tc.expected_recommendation.category.value.upper()}]": tc
        for tc in active_pool
    }

    selected_label = st.sidebar.selectbox(
        "Select Test Case to Inspect",
        options=list(case_options.keys()),
    )
    selected_case = case_options[selected_label]

    st.sidebar.divider()
    st.sidebar.caption(
        f"**Dataset ID:** `{dataset.dataset_id}`\n\n"
        f"**Generated:** `{dataset.generated_date}`\n\n"
        "**Guardrail:** AI-generated or lexical inferences are never treated as confirmed "
        "composition without a traceable source."
    )

    tab_inspector, tab_overview, tab_review = st.tabs(
        [
            f"Decision Support Report ({selected_case.test_case_id})",
            f"Benchmark Dataset Overview ({len(filtered_cases)}/{len(all_cases)})",
            "Human Review & Audit Simulator",
        ]
    )

    with tab_inspector:
        render_item_inspector(selected_case, usgs_map)

    with tab_overview:
        st.subheader("Curated 9-Item Benchmark Test Matrix")
        if not filtered_cases:
            st.warning("No test cases match the current sidebar filters; showing all 9 benchmark items.")
        overview_df = build_overview_dataframe(active_pool, usgs_map)
        st.dataframe(overview_df, hide_index=True, use_container_width=True)

        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("#### Test Cases by Recommendation Category")
            cat_counts = (
                pd.Series([tc.expected_recommendation.category.value for tc in all_cases])
                .value_counts()
                .rename_axis("Recommendation Category")
                .reset_index(name="Test Case Count")
            )
            st.bar_chart(cat_counts, x="Recommendation Category", y="Test Case Count")
        with c_chart2:
            st.markdown("#### Material Assertions by USGS 2025 Critical Mineral")
            mat_counts = (
                pd.Series([ev.material_id for tc in all_cases for ev in tc.composition_evidence])
                .value_counts()
                .rename_axis("USGS 2025 Critical Mineral")
                .reset_index(name="Assertion Count")
            )
            st.bar_chart(mat_counts, x="USGS 2025 Critical Mineral", y="Assertion Count")

    with tab_review:
        render_human_review_simulator(selected_case, usgs_map)


if __name__ == "__main__":
    main()
