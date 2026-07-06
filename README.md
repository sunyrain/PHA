# PHA: Protein-Hydrogel Adsorption Dataset

> Online database browser: <https://sunyrain.github.io/PHA/>

PHA is a literature-mined dataset for protein-hydrogel adsorption, immobilization,
antifouling, and related biointerface measurements. The primary record unit is:

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
| Conservative model-ready rows | 2,325 |
| Inverse-design seed rows | 2,325 |
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
| `data/curated/pha_scientific_dataset_20260705/data/model_records.csv` | Conservative supervised-learning subset. |
| `data/curated/pha_scientific_dataset_20260705/data/inverse_design_seed.csv` | Compact table for inverse-design and generation experiments. |
| `data/curated/pha_scientific_dataset_20260705/data/materials.csv` | Material, monomer, crosslinker, ligand, and filler mentions. |
| `data/curated/pha_scientific_dataset_20260705/data/proteins.csv` | Protein mentions and reported protein properties. |
| `data/curated/pha_scientific_dataset_20260705/metadata/field_coverage.csv` | Field-level coverage audit. |
| `data/curated/pha_scientific_dataset_20260705/metadata/data_dictionary.csv` | Column descriptions for major tables. |
| `extraction/schemas/` | JSON schemas for adsorption records, candidate designs, and article outputs. |
| `extraction/prompts/` | Extraction and field-completion prompt versions. |
| `reports/` | Completion and coverage audits for the public release. |

## Recommended Use

- Use `model_records.csv` for conservative tabular prediction baselines.
- Use `inverse_design_seed.csv` for hydrogel design and candidate-generation experiments.
- Use DOI-level `doi_split` for train/validation/test separation.
- Use `field_coverage.csv`, `model_ready_reason`, `quality__source_quality_score`,
  and `quality__needs_manual_review` before model training or benchmark claims.
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
python scripts/build_site_data.py
```

This regenerates `docs/pha_records_browser.json` and `docs/pha_summary.json` from
the curated release package.

## GitHub Pages Deployment

The repository is prepared for GitHub Pages through `.github/workflows/pages.yml`.
On every push to `main`, the workflow uploads the `docs/` directory as the Pages
artifact. The browser is fully static and reads:

- `docs/index.html`
- `docs/pha_records_browser.json`
- `docs/pha_summary.json`

Before pushing a refreshed release, rebuild the curated package if needed, rerun
`python scripts/build_site_data.py`, and commit the changed `docs/` files.

## Citation

If you use this dataset, cite this repository and the underlying source papers
identified by DOI in the relevant rows. A formal dataset citation can be added
after archival release.

## License

Code and site files are distributed under the MIT License. Dataset records are
provided for academic and research use with source-paper citation expected.
