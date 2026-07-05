# PHA extraction coverage and SOTA database comparison - 2026-07-05

## 1. Package audited

- Curated package: `PHA/data/curated/pha_scientific_dataset_20260705`
- Source DB: `PHA/data/processed/pha_extraction_1000_xhigh_fulltext_w8/codex_extraction_results.db`
- Audit JSON: `PHA/data/processed/pha_extraction_1000_xhigh_fulltext_w8/quality_audit_20260705_034010.json`
- Complete field coverage table: `PHA/data/curated/pha_scientific_dataset_20260705/metadata/field_coverage.csv`

## 2. Extraction status

| item | count |
|---|---:|
| local extractable articles | 1230 |
| successful articles | 985 |
| partial/no-record articles | 245 |
| failed articles | 0 |
| record-level rows | 6436 |
| conservative model-ready rows | 2325 |
| inverse-design seed rows | 2325 |
| material mentions | 13662 |
| protein mentions | 4290 |
| special fields | 5363 |

Interpretation:

- `success` means at least one record-level protein-hydrogel adsorption, binding, immobilization, antifouling, or related measurable interaction was extracted.
- `partial` means the article was processed without an extraction error but yielded zero record rows.
- `failed` is now zero after recovering the HydroMIP DOI `10.1016/j.aca.2013.11.052`.

The primary training surfaces are:

- `data/model_records.csv`
- `data/inverse_design_seed.csv`
- `data/records_raw.jsonl` for audit and outlier tracing

## 3. Field-group coverage

| group | coverage | comment |
|---|---:|---|
| provenance | 98.98% | strong; DOI/title/evidence nearly complete |
| hydrogel identity | 70.28% | usable for modeling; material naming still heterogeneous |
| preparation | 19.58% | main bottleneck for inverse design |
| hydrogel properties | 15.11% | sparse; denominator includes roughness/thickness/stability fields |
| protein | 64.21% | good for protein identity; MW/pI only medium coverage |
| experiment | 54.12% | pH/contact-time/buffer useful, replicate count sparse |
| outcome | 22.68% | expected because multiple target types compete |
| mechanism/quality | 89.41% | mechanism/control/quality flags mostly present |

The apparent low outcome-group percentage does not mean targets are absent. It reflects a wide target schema where each row usually has only one or a few outcome types.

## 4. Key field coverage

High coverage fields:

| field | present | coverage |
|---|---:|---:|
| `provenance.doi` | 6436 | 100.00% |
| `provenance.evidence_text` | 6436 | 100.00% |
| `hydrogel.hydrogel_name` | 6434 | 99.97% |
| `hydrogel.hydrogel_format` | 6435 | 99.98% |
| `hydrogel.polymer_backbone` | 6391 | 99.30% |
| `hydrogel.monomers` | 6436 | 100.00% |
| `hydrogel.functional_groups` | 6436 | 100.00% |
| `protein.protein_name` | 6429 | 99.89% |
| `protein.protein_role` | 6436 | 100.00% |
| `experiment.experiment_mode` | 6436 | 100.00% |
| `outcome.raw_metric_name` | 6436 | 100.00% |
| `quality.source_quality_score` | 6436 | 100.00% |

Medium coverage fields:

| field | present | coverage |
|---|---:|---:|
| `protein.protein_abbreviation` | 4978 | 77.35% |
| `protein.protein_species_or_source` | 5381 | 83.61% |
| `protein.protein_initial_concentration` | 4487 | 69.72% |
| `protein.protein_matrix` | 5998 | 93.19% |
| `experiment.hydrogel_dosage` | 3480 | 54.07% |
| `experiment.solution_volume` | 3371 | 52.38% |
| `experiment.pH` | 3826 | 59.45% |
| `experiment.buffer` | 4678 | 72.68% |
| `experiment.temperature_C` | 3164 | 49.16% |
| `experiment.contact_time` | 4567 | 70.96% |
| `experiment.detection_method` | 6027 | 93.65% |
| `outcome.raw_metric_value` | 5984 | 92.98% |
| `outcome.raw_metric_unit` | 5146 | 79.96% |

Low but important fields:

| field | present | coverage |
|---|---:|---:|
| `hydrogel.monomer_ratios` | 281 | 4.37% |
| `hydrogel.crosslinker_concentration` | 219 | 3.40% |
| `hydrogel.initiator` | 126 | 1.96% |
| `hydrogel.preparation_solvent` | 139 | 2.16% |
| `hydrogel.preparation_pH` | 6 | 0.09% |
| `hydrogel.preparation_temp_C` | 155 | 2.41% |
| `hydrogel.gelation_time` | 63 | 0.98% |
| `hydrogel.post_treatment` | 181 | 2.81% |
| `hydrogel_properties.surface_area` | 39 | 0.61% |
| `hydrogel_properties.zeta_potential_mV` | 429 | 6.67% |
| `hydrogel_properties.contact_angle_deg` | 607 | 9.43% |
| `hydrogel_properties.young_modulus` | 345 | 5.36% |
| `experiment.replicate_count` | 132 | 2.05% |

