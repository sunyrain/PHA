# PHA Extraction Fields

Date: 2026-07-01

Project: PHA, Protein Hydrogel Adsorption

## Goal

The PHA database should support data-driven design of hydrogel systems that
adsorb, selectively adsorb, weakly adsorb, or resist adsorption of a target
protein. The extracted data must preserve:

- hydrogel composition, preparation, and physical properties;
- protein identity and protein physicochemical descriptors;
- experimental adsorption/separation/antifouling conditions;
- quantitative outcomes and local controls;
- mechanism evidence and confidence.

## Record Unit

Use one record for:

`paper + hydrogel material + protein target + experimental condition + measured outcome`

Do not compress multiple proteins, hydrogels, pH values, salt concentrations,
temperatures, or time points into one record when they have distinct measured
outcomes.

## Design-Space And Inverse-Design Addendum

The final PHA task is not only extraction. It is inverse design under
multi-protein constraints: design a hydrogel that adsorbs one protein set,
rejects another protein set, and can be matched to a feasible fabrication and
operating process. The literature record schema therefore needs to support
derived design views in addition to single adsorption records.

| Module | Fields |
| --- | --- |
| Design-space position | `application_scenario`, `material_family`, `format_family`, `functionalization_strategy`, `network_structure_level`, `tunable_variables`, `systematic_variable_scan` |
| Protein-panel outcome | `target_protein_set`, `reject_protein_set`, `competitor_protein_set`, `mixture_matrix`, `protein_panel_size`, `protein_adsorption_vector`, `selectivity_ranking` |
| Design constraints | `required_adsorbed_proteins`, `required_rejected_proteins`, `min_adsorption_threshold`, `max_reject_adsorption_threshold`, `min_selectivity_threshold`, `allowed_operating_window` |
| Process matching | `recommended_fabrication_method`, `key_formulation_ratio`, `crosslinking_or_grafting_conditions`, `coating_conditions`, `wash_solution`, `elution_solution`, `regeneration_method`, `sterilization_or_storage`, `scale_up_risk` |
| Feasibility assessment | `precursor_availability`, `synthesis_complexity`, `aqueous_or_mild_preparation`, `toxic_monomer_or_metal_flag`, `reuse_feasibility`, `application_fit` |
| Inverse-design output | `candidate_hydrogel`, `matched_process`, `expected_adsorbed_proteins`, `expected_rejected_proteins`, `supporting_dois`, `extrapolation_risk`, `design_confidence`, `recommended_validation_experiments` |

These fields do not all belong in every literature-extraction row. They should
be used to build three derived tables:

| Derived table | Purpose |
| --- | --- |
| `pha_protein_response_matrix` | Hydrogel-condition rows by protein columns, with adsorption values or labels. |
| `pha_inverse_design_requests` | User or expert design tasks: adsorb set, reject set, operating constraints, and process constraints. |
| `pha_candidate_designs` | Proposed hydrogel recipes, matched processes, evidence records, risks, and validation experiments. |

## Field Priority

- `P0`: required for a useful modeling record.
- `P1`: high value, extract whenever reported.
- `P2`: optional but useful for mechanism, preparation, or quality control.

## Provenance And Evidence

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `record_id` | P0 | string | Stable local ID. Suggested format: `PHA-{doi_hash}-{row}`. |
| `schema_version` | P0 | string | Start with `0.1.0`. |
| `doi` | P0 | string/null | DOI when available. |
| `pmid` | P1 | string/null | PubMed ID when available. |
| `title` | P0 | string | Article title. |
| `year` | P0 | integer/null | Publication year. |
| `journal` | P1 | string/null | Journal name. |
| `query_family` | P1 | array[string] | Search families that retrieved the article, e.g. `Q1`, `Q5`. |
| `source_section` | P1 | string/null | Methods, Results, Table 1, Figure 3, SI, etc. |
| `source_table_or_figure` | P1 | string/null | Exact table/figure identifier if applicable. |
| `evidence_text` | P0 | string | Short evidence snippet or table-cell provenance. |
| `extraction_method` | P1 | enum | `manual`, `llm_fulltext`, `llm_abstract`, `table_parser`, `hybrid`. |
| `extraction_confidence` | P0 | number | 0 to 1. Lower if inferred, unit-ambiguous, or abstract-only. |
| `review_status` | P0 | enum | `raw`, `needs_review`, `reviewed`, `rejected`. |

