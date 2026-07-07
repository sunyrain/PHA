# PHA: Protein-Hydrogel Adsorption Dataset

> Online database browser: <https://sunyrain.github.io/PHA/>

PHA means **Protein-Hydrogel Adsorption** in this repository. It does not refer
to polyhydroxyalkanoates. PHA is a literature-mined dataset for
protein-hydrogel adsorption, immobilization, antifouling, and related
biointerface measurements. The primary record unit is:

`paper + hydrogel/sample + protein/mixture + experimental condition + measured outcome`

The repository follows the OPV dataset style: a static GitHub Pages browser in
`docs/`, release-ready CSV/JSONL files under `data/curated/`, and transparent
schema, prompt, audit, and extraction artifacts.

## Current Release

Release package: `data/curated/pha_scientific_dataset_20260705`

| Item | Count |
|---|---:|
| Articles | 1,230 |
| Successful article extractions | 985 |
| Partial/no-record articles | 245 |
| Failed articles | 0 |
| Record-level rows | 6,436 |
| Model-ready rows | 3,589 |
| Strong/medium comparable rows | 3,839 |
| Inverse-design seed rows | 2,337 |
| Material mentions | 13,662 |
| Protein mentions | 4,290 |
| Special fields | 5,363 |

## Main Files

| Path | Purpose |
|---|---|
| `docs/index.html` | Static online browser for records, filters, details, and filtered CSV export. |
| `docs/pha_records_browser.json` | Lightweight browser payload derived from all record rows. |
| `data/curated/pha_scientific_dataset_20260705/data/records_flat.csv` | Full flattened record-level table. |
| `data/curated/pha_scientific_dataset_20260705/data/records_raw.jsonl` | Raw nested record JSONL for lossless parsing and audit. |
| `data/curated/pha_scientific_dataset_20260705/data/model_records.csv` | Curated supervised-learning subset with application, interaction, and target-comparability strata. |
| `data/curated/pha_scientific_dataset_20260705/data/record_standardization.csv` | Sidecar with standardized interaction, assay mode, application, comparability, model-ready blocker, Q5 triage, and review-priority fields. |
| `data/curated/pha_scientific_dataset_20260705/data/inverse_design_seed.csv` | Compact table for inverse-design and generation experiments. |
| `data/curated/pha_scientific_dataset_20260705/data/materials.csv` | Material, monomer, crosslinker, ligand, and filler mentions. |
| `data/curated/pha_scientific_dataset_20260705/data/proteins.csv` | Protein mentions and reported protein properties. |
| `data/curated/pha_scientific_dataset_20260705/metadata/field_coverage.csv` | Field-level coverage audit. |
| `data/curated/pha_scientific_dataset_20260705/metadata/data_dictionary.csv` | Column descriptions for major tables. |
| `data/curated/pha_scientific_dataset_20260705/metadata/curation_summary_20260707.md` | Current-release curation counts, controlled-field distributions, and compatibility note. |
| `extraction/schemas/` | JSON schemas for adsorption records, candidate designs, and article outputs. |
| `extraction/prompts/` | Extraction and field-completion prompt versions. |
| `reports/` | Completion and coverage audits for the public release. |

## Recommended Use

- Use `model_records.csv` for tabular prediction baselines; it includes
  application context, interaction type, and target-comparability strata.
- Use `inverse_design_seed.csv` for hydrogel design and candidate-generation experiments.
- Use DOI-level `doi_split` for train/validation/test separation.
- Use `field_coverage.csv`, `model_ready_reason`, `model_ready_blocker`,
  `comparable_target_class`, `manual_review_priority`,
  `quality__source_quality_score`, and `quality__needs_manual_review` before
  model training or benchmark claims.
- Treat PubChem, UniProt, and RCSB descriptor tables as external sidecars; they do
  not overwrite observed experimental fields.

## Limitations

The dataset is literature-mined and has not been manually verified end to end.
Preparation and hydrogel physical-property fields are sparse in many papers.
The public release does not include copyrighted article full text or raw local
article captures; `source_json` values are sanitized to `local_article_corpus/...`
identifiers for provenance traceability.

## Rebuilding The Browser Payload

From the repository root:

```powershell
.\scripts\apply_standardization.ps1
.\scripts\build_site_data.ps1
```

The first command applies deterministic curation fields and refreshes
sidecar/audit outputs. The second regenerates `docs/pha_records_browser.json`
and `docs/pha_summary.json` from the curated release package.

## GitHub Pages Deployment

The repository publishes GitHub Pages from `main/docs`. The optional
`.github/workflows/pages.yml` workflow is kept for manual dispatch only. The
browser is fully static and reads:

- `docs/index.html`
- `docs/pha_records_browser.json`
- `docs/pha_summary.json`

Before pushing a refreshed release, rebuild the curated package if needed, rerun
the standardization and site-data scripts above, and commit the changed data,
metadata, report, and `docs/` files.

## Citation

If you use this dataset, cite this repository and the underlying source papers
identified by DOI in the relevant rows. A formal dataset citation can be added
after archival release.

## License

Code and site files are distributed under the MIT License. Dataset records are
provided for academic and research use with source-paper citation expected.
