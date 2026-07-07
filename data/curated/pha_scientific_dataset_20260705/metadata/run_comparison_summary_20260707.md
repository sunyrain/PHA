# PHA Incremental Standardization Run Comparison

Generated: 2026-07-07T15:46:05

This run is an incremental update to the existing PHA = Protein-Hydrogel Adsorption release. It does not redesign the Q1-Q7 retrieval protocol, record granularity, or legacy output structure.

## Core Counts

| Metric | Count |
|---|---:|
| Articles | 1230 |
| Records | 6436 |
| Legacy model_ready | 2337 |
| model_ready_v2 | 3589 |
| Legacy comparable numeric | 4021 |

## comparable_target_class

| Category | Count |
|---|---:|
| strong | 2401 |
| medium | 1438 |
| not_comparable | 1377 |
| weak | 1220 |

## interaction_type

| Category | Count |
|---|---:|
| covalent_immobilization | 1423 |
| physical_adsorption | 1141 |
| entrapment | 994 |
| selective_adsorption | 976 |
| affinity_binding | 748 |
| antifouling_low_adsorption | 545 |
| unknown | 245 |
| nonspecific_adsorption | 228 |
| protein_fouling | 136 |

## experiment_mode_primary

| Category | Count |
|---|---:|
| surface | 1372 |
| column | 1321 |
| batch | 1008 |
| hemocompatibility | 841 |
| immobilization | 729 |
| other | 402 |
| biofouling | 371 |
| QCM_SPR | 214 |
| microarray | 123 |
| flow | 55 |

## application_context

| Category | Count |
|---|---:|
| protein_immobilization | 1878 |
| biointerface_adsorption | 1411 |
| purification | 1344 |
| antifouling | 636 |
| hemocompatibility | 493 |
| mechanism_study | 436 |
| other | 123 |
| screening_library | 115 |

## manual_review_priority

| Category | Count |
|---|---:|
| high | 4626 |
| medium | 1675 |
| low | 135 |

## Q1-Q7 Query Family Contribution

Query-family contribution is not available in the current public release metadata. The next retrieval run should retain per-article Q1-Q7 family hits so this comparison can be populated without changing record granularity.

## Incremental Fields Added

- `interaction_type`: Controlled interaction class: physical adsorption, nonspecific adsorption, selective adsorption, affinity binding, covalent immobilization, entrapment, antifouling low adsorption, protein fouling, or unknown.
- `is_covalent_binding`: yes/no/unclear flag indicating whether protein binding or immobilization is covalent.
- `experiment_mode_primary`: Coarse controlled assay mode derived from experiment_mode, adsorption_type, detection method, outcome, and evidence.
- `experiment_mode_detail`: Fine controlled assay mode derived from the same fields while preserving the original experiment_mode text.
- `application_context`: Controlled application context: biointerface adsorption, purification, antifouling, protein immobilization, hemocompatibility, screening library, mechanism study, or other.
- `comparable_target_class`: Comparability tier for the selected target: strong, medium, weak, or not_comparable.
- `model_ready_v2`: Rule-derived model-ready flag using standardized interaction/application/comparability fields while keeping the original model_ready column unchanged.
- `model_ready_blocker`: Semicolon-separated reasons preventing model_ready_v2=true, or ready_v2.
- `manual_review_priority`: Rule-derived manual review priority: high, medium, or low.
- `q5_protein_evidence_flag`: Whether an antifouling/low-adsorption candidate has protein, serum, plasma, albumin, fibrinogen, IgG, or total-protein evidence.
- `q5_triage_action`: Q5 protein-antifouling rule action: keep, downweight, exclude_candidate, or not_applicable.
- `standardization_rules_version`: Version identifier for the deterministic standardization rules.
