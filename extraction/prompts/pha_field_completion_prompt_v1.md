# PHA Field Completion Prompt v1

Return JSON only. Complete missing preparation, characterization, protein-property, and assay-condition fields for an already extracted protein-hydrogel adsorption article.

Use only the supplied article context. Do not invent values. Use null for unknown scalar values and [] for unknown arrays.

Top-level JSON keys:
- schema_version: "0.1.0"
- prompt_version: "field_completion_v1"
- article
- record_updates
- article_level_properties
- evidence_index
- completion_note

For each item in record_updates:
- record_id_hint: existing record id, hydrogel name, protein name, or condition hint when provided.
- hydrogel_name
- protein_name
- preparation_update:
  - monomer_ratios
  - crosslinker_concentration
  - initiator
  - synthesis_method
  - preparation_solvent
  - preparation_pH
  - preparation_temp_C
  - gelation_time
  - post_treatment
  - washing_or_conditioning
  - storage_condition
- hydrogel_property_update:
  - swelling_ratio
  - water_content_pct
  - porosity_pct
  - pore_size
  - mesh_size
  - surface_area
  - particle_size
  - thickness
  - roughness
  - zeta_potential_mV
  - contact_angle_deg
  - young_modulus
  - mechanical_modulus
  - responsive_type
  - degradation_or_stability
- protein_property_update:
  - molecular_weight_kDa
  - pI
  - charge_at_experiment_pH
  - protein_initial_concentration
  - protein_matrix
  - competitor_proteins
- assay_condition_update:
  - experiment_mode
  - pH
  - buffer
  - ionic_strength
  - salt_type
  - salt_concentration
  - temperature_C
  - contact_time
  - hydrogel_dosage
  - solution_volume
  - flow_rate
  - detection_method
  - replicate_count
- evidence_text: short exact evidence phrase from the context.
- source_section
- source_table_or_figure
- confidence: 0 to 1.

Article-level properties should capture characterization data that apply to all records in the article or to a material family but cannot be confidently mapped to a single record.

Do not re-extract adsorption outcome values unless they are needed to disambiguate the condition attached to a missing field. If a field is absent from the article, leave it null/[] and say so in completion_note.
