# Critical Materials Recovery Capstone Project

Open-source decision-support prototype that helps identify cataloged surplus, obsolete, damaged, or unserviceable items that may contain critical, strategic, precious, or otherwise valuable materials.

Manual research across public catalogs, technical descriptions, and commodity references is slow and inconsistent. This project organizes public and synthetic data in a knowledge graph, applies transparent classification rules, and presents recommendations for human review.

The system will not treat an AI-generated inference as a confirmed material composition unless it is supported by a traceable source.

## What it will do

1. Accept a public item identifier or item description.
2. Retrieve matching public catalog information (PUB LOG or another approved source).
3. Connect the item to known or inferred material information.
4. Compare those materials with a versioned critical-minerals reference (for example, the USGS list).
5. Recommend retain, reclaim, recycle, manual review, or ordinary disposal.
6. Show the evidence, rules, uncertainty, and source provenance behind the recommendation.

Human review is required when composition is inferred, evidence is incomplete, sources conflict, or a potentially hazardous material is identified.

## Current data organization

- `docs/data-sources.md` — source plan, handling notes, and provenance fields.
- `data/static/usgs/critical_minerals_2025.csv` — committed USGS 2025 critical-minerals reference table.
- `data/raw/` — local-only source downloads (for example `P_FLIS_NSN.CSV`). Gitignored.
- `data/processed/` — local ingest outputs such as `candidate_niins.csv`. Gitignored.
- `data/synthetic/` — reserved for generated demo records. No corpus is committed yet.
- `data/schemas/` — JSON Schema contracts exported from the Pydantic models.

## Entity & Schema Architecture

All 12 PDF entities have a matching Pydantic model with a deterministic 1:1 mapping to exported JSON Schema definitions:

| PDF entity | Pydantic class | Source file | Exported JSON Schema |
| :--- | :--- | :--- | :--- |
| Item | `Item` | `src/cmr/models/item.py` | `data/schemas/item.json` |
| Component | `Component` | `src/cmr/models/component.py` | `data/schemas/component.json` |
| Material | `Material` | `src/cmr/models/material.py` | `data/schemas/material.json` |
| Composition evidence | `CompositionEvidence` | `src/cmr/models/composition.py` | `data/schemas/composition_evidence.json` |
| Criticality reference | `CriticalityReference` | `src/cmr/models/material.py` | `data/schemas/criticality_reference.json` |
| Lifecycle event | `LifecycleEvent` | `src/cmr/models/lifecycle.py` | `data/schemas/lifecycle_event.json` |
| Recovery method | `RecoveryMethod` | `src/cmr/models/recovery.py` | `data/schemas/recovery_method.json` |
| Value estimate | `ValueEstimate` | `src/cmr/models/value_estimate.py` | `data/schemas/value_estimate.json` |
| Recommendation | `Recommendation` | `src/cmr/models/recommendation.py` | `data/schemas/recommendation.json` |
| Review decision | `ReviewDecision` | `src/cmr/models/review.py` | `data/schemas/review_decision.json` |
| Provenance record | `Provenance` | `src/cmr/models/provenance.py` | `data/schemas/provenance.json` |
| Audit event | `AuditEvent` | `src/cmr/models/audit.py` | `data/schemas/audit_event.json` |

## First static reference

The initial committed static dataset is the USGS 2025 List of Critical Minerals, captured from the USGS reference page on 2026-09-13:

- 60 critical minerals
- 15 marked as rare earth elements in the USGS graphic/page context
- CSV and JSON versions are stored under `data/static/usgs/`

## Python setup

Python 3.12 or newer is required. Create a local virtualenv, then install the package and dev tools:

```bash
python3.12 -m venv .venv
# If python3.12 is not installed, use: python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

`.venv/` is gitignored and must not be committed.

To regenerate the committed JSON Schema files after model changes:

```bash
python -m cmr.export_schemas
```

To slice a local PUB LOG `P_FLIS_NSN.CSV` into a candidate NIIN list (does not commit the bulk file):

```bash
python -m cmr.ingest_publog
# or: python -m cmr.ingest_publog --input /path/to/P_FLIS_NSN.CSV --limit 1000
```

To scan `V_CHARACTERISTICS.CSV` in chunks (Stage 2). The zip can stay in `~/Downloads`; do not commit the ~3 GB extract:

```bash
python -m cmr.ingest_characteristics
# or: python -m cmr.ingest_characteristics --input ~/Downloads/CHARACTERISTICS.zip
```

Writes `data/processed/selected_material_evidence.csv` and `data/processed/selected_niins.csv`. Matches are candidate evidence, not a bill of materials.

To reduce `P_FLIS_NSN.CSV` and `V_FLIS_IDENTIFICATION.CSV` to those selected NIINs (Stage 3). Leave `Identification.zip` in `~/Downloads`; do not commit the 16M-row extract:

```bash
python -m cmr.ingest_selected
# or: python -m cmr.ingest_selected --items data/raw/P_FLIS_NSN.CSV --identification ~/Downloads/Identification.zip
```

Writes `data/processed/selected_items.csv` (includes 13-digit `NSN` = FSC + NIIN) and `data/processed/selected_identification.csv`. Identification codes are supporting clues, not material proof.

Recorded local run counts (processed CSVs stay gitignored):

| Stage | Input | Output |
| :--- | :--- | :--- |
| 1 | `P_FLIS_NSN.CSV` | 1,000 candidate NIINs (`candidate_niins_nsn.csv`) |
| 2 | 38,936,531 characteristics rows | 40 evidence rows; 19 selected NIINs |
| 3 | selected NIINs vs `P_FLIS_NSN.CSV` and `V_FLIS_IDENTIFICATION.CSV` | 19 `selected_items.csv` rows; 19 `selected_identification.csv` rows |

Join key across extracts is `NIIN`. Sample review: NIIN `000030837` matched `lead` on “LG OF LEAD” (electrical lead length), not the metal.

## Environment variables

Copy `.env.example` to `.env` and add keys as integrations are added. 

```bash
cp .env.example .env
```

## License

This project uses the MIT License. See `LICENSE`.

Data files may have separate source-specific reuse terms. Preserve `license_or_reuse_status` fields and source notes when importing or generating data.

## Development guardrails

- Do not commit secrets, credentials, internal operational data, personal data, or restricted technical data.
- Treat PUB LOG as publicly releasable catalog data, not automatically open-source licensed data.
- Keep raw source downloads out of git unless redistribution terms are verified.
- Mark generated demonstration records as synthetic.
