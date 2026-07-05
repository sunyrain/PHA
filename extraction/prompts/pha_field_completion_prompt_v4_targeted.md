# PHA Field Completion Prompt v4 Targeted Patch

Return JSON only. Complete missing fields for an existing protein-hydrogel
adsorption article by emitting patch records, not rewritten records.

Use only the supplied article context and existing record list. Do not invent
experimental values. If a value is not directly supported by local evidence,
omit it. External descriptors, literature priors, and inferred values must not
be written as observed experimental patches.

Top-level JSON keys:
- schema_version: "0.3.0"
- prompt_version: "field_completion_v4_targeted_patch"
- article
- record_patches
- article_level_properties
- completion_note

Article object:
- doi
- title
- article_type
- article_type_reason

article_type must be one of:
- cryogel_column
- mip_imprinting
- antifouling_surface
- enzyme_immobilization
- micro_nanogel
- general_batch_adsorption

Choose article_type from article evidence, not only from the hint. Use the hint
only as a weak prior.

Record patch object:
{
  "record_id": "exact existing record_id",
  "target_path": "section.field",
  "value": "scalar, array, or object value",
  "value_origin": "observed_fulltext",
  "evidence_text": "short quote or table-row fragment from context",
  "source_section": "Methods/Table/Figure/Results section name",
  "source_table_or_figure": "table/figure id if available",
  "confidence": 0.0,
  "field_rationale": "why this field maps to this record"
}

Rules:
- record_id must exactly match a record_id from [EXISTING_RECORDS_WITH_MISSING_FOCUS].
- target_path must be one of the allowed paths below.
- value_origin must be "observed_fulltext" for all record_patches.
- evidence_text and source_section are required for every patch.
- Only output patches for fields that are missing in the existing record list.
- If a value applies to every record and the mapping is clear, repeat one patch
  per exact record_id.
- If the value is article-level but cannot be mapped to exact record_id, put it
  in article_level_properties instead.
- Do not output null, empty strings, empty arrays, "unknown", or "not reported".
- Prefer compact numeric objects for measured values:
  {"value": 10, "unit": "um", "raw_text": "pores of 10 um"}.

Allowed target_path values:
- hydrogel.monomer_ratios
- hydrogel.crosslinker_concentration
- hydrogel.initiator
- hydrogel.synthesis_method
- hydrogel.preparation_solvent
- hydrogel.preparation_pH
- hydrogel.preparation_temp_C
- hydrogel.gelation_time
- hydrogel.post_treatment
- hydrogel_properties.swelling_ratio
- hydrogel_properties.water_content_pct
- hydrogel_properties.porosity_pct
- hydrogel_properties.pore_size
- hydrogel_properties.mesh_size
- hydrogel_properties.surface_area
- hydrogel_properties.particle_size
- hydrogel_properties.thickness
- hydrogel_properties.roughness
- hydrogel_properties.zeta_potential_mV
- hydrogel_properties.contact_angle_deg
- hydrogel_properties.young_modulus
- hydrogel_properties.responsive_type
- hydrogel_properties.degradation_or_stability
- protein.molecular_weight_kDa
- protein.pI
- protein.charge_at_experiment_pH
- protein.protein_initial_concentration
- protein.protein_matrix
- protein.competitor_proteins
- experiment.experiment_mode
- experiment.pH
- experiment.buffer
- experiment.ionic_strength
- experiment.salt_type
- experiment.salt_concentration
- experiment.temperature_C
- experiment.contact_time
- experiment.hydrogel_dosage
- experiment.solution_volume
- experiment.flow_rate
- experiment.detection_method
- experiment.replicate_count
- outcome.q_norm_mg_g
- outcome.q_norm_mg_mL_bed
- outcome.surface_adsorption_ug_cm2
- outcome.removal_efficiency_pct
- outcome.binding_efficiency_pct
- outcome.recovery_pct
- outcome.purity_pct
- outcome.dynamic_binding_capacity
- outcome.selectivity_factor
- outcome.imprinting_factor
- outcome.association_constant_Ka
- outcome.dissociation_constant_Kd
- outcome.fouling_reduction_pct
- outcome.retained_capacity_pct
- outcome.raw_metric_value
- outcome.raw_metric_unit

Targeted extraction by article_type:

cryogel_column:
- Prioritize cryogelation/freezing temperature, thawing/washing, monomer and
  crosslinker recipe, ligand activation, bed volume, flow rate, loading volume,
  breakthrough/dynamic binding capacity, pore size, swelling, pressure or
  stability, regeneration cycles.

mip_imprinting:
- Prioritize template molecule/protein, functional monomer ratio, crosslinker
  concentration, initiator, polymerization conditions, washing/template removal,
  imprinting factor, selectivity factor, binding constant, pH and temperature.

antifouling_surface:
- Prioritize coating/film thickness, support/substrate if present, contact
  angle, roughness, zeta potential, protein surface adsorption, fouling
  reduction, serum/plasma conditions, controls, incubation time.

enzyme_immobilization:
- Prioritize enzyme identity, immobilization chemistry, crosslinker/spacer,
  enzyme loading, retained activity/capacity, flow/incubation conditions,
  storage/reuse stability, temperature and pH.

micro_nanogel:
- Prioritize particle size, DLS/TEM/SEM method, zeta potential, swelling,
  LCST/responsive class, monomer/crosslinker ratios, protein loading,
  adsorption or release condition.

general_batch_adsorption:
- Prioritize monomer/crosslinker recipe, pH, buffer, ionic strength, protein
  concentration, hydrogel dose, solution volume, contact time, temperature,
  q/equilibrium/kinetic/isotherm parameters.

article_level_properties item:
{
  "field_name": "short field name or section.field",
  "value": "supported value",
  "value_origin": "observed_fulltext",
  "evidence_text": "short evidence phrase",
  "source_section": "section/table/figure",
  "source_table_or_figure": "table/figure id if available",
  "confidence": 0.0,
  "why_article_level": "why it cannot be safely assigned to one record"
}

If nothing can be safely filled, return an empty record_patches array and
explain briefly in completion_note.
