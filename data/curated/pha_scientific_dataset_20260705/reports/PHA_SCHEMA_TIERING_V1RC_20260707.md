# PHA Schema Tiering v1.0-rc

Generated: 2026-07-07

## Recommendation

Split the PHA record schema into two layers:

- `records_core_v1rc_20260707.csv`: compact main table for browsing, filtering, splits, and first-pass modeling.
- `record_additional_values_v1rc_20260707.csv`: record-level long-form companion table for sparse preparation, property, endpoint-specific, provenance, and control values.
- `field_tiers_v1rc_20260707.csv`: field-level tier map describing whether each fixed field is a main field or an additional value.

Keep `records_flat.csv` as the archival wide table for backward compatibility, but do not use it as the default display/modeling table.

## Counts

- Fixed fields reviewed: 90
- Main fields: 29
- Additional-value fields: 61
- Core table size: 6436 rows x 45 columns
- Additional long table: 135746 rows

## Tier Counts

| tier | fields | additional rows |
|---|---:|---:|
| control_detail | 3 | 13516 |
| core_experiment | 8 | 0 |
| core_identity | 3 | 0 |
| core_interpretation | 1 | 0 |
| core_material | 7 | 0 |
| core_outcome | 4 | 0 |
| core_protein | 4 | 0 |
| core_quality | 2 | 0 |
| endpoint_model_detail | 2 | 1413 |
| endpoint_value | 14 | 5805 |
| experiment_detail | 10 | 31091 |
| material_detail | 2 | 6053 |
| preparation_detail | 9 | 28631 |
| property_detail | 15 | 23156 |
| protein_descriptor_detail | 3 | 7166 |
| provenance_detail | 2 | 12479 |
| quality_detail | 1 | 6436 |

## Main Fields

Main fields are limited to identity, material backbone, protein identity, core experimental conditions, raw outcome, mechanism tags, and quality gates.

| tier | field | effective coverage | label |
|---|---|---:|---|
| core_experiment | `experiment.adsorption_type` | 99.98% | Adsorption type |
| core_experiment | `experiment.buffer` | 80.92% | Buffer |
| core_experiment | `experiment.competition_system` | 85.13% | Competition system |
| core_experiment | `experiment.contact_time` | 78.67% | Contact time |
| core_experiment | `experiment.detection_method` | 95.62% | Detection |
| core_experiment | `experiment.experiment_mode` | 100.00% | Experiment mode |
| core_experiment | `experiment.pH` | 71.75% | Assay pH |
| core_experiment | `experiment.temperature_C` | 68.97% | Temperature |
| core_identity | `provenance.doi` | 100.00% | DOI |
| core_identity | `provenance.title` | 100.00% | Article title |
| core_identity | `provenance.year` | 100.00% | Year |
| core_interpretation | `mechanism.mechanism_tags` | 99.83% | Mechanism tags |
| core_material | `hydrogel.crosslinker` | 81.63% | Crosslinker |
| core_material | `hydrogel.functional_groups` | 95.46% | Functional groups |
| core_material | `hydrogel.hydrogel_format` | 99.98% | Format |
| core_material | `hydrogel.hydrogel_name` | 99.97% | Hydrogel |
| core_material | `hydrogel.monomers` | 95.20% | Monomers |
| core_material | `hydrogel.polymer_backbone` | 98.01% | Backbone |
| core_material | `hydrogel.synthesis_method` | 97.59% | Synthesis method |
| core_outcome | `outcome.outcome_label` | 100.00% | Outcome label |
| core_outcome | `outcome.raw_metric_name` | 100.00% | Raw metric |
| core_outcome | `outcome.raw_metric_unit` | 63.53% | Raw unit |
| core_outcome | `outcome.raw_metric_value` | 94.76% | Raw value |
| core_protein | `protein.protein_abbreviation` | 77.35% | Protein abbreviation |
| core_protein | `protein.protein_name` | 99.89% | Protein |
| core_protein | `protein.protein_role` | 100.00% | Protein role |
| core_protein | `protein.protein_species_or_source` | 83.53% | Protein source |
| core_quality | `quality.needs_manual_review` | 100.00% | Needs review |
| core_quality | `quality.source_quality_score` | 100.00% | Quality score |

## Additional Value Fields

