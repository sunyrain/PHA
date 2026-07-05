# Datasheet

## Motivation

The dataset is intended to support protein-hydrogel adsorption analysis, tabular predictive modeling, and inverse design of hydrogel materials.

## Composition

The package contains article-level source metadata, record-level structured facts, raw nested JSON, material/protein entity tables, special article-specific fields, and conservative model-ready subsets.

## Collection Process

Records were mined from locally stored article JSON files using a Codex extraction prompt and then audited for status, field coverage, quality flags, and model readiness.

## Preprocessing

The curated export flattens nested JSON into CSV, preserves raw JSONL, assigns curation decisions to sources, normalizes record IDs, and computes model-ready flags. It keeps second-pass field completion as auditable patches and keeps PubChem/UniProt/RCSB values as external descriptor sidecars.

## Recommended Uses

- Exploratory analysis of protein-hydrogel adsorption and antifouling literature.
- Baseline tabular models using high-confidence model-ready records.
- Descriptor enrichment through PubChem and UniProt before deep learning.
- Candidate generation and inverse design using `inverse_design_seed.csv`.

## Discouraged Uses

- Treating all raw records as ground truth without manual verification.
- Training high-stakes models without checking source evidence and missingness.
- Comparing incompatible targets without unit normalization and assay-mode stratification.

## Maintenance

Regenerate this package from the SQLite extraction database after new extraction, manual review, enrichment, or schema changes.

Generated: 2026-07-05T11:36:45
