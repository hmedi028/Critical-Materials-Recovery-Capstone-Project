# Data Sources

This project separates source acquisition notes from committed static reference data.

## Commit-safe static references

| Dataset | Local file | Use | Source | Retrieval |
|---|---|---|---|---|
| USGS 2025 List of Critical Minerals | `data/static/usgs/critical_minerals_2025.csv` and `.json` | Versioned criticality reference for material comparison rules | https://www.usgs.gov/programs/mineral-resources-program/science/about-2025-list-critical-minerals | 2026-09-13 |

## Candidate ingestion sources

| Source | Role in prototype | Handling notes |
|---|---|---|
| PUB LOG / FLIS public logistics data | Public item records: identifiers, names, classifications, characteristics, reference relationships | Keep acquisition script separate from committed bulk files. Confirm redistribution terms before committing any original extracts. |
| USGS Mineral Commodity Summaries | Context for uses, production, supply-risk discussion, historical annual values | Treat annual values as reference context, not live commodity prices. |
| NIST Materials Data Repository | Optional materials-property or research datasets | Check license per selected record; public availability does not imply uniform reuse rights. |
| Synthetic bills of materials and lifecycle events | Demo-only item composition, quantities, recovery yields, costs, and review decisions | Clearly label generated data; avoid copying or perturbing restricted/proprietary records. |

## Provenance fields to preserve

Every imported or generated record should carry at least:

- `source_name`
- `source_url` or stable source record identifier
- `retrieved_date` or `generated_date`
- `license_or_reuse_status`
- `evidence_quality`
- `is_synthetic`

## Repository data layout

```text
data/
  static/      # small committed reference tables used by rules/tests
  raw/         # uncommitted source downloads or local extracts
  processed/   # normalized generated outputs, usually reproducible
  synthetic/   # committed/generated demo-safe records
  schemas/     # JSON schema or data contracts
```

## PUB LOG Pipeline Validation — Card #616

### Source and processing

- **Source:** Defense Logistics Agency (DLA), PUB LOG / FLIS public logistics data.
- **Characteristics source file:** `V_CHARACTERISTICS.CSV`, downloaded from the DLA PUB LOG data page.
- **Reference list:** USGS 2025 List of Critical Minerals, stored at `data/static/usgs/critical_minerals_2025.csv`.
- **Processing:** Stage 2 scans characteristics records for candidate NIINs and material terms; Stage 3 filters item and identification records for the selected NIINs.
- **Source text retention:** `selected_material_evidence.csv` preserves `REQUIREMENTS_STATEMENT` and `CLEAR_TEXT_REPLY` for manual review.

### Validation results

| Check | Observed result |
|---|---:|
| Stage 2 source rows read | 38,936,663 |
| Stage 2 candidate NIINs | 5,613 |
| Stage 2 evidence rows | 4,169 |
| Stage 2 selected NIINs | 1,625 |
| Unique NIINs in evidence | 1,636 |
| Evidence NIINs absent from selected list | 11 |
| Stage 3 selected item rows | 1,625 |
| Stage 3 identification rows | 1,625 |
| Duplicate NIINs in each Stage 3 output | 0 |
| Selected NIINs missing from either Stage 3 output | 0 |

The 11 NIINs present in the evidence output but absent from the selected list had discovery-only matches for terms such as `alloy`, `coating`, or `plating`. The pipeline does not add discovery-only matches to the selected NIIN set.

### Manual review and interpretation

A deterministic sample of 15 material-specific evidence rows was reviewed. The sample included plausible matches in item descriptions, conductor material fields, and chemical-composition records. Some records mentioned trace constituents or impurity limits, so the presence of a matched word alone does not establish that a material is a primary component or is economically recoverable.

- Treat material matches as **candidate evidence**, not proof that an item contains a recoverable critical material.
- Preserve the source fields and matched term so reviewers can inspect the context.
- `CRIT_CD`, `PMIC`, `DMIL`, `HMIC`, and `HCC` are supporting identification indicators only; they do not prove material presence.
- Absence of a material term in the scanned text does not prove that the item contains no critical material.
- Stage 3 count and NIIN-set checks passed for the generated item and identification extracts.

### Outstanding validation work

- [x] Validate Stage 2–3 consistency: all 1,625 selected NIINs appear in both selected-item and identification outputs, with no missing NIINs, duplicates, or set differences.
- [x] Validate source-text retention: all 4,169 evidence rows retain non-empty `REQUIREMENTS_STATEMENT` and `CLEAR_TEXT_REPLY` values.
- [x] Review a reproducible 30-row sample: 25 VALID, 3 AMBIGUOUS, and 2 FALSE POSITIVE; labels remain preliminary pending teammate review.
- [x] Verify source-record integrity for all 5,613 current candidate NIINs: all exist in `P_FLIS_NSN.CSV`, with matching FSC and item-name values and no populated cancellation field.
- [ ] Confirm the intended Stage 1 candidate-selection scope and original provenance. The current 5,613-candidate list differs from the README's documented 1,000-candidate run; its original selection method remains unknown.
- [ ] Obtain teammate/reviewer verification of the manual-review sample.
- [ ] Obtain product-owner acceptance and record any remaining issues and corrective actions before marking Card #616 complete.

