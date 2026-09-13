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
- `data/raw/` — local-only source downloads for ingestion development.
- `data/synthetic/` — generated demo-safe records.
- `data/schemas/` — future validation contracts.

## First static reference

The initial committed static dataset is the USGS 2025 List of Critical Minerals, captured from the USGS reference page on 2026-09-13:

- 60 critical minerals
- 15 marked as rare earth elements in the USGS graphic/page context
- CSV and JSON versions are stored under `data/static/usgs/`

## Environment variables

Copy `.env.example` to `.env` and add keys as integrations are added. `.env` is gitignored and must never be committed.

```bash
cp .env.example .env
```

## Development guardrails

- Do not commit secrets, credentials, internal operational data, personal data, or restricted technical data.
- Treat PUB LOG as publicly releasable catalog data, not automatically open-source licensed data.
- Keep raw source downloads out of git unless redistribution terms are verified.
- Mark generated demonstration records as synthetic.
