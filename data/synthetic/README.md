# Synthetic evaluation corpus

Demonstration records generated for schema validation and later rule evaluation. They are labeled `is_synthetic=true` and released under CC0 1.0 Universal.

The committed files contain **100 labeled items**: the original 7 templates (`SYN-ITEM-001` … `007`) plus generated variants. Expected recommendation categories are stored in `recommendations.json`.

Regenerate after generator changes:

```bash
python -m cmr.generate_synthetic
```

Do not add personal data, real facility locations, credentials, or restricted technical content.
