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
