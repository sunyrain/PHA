# Datasheet

## Motivation

The dataset is intended to support protein-hydrogel adsorption analysis, tabular predictive modeling, and inverse design of hydrogel materials. PHA means Protein-Hydrogel Adsorption in this package and does not refer to polyhydroxyalkanoates.

## Composition

The package contains article-level source metadata, record-level structured facts, raw nested JSON, material/protein entity tables, special article-specific fields, a curated model-ready subset, and deterministic curation sidecars.

## Collection Process

Records were mined from locally stored article JSON files using a Codex extraction prompt and then audited for status, field coverage, quality flags, and model readiness.

## Preprocessing

The curated export flattens nested JSON into CSV, preserves raw JSONL, assigns curation decisions to sources, normalizes record IDs, and computes model-ready flags. It keeps second-pass field completion as auditable patches and keeps PubChem/UniProt/RCSB values as external descriptor sidecars.

The deterministic curation layer adds `interaction_type`, `is_covalent_binding`, `experiment_mode_primary`, `experiment_mode_detail`, `application_context`, `comparable_target_class`, `model_ready`, `model_ready_blocker`, `manual_review_priority`, and Q5 antifouling triage fields. Experimental values remain evidence-derived from the local corpus; the curation fields are rule-derived labels for stratification, audit, and model filtering.

## Recommended Uses

- Exploratory analysis of protein-hydrogel adsorption and antifouling literature.
- Baseline tabular models using high-confidence model-ready records.
- Stratified baselines using `model_records.csv`, especially when separating purification, immobilization, antifouling, and biointerface adsorption contexts.
- Descriptor enrichment through PubChem and UniProt before deep learning.
- Candidate generation and inverse design using `inverse_design_seed.csv`.

## Discouraged Uses

- Treating all raw records as ground truth without manual verification.
- Training high-stakes models without checking source evidence and missingness.
- Comparing incompatible targets without unit normalization and assay-mode stratification.
- Mixing `weak` or `not_comparable` target classes with strong capacity/surface-adsorption targets in a single regression target.

## Maintenance

Regenerate this package from the SQLite extraction database after new extraction, manual review, enrichment, or schema changes. Then rerun `scripts/apply_standardization.ps1` and `scripts/build_site_data.ps1` before publishing.

Generated: 2026-07-06T20:36:46
