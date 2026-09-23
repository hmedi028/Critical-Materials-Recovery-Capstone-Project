# Raw Data

Place local source downloads here while developing ingestion scripts.

Do not commit original PUB LOG/FLIS bulk files or other substantial source extracts until the team has confirmed current redistribution terms and license/reuse status.

## PUB LOG / FLIS (local only)

Extract `P_FLIS_NSN.CSV` here (or pass `--input` to `python -m cmr.ingest_publog`). This folder is gitignored.

The Stage 1 candidate slice is written to `data/processed/candidate_niins.csv`, which is also gitignored.