The validation script was rerun after the documentation update. It reported 1,625 selected NIINs, 4,169 evidence rows, 1,625 selected-item rows, and 1,625 identification rows. It found zero missing selected NIINs, zero item-versus-identification NIIN differences, and no duplicate NIINs in the selected NIIN, selected-item, or identification files.

Eleven evidence NIINs were not selected; all were discovery-only evidence. All 1,625 selected NIINs had specific material evidence. Both retained source-text fields were non-empty in all 4,169 evidence rows.

These checks establish pipeline-output consistency and source-text retention, not material composition or recoverability. Identification codes remain supporting indicators only. Card #616 is not fully complete until the Stage 1 provenance issue is resolved or explicitly accepted by the product owner, and the required reviews are recorded.
### Manual Material-Match Sample Review

A reproducible sample of 30 rows was drawn from
`data/processed/selected_material_evidence.csv` using pandas
with `random_state=616`. Review labels and notes are recorded in
`data/processed/material_match_manual_review.csv`.

Preliminary review summary:
- Rows reviewed: 30
- Labeled VALID: 25
- Labeled FALSE POSITIVE: 2
- Labeled AMBIGUOUS: 3

The review compares each matched term with its retained source text.
A keyword match can be textually supported without proving that a
material is recoverable, economically significant, or present in a
finished item in a meaningful quantity. Trace constituents and
impurity limits require particular care. Generic discovery terms such
as "coating" and "alloy" do not independently identify a specific
critical material.

These labels are preliminary, text-based judgments and should be
verified during teammate review. The 30-row sample is not sufficient
to establish the pipeline's overall false-positive rate. Matches are
candidate evidence, not proof of material presence or recoverability.
CRIT_CD, PMIC, DMIL, HMIC, and HCC are supporting indicators only;
their values and the absence of a material keyword do not establish
whether critical material is present or absent.

### Stage 1 Candidate Provenance — Open Issue

The current `data/processed/candidate_niins.csv` contains 5,613 rows and 5,613 unique NIINs across 283 FSC categories. Its recorded filesystem timestamp is 2026-10-11 22:03:06.

**Source-record integrity is verified:** all 5,613 candidate NIINs were found in `P_FLIS_NSN.CSV`, and all matched records have identical FSC and item-name values. None of the matched source records has a populated cancellation field.

The current `src/cmr/ingest_publog.py` defaults to four FSCs (5960, 5998, 6140, and 2840), excludes cancelled NIINs, and limits output to 1,000 distinct NIINs. Its actual default output is `data/processed/candidate_niins_nsn.csv`. The CLI help text has been corrected to identify the same output path.

The separate `data/processed/candidate_niins.csv` contains 5,613 rows and 5,613 unique NIINs across 283 FSC categories. Its source-record integrity is verified, but its original selection process and intended scope remain unresolved. Matching source records verifies data integrity, not the criteria used to select the candidates.

The README documents a 1,000-candidate run producing 40 evidence rows and 19 selected NIINs. The current processed outputs contain 5,613 candidates, 4,169 evidence rows, and 1,625 selected NIINs.

The candidate dataset's Git history identifies commit `ba04366319f116d285629aa6fd8b705a52267b14`, authored by `hmedi028` on September 27, 2026, with the message "Add candidate NIIN dataset from P_FLIS_NSN." The commit adds `data/processed/candidate_niins.csv` but does not document its generation settings. The parent version of `src/cmr/ingest_publog.py` used this filename by default, but its default limit was 1,000 distinct NIINs and its target FSCs were 5960, 5998, 6140, and 2840.

The original selection process for the 5,613-row dataset therefore remains unresolved. The commit establishes when and by whom the file was added, not which limit, filters, or process generated it. Confirmation from the dataset author is needed before the intended Stage 1 scope can be considered verified.

**Status: partially verified; selection provenance unresolved.**

Do not replace the existing candidate list or downstream outputs until the intended Stage 1 scope is confirmed. For the next reproducible run, record the script version, input path, FSC filters, limit, output path, candidate count, and downstream counts. Preserve the existing outputs when testing an alternative scope.

Card #616 must also retain the documented manual-review limitations and obtain teammate/reviewer and product-owner acceptance before being marked fully complete.