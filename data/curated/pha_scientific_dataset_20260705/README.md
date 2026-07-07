# PHA Protein-Hydrogel Adsorption Dataset

Generated: 2026-07-06T20:36:46

## Scope

This curated package organizes literature-derived protein-hydrogel adsorption, binding, immobilization, antifouling, and related biointerface records extracted from the local PHA corpus. Here PHA means Protein-Hydrogel Adsorption and does not refer to polyhydroxyalkanoates.

The primary unit is one record:

`paper + hydrogel/sample + protein/mixture + experimental condition + measured outcome`

## Contents

- `data/sources.csv`: article-level metadata, extraction status, and curation decision.
- `data/records_flat.csv`: flattened record-level table with provenance, hydrogel, protein, condition, outcome, mechanism, and quality fields.
- `data/records_core.csv`: compact record-level main table for browsing, filtering, splits, and first-pass modeling.
- `data/record_additional_values.csv`: long-form record-level companion table for sparse preparation, property, endpoint-specific, provenance, and control values.
- `data/field_tiers.csv`: field-level map separating main fields from record additional values.
- `data/records_raw.jsonl`: raw nested record JSON for lossless downstream parsing.
- `data/model_records.csv`: conservative model-ready subset.
- `data/model_records_v2.csv`: deterministic standardization v2 model-ready subset with interaction/application/comparability strata.
- `data/record_standardization.csv`: record-level sidecar containing `interaction_type`, `experiment_mode_primary`, `experiment_mode_detail`, `application_context`, `comparable_target_class`, `model_ready_v2`, `model_ready_blocker`, `manual_review_priority`, and Q5 triage fields.
- `data/inverse_design_seed.csv`: compact table for inverse-design and generative-model experiments.
- `data/materials.csv`: material, monomer, crosslinker, ligand, filler, and related mentions.
- `data/proteins.csv`: protein mentions and reported protein properties.
- `data/material_descriptors.csv`: flattened PubChem descriptors with match status.
- `data/protein_descriptors.csv`: flattened UniProt descriptors with QA status.
- `data/special_fields.csv`: article-specific fields outside the common schema.
- `metadata/field_coverage.csv`: coverage audit for common fields.
- `metadata/field_completion_candidates.csv`: DOI-level priority queue for second-pass preparation/property completion.
- `metadata/completion_patches.csv`: patch-first second-pass field-completion proposals and apply status.
- `metadata/article_level_properties.csv`: observed article-level values that could not be safely mapped to exact records.
- `metadata/completion_coverage_before_after.csv`: coverage deltas from the latest completion run.
- `metadata/completion_patch_audit.csv`: patch status counts by target path.
- `metadata/external_descriptor_audit.csv`: PubChem/UniProt/RCSB sidecar descriptor QA summary.
- `metadata/data_dictionary.csv`: table and column descriptions.
- `metadata/failed_articles.csv`: failed DOI audit and relevance decision.
- `metadata/partial_articles.csv`: article-level no-record exclusions.
- `metadata/checksums_sha256.csv`: file checksums.
- `metadata/run_comparison_summary_20260707.md`: incremental update comparison for legacy and standardization v2 counts/distributions.
- `reports/PHA_SCHEMA_TIERING_V1RC_20260707.md`: rationale for the compact main table and additional-value sidecar.

## Summary

- Articles: 1230
- Success / partial / failed: 985 / 245 / 0
- Records: 6436
- Model-ready records: 2337
- Model-ready v2 records: 3589
- Strong/medium comparable records: 3839
- Main schema: 29 legacy main fields + 12 standardization v2 fields + 61 additional-value fields
- Inverse-design seed rows: 2337
- Completion patches: 56978

## Curation Rules

Records are marked model-ready only when they come from a successful article extraction, have a numeric target, are not marked for manual review, have source quality score >= 2, and include hydrogel and protein identity.

Standardization v2 is an incremental deterministic post-processing layer. It preserves the legacy `model_ready` field and adds controlled `interaction_type`, `experiment_mode_primary/detail`, `application_context`, `comparable_target_class`, `model_ready_v2`, `model_ready_blocker`, `manual_review_priority`, and Q5 protein-antifouling triage fields. Q5 antifouling candidates are kept as protein-relevant only when they include protein, serum, plasma, albumin, fibrinogen, IgG, blood, or total-protein evidence.

Failed but relevant articles are retained in `sources.csv` and `failed_articles.csv` for traceability. They are excluded from record-level and model-ready training tables until manually extracted or successfully retried.

Second-pass completion uses a patch-first workflow. Only `observed_fulltext` patches with exact record IDs, non-empty evidence, source section, empty target fields, and whitelisted target paths may be applied to nested records. External descriptors are exported as sidecar features and must not overwrite observed experimental fields.

## Known Limitations

The dataset is literature-mined and not manually verified end-to-end. Preparation and hydrogel physical-property coverage are much lower than identity and outcome coverage. Use `field_coverage.csv`, `completion_patch_audit.csv`, `external_descriptor_audit.csv`, `model_ready_reason`, `model_ready_blocker`, `comparable_target_class`, `manual_review_priority`, and provenance/evidence columns when building predictive or generative models.
