# PHA dataset completion audit - 2026-07-05

This report records the current local closed loop for the protein-hydrogel
adsorption dataset.

## 1. Final package

- Curated package: `PHA/data/curated/pha_scientific_dataset_20260705`
- Source extraction DB: `PHA/data/processed/pha_extraction_1000_xhigh_fulltext_w8/codex_extraction_results.db`
- Latest audit: `PHA/data/processed/pha_extraction_1000_xhigh_fulltext_w8/QUALITY_AUDIT_20260705_034010.md`
- Latest audit JSON: `PHA/data/processed/pha_extraction_1000_xhigh_fulltext_w8/quality_audit_20260705_034010.json`

Package tables:

| file | shape | purpose |
|---|---:|---|
| `data/sources.csv` | 1230 x 12 | article-level provenance and curation decisions |
| `data/records_flat.csv` | 6436 x 102 | full flattened record-level table |
| `data/records_raw.jsonl` | 6436 records | raw nested record JSON |
| `data/model_records.csv` | 2325 x 102 | conservative model-ready rows |
| `data/inverse_design_seed.csv` | 2325 x 63 | compact inverse-design table |
| `data/materials.csv` | 13662 x 8 | material mentions and PubChem enrichment payloads |
| `data/material_descriptors.csv` | 13662 x 15 | flattened PubChem descriptor table |
| `data/proteins.csv` | 4290 x 11 | protein mentions and UniProt enrichment payloads |
| `data/protein_descriptors.csv` | 4290 x 20 | flattened UniProt descriptor table with QA status |
| `data/special_fields.csv` | 5363 x 7 | article-specific unusual fields |
| `metadata/checksums_sha256.csv` | 26 x 3 | file integrity checksums |

## 2. Article audit

- Total local extractable articles: 1230
- Successful extraction: 985
- Partial extraction: 245
- Failed extraction: 0
- Record rows: 6436
- Material mentions: 13662
- Protein mentions: 4290
- Special fields: 5363

The previously failed article was recovered:

- DOI: `10.1016/j.aca.2013.11.052`
- Title: `Enhanced selectivity of hydrogel-based molecularly imprinted polymers (HydroMIPs) following buffer conditioning`
- Recovery: single-DOI medium retry with shorter context succeeded.
- Extracted records: 10
- Second-pass field completion: 9 updates, 24 applied fields.

No failed articles remain. No irrelevant failed article required deletion.

## 3. Field completion

Second-pass field completion was changed from full-output JSON to compact patch
JSON:

- Prompt: `PHA/extraction/prompts/pha_field_completion_prompt_v2.md`
- Runner: `PHA/extraction/scripts/run_pha_field_completion.py`
- Default context mode: field-relevant table/text snippets, 12k context chars
- Default behavior: fill missing fields only; never overwrite existing values

Completed second-pass work:

| run | result |
|---|---:|
| top6 v1 pilot | 244 fields applied |
| v2 probe | 30 fields applied |
| v2 batch40 | 33/34 success, 1080 fields applied |
| failed DOI retry | 1/1 success, 43 fields applied |
| recovered HydroMIP retry | 10 extracted records, 24 completion fields applied |
| offline reapply after mapping expansion | 112 additional fields applied |

The batch40 parse failure was `10.1016/j.colsurfb.2013.09.018`; it was a malformed JSON output after Codex reconnects. A single-DOI retry succeeded and added 43 fields.

## 4. Key coverage after completion

| field | present | coverage |
|---|---:|---:|
| `hydrogel.monomer_ratios` | 281 | 4.37% |
| `hydrogel.crosslinker_concentration` | 219 | 3.40% |
| `hydrogel.initiator` | 126 | 1.96% |
| `hydrogel.preparation_solvent` | 134 | 2.09% |
| `hydrogel.preparation_temp_C` | 155 | 2.41% |
| `hydrogel.post_treatment` | 181 | 2.81% |
| `hydrogel_properties.swelling_ratio` | 1654 | 25.70% |
| `hydrogel_properties.surface_area` | 39 | 0.61% |
| `hydrogel_properties.roughness` | 12 | 0.19% |
| `hydrogel_properties.young_modulus` | 345 | 5.37% |
| `hydrogel_properties.degradation_or_stability` | 36 | 0.56% |
| `protein.molecular_weight_kDa` | 2243 | 34.85% |
| `protein.pI` | 2020 | 31.39% |
| `experiment.pH` | 3826 | 59.45% |
| `experiment.temperature_C` | 3164 | 49.16% |
| `experiment.contact_time` | 4567 | 70.96% |
| `experiment.replicate_count` | 132 | 2.05% |

Compared with the pre-completion audit at `20260705_022422`, preparation group
coverage improved from 17.77% to 19.57%. Hydrogel-property absolute fields were
added, but the group percentage is not directly comparable because roughness,
thickness, and stability were added to the denominator.

## 5. External enrichment

The extraction DB already has enrichment columns and lookup functions:

- PubChem lookup for small molecules/material mentions
- UniProt lookup for protein mentions

Current enrichment payload coverage:

- `material_descriptors.csv`: 931 matched PubChem rows, 12724 not yet queried, 7 errors
- `protein_descriptors.csv`: 338 matched UniProt rows, 3951 not yet queried, 1 error
- UniProt QA flags: 67 directly usable matches, 272 matches needing accession/species review

Important caution: generic UniProt queries can produce noisy matches for broad
names such as `immunoglobulin G`. Before using sequence embeddings, filter by
species/source, protein family, accession confidence, and query provenance.

## 6. Model-ready organization

Use `data/model_records.csv` for conservative supervised learning and
`data/inverse_design_seed.csv` for generation/inverse-design experiments.

The curated package includes DOI-level deterministic splits:

- `train`
- `validation`
- `test`

Recommended first targets:

- `q_norm_mg_g`
- `surface_adsorption_ug_cm2`
- `removal_efficiency_pct`
- `binding_efficiency_pct`
- `recovery_pct`
- `purity_pct`
- `fouling_reduction_pct`
- `retained_capacity_pct`

Recommended first modeling path:

1. Start with CatBoost/LightGBM on `inverse_design_seed.csv`.
2. Use DOI split, not random row split, for real evaluation.
3. Add PubChem descriptors only for high-confidence monomer/crosslinker/ligand matches.
4. Add UniProt descriptors only after accession QA.
5. Keep raw `records_raw.jsonl` as the audit source for outlier review.

## 7. Remaining limitations

- Physical-property fields remain sparse because many papers do not report them or report them only at material-family level.
- Failed-article count is now zero; future failures should still be audited before deletion or retry.
- Some PubChem/UniProt enrichments are intentionally partial and require match-confidence filtering.
- `model_records.csv` is conservative; excluded rows may still be useful for weak supervision, retrieval, or qualitative generation.
