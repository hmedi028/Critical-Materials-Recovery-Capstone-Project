# Data Directory

- `static/`: small, versioned reference datasets safe to commit.
- `raw/`: local source downloads; do not commit bulk/raw files unless their redistribution terms are confirmed.
- `processed/`: local normalized outputs created by scripts (gitignored), including Stage 1–3 selected extracts and Priority 4 `selected_items_classified.csv` / `classification_groups.csv` / `classification_unmatched.csv`.
- `synthetic/`: reserved for generated demo records. None are committed yet.
- `schemas/`: JSON Schema contracts exported from `src/cmr` models.

Start with `static/usgs/critical_minerals_2025.csv` as the criticality reference table for rule development.

After model changes, regenerate committed JSON Schema files from the repository root:

```bash
python -m cmr.export_schemas
```

## Entity and schema architecture

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