These fields are retained, but not promoted into the main table. They are sparse, article-type-specific, endpoint-specific, descriptor-like, or provenance/control details.

| tier | fields | field list |
|---|---:|---|
| control_detail | 3 | `mechanism.control_material`, `mechanism.control_type`, `mechanism.fold_change_vs_control` |
| endpoint_model_detail | 2 | `outcome.isotherm_model`, `outcome.kinetic_model` |
| endpoint_value | 14 | `outcome.association_constant_Ka`, `outcome.binding_efficiency_pct`, `outcome.dissociation_constant_Kd`, `outcome.dynamic_binding_capacity`, `outcome.fouling_reduction_pct`, `outcome.imprinting_factor`, `outcome.purity_pct`, `outcome.q_norm_mg_g`, `outcome.q_norm_mg_mL_bed`, `outcome.recovery_pct`, `outcome.removal_efficiency_pct`, `outcome.retained_capacity_pct`, `outcome.selectivity_factor`, `outcome.surface_adsorption_ug_cm2` |
| experiment_detail | 10 | `experiment.flow_rate`, `experiment.hydrogel_dosage`, `experiment.ionic_strength`, `experiment.replicate_count`, `experiment.salt_concentration`, `experiment.salt_type`, `experiment.solution_volume`, `protein.competitor_proteins`, `protein.protein_initial_concentration`, `protein.protein_matrix` |
| material_detail | 2 | `hydrogel.filler_or_composite`, `hydrogel.ligand_or_affinity_group` |
| preparation_detail | 9 | `hydrogel.crosslinker_concentration`, `hydrogel.gelation_time`, `hydrogel.initiator`, `hydrogel.monomer_ratios`, `hydrogel.post_treatment`, `hydrogel.preparation_pH`, `hydrogel.preparation_solvent`, `hydrogel.preparation_temp_C`, `hydrogel.substrate_or_support` |
| property_detail | 15 | `hydrogel_properties.charge_class`, `hydrogel_properties.contact_angle_deg`, `hydrogel_properties.degradation_or_stability`, `hydrogel_properties.mesh_size`, `hydrogel_properties.particle_size`, `hydrogel_properties.pore_size`, `hydrogel_properties.porosity_pct`, `hydrogel_properties.responsive_type`, `hydrogel_properties.roughness`, `hydrogel_properties.surface_area`, `hydrogel_properties.swelling_ratio`, `hydrogel_properties.thickness`, `hydrogel_properties.water_content_pct`, `hydrogel_properties.young_modulus`, `hydrogel_properties.zeta_potential_mV` |
| protein_descriptor_detail | 3 | `protein.charge_at_experiment_pH`, `protein.molecular_weight_kDa`, `protein.pI` |
| provenance_detail | 2 | `provenance.source_section`, `provenance.source_table_or_figure` |
| quality_detail | 1 | `quality.unit_normalized` |

## Key Demotions In This Pass

- `hydrogel.ligand_or_affinity_group`: raw coverage 99.67%, effective coverage 61.36%. Many records contain empty-list or generic values, so it works better as material detail.
- `hydrogel.filler_or_composite`: raw coverage 99.78%, effective coverage 32.69%. True coverage is low and fillers/composites are not universal across hydrogel systems.
- `protein.competitor_proteins`: raw coverage 100.00%, effective coverage 24.38%. Empty lists inflated raw coverage; keep it as competition-system detail.
- `hydrogel_properties.responsive_type`: raw coverage 95.84%, effective coverage 56.51%. It is often conceptual and not directly comparable, so it belongs in detail/additional values.

## Default Usage

- Website main list: use `records_core` semantics and show only DOI/year/hydrogel/protein/mode/target/value/quality.
- Record detail page: join `record_additional_values` by `record_id` and group by preparation/property/endpoint/control/provenance.
- Modeling: start from `model_records.csv` or `records_core_v1rc_20260707.csv`, then selectively join `endpoint_value`, `property_detail`, or `preparation_detail`.
- Scientific Data package: describe `records_flat.csv` as the archival wide table and `record_additional_values` as the sparse long-form companion table.

## Files

- `field_tiers_v1rc_20260707.csv`
- `records_core_v1rc_20260707.csv`
- `record_additional_values_v1rc_20260707.csv`