## Article Triage

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `relevance_label` | P0 | enum | `include`, `maybe`, `exclude`. |
| `relevance_reason` | P1 | string | Short reason for the label. |
| `study_type` | P0 | array[enum] | One or more of the study-type vocabulary below. |
| `is_review` | P1 | boolean/null | Exclude reviews from record extraction unless they contain reusable curated data. |
| `has_quantitative_adsorption` | P0 | boolean | True if capacity, coverage, removal, recovery, fouling reduction, or comparable metric is reported. |
| `has_control_or_comparator` | P1 | boolean | Important for deriving positive/negative labels. |

Study-type vocabulary:

- `adsorption_capacity`
- `separation_purification`
- `antifouling_low_adsorption`
- `imprinting_affinity`
- `mechanism_property`
- `screening_library`
- `protein_immobilization`
- `biocompatibility_fouling`
- `biointerface_blood_contact`
- `protein_corona_competition`
- `formulation_process`
- `ai_training_dataset`

## Hydrogel Identity And Preparation

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `hydrogel_id` | P0 | string | Local material/sample ID. |
| `hydrogel_name` | P0 | string | Author sample code or descriptive name. |
| `hydrogel_format` | P0 | enum | See controlled vocabulary below. |
| `polymer_backbone` | P0 | array[string] | Chitosan, PEG, polyacrylamide, PNIPAm, alginate, cellulose, etc. |
| `monomers` | P1 | array[string] | Monomers/comonomers, e.g. NIPAm, acrylamide, DMAEMA. |
| `monomer_ratios` | P1 | string/null | Preserve reported ratios and units. |
| `crosslinker` | P1 | array[string] | NMBA, glutaraldehyde, PEGDA, modified chitosan, etc. |
| `crosslinker_concentration` | P1 | string/null | Preserve raw value and unit. |
| `initiator` | P2 | array[string] | APS/TEMED, photoinitiator, redox initiator, etc. |
| `synthesis_method` | P1 | array[enum/string] | Free-radical polymerization, cryopolymerization, grafting, coating, microfluidics, etc. |
| `preparation_solvent` | P2 | string/null | Water, buffer, organic solvent, mixed solvent. |
| `preparation_pH` | P2 | number/string/null | Use raw string if not numeric. |
| `preparation_temp_C` | P2 | number/null | Preparation temperature. |
| `gelation_time` | P2 | string/null | Raw reported gelation/polymerization time. |
| `functional_groups` | P0 | array[string] | Amine, carboxyl, sulfonate, quaternary ammonium, phenyl, zwitterion, etc. |
| `ligand_or_affinity_group` | P1 | array[string] | Amino acid ligand, aptamer, boronate, metal-chelate, dye, ion-exchange group. |
| `metal_ion_or_bridge` | P1 | array[string] | Cu(II), Ni(II), Zn(II), etc. |
| `template_molecule` | P1 | string/null | Protein or molecule used for imprinting. |
| `filler_or_composite` | P1 | array[string] | CNC, graphene oxide, silica, magnetic particle, clay, MOF, nanogel, etc. |
| `substrate_or_support` | P1 | string/null | PVC, membrane, column, device, electrode, tissue-culture support. |
| `post_treatment` | P2 | string/null | Washing, template removal, elution, sterilization, drying. |

Hydrogel-format vocabulary:

- `bulk_gel`
- `film`
- `coating`
- `bead`
- `microgel`
- `nanogel`
- `cryogel`
- `monolith`
- `membrane`
- `column_bed`
- `scaffold`
- `composite`
- `other`

