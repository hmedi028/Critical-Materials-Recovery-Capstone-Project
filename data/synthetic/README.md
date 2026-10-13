# Curated Test & Synthetic Dataset

`data/synthetic/test_cases.json` contains **9 curated test cases** (`TC-01` through `TC-09`) prepared for initial prototype validation and benchmark testing.

Do not add personal data, real facility locations, credentials, or restricted technical content.

## Overview of selected test items

The 9 test cases combine all **7 distinct real PUB LOG item profiles** produced by Stages 1–3 and Priority 4 (`data/processed/selected_items_classified.csv`, `selected_identification.csv`, `selected_material_evidence.csv`) with **2 synthetic seed items** (`6140-SYN-000001` and `5998-SYN-000002`) so that all four target Federal Supply Classes (`5998`, `5960`, `2840`, `6140`), rare-earth elements, and all five recommendation categories (`retain`, `reclaim`, `recycle`, `manual_review`, `dispose`) are covered:

| Test Case | Item ID (`NSN` / Synthetic ID) | Item Name | Item Origin | Condition (`LifecycleEvent`) | Materials (`CompositionEvidence`) | Key Codes / Edge Case | Expected Outcome (`human_review_required`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-01` | `5998000012446` | `PRINTED WIRING BOARD` (`TEST SET,RADAR,AN/UPM-141`) | Public PUB LOG (`NIIN 000012446`) | `unserviceable` (`25 EA`) | `copper` (18%), `tin` (2.4%), `lead` (1.6%) | `FSC 5998`, `INC 61737`, `DMIL D`, `MRC FEAT` MIL-P-13949 / MIL-STD-275 | `reclaim` (`false`) |
| `TC-02` | `2840000030837` | `TUBE AND LEAD ASSEMBLY` (`ENG T400-CP400`) | Public PUB LOG (`NIIN 000030837`) | `unserviceable` (`8 EA`) | `lead` (`conflicting` / `inferred`) | False-positive `"16.750 IN. APPROX. LG OF LEAD"` (wire length) + unmatched `INC 77777` | `manual_review` (`true`) |
| `TC-03` | `5960000032725` | `SHIELD,ELECTRON TUBE` | Public PUB LOG (`NIIN 000032725`) | `damaged` (`40 EA`) | `aluminum` (55%), `copper` (43.2%), `beryllium` (1.8% `inferred`) | `FSC 5960`, `INC 10195`, `HMIC P` (Hazardous Material Indicator) on Copper Alloy 170/172 | `manual_review` (`true`) |
| `TC-04` | `5998000036115` | `EXTENDER CARD,ELECTRONIC TEST` | Public PUB LOG (`NIIN 000036115`) | `serviceable` (`12 EA`) | `aluminum` (22%) | `FSC 5998`, `INC 62400`, `ESD_EMI B`; serviceable operational state | `retain` (`false`) |
| `TC-05` | `5998000037075` | `CIRCUIT CARD ASSEMBLY` (`66254224314 SPECTRUM ANALYZER`) | Public PUB LOG (`NIIN 000037075`) | `unserviceable` (`15 EA`) | `silver` (`4.5 g`) | `FSC 5998`, `INC 61638`, `PMIC S` (Silver), `MRC PMLC` `"SILVER RESISTOR"` | `reclaim` (`false`) |
| `TC-06` | `5998000038520` | `HOLDER,ELECTRICAL CARD` | Public PUB LOG (`NIIN 000038520`) | `unserviceable` (`120 EA`) | `aluminum` (97.2%), `magnesium` (2.5%) | `FSC 5998`, `INC 31930`, `MRC MATT`/`MDCL` `QQ-A-250/8 ALLOY 5052-H32` | `recycle` (`false`) |
| `TC-07` | `2840000039754` | `PLATE,COMPONENT MOUNTING,AIRCRAF` (`TF-30 AIRCRAFT GAS TURBINE ENGINE`) | Public PUB LOG (`NIIN 000039754`) | `unserviceable` (`6 EA`) | `nickel` (62%), `chromium` (19%) | `FSC 2840`, `INC 50354`, `CRIT_CD Y`, `MRC MATT` `"OVERALL NICKEL ALLOY"` | `reclaim` (`false`) |
| `TC-08` | `6140-SYN-000001` | `BATTERY,STORAGE,NICKEL-METAL HYDRIDE` | Synthetic (`CC0-1.0`) | `unserviceable` (`10 EA`) | `nickel` (`420 g`), `cobalt` (`45 g`), `lanthanum` (`85 g`, REE) | `FSC 6140`, `CRIT_CD Y`; covers rechargeable batteries & rare-earth elements | `reclaim` (`false`) |
| `TC-09` | `5998-SYN-000002` | `SPACER,CIRCUIT CARD,PHENOLIC` | Synthetic (`CC0-1.0`) | `damaged` (`200 EA`) | None (`[]`) | `FSC 5998`, non-metallic phenolic resin spacer (negative control) | `dispose` (`false`) |

## Structure of each test case

Each entry in `test_cases.json` bundles the linked Pydantic v2 models (`src/cmr/models/`) for one item:

- `item` (`Item` — `data/schemas/item.json`): Public or synthetic item record (`public_item_id`, `name`, `category`, `public_characteristics`, plus `Provenance`).
- `lifecycle_event` (`LifecycleEvent` — `data/schemas/lifecycle_event.json`): Synthetic warehouse inspection/storage/disposition record (`condition`, `quantity`, `quantity_unit`, `generic_location_code`, `is_synthetic: true`).
- `composition_evidence` (`list[CompositionEvidence]` — `data/schemas/composition_evidence.json`): Material assertions linking `item_id` to a `material_id` in `data/static/usgs/critical_minerals_2025.csv`, with measured `quantity`+`quantity_unit` or `percentage`, `evidence_type`, and `value_basis`.
- `recovery_method` (`RecoveryMethod | null` — `data/schemas/recovery_method.json`): Optional documented recovery process and `expected_yield`.
- `value_estimate` (`ValueEstimate | null` — `data/schemas/value_estimate.json`): Optional illustrative recovery value and cost estimate (`is_illustrative: true`).
- `expected_recommendation` (`Recommendation` — `data/schemas/recommendation.json`): Expected benchmark output (`category`, `explanation`, `confidence`, `human_review_required`).

## Source documentation and provenance

1. **DLA PUB LOG (U.S. Government Public Information, retrieved `2026-10-08`):**
   - `P_FLIS_NSN.CSV`: `FSC`, `NIIN`, `NSN`, `ITEM_NAME`, `INC`.
   - `V_FLIS_IDENTIFICATION.CSV`: `END_ITEM_NAME`, `CRIT_CD`, `PMIC`, `DMIL`, `HMIC`, `ESD_EMI`, `DMIL_INT_CD`.
   - `V_H2_FSG.CSV`, `V_H2_FSC.CSV`, `V_H6_NAME_INC.CSV`: `FSG_TITLE`, `FSC_TITLE`, `INC_DEFINITION` (including unmatched `INC 77777` on `NIIN 000030837`).
   - `V_CHARACTERISTICS.CSV`: `MRC` (`FEAT`, `MATT`, `MDCL`, `PMLC`, `TEXT`) and `CLEAR_TEXT_REPLY`.
2. **USGS 2025 List of Critical Minerals (`data/static/usgs/critical_minerals_2025.csv`, retrieved `2026-09-13`):**
   - Authoritative criticality reference for `aluminum`, `beryllium`, `chromium`, `cobalt`, `copper`, `lanthanum` (REE), `lead`, `magnesium`, `nickel`, `silver`, and `tin`.
3. **CMR Synthetic Operational & BOM Seed (`CC0-1.0`, generated `2026-10-13`):**
   - Supplies warehouse lifecycle conditions/quantities (`LifecycleEvent`), nominal alloy/component mass percentages (`CompositionEvidence` with `is_synthetic: true` and `value_basis: "synthetic"` or `"inferred"`), recovery processes (`RecoveryMethod`), illustrative value estimates (`ValueEstimate`), and synthetic seed items `TC-08` and `TC-09`.

## Validating the test cases

Run the test-case validator from the repository root:

```bash
python -m cmr.test_cases
# or run the unit test suite:
python -m unittest discover -s tests
```
