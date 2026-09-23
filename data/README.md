# Data Directory

- `static/`: small, versioned reference datasets safe to commit.
- `raw/`: local source downloads; do not commit bulk/raw files unless their redistribution terms are confirmed.
- `processed/`: local normalized outputs created by scripts (gitignored), including `candidate_niins.csv` from `python -m cmr.ingest_publog`.
- `synthetic/`: reserved for generated demo records. None are committed yet.
- `schemas/`: JSON Schema contracts exported from `src/cmr` models.

Start with `static/usgs/critical_minerals_2025.csv` as the criticality reference table for rule development.
