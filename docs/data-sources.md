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
