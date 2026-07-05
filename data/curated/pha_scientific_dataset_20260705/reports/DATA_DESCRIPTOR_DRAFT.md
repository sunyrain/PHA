# A Literature-Mined Dataset of Protein-Hydrogel Adsorption and Interaction Records

## Background & Summary

This dataset organizes literature-derived records describing protein adsorption, binding, immobilization, antifouling, controlled release, and related protein-hydrogel or protein-nanogel interactions.

The dataset is designed for reuse in:

- quantitative analysis of protein-hydrogel interactions;
- tabular machine-learning baselines;
- descriptor-enriched protein/material modeling;
- generative and inverse-design studies for hydrogel formulations.

The primary record unit is:

`paper + hydrogel/sample + protein/mixture + experimental condition + measured outcome`

## Methods

### Input Data

The source corpus was assembled from local article JSON files under `PHA/data/article_data`. The local extraction script prepared 1230 article contexts that had source metadata, a successful local article download/parse flag, an article path, and a readable JSON file.

### Literature Mining

Articles were processed with the PHA Codex extraction prompt v3. The extraction schema requested article metadata, record-level adsorption facts, material mentions, protein mentions, special article-specific fields, provenance evidence, quality flags, and model-readiness hints.

The full local run used xhigh reasoning, 12 workers, full article context, and a 3600 s timeout. A targeted reduced-context retry recovered three of four failed articles. The remaining failed article is retained as a relevant but unresolved source.

### Curation and Export

The curated export was generated from `codex_extraction_results.db` using:

```powershell
.\.venv\Scripts\python.exe PHA\extraction\scripts\build_pha_scientific_dataset.py `
  --db PHA\data\processed\pha_extraction_1000_xhigh_fulltext_w8\codex_extraction_results.db `
  --output-dir PHA\data\curated\pha_scientific_dataset_20260705 `
  --audit-md PHA\data\processed\pha_extraction_1000_xhigh_fulltext_w8\QUALITY_AUDIT_20260705_021519.md
```

The export preserves raw nested record JSON while also providing flattened tables for analysis. Model-ready records are conservatively filtered to successful article extractions with numeric targets, no manual-review flag, source quality score at least 2, and hydrogel/protein identity present.

## Data Records

The data package is located at:

`PHA/data/curated/pha_scientific_dataset_20260705`

Files:

- `README.md`: package overview and curation rules.
- `data/sources.csv`: 1230 article-level rows with extraction status and curation decision.
- `data/records_flat.csv`: 6426 flattened record-level rows.
- `data/records_raw.jsonl`: lossless nested record JSON.
- `data/model_records.csv`: 2317 conservative model-ready records.
- `data/inverse_design_seed.csv`: 2317 compact rows for inverse-design workflows.
- `data/materials.csv`: 13654 material mentions.
- `data/proteins.csv`: 4285 protein mentions.
- `data/special_fields.csv`: 5356 special fields.
- `metadata/field_coverage.csv`: common-field coverage audit.
- `metadata/field_completion_candidates.csv`: DOI-level queue for second-pass preparation/property completion.
- `metadata/failed_articles.csv`: failed-source audit.
- `metadata/partial_articles.csv`: no-record article exclusions.
- `metadata/data_dictionary.csv`: table and column descriptions.
- `metadata/datasheet.md`: dataset datasheet.
- `metadata/checksums_sha256.csv`: file checksums.

## Technical Validation

Validation performed:

- SQLite table counts and status counts were checked after extraction.
- Record IDs were normalized and duplicate record IDs are zero.
- A quality audit generated field coverage, model-readiness counts, issue samples, and failed/partial article summaries.
- The latest audit is copied to `reports/QUALITY_AUDIT_20260705_021519.md`.
- CSV/JSONL exports were read back and checked for expected row counts.
- SHA-256 checksums were generated for all package files.

Known validation limitations:

- LLM-extracted values are not fully manually verified.
- Many preparation and physical-property fields are absent from source text or require a second targeted extraction pass.
- Unit normalization is partial; model users should prefer normalized target columns where available.
- The remaining failed HydroMIP article is relevant but unresolved due to repeated network/model stream failures.

## Usage Notes

Recommended starting points:

- Use `data/model_records.csv` for conservative tabular baseline models.
- Use `data/inverse_design_seed.csv` for hydrogel inverse-design experiments.
- Use `metadata/field_completion_candidates.csv` to prioritize second-pass extraction of preparation and characterization fields.
- Use `data/records_raw.jsonl` when nested provenance, mechanism, or side outcomes are needed.

Recommended modeling filters:

- group splits by DOI for performance estimates;
- stricter family splits by hydrogel family and protein family for extrapolation tests;
- separate targets by unit and assay type;
- treat antifouling, adsorption-capacity, surface-adsorption, and immobilization outcomes as related but non-identical tasks.

## Data Availability

The current package is a local curated export. For public release, deposit the package in a suitable data repository and update this section with repository DOI, accession, license, and version.

## Code Availability

The local scripts used for extraction, normalization, audit, and package export are in:

- `PHA/extraction/scripts/run_codex_pha_extraction.py`
- `PHA/extraction/scripts/normalize_pha_extraction_db.py`
- `PHA/extraction/scripts/audit_pha_extraction_quality.py`
- `PHA/extraction/scripts/build_pha_scientific_dataset.py`

## Next Curation Tasks

1. Manually extract or retry `10.1016/j.aca.2013.11.052`.
2. Run second-pass field completion for the highest-priority DOI rows in `metadata/field_completion_candidates.csv`.
3. Add PubChem and UniProt identifiers/descriptors for model-ready rows.
4. Create benchmark train/validation/test splits and baseline models.
