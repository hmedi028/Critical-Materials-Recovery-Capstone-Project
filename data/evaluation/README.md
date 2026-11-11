# Evaluation Dataset and Expected Outcomes

## Purpose
This evaluation dataset supports reproducible testing of the Critical Materials Recovery recommendation workflow. It uses the existing synthetic demonstration corpus rather than generating duplicate records.

## Dataset
The source records are located in `data/synthetic/`. The corpus contains 100 synthetic item records and associated component, composition evidence, lifecycle event, recommendation, and human review records.

The USGS 2025 Critical Minerals List in `data/static/usgs/` is used as a public reference for material names. Item descriptions, bills of materials, lifecycle events, and recommendations in the synthetic corpus are not real-world observations.

## Expected Outcome Categories
Expected outcomes are documented using these scenario-level guidelines:

- **retain:** The item is serviceable and does not have a demonstrated priority for material recovery.
- **reclaim:** The item is unserviceable and contains a material identified for recovery in the scenario.
- **recycle:** The item is damaged and contains recyclable material without a higher-priority reclaim scenario.
- **dispose:** The item is damaged and has no identified critical or recyclable material content.
- **manual_review:** Composition evidence is inferred, incomplete, or conflicting and requires human review.

These are benchmark scenario rules, not universal disposal or recovery policies.

## Evaluation Limitations
The synthetic corpus includes recommendation records generated as part of the demonstration data. Comparing those records with expected outcomes is a consistency check, not an independent measurement of a production recommendation engine's accuracy.

Synthetic records must remain clearly identified as synthetic. Expected outcomes should be reviewed by a qualified human before being treated as operational decisions.
