# PUB LOG / FLIS glossary

Short names used in ingest scripts and processed extracts. Codes stay in the data; this table is only a legend.

| Acronym | Meaning |
| :--- | :--- |
| **FSC** | Federal Supply Class — 4-digit item category (e.g. `5998` circuit cards, `6140` batteries) |
| **FSG** | Federal Supply Group — first two digits of FSC (e.g. `59` electrical/electronic components, `28` engines/turbines) |
| **NIIN** | National Item Identification Number — 9-digit public item ID |
| **NSN** | National Stock Number — 13 digits: FSC + NIIN |
| **INC** | Item Name Code — 5-digit coded name (`77777` often means unassigned / unknown) |
| **FLIS** | Federal Logistics Information System |
| **PUB LOG** | Publicly releasable logistics catalog extract |

`ITEM_NAME` and `END_ITEM_NAME` are not acronyms; they are the short item name and the end-item / application name.

Classification lookups (H2 FSG/FSC, H6 INC) describe item type. They do not establish material composition.

## Material-evidence validation

| Term | Meaning |
| :--- | :--- |
| **Material match** | A text match between a source characteristic field and a listed material term. It is a candidate signal, not proof of material presence. |
| **Candidate evidence** | A source record flagged for review because its text contains a material term. |
| **Matched term** | The specific word or phrase detected by the pipeline in the source text. |
| **Discovery term** | A broad term such as `alloy`, `coating`, or `plating` used to identify potentially relevant records without identifying a specific critical material. |
| **Source text** | The original `REQUIREMENTS_STATEMENT` and `CLEAR_TEXT_REPLY` fields retained for reviewing a match in context. |
| **Supporting identification codes** | `CRIT_CD`, `PMIC`, `DMIL`, `HMIC`, and `HCC`. These provide supporting item information but do not prove material composition. |
| **False positive** | A text match that does not provide relevant evidence for the material being investigated, after reviewing its context. |
| **Trace constituent** | A material mentioned at a low concentration or as an impurity limit; its mention does not establish that it is a primary or recoverable component. |

**Interpretation note:** Failure to find a material term in the scanned text does not establish that an item contains no critical material. Text matching and identification codes are screening aids, not confirmation of composition or recoverability.
