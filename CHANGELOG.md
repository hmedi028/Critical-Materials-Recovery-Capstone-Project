# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.4.0] - 2026-10-13

### Added

- Curated 9-item benchmark test dataset (`data/synthetic/test_cases.json`) combining all 7 distinct public DLA PUB LOG item profiles (`TC-01` through `TC-07`) with 2 synthetic seed items (`TC-08` NiMH battery with rare-earth lanthanum and `TC-09` non-metallic phenolic spacer negative control).
- Test-case loader and contract validator (`src/cmr/test_cases.py`, runnable via `python -m cmr.test_cases`) verifying Pydantic v2 schemas (`Item`, `LifecycleEvent`, `CompositionEvidence`, `RecoveryMethod`, `ValueEstimate`, `Recommendation`), referential integrity, and USGS 2025 critical-mineral references.
- Automated unit test suite (`tests/test_test_cases.py`, runnable via `python -m unittest discover -s tests`) asserting 5–10 test items, coverage across all five `RecommendationCategory` values (`retain`, `reclaim`, `recycle`, `manual_review`, `dispose`), and human-review routing edge cases (`NIIN 000030837` false-positive `"LG OF LEAD"` + unmatched `INC 77777`, and `NIIN 000032725` hazardous material indicator `HMIC=P`).
- Test dataset documentation and source attribution in `data/synthetic/README.md`, `data/README.md`, and `README.md`.

## [0.3.0] - 2026-10-08

### Added

- Priority 4 classification lookup pipeline (`src/cmr/ingest_classifications.py`) joining `selected_items.csv` to `V_H2_FSG.CSV`, `V_H2_FSC.CSV`, and `V_H6_NAME_INC.CSV` to generate `selected_items_classified.csv`, `classification_groups.csv`, and `classification_unmatched.csv`.
- Stage 3 PUB LOG reduction pipeline (`src/cmr/ingest_selected.py`) producing `selected_items.csv` (with compiled 13-digit `NSN`) and `selected_identification.csv` (`CRIT_CD`, `PMIC`, `DMIL`, `HMIC`, `HCC`, `ENAC`, `ESD_EMI`, `DMIL_INT_CD`).
- Stage 2 streaming characteristics scanner (`src/cmr/ingest_characteristics.py`) matching candidate NIINs against USGS 2025 critical minerals and discovery terms (`alloy`, `coating`, `plating`) directly from `CHARACTERISTICS.zip`.
- Stage 1 PUB LOG NSN candidate slicer (`src/cmr/ingest_publog.py`) filtering non-cancelled items in FSCs `5960`, `5998`, `6140`, and `2840`.
- PUB LOG / FLIS acronym glossary (`docs/glossary.md`) and version badge on `README.md` linking to this changelog.

### Changed

- Reorganized `README.md` with a Table of Contents, Setup instructions, and multi-stage ingestion usage and row counts.
- Moved the 12-entity Pydantic-to-JSON-Schema architecture table to `data/README.md`.

## [0.2.0] - 2026-09-25

### Added

- Complete 12-entity Pydantic v2 data model (`src/cmr/models/`) and JSON Schema exporter (`src/cmr/export_schemas.py` -> `data/schemas/*.json`).
- Static USGS 2025 List of Critical Minerals dataset (`data/static/usgs/critical_minerals_2025.csv` and `.json`, 60 minerals including 15 rare earth elements).

[Unreleased]: https://github.com/hmedi028/Critical-Materials-Recovery-Capstone-Project/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/hmedi028/Critical-Materials-Recovery-Capstone-Project/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/hmedi028/Critical-Materials-Recovery-Capstone-Project/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/hmedi028/Critical-Materials-Recovery-Capstone-Project/releases/tag/v0.2.0