## Hydrogel Properties

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `charge_class` | P0 | enum/null | `cationic`, `anionic`, `zwitterionic`, `mixed_charge`, `neutral`, `amphiphilic`, `unknown`. |
| `net_charge_condition` | P1 | string/null | Condition-dependent charge, e.g. positive at pH 7.0. |
| `responsive_type` | P1 | array[enum/string] | pH, temperature, ionic strength, redox, light, enzyme, glucose, none. |
| `lcst_C` | P1 | number/null | Useful for PNIPAm-like systems. |
| `swelling_ratio` | P1 | object/null | Raw value, unit, condition. |
| `water_content_pct` | P2 | number/null | If reported. |
| `porosity_pct` | P1 | number/null | If reported. |
| `pore_size` | P1 | object/null | Value/range, unit, method, condition. |
| `mesh_size` | P1 | object/null | Value/range, unit, method, condition. |
| `surface_area` | P2 | object/null | BET or equivalent. |
| `particle_size` | P1 | object/null | For beads, microgels, nanogels. |
| `zeta_potential_mV` | P1 | object/null | Value and pH/medium. |
| `contact_angle_deg` | P2 | object/null | Surface hydrophilicity. |
| `young_modulus` | P1 | object/null | Value and unit, e.g. MPa/kPa. |
| `adhesion_energy` | P2 | object/null | Important for coatings. |
| `permeability` | P2 | object/null | Especially for cryogels/columns. |
| `thermal_stability` | P2 | string/null | Degradation temperature or TGA note. |
| `cycle_stability` | P1 | object/null | Retained performance after reuse or stress tests. |
| `morphology_method` | P2 | array[string] | SEM, ESEM, AFM, TEM, CLSM, etc. |

For object-valued numeric fields, preserve:

```json
{"value": 5.72, "min": null, "max": null, "unit": "mg/g", "condition": "pH 7, 25 C", "raw_text": "Qmax = 5.72 mg/g"}
```

## Protein Target

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `protein_name` | P0 | string | Full name if available. |
| `protein_abbreviation` | P0 | string/null | BSA, HSA, IgG, OVA, LYZ, FIB, etc. |
| `protein_species_or_source` | P1 | string/null | Bovine, human, chicken egg white, plant extract, recombinant, etc. |
| `protein_role` | P0 | enum | `target`, `template`, `competitor`, `mixture_component`, `fouling_protein`, `immobilized_enzyme`, `unknown`. |
| `molecular_weight_kDa` | P1 | number/null | Reported value or curated canonical value. |
| `pI` | P1 | number/null | Reported or curated value; mark source. |
| `charge_at_experiment_pH` | P1 | enum/null | `positive`, `negative`, `near_neutral`, `mixed`, `unknown`. |
| `protein_initial_concentration` | P0 | object/null | Raw and normalized if possible. |
| `protein_matrix` | P1 | enum/string | Buffer, serum, plasma, egg white, crude extract, mixture, cell-culture medium, whole blood. |
| `competitor_proteins` | P1 | array[string] | Required for selectivity records. |
| `protein_labeling` | P2 | string/null | Fluorescent/radio/biotin labels if used. |
| `protein_class` | P1 | string/null | Albumin, enzyme, antibody, coagulation protein, complement protein, cytokine, food protein, etc. |
| `blood_related` | P1 | boolean/null | Whether the protein is blood/plasma/coagulation related. |
| `inflammation_related` | P1 | boolean/null | Whether the protein is inflammation, immune, complement, or foreign-body-response related. |

## Experiment Conditions

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `experiment_mode` | P0 | enum | Batch, column, surface, QCM, SPR, microarray, flow, implant, hemocompatibility, microscopy. |
| `hydrogel_dosage` | P1 | object/null | Mass, area, volume, bed volume, or coating area. |
| `solution_volume` | P1 | object/null | Protein solution/feed volume. |
| `pH` | P0 | number/string/null | Required when available because charge drives adsorption. |
| `buffer` | P1 | string/null | PBS, phosphate, acetate, Tris, etc. |
| `ionic_strength` | P1 | object/null | If reported separately. |
| `salt_type` | P1 | string/null | NaCl, sodium sulfate, phosphate, etc. |
| `salt_concentration` | P1 | object/null | Value and unit. |
| `temperature_C` | P1 | number/null | Especially for thermoresponsive hydrogels. |
| `contact_time` | P0 | object/null | Incubation/equilibration time, or column residence time. |
| `flow_rate` | P1 | object/null | Column or flow assay. |
| `loading_volume_CV` | P1 | number/null | Column volumes if applicable. |
| `wash_solution` | P2 | string/null | Washing buffer. |
| `elution_solution` | P1 | string/null | Salt, pH, EDTA, competitor, etc. |
| `regeneration_cycles` | P1 | integer/null | Number of reuse cycles tested. |
| `detection_method` | P1 | array[string] | UV-vis, BCA, Bradford, fluorescence, HPLC, electrophoresis, ELISA, QCM, SPR. |
| `replicate_count` | P2 | integer/null | If reported. |
| `adsorption_type` | P1 | enum/null | `endpoint`, `dynamic`, `equilibrium`, `time_course`, `breakthrough`, `unknown`. |
| `competition_system` | P1 | enum/null | `single_protein`, `binary`, `multi_protein`, `serum`, `plasma`, `crude_extract`, `whole_blood`, `unknown`. |
| `desorption_test` | P1 | boolean/null | Whether desorption, elution, or reversibility was explicitly tested. |