Property fields with useful but incomplete coverage:

| field | present | coverage |
|---|---:|---:|
| `hydrogel_properties.swelling_ratio` | 1654 | 25.70% |
| `hydrogel_properties.pore_size` | 1874 | 29.12% |
| `hydrogel_properties.particle_size` | 1954 | 30.36% |
| `protein.molecular_weight_kDa` | 2243 | 34.85% |
| `protein.pI` | 2020 | 31.39% |
| `protein.charge_at_experiment_pH` | 2269 | 35.25% |

Full field-by-field coverage is in `metadata/field_coverage.csv`.

## 5. Target coverage and model readiness

Audit-level usable numeric target, without manual-review rows:

- `records_with_any_target_and_not_review`: 2652
- percentage of all records: 41.21%

Conservative model-ready table:

- `model_records.csv`: 2325 rows
- stricter rule: successful source article, numeric target, `needs_manual_review = false`, source-quality score >= 2, hydrogel identity present, and protein identity present.

Model split:

| split | all records | model records |
|---|---:|---:|
| train | 5262 | 1909 |
| validation | 596 | 241 |
| test | 578 | 175 |

Main targets in `model_records.csv`:

| target | rows |
|---|---:|
| `q_norm_mg_g` | 894 |
| `surface_adsorption_ug_cm2` | 278 |
| `recovery_pct` | 197 |
| `binding_efficiency_pct` | 172 |
| `retained_capacity_pct` | 92 |
| `fouling_reduction_pct` | 89 |
| `removal_efficiency_pct` | 60 |
| `purity_pct` | 14 |

Recommended first supervised targets:

1. `q_norm_mg_g`
2. `surface_adsorption_ug_cm2`
3. `recovery_pct`
4. `binding_efficiency_pct`
5. `fouling_reduction_pct`

## 6. Dataset composition

Most frequent proteins:

| protein | records |
|---|---:|
| bovine serum albumin | 1350 |
| lysozyme | 788 |
| fibrinogen | 193 |
| human serum albumin | 190 |
| immunoglobulin G | 187 |
| hemoglobin | 117 |
| lipase | 111 |
| human immunoglobulin G | 94 |
| cytochrome c | 73 |
| ovalbumin | 53 |

Most frequent hydrogel formats:

| format | records |
|---|---:|
| cryogel column | 207 |
| monolithic cryogel column | 157 |
| nanogel | 144 |
| supermacroporous cryogel column | 96 |
| microgel | 89 |
| membrane | 73 |
| microspheres | 71 |
| contact lens | 64 |
| bulk hydrogel | 61 |

Most frequent experiment modes:

| mode | records |
|---|---:|
| batch adsorption | 388 |
| batch incubation | 104 |
| continuous column adsorption | 96 |
| static batch adsorption | 87 |
| batch adsorption isotherm | 79 |
| static incubation | 78 |
| batch adsorption kinetics | 61 |
| batch immobilization | 60 |

## 7. Partial/no-record audit

The 245 partial articles are not extraction failures. They were processed but no record-level protein-hydrogel adsorption row was produced.

Rough title-based categories:

| category | articles |
|---|---:|
| non-protein ion/dye/metal/DNA adsorption | 180 |
| protein word present but no adsorption record | 23 |
| other or needs title-level manual review | 19 |
| release/delivery/drug/cell/tissue focus | 17 |
| sensing/imaging/catalysis | 3 |
| antibacterial/biofouling non-protein | 2 |
| materials/methods only | 1 |

Recommendation: keep `metadata/partial_articles.csv` and `sources.csv` for provenance. They are already excluded from record-level training tables.

## 8. External descriptor enrichment

Current descriptor exports:

| table | rows | matched | needs review / not queried |
|---|---:|---:|---:|
| `material_descriptors.csv` | 13662 | 931 PubChem matches | 12724 not queried, 7 errors |
| `protein_descriptors.csv` | 4290 | 338 UniProt matches | 272 matched but needs review, 3951 not queried |

Use these cautiously:

- PubChem matches are useful for monomers, crosslinkers, ligands, small fillers, and ions.
- UniProt matches are noisy for broad terms such as albumin, IgG, protein A, enzyme, or generic species-free names.
- For sequence embeddings, use only `qa_status == usable` first, then manually review `needs_review`.

## 9. International SOTA database landscape

### Closest domain match: BAD 2.0

The Biomolecular Adsorption Database (BAD) is the closest public protein-adsorption database. It aggregates literature-derived protein adsorption data at solid-liquid interfaces, stores data in MySQL, and provides searchable/filterable tables. Its schema includes protein, PDB ID, surface concentration, solution concentration, adsorbing surface, contact angle, surface tension, pH, ionic strength, temperature, method, experiment type, reference DOI, year, validation, and notes.

