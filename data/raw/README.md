# Raw Data

Place local source downloads here while developing ingestion scripts.

Do not commit original PUB LOG/FLIS bulk files or other substantial source extracts until the team has confirmed current redistribution terms and license/reuse status.

## PUB LOG / FLIS (local only)

Extract `P_FLIS_NSN.CSV` here (or pass `--input` to `python -m cmr.ingest_publog`). This folder is gitignored.

The Stage 1 FSC candidate slice is written to `data/processed/candidate_niins_nsn.csv`, which is also gitignored.

For Stage 2, leave `CHARACTERISTICS.zip` in `~/Downloads` (or pass `--input`). Do not copy `V_CHARACTERISTICS.CSV` (~3 GB) into this folder or commit it. Run:

```bash
python -m cmr.ingest_characteristics --input ~/Downloads/CHARACTERISTICS.zip
```

Stage 2 writes `data/processed/selected_material_evidence.csv` and `data/processed/selected_niins.csv`.
