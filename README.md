# Critical Materials Recovery Capstone Project

Open-source decision-support prototype that helps identify cataloged surplus, obsolete, damaged, or unserviceable items that may contain critical, strategic, precious, or otherwise valuable materials.

Manual research across public catalogs, technical descriptions, and commodity references is slow and inconsistent. This prototype links public DLA PUB LOG catalog records and synthetic operational states to the USGS 2025 Critical Minerals List, applies explicit classification rules, and presents recommendations for human review.

The system does not treat an AI-generated inference as a confirmed material composition unless it is supported by a traceable source.

[Version](CHANGELOG.md)
[Python](https://www.python.org/)
[Pydantic](https://docs.pydantic.dev/)

## Table of contents

- [What it does](#what-it-does)
- [Setup](#setup)
- [Usage](#usage)
- [Data organization](#data-organization)
- [USGS reference](#usgs-reference)
- [Development guardrails](#development-guardrails)
- [License](#license)

## What it does

The current prototype runs on a curated 9-item benchmark (7 PUB LOG profiles and 2 synthetic seeds):

1. Ingest local PUB LOG extracts (Stages 1–3 and Priority 4 classification lookups) without committing bulk source files.
2. Validate linked `Item`, `LifecycleEvent`, `CompositionEvidence`, and optional recovery/value records against the Pydantic contracts.
3. Compare material assertions with the committed USGS 2025 critical-minerals table.
4. Compute `retain`, `reclaim`, `recycle`, `manual_review`, or `dispose` with a deterministic engine (`src/cmr/recommend.py`) and an `AuditEvent` rule trace.
5. Assemble presentation objects (`src/cmr/reporting.py`) and show them in Streamlit: a chart-first **Summary** dashboard and one **Detailed Analytics** inspector for the selected case.

Human review is required when composition is inferred, evidence is incomplete, sources conflict, or a potentially hazardous material is identified. `expected_recommendation` on each test case is the benchmark oracle; the engine does not read it.

Not in this prototype yet: live lookup of an arbitrary public item ID against full PUB LOG, a knowledge graph, loading gitignored `data/processed/*.csv` into the demo, or CSV/PDF/HTML export (those controls are visible placeholders).

## Setup

Python 3.12 or newer is required.

Create a local virtualenv, then install the package:

```bash
python3.12 -m venv .venv
# If python3.12 is not installed, use: python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# Optional: install the Streamlit demo interface
pip install -e ".[demo]"
```

`.venv/` is gitignored and must not be committed.

Copy `.env.example` to `.env` and add keys as integrations are added. Do not commit secrets.

```bash
cp .env.example .env
```



## Usage

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


| Stage | Input                                                              | Output                                                              |
| ----- | ------------------------------------------------------------------ | ------------------------------------------------------------------- |
| 1     | `P_FLIS_NSN.CSV`                                                   | 1,000 candidate NIINs (`candidate_niins_nsn.csv`)                   |
| 2     | 38,936,531 characteristics rows                                    | 40 evidence rows; 19 selected NIINs                                 |
| 3     | selected NIINs vs `P_FLIS_NSN.CSV` and `V_FLIS_IDENTIFICATION.CSV` | 19 `selected_items.csv` rows; 19 `selected_identification.csv` rows |


Join key across extracts is `NIIN`. Sample review: NIIN `000030837` matched `lead` on “LG OF LEAD” (electrical lead length), not the metal.

To translate FSC, FSG, and INC on the selected items (Priority 4). Leave `V_H2_FSG.CSV`, `V_H2_FSC.CSV`, and `V_H6_NAME_INC.CSV` in `data/raw/`; do not commit them:

```bash
python -m cmr.ingest_classifications
```

Writes `data/processed/selected_items_classified.csv` (codes plus readable titles, joined on `NIIN`/`NSN`), `classification_groups.csv`, and `classification_unmatched.csv`. Lookups describe item type, not material composition.

Priority 4 local run: 19 classified items; 8 groups. Thin-slice categories present: FSG 59 (FSC `5998` boards/cards, FSC `5960` electron tubes) and FSG 28 (FSC `2840` aircraft gas-turbine components). FSC `6140` is a Stage 1 candidate class and is not in this 19-item slice. Unmatched: INC `77777` on NIIN `000030837` is not in `V_H6_NAME_INC.CSV`; the item and FSC/FSG titles were kept.

To validate the curated 9-item test dataset (`data/synthetic/test_cases.json`, documented in `[data/synthetic/README.md](data/synthetic/README.md)`) against the Pydantic contracts and USGS 2025 reference table:

```bash
python -m cmr.test_cases
python -m unittest discover -s tests
```

To compute recommendations for the 9 benchmark cases with the deterministic engine (`src/cmr/recommend.py`):

```bash
python -m cmr.recommend
```

The engine evaluates item, lifecycle, composition, and USGS 2025 inputs only. It does not read `expected_recommendation`; that field remains the benchmark oracle.

Presentation objects for the demo live in `src/cmr/reporting.py` (`RecommendationReport` per item, `DashboardSummary` for fleet totals). They compose the existing domain models and are not a 13th PDF entity; `python -m cmr.export_schemas` still writes only the 12 contracts under `data/schemas/`.

To launch the interactive Streamlit decision-support demo (`src/cmr/demo_app.py`):

```bash
streamlit run src/cmr/demo_app.py
```

The demo has two views:

- **Summary** — chart-first dashboard from `DashboardSummary` (all five recommendation categories including zeros, review load, PUB LOG vs synthetic origin, USGS mineral assertion counts) plus a compact item table.
- **Detailed Analytics** — one inspector for the selected benchmark case, a comparison matrix, and the human-review simulator.

Dashboard numbers come from `cmr.reporting`, not hard-coded ingest funnel counts. JSON download of the dashboard summary or selected-case report is a demo/presentation dump. Matrix CSV and PDF/HTML export are visible placeholders and are not implemented yet.



## Data organization

- `[data/README.md](data/README.md)` — data-directory layout and the 12-entity Pydantic / JSON Schema mapping. Presentation DTOs in `src/cmr/reporting.py` are not a 13th exported schema.
- `[data/synthetic/README.md](data/synthetic/README.md)` — curated 9-item test dataset (`data/synthetic/test_cases.json`), scenarios, and source attribution.
- `[docs/data-sources.md](docs/data-sources.md)` — source plan, handling notes, and provenance fields.
- `[docs/glossary.md](docs/glossary.md)` — PUB LOG / FLIS acronym legend (FSC, FSG, NIIN, NSN, INC).
- `data/static/usgs/critical_minerals_2025.csv` — committed USGS 2025 critical-minerals reference table.
- `data/raw/` — local-only source downloads (for example `P_FLIS_NSN.CSV`). Gitignored.
- `data/processed/` — local ingest outputs such as `candidate_niins.csv`. Gitignored.
- `data/schemas/` — JSON Schema contracts exported from the 12 PDF entity models.



## USGS reference

The initial committed static dataset is the USGS 2025 List of Critical Minerals, captured from the USGS reference page on 2026-09-13:

- 60 critical minerals
- 15 marked as rare earth elements in the USGS graphic/page context
- CSV and JSON versions are stored under `data/static/usgs/`



## Development guardrails

- Do not commit secrets, credentials, internal operational data, personal data, or restricted technical data.
- Treat PUB LOG as publicly releasable catalog data, not automatically open-source licensed data.
- Keep raw source downloads out of git unless redistribution terms are verified.
- Mark generated demonstration records as synthetic.
- Do not register `RecommendationReport` or `DashboardSummary` with `python -m cmr.export_schemas`; JSON downloads from the demo are presentation dumps, not domain contracts.



## License

This project uses the MIT License. See `LICENSE`.

Data files may have separate source-specific reuse terms. Preserve `license_or_reuse_status` fields and source notes when importing or generating data.