Source: https://molecularsense.com/bad-2/

Comparison with PHA:

- BAD is surface-adsorption oriented and broad across solid surfaces.
- PHA is narrower in material class but richer for hydrogel/cryogel/nanogel adsorption, chromatography, immobilization, imprinting, antifouling, and hydrogel-specific inverse-design fields.
- BAD emphasizes protein/surface/fluid descriptors; PHA additionally keeps hydrogel preparation, material format, monomers, crosslinkers, ligands, fillers, and record-level evidence text.

### Biomaterials literature infrastructure: DEBBIE and BIOMATDB

DEBBIE is an automatically curated biomaterials literature database from PubMed abstracts, with annotations over biomaterial-related entity classes. It is useful for literature discovery and ontology-backed retrieval, not direct quantitative adsorption modeling.

Source: https://debbie.bsc.es/

BIOMATDB aims to create an advanced biomaterials database/marketplace with detailed biomaterial properties, biological testing, visual analytics, and decision support for biomaterials and medical-device use cases.

Source: https://www.biomatdb.eu/

Comparison with PHA:

- DEBBIE/BIOMATDB are broader biomaterials resources.
- PHA is more measurement-centric for one specific task: hydrogel-protein adsorption/retention/fouling/immobilization records.
- PHA currently has stronger quantitative modeling tables than DEBBIE-style abstract annotations, but weaker controlled ontology coverage.

### Polymer/materials databases

PoLyInfo is the strongest established polymer-property database. NIMS reports more than 552k property points, about 100 property types, polymer structures, monomers, polymerization methods, processing, and measurement conditions. It is not protein-adsorption-specific and has strict anti-scraping/use restrictions.

Source: https://polymer.nims.go.jp/

OpenPoly is a 2025 open experimental polymer database/benchmark with 3985 polymer-property points across 26 properties and model benchmarks. It is useful as a modern benchmark pattern for polymer ML packaging.

Source: https://link.springer.com/article/10.1007/s10118-025-3402-y

Polymer Genome is explicitly an informatics/prediction platform, not a database, and focuses on polymer property prediction from repeat-unit SMILES.

Source: https://www.polymergenome.org/

Comparison with PHA:

- Polymer databases provide broader polymer-property descriptors and benchmark conventions.
- PHA provides interaction/outcome records involving hydrogel material + protein + condition + target, which polymer-property databases generally do not cover.
- PHA should borrow their descriptor discipline: polymer identifiers, monomer structures, processing/measurement conditions, and benchmark splits.

### General FAIR materials data infrastructure

MDF provides dataset publishing/discovery/access infrastructure and reports 880+ datasets, 600+ TB hosted, and 60+ ML-ready datasets.

Source: https://www.materialsdatafacility.org/

NOMAD provides free/open-source materials data management and FAIR structured extraction/metadata over millions of materials-science data items from codes, sources, and workflows.

Source: https://nomad-lab.eu/

Materials Project is a public DOE-backed resource for precomputed materials properties and API-driven access, mostly inorganic crystals/molecules rather than biomaterial adsorption experiments.

Source: https://docs.materialsproject.org/

Comparison with PHA:

- These are infrastructure-scale and schema/FAIR exemplars.
- PHA is a task-specific literature-mined dataset. Its scale is much smaller, but its record definition is much closer to hydrogel inverse design than general computational-materials repositories.

## 10. Overall assessment

Strengths:

- Failed articles are cleared.
- Record IDs are stable and unique.
- Provenance/evidence coverage is strong.
- Core identity and outcome extraction are usable.
- DOI-level split, raw JSON, flat table, descriptors, and checksums are in place.
- The dataset is already usable for first-round tabular ML and inverse-design baseline work.

Main weaknesses:

- Preparation stoichiometry and processing details are sparse.
- Hydrogel physical properties are sparse and unevenly reported.
- External descriptors are only partially enriched.
- Protein sequence mapping requires QA before deep protein embeddings.
- Some target names outside the main normalized targets remain heterogeneous and should be cleaned before multitask modeling.

Recommended next work:

1. Train a first CatBoost/LightGBM baseline on `inverse_design_seed.csv`.
2. Use DOI split only; avoid random row split for claims.
3. Run outlier audit on `q_norm_mg_g > 1000`, very high `surface_adsorption_ug_cm2`, and percentages >100.
4. Normalize target taxonomy before multitask learning.
5. Manually enrich top monomers/crosslinkers/ligands in the 2325 model rows.
6. QA UniProt accessions before sequence embeddings.
7. Treat PHA as complementary to BAD 2.0: hydrogel-specific, condition-rich, inverse-design oriented.