## Adsorption And Separation Outcomes

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `outcome_label` | P0 | enum | See controlled vocabulary below. |
| `outcome_basis` | P0 | string | Why this label was assigned. |
| `raw_metric_name` | P0 | string | q, Qmax, removal, recovery, surface coverage, fouling reduction, etc. |
| `raw_metric_value` | P0 | number/string/null | Preserve raw value. |
| `raw_metric_unit` | P0 | string/null | Preserve raw unit. |
| `q_norm_mg_g` | P1 | number/null | Adsorbed protein per dry hydrogel mass. |
| `q_norm_mg_mL_bed` | P1 | number/null | For cryogels/columns/monoliths. |
| `surface_adsorption_ug_cm2` | P1 | number/null | For coatings/surfaces. |
| `removal_efficiency_pct` | P1 | number/null | If removal from solution is reported. |
| `binding_efficiency_pct` | P1 | number/null | If binding fraction is reported. |
| `recovery_pct` | P1 | number/null | Protein recovery after elution/purification. |
| `purity_pct` | P1 | number/null | Purification outcome. |
| `dynamic_binding_capacity` | P1 | object/null | Column breakthrough capacity. |
| `selectivity_factor` | P1 | object/null | Include comparator protein/material. |
| `imprinting_factor` | P1 | number/null | Imprinted vs non-imprinted ratio if available. |
| `association_constant_Ka` | P1 | object/null | Preserve unit, model, condition. |
| `dissociation_constant_Kd` | P1 | object/null | Preserve unit, model, condition. |
| `isotherm_model` | P1 | string/null | Langmuir, Freundlich, Sips, Scatchard, etc. |
| `isotherm_parameters` | P1 | object/null | Model parameters and units. |
| `kinetic_model` | P1 | string/null | PFO, PSO, intraparticle diffusion, etc. |
| `kinetic_parameters` | P1 | object/null | Model parameters and units. |
| `fouling_reduction_pct` | P1 | number/null | For protein-resistant hydrogels. |
| `retained_capacity_pct` | P1 | number/null | After regeneration or stress. |
| `protein_corona` | P1 | object/null | Corona composition, dominant proteins, exchange dynamics, or characterization evidence. |
| `competitive_adsorption_result` | P1 | object/null | Multi-protein competition outcome, adsorption ranking, or replacement behavior. |
| `adsorption_reversibility` | P1 | object/null | Desorption, elution, exchange, hysteresis, or retained binding after wash. |
| `side_outcomes` | P2 | object/null | Platelet adhesion, cell adhesion, bacterial adhesion, thrombus, etc. |

Outcome-label vocabulary:

- `adsorbing`
- `selective_adsorbing`
- `weak_adsorbing`
- `non_adsorbing`
- `antifouling`
- `protein_immobilization`
- `ambiguous`

Extraction rule: do not impose one universal adsorption threshold during
extraction. Store the raw measurement and local control first; derive modeling
labels later under task-specific thresholds.

## Mechanism And Controls

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `mechanism_tags` | P0 | array[enum] | Use controlled vocabulary below. |
| `mechanism_evidence_text` | P1 | string/null | Author claim or direct experimental support. |
| `author_claimed_mechanism` | P1 | boolean | True if the mechanism is stated by the paper. |
| `inferred_mechanism` | P1 | boolean | True if inferred during curation; lower confidence. |
| `control_type` | P1 | enum/string/null | Non-imprinted gel, blank gel, commercial resin, no ligand, opposite charge, etc. |
| `control_material` | P1 | string/null | Name/code of comparator. |
| `control_outcome` | P1 | object/null | Comparator metric. |
| `fold_change_vs_control` | P1 | number/null | If calculable. |
| `comparator_notes` | P2 | string/null | Notes on comparability. |
| `protein_unfolding` | P1 | object/boolean/null | Evidence for protein unfolding, denaturation, or conformational change on the hydrogel. |
| `protein_corona_evidence` | P1 | string/null | Experimental evidence for corona formation, composition, or exchange. |

