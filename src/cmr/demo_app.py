# Current Streamlit demo: computed Recommendation + AuditEvent via recommend.py,
# presented through reporting.py (Summary vs Detailed Analytics).
#
# Previous version (v0.4.0) used:
# - TestCaseRecord.expected_recommendation as the live on-screen recommendation
# - derive_rules_executed() as a hardcoded audit trace
# - a hardcoded ingest-funnel KPI strip (38.9M rows / 19 NIINs / 9 cases)
# Those paths were replaced; test_cases.json and USGS 2025 remain the inputs.
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from cmr.models import (
    AuditEvent,
    Recommendation,
    RecommendationCategory,
    ReviewDecision,
    ReviewerRole,
    ReviewOutcome,
)
from cmr.models.material import load_usgs_critical_minerals
from cmr.recommend import recommend_item
from cmr.reporting import (
    ORIGIN_PUB_LOG,
    ORIGIN_SYNTHETIC,
    DashboardSummary,
    RecommendationReport,
    build_dashboard_summary,
    build_recommendation_report,
)
from cmr.test_cases import (
    DEFAULT_TEST_CASES_PATH,
    DEFAULT_USGS_PATH,
    TestCaseDataset,
    load_test_case_dataset,
)

CATEGORY_LABELS: dict[RecommendationCategory, str] = {
    RecommendationCategory.RECLAIM: "RECLAIM",
    RecommendationCategory.MANUAL_REVIEW: "MANUAL REVIEW",
    RecommendationCategory.RETAIN: "RETAIN",
    RecommendationCategory.RECYCLE: "RECYCLE",
    RecommendationCategory.DISPOSE: "DISPOSE",
}

EXPORT_CAPTION = (
    "JSON is a demo/presentation dump from `cmr.reporting`, not a 13th domain schema. "
    "CSV and PDF/HTML export are planned."
)
VIEW_SUMMARY = "Summary"
VIEW_DETAILED = "Detailed Analytics"


@st.cache_data
def get_loaded_data() -> TestCaseDataset:
    return load_test_case_dataset(DEFAULT_TEST_CASES_PATH, DEFAULT_USGS_PATH)


def load_reports() -> tuple[TestCaseDataset, list[RecommendationReport], DashboardSummary]:
    dataset = get_loaded_data()
    usgs_map = {m.material_id: m for m in load_usgs_critical_minerals(DEFAULT_USGS_PATH)}
    reports: list[RecommendationReport] = []
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
    return dataset, reports, build_dashboard_summary(reports)


def extract_mrc_summary(chars: dict[str, str]) -> tuple[str, str]:
    mrc_keys = [k for k in chars if k.startswith("MRC_") or k == "SYNTHETIC_SPEC"]
    if not mrc_keys:
        return "None", "No characteristic text recorded"
    labels = ", ".join(mrc_keys)
    values = " | ".join(f"{k}: {chars[k]}" for k in mrc_keys)
    return labels, values


def build_overview_dataframe(reports: list[RecommendationReport]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for report in reports:
        rec = report.recommendation
        expected = report.expected_recommendation
        oracle_match = (
            rec.category == expected.category
            and rec.human_review_required == expected.human_review_required
        )
        ree_present = any(material.is_rare_earth_element for material in report.materials)
        chars = report.item.public_characteristics
        lifecycle = report.lifecycle_event
        rows.append(
            {
                "Test Case": report.test_case_id,
                "Public Item ID / NSN": report.item.public_item_id,
                "Item Name": report.item.name,
                "FSC": chars.get("FSC", ""),
                "Origin": report.origin_label,
                "Condition": lifecycle.condition.value,
                "Lot Qty": f"{lifecycle.quantity} {lifecycle.quantity_unit}",
                "USGS 2025 Material Assertions": (
                    ", ".join(material.material_id for material in report.materials)
                    if report.materials
                    else "none (non-metallic)"
                ),
                "REE": "Yes" if ree_present else "No",
                "Computed Outcome": rec.category.value.upper(),
                "Expected Outcome": expected.category.value.upper(),
                "Oracle": "MATCH" if oracle_match else "MISMATCH",
                "Confidence": f"{rec.confidence:.0%}",
                "Human Review": "REQUIRED" if rec.human_review_required else "No",
                "Synthetic": "Synthetic" if report.item.is_synthetic else "Public catalog",
            }
        )
    return pd.DataFrame(rows)


def build_compact_table(reports: list[RecommendationReport]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Test Case": report.test_case_id,
                "Item Name": report.item.name,
                "Origin": report.origin_label,
                "Category": CATEGORY_LABELS[report.recommendation.category],
                "Human Review": "Required" if report.recommendation.human_review_required else "No",
                "Synthetic": "Synthetic" if report.item.is_synthetic else "Public catalog",
            }
            for report in reports
        ]
    )


