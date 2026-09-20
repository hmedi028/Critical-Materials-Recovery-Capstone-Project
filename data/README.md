# Data Directory

- `static/`: small, versioned reference datasets safe to commit.
- `raw/`: local source downloads; do not commit bulk/raw files unless their redistribution terms are confirmed.
- `processed/`: normalized outputs created by scripts.
- `synthetic/`: generated demo records with no personal, restricted, or proprietary content. CC0 evaluation corpus of 100 labeled items; regenerate with `python -m cmr.generate_synthetic`.
- `schemas/`: JSON Schema contracts exported from `src/cmr` models.

Start with `static/usgs/critical_minerals_2025.csv` as the criticality reference table for rule development.
