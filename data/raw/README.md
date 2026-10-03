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

For Stage 3, leave `Identification.zip` in `~/Downloads` (or pass `--identification`). Do not copy `V_FLIS_IDENTIFICATION.CSV` into this folder or commit it. Run:

```bash
python -m cmr.ingest_selected --items data/raw/P_FLIS_NSN.CSV --identification ~/Downloads/Identification.zip
```

Stage 3 writes `data/processed/selected_items.csv` and `data/processed/selected_identification.csv`. Recorded local counts: 1,000 Stage 1 candidates; Stage 2 read 38,936,531 characteristics rows and kept 40 evidence rows / 19 NIINs; Stage 3 wrote 19 item rows and 19 identification rows. Sample review: NIIN `000030837` `lead` is electrical lead length, not the metal. Join key is `NIIN`.