def category_chart_frame(summary: DashboardSummary) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Recommendation Category": CATEGORY_LABELS[RecommendationCategory(key)],
                "Test Case Count": value,
            }
            for key, value in summary.counts_by_category.items()
        ]
    )


def review_chart_frame(summary: DashboardSummary) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Review Status": "Human review required", "Count": summary.human_review_count},
            {"Review Status": "Auto-verified", "Count": summary.auto_verified_count},
        ]
    )


def origin_chart_frame(summary: DashboardSummary) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Origin": ORIGIN_PUB_LOG, "Count": summary.public_item_count},
            {"Origin": ORIGIN_SYNTHETIC, "Count": summary.synthetic_item_count},
        ]
    )


def material_chart_frame(summary: DashboardSummary) -> pd.DataFrame:
    rows = sorted(
        summary.material_assertion_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    return pd.DataFrame(
        [
            {"USGS 2025 Critical Mineral": material_id, "Assertion Count": count}
            for material_id, count in rows
        ]
    )


def render_export_placeholders(
    *,
    json_label: str,
    json_filename: str,
    json_payload: str,
    json_key: str,
    csv_key: str,
    pdf_key: str,
) -> None:
    st.subheader("Export")
    st.caption(EXPORT_CAPTION)
    col_json, col_csv, col_pdf = st.columns(3)
    with col_json:
        st.download_button(
            json_label,
            data=json_payload,
            file_name=json_filename,
            mime="application/json",
            key=json_key,
        )
    with col_csv:
        st.button(
            "Download matrix CSV (planned)",
            disabled=True,
            help="CSV export is planned for a later story.",
            key=csv_key,
        )
    with col_pdf:
        st.button(
            "Download PDF / HTML brief (planned)",
            disabled=True,
            help="PDF/HTML export is planned for a later story.",
            key=pdf_key,
        )


def render_oracle_check(computed: Recommendation, expected: Recommendation) -> None:
    matched = (
        computed.category == expected.category
        and computed.human_review_required == expected.human_review_required
    )
    if matched:
        st.success(
            f"**Computed vs expected:** MATCH (`{computed.category.value}` / "
            f"human_review={computed.human_review_required})"
        )
    else:
        st.error(
            f"**Computed vs expected:** MISMATCH — computed `{computed.category.value}` "
            f"(review={computed.human_review_required}) vs expected `{expected.category.value}` "
            f"(review={expected.human_review_required})"
        )


def render_recommendation_banner(rec: Recommendation, scenario: str) -> None:
    cat_label = CATEGORY_LABELS[rec.category]
    review_badge = (
        "HUMAN REVIEW REQUIRED" if rec.human_review_required else "AUTO-VERIFIED (NO HUMAN REVIEW REQUIRED)"
    )
    header_text = (
        f"**Computed Recommendation: `{cat_label}`** &nbsp;|&nbsp; "
        f"**Confidence:** `{rec.confidence:.0%}` &nbsp;|&nbsp; "
        f"**Gate:** `{review_badge}`\n\n"
        f"{rec.explanation}\n\n"
        f"*Scenario:* {scenario}"
    )
    if rec.human_review_required:
        st.warning(header_text)
    elif rec.category == RecommendationCategory.RECLAIM:
        st.success(header_text)
    elif rec.category == RecommendationCategory.DISPOSE:
        st.error(header_text)
    else:
        st.info(header_text)


def render_item_inspector(report: RecommendationReport) -> None:
    rec = report.recommendation
    render_recommendation_banner(rec, report.scenario)
    render_oracle_check(rec, report.expected_recommendation)

    col_item, col_life = st.columns(2)
    chars = report.item.public_characteristics

    with col_item:
        with st.container(border=True):
            origin_tag = report.origin_label
            st.subheader(f"Item & Classification (`Item` — {origin_tag})")
            meta_rows = [
                ("Public Item ID / NSN", report.item.public_item_id),
                ("NIIN", chars.get("NIIN", "Synthetic")),
                ("Item Name", report.item.name),
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
                ("Item Evidence Quality", report.item.evidence_quality.value),
                ("Source Record ID", report.item.source_record_id or str(report.item.source_url)),
                ("License / Reuse Status", report.item.license_or_reuse_status),
                ("Synthetic", "Yes" if report.item.is_synthetic else "No"),
            ]
            st.dataframe(
                pd.DataFrame(meta_rows, columns=["Attribute", "Value"]),
                hide_index=True,
                use_container_width=True,
            )

    with col_life:
        with st.container(border=True):
            st.subheader("Warehouse Lifecycle & Characteristic Reply (`LifecycleEvent`)")
            lifecycle = report.lifecycle_event
            life_rows = [
                ("Lifecycle Event ID", lifecycle.event_id),
                ("Event Type", lifecycle.event_type.value),
                ("Warehouse Condition", lifecycle.condition.value.upper()),
                ("Quantity", f"{lifecycle.quantity} {lifecycle.quantity_unit}"),
                ("Generic Location Code", lifecycle.generic_location_code),
                ("Timestamp (UTC)", lifecycle.timestamp.isoformat()),
                ("Provenance Source", f"{lifecycle.source_name} ({lifecycle.source_record_id})"),
                (
                    "Synthetic Flag",
                    f"is_synthetic={lifecycle.is_synthetic} ({lifecycle.license_or_reuse_status})",
                ),
            ]
            st.dataframe(
                pd.DataFrame(life_rows, columns=["Attribute", "Value"]),
                hide_index=True,
                use_container_width=True,
            )
            mrc_label, mrc_text = extract_mrc_summary(chars)
            st.caption(f"Raw Characteristic Reply ({mrc_label})")
            st.code(mrc_text, language="text")
            st.caption(report.source_notes)

    st.markdown("#### Material Composition Evidence & USGS 2025 Criticality Match (`CompositionEvidence`)")
    if report.materials:
        ev_rows = [
            {
                "Material ID": material.material_id,
                "Material Name": material.material_name,
                "USGS 2025 Critical Mineral": "Yes (2025)" if material.usgs_match else "No",
                "Rare Earth (REE)": "Yes (REE)" if material.is_rare_earth_element else "No",
                "Measured Amount": material.measured_amount,
                "Value Basis": material.value_basis.value,
                "Evidence Quality": material.evidence_quality.value,
                "Synthetic": material.is_synthetic,
                "Source Record ID": material.source_record_id or "",
                "Source Name": material.source_name,
            }
            for material in report.materials
        ]
        st.dataframe(pd.DataFrame(ev_rows), hide_index=True, use_container_width=True)
        st.caption(
            "A USGS 2025 list match is a material assertion, not confirmed composition. "
            "The engine treats composition as confirmed only when `evidence_quality=confirmed` "
            "and `value_basis` is not `inferred`."
        )
    else:
        st.info(
            "No critical, strategic, or precious material assertions (`materials = []`). "
            "This item serves as a non-metallic negative control and routes to `DISPOSE`."
        )

    if report.recovery_method or report.value_estimate:
        col_rec, col_val = st.columns(2)
        with col_rec:
            if report.recovery_method:
                recovery = report.recovery_method
                with st.container(border=True):
                    st.subheader("Documented Recovery Method (`RecoveryMethod`)")
                    st.markdown(
                        f"- **Method ID:** `{recovery.recovery_method_id}` "
                        f"(Target Material: `{recovery.material_id}`)\n"
                        f"- **Process:** {recovery.process_name}\n"
                        f"- **Expected Yield:** `{recovery.expected_yield:.0%}`\n"
                        f"- **Handling Notes:** {recovery.handling_notes or 'None'}\n"
                        f"- **Provenance:** {recovery.source_name} "
                        f"(`{recovery.source_record_id}`, `{recovery.license_or_reuse_status}`)\n"
                        f"- **Synthetic:** `{recovery.is_synthetic}`"
                    )
        with col_val:
            if report.value_estimate:
                estimate = report.value_estimate
                net_val = estimate.reference_value - estimate.recovery_cost
                with st.container(border=True):
                    st.subheader("Illustrative Value Estimate (`ValueEstimate`)")
                    st.markdown(
                        f"- **Estimate ID:** `{estimate.estimate_id}` "
                        f"(`is_illustrative={estimate.is_illustrative}`)\n"
                        f"- **Material & Quantity:** `{estimate.quantity} {estimate.quantity_unit}` "
                        f"of `{estimate.material_id}`\n"
                        f"- **Gross Reference Value:** `${estimate.reference_value} {estimate.currency}`\n"
                        f"- **Estimated Recovery Cost:** `${estimate.recovery_cost} {estimate.currency}`\n"
                        f"- **Net Illustrative Margin:** `${net_val:+.2f} {estimate.currency}` "
                        f"(Calc Date: `{estimate.calculation_date}`)\n"
                        f"- **Synthetic:** `{estimate.is_synthetic}`"
                    )

    with st.expander("View Executed Rules, Audit Trail & Presentation JSON"):
        col_audit, col_report = st.columns(2)
        with col_audit:
            st.markdown("**Engine `AuditEvent` (`rules_executed` from `recommend_item`)**")
            st.json(report.audit_event.model_dump(mode="json"))
        with col_report:
            st.markdown("**`RecommendationReport` presentation dump (`cmr.reporting`)**")
            st.json(report.model_dump(mode="json"))


def render_human_review_simulator(report: RecommendationReport) -> None:
    rec = report.recommendation
    st.subheader(f"Interactive Human Review & Audit Simulator — {report.test_case_id} ({report.item.name})")
    if rec.human_review_required:
        st.warning(
            f"`{report.test_case_id}` (`{report.item.public_item_id}`) triggered a mandatory **Human Review Gate** "
            f"(`human_review_required=True`). Reason: {rec.explanation}"
        )
    else:
        st.info(
            f"`{report.test_case_id}` (`{report.item.public_item_id}`) did not require mandatory human review "
            "(`human_review_required=False`), but you can still simulate a supervisor or specialist override below."
        )

    default_reason = (
        "Confirmed '16.750 IN. APPROX. LG OF LEAD' refers to electrical wire length, not elemental lead; "
        "INC 77777 logged for catalog follow-up."
        if report.test_case_id == "TC-02"
        else (
            "Hazardous Material Indicator HMIC=P (Copper Alloy 170/172 beryllium hazard) verified; "
            "route to certified beryllium-safe reclamation handler."
            if report.test_case_id == "TC-03"
            else f"Reviewed supporting evidence and approved {rec.category.value} disposition."
        )
    )

    with st.form(key=f"review_form_{report.test_case_id}"):
        col_a, col_b = st.columns(2)
        with col_a:
            role_choice = st.selectbox(
                "Reviewer Role (`ReviewerRole`)",
                options=[r.value for r in ReviewerRole],
                index=2 if report.test_case_id == "TC-03" else 0,
            )
        with col_b:
            outcome_choice = st.selectbox(
                "Review Decision Outcome (`ReviewOutcome`)",
                options=[o.value for o in ReviewOutcome],
                index=2 if report.test_case_id in {"TC-02", "TC-03"} else 0,
            )
        reason_text = st.text_area(
            "Review Justification (`reason`)",
            value=default_reason,
        )
        submitted = st.form_submit_button("Validate & Record ReviewDecision + AuditEvent")

    justification = reason_text.strip()
    if submitted and not justification:
        st.error("A review reason is required.")
    elif justification and (submitted or rec.human_review_required):
        now = datetime.now(timezone.utc)
        review_record = ReviewDecision(
            review_id=f"REV-{report.test_case_id}-001",
            recommendation_id=rec.recommendation_id,
            reviewer_role=ReviewerRole(role_choice),
            decision=ReviewOutcome(outcome_choice),
            reason=justification,
            timestamp=now,
        )
        audit_record = AuditEvent(
            audit_id=f"AUD-REV-{report.test_case_id}-001",
            analysis_id=report.audit_event.analysis_id,
            action=f"human_review_{review_record.decision.value}",
            rules_executed=list(report.audit_event.rules_executed)
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


def render_summary_view(
    summary: DashboardSummary,
    reports: list[RecommendationReport],
) -> None:
    st.subheader("Recommendation Summary")
    st.caption(
        "Dashboard numbers are computed from `cmr.reporting.DashboardSummary` over the 9-item benchmark. "
        "PUB LOG ingest funnel counts belong in README documentation, not as live KPIs."
    )

    top = st.columns(5)
    top[0].metric("Items analyzed", str(summary.items_analyzed))
    top[1].metric("Human review", str(summary.human_review_count))
    top[2].metric("Auto-verified", str(summary.auto_verified_count))
    top[3].metric("PUB LOG items", str(summary.public_item_count))
    top[4].metric("Synthetic items", str(summary.synthetic_item_count))

    category_cols = st.columns(len(RecommendationCategory))
    for column, category in zip(category_cols, RecommendationCategory, strict=True):
        column.metric(CATEGORY_LABELS[category], str(summary.counts_by_category[category.value]))

    chart_top = st.columns(2)
    with chart_top[0]:
        st.markdown("#### Recommendation mix")
        st.bar_chart(category_chart_frame(summary), x="Recommendation Category", y="Test Case Count")
    with chart_top[1]:
        st.markdown("#### Review load")
        st.bar_chart(review_chart_frame(summary), x="Review Status", y="Count")

    chart_bottom = st.columns(2)
    with chart_bottom[0]:
        st.markdown("#### Item origin")
        st.bar_chart(origin_chart_frame(summary), x="Origin", y="Count")
    with chart_bottom[1]:
        st.markdown("#### USGS 2025 mineral assertions")
        material_df = material_chart_frame(summary)
        if material_df.empty:
            st.info("No material assertions in the current summary.")
        else:
            st.caption("Counts are composition assertions, not distinct items.")
            st.bar_chart(material_df, x="USGS 2025 Critical Mineral", y="Assertion Count")

    st.markdown("#### Benchmark items")
    st.dataframe(build_compact_table(reports), hide_index=True, use_container_width=True)

    render_export_placeholders(
        json_label="Download dashboard JSON",
        json_filename="cmr-dashboard-summary.json",
        json_payload=summary.model_dump_json(indent=2),
        json_key="download-dashboard-json",
        csv_key="summary-csv-planned",
        pdf_key="summary-pdf-planned",
    )


def filter_reports(
    reports: list[RecommendationReport],
    *,
    category_filter: str,
    origin_filter: str,
    only_review: bool,
    search_query: str,
) -> list[RecommendationReport]:
    filtered: list[RecommendationReport] = []
    for report in reports:
        rec = report.recommendation
        if category_filter != "All" and rec.category.value != category_filter:
            continue
        if origin_filter == ORIGIN_PUB_LOG and report.item.is_synthetic:
            continue
        if origin_filter == ORIGIN_SYNTHETIC and not report.item.is_synthetic:
            continue
        if only_review and not rec.human_review_required:
            continue
        if search_query:
            haystack = " ".join(
                [
                    report.test_case_id,
                    report.item.public_item_id,
                    report.item.name,
                    report.scenario,
                    " ".join(report.item.public_characteristics.values()),
                    " ".join(material.material_id for material in report.materials),
                ]
            ).lower()
            if search_query not in haystack:
                continue
        filtered.append(report)
    return filtered


def render_detailed_view(reports: list[RecommendationReport]) -> None:
    st.sidebar.header("Benchmark Controls")
    category_filter = st.sidebar.selectbox(
        "Filter by Computed Recommendation",
        options=["All"] + [category.value for category in RecommendationCategory],
        index=0,
    )
    origin_filter = st.sidebar.radio(
        "Item Origin",
        options=["All", ORIGIN_PUB_LOG, ORIGIN_SYNTHETIC],
        index=0,
    )
    only_review = st.sidebar.checkbox("Only items requiring Human Review", value=False)
    search_query = st.sidebar.text_input("Search by NSN, NIIN, Name, or Material", value="").strip().lower()

    filtered_reports = filter_reports(
        reports,
        category_filter=category_filter,
        origin_filter=origin_filter,
        only_review=only_review,
        search_query=search_query,
    )
    if not filtered_reports:
        st.warning("No test cases match the current sidebar filters; showing all benchmark items.")
        active_reports = reports
    else:
        active_reports = filtered_reports

    case_options = {
        f"{report.test_case_id} | {report.item.public_item_id} — {report.item.name} "
        f"[{report.recommendation.category.value.upper()}]": report
        for report in active_reports
    }
    selected_label = st.sidebar.selectbox(
        "Select Test Case to Inspect",
        options=list(case_options.keys()),
    )
    selected_report = case_options[selected_label]

    st.subheader(f"Detailed Analytics — {selected_report.test_case_id}")
    render_export_placeholders(
        json_label="Download selected-case JSON",
        json_filename=f"cmr-report-{selected_report.test_case_id}.json",
        json_payload=selected_report.model_dump_json(indent=2),
        json_key="download-case-json",
        csv_key="detail-csv-planned",
        pdf_key="detail-pdf-planned",
    )

    tab_inspector, tab_matrix, tab_review = st.tabs(
        [
            f"Item report ({selected_report.test_case_id})",
            f"Comparison matrix ({len(filtered_reports)}/{len(reports)})",
            "Human review simulator",
        ]
    )
    with tab_inspector:
        render_item_inspector(selected_report)
    with tab_matrix:
        st.markdown("#### Curated benchmark comparison matrix")
        st.dataframe(build_overview_dataframe(active_reports), hide_index=True, use_container_width=True)
    with tab_review:
        render_human_review_simulator(selected_report)


def main() -> None:
    st.set_page_config(
        page_title="CMR Decision-Support Prototype",
        layout="wide",
    )
    dataset, reports, summary = load_reports()

    st.title("Critical Materials Recovery - Decision-Support Prototype")
    st.caption(
        "Explainable decision-support demonstration linking public DLA PUB LOG catalog items, "
        "synthetic operational states, and the USGS 2025 Critical Minerals List."
    )

    view = st.segmented_control(
        "Dashboard view",
        options=[VIEW_SUMMARY, VIEW_DETAILED],
        default=VIEW_SUMMARY,
        key="dashboard_view",
    ) or VIEW_SUMMARY

    st.sidebar.caption(
        f"**Dataset ID:** `{dataset.dataset_id}`\n\n"
        f"**Generated:** `{dataset.generated_date}`\n\n"
        "**Guardrail:** AI-generated or lexical inferences are never treated as confirmed "
        "composition without a traceable source."
    )

    if view == VIEW_SUMMARY:
        render_summary_view(summary, reports)
    else:
        render_detailed_view(reports)


if __name__ == "__main__":
    main()
