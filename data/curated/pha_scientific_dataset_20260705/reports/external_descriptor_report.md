# PHA external descriptor sidecar report

- Generated: 2026-07-05T11:33:27
- Source DB: `PHA/data\processed\pha_extraction_1000_xhigh_fulltext_w8\codex_extraction_results.db`
- Query API: False
- Output dir: `PHA\data\processed\pha_external_descriptors`

## Audit

- PubChem material: rows=13662, matched=931, usable=931, needs_review=0, not_queried=8729, skipped=3995, errors=7
- UniProt protein: rows=4290, matched=338, usable=70, needs_review=268, not_queried=2795, skipped=1156, errors=1
- RCSB PDB structure: rows=70, matched=0, usable=0, needs_review=0, not_queried=70, skipped=0, errors=0

## Policy

External descriptors are sidecar features only. They must not overwrite observed experimental fields in adsorption records.