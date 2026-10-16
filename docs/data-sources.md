
### Reproducible 19-Item Scope Validation — October 2026

A separate validation run reproduced the 19-item scope documented in the README. All outputs were written to temporary files under `/tmp`; the existing project outputs were not overwritten.

| Validation stage | Result |
|---|---:|
| Stage 1 candidate NIINs | 1,000 unique NIINs |
| Stage 2 material-evidence rows | 40 |
| Stage 2 selected NIINs | 19 |
| Stage 3 selected item rows | 19 |
| Stage 3 identification rows | 19 |
| Duplicate NIINs in selected, item, and identification outputs | 0 |
| Selected NIINs missing from either Stage 3 output | 0 |
| Selected NIINs with material evidence | 19 of 19 |
| Evidence NIINs outside the selected set | 0 |

The selected NIIN set matched exactly between the Stage 2 selection, Stage 3 item output, and Stage 3 identification output. Every selected NIIN had at least one retained material-evidence row.

Temporary validation outputs:
- `/tmp/candidate_niins_scope_check.csv`
- `/tmp/evidence_scope_check.csv`
- `/tmp/selected_scope_check.csv`
- `/tmp/selected_items_scope_check.csv`
- `/tmp/selected_identification_scope_check.csv`

These results establish reproducible pipeline counts and consistency across outputs. Material keyword matches remain candidate evidence, not proof of material composition or recoverability. Identification codes such as `CRIT_CD`, `PMIC`, `DMIL`, `HMIC`, and `HCC` are supporting codes, not material proof.

This validation did not replace the existing processed datasets or resolve the original provenance of the 5,613-row `candidate_niins.csv` dataset. Teammate verification and Product Owner acceptance remain outstanding.