Mechanism-tag vocabulary:

- `electrostatic_attraction`
- `electrostatic_repulsion`
- `hydrophobic_interaction`
- `hydrogen_bonding`
- `van_der_waals`
- `steric_hindrance`
- `hydration_layer`
- `size_exclusion`
- `pore_diffusion`
- `molecular_imprinting`
- `shape_memory`
- `coordination_metal_bridge`
- `ion_exchange`
- `boronate_affinity`
- `ligand_affinity`
- `aptamer_recognition`
- `pH_responsive`
- `temperature_responsive`
- `salt_responsive`
- `protein_conformation_change`
- `protein_unfolding`
- `protein_corona_formation`
- `competitive_adsorption`
- `unknown`

## Biointerface Response

These fields are expert-added auxiliary outcomes for blood-contacting,
biointerface, wound-dressing, inflammatory, or antifouling contexts. They
should not replace protein adsorption outcomes, but they should be retained
when the paper links protein adsorption to downstream biological response.

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `platelet_adhesion` | P1 | object/null | Platelet adhesion amount, image evidence, or reduction vs control. |
| `platelet_activation` | P1 | object/null | Activation markers or qualitative author claim. |
| `macrophage_polarization` | P2 | object/null | M1/M2 or inflammatory phenotype data. |
| `complement_activation` | P1 | object/null | C3a, C5a, complement deposition, or related markers. |
| `cell_adhesion` | P2 | object/null | Cell adhesion/spreading when tied to protein adsorption or antifouling. |
| `hemocompatibility` | P1 | object/null | Hemolysis, clotting, thrombogenicity, or blood-compatibility evidence. |
| `foreign_body_response` | P2 | object/null | Capsule formation, inflammation, implant response, or in vivo interface outcome. |

## AI Modeling Labels

These fields support later filtering and supervised learning. They can be
assigned after extraction and curation, rather than directly copied from the
paper.

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `application_scenario` | P1 | string/null | Purification, depletion, antifouling coating, blood-contacting material, wound dressing, sensor enrichment, etc. |
| `prediction_target` | P1 | string/null | Classification, capacity regression, selectivity ranking, process recommendation, or mechanism label. |
| `positive_negative_sample` | P1 | enum/null | `positive`, `negative`, `weak`, `mixed`, `ambiguous`. |
| `importance_score` | P2 | number/null | 0-1 curation score for training priority. |
| `usable_for_training` | P1 | boolean/null | Whether the record is suitable for model training after quality checks. |

## Normalization And Quality

| Field | Priority | Type | Notes |
| --- | --- | --- | --- |
| `unit_normalized` | P0 | boolean | True if normalized fields were calculated. |
| `normalization_notes` | P1 | string/null | Document assumptions and conversions. |
| `value_ambiguity` | P1 | string/null | Ambiguous dry/wet mass, bed volume, missing concentration, plot-only data, etc. |
| `missing_conditions` | P1 | array[string] | Important absent metadata, e.g. pH, contact time. |
| `source_quality_score` | P0 | integer | 0 to 3. Suggested rubric below. |
| `needs_manual_review` | P0 | boolean | True for low confidence, inferred values, or plot-only values. |
| `exclusion_reason` | P0 | string/null | Required if relevance is `exclude`. |

Source-quality score:

- `3`: full quantitative record with units, conditions, comparator/control, and clear evidence.
- `2`: quantitative record with most conditions but limited controls or minor ambiguity.
- `1`: semi-quantitative or abstract-only record useful for triage but not final modeling.
- `0`: irrelevant or unusable for extraction.

## First-Pass Extraction Strategy

1. Triage title and abstract into `include`, `maybe`, or `exclude`.
2. Prioritize full text for papers containing capacity, isotherm, kinetic,
   selectivity, recovery, antifouling reduction, or reuse data.
3. Extract article-level metadata once, then emit multiple records for every
   hydrogel-protein-condition-outcome combination.
4. Preserve all raw values and units before normalization.
5. Mark mechanism tags as author-claimed unless they are curator-inferred.
6. Keep adsorption and low-adsorption records in the same schema so the
   eventual model can learn both positive and negative design examples.
