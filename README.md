# Critical Materials Recovery Capstone Project

Open-source decision-support prototype that helps identify cataloged surplus, obsolete, damaged, or unserviceable items that may contain critical, strategic, precious, or otherwise valuable materials.

Manual research across public catalogs, technical descriptions, and commodity references is slow and inconsistent. This project organizes public and synthetic data in a knowledge graph, applies transparent classification rules, and presents recommendations for human review.

The system will not treat an AI-generated inference as a confirmed material composition unless it is supported by a traceable source.

[![Version](https://img.shields.io/badge/version-0.3.0-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.6+-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

## Table of contents

- [What it will do](#what-it-will-do)
- [Setup](#setup)
- [Usage](#usage)
- [Data organization](#data-organization)
- [USGS reference](#usgs-reference)
- [Development guardrails](#development-guardrails)
- [License](#license)

## What it will do

1. Accept a public item identifier or item description.
2. Retrieve matching public catalog information (PUB LOG or another approved source).
3. Connect the item to known or inferred material information.
4. Compare those materials with a versioned critical-minerals reference (for example, the USGS list).
5. Recommend retain, reclaim, recycle, manual review, or ordinary disposal.
6. Show the evidence, rules, uncertainty, and source provenance behind the recommendation.

Human review is required when composition is inferred, evidence is incomplete, sources conflict, or a potentially hazardous material is identified.

## Setup

Python 3.12 or newer is required.

Create a local virtualenv, then install the package:

```bash
python3.12 -m venv .venv
# If python3.12 is not installed, use: python3 -m venv .venv
source .venv/bin/activate
pip install -e .
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

| Stage | Input | Output |
| :--- | :--- | :--- |
| 1 | `P_FLIS_NSN.CSV` | 1,000 candidate NIINs (`candidate_niins_nsn.csv`) |
| 2 | 38,936,531 characteristics rows | 40 evidence rows; 19 selected NIINs |
| 3 | selected NIINs vs `P_FLIS_NSN.CSV` and `V_FLIS_IDENTIFICATION.CSV` | 19 `selected_items.csv` rows; 19 `selected_identification.csv` rows |

Join key across extracts is `NIIN`. Sample review: NIIN `000030837` matched `lead` on “LG OF LEAD” (electrical lead length), not the metal.

To translate FSC, FSG, and INC on the selected items (Priority 4). Leave `V_H2_FSG.CSV`, `V_H2_FSC.CSV`, and `V_H6_NAME_INC.CSV` in `data/raw/`; do not commit them:

```bash
python -m cmr.ingest_classifications
```

Writes `data/processed/selected_items_classified.csv` (codes plus readable titles, joined on `NIIN`/`NSN`), `classification_groups.csv`, and `classification_unmatched.csv`. Lookups describe item type, not material composition.

Priority 4 local run: 19 classified items; 8 groups. Thin-slice categories present: FSG 59 (FSC `5998` boards/cards, FSC `5960` electron tubes) and FSG 28 (FSC `2840` aircraft gas-turbine components). FSC `6140` is a Stage 1 candidate class and is not in this 19-item slice. Unmatched: INC `77777` on NIIN `000030837` is not in `V_H6_NAME_INC.CSV`; the item and FSC/FSG titles were kept.

## Data organization

- `data/README.md` — data-directory layout and the 12-entity Pydantic / JSON Schema mapping.
- `docs/data-sources.md` — source plan, handling notes, and provenance fields.
- `docs/glossary.md` — PUB LOG / FLIS acronym legend (FSC, FSG, NIIN, NSN, INC).
- `data/static/usgs/critical_minerals_2025.csv` — committed USGS 2025 critical-minerals reference table.
- `data/raw/` — local-only source downloads (for example `P_FLIS_NSN.CSV`). Gitignored.
- `data/processed/` — local ingest outputs such as `candidate_niins.csv`. Gitignored.
- `data/synthetic/` — reserved for generated demo records. No corpus is committed yet.
- `data/schemas/` — JSON Schema contracts exported from the Pydantic models.

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

## License

This project uses the MIT License. See `LICENSE`.

Data files may have separate source-specific reuse terms. Preserve `license_or_reuse_status` fields and source notes when importing or generating data.
