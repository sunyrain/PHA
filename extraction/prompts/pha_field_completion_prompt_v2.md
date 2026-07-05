# PHA Field Completion Prompt v2

Return JSON only. Complete missing preparation, characterization, protein-property,
and assay-condition fields for an already extracted protein-hydrogel adsorption
article.

Use only the supplied article context and existing record list. Do not invent
values. Do not output null, empty strings, empty arrays, or fields that are not
explicitly supported by evidence.

Top-level JSON keys:
- schema_version: "0.2.0"
- prompt_version: "field_completion_v2_compact_patch"
- article
- record_updates
- article_level_properties
- completion_note

For record_updates:
- Output one item only when at least one field can be filled for that exact
  existing record.
- record_id_hint must be the exact existing record_id from
  [EXISTING_RECORDS_WITH_MISSING_FOCUS].
- Include only update sections and fields that contain supported values.
- Keep evidence_text to one short phrase or table row fragment.
- Do not repeat adsorption outcome values unless needed to disambiguate the
  condition attached to the missing field.

Allowed update sections and fields:
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

Each record update must use this compact shape:
{
  "record_id_hint": "exact existing record_id",
  "preparation_update": {"field": "value"},
  "hydrogel_property_update": {"field": "value"},
  "protein_property_update": {"field": "value"},
  "assay_condition_update": {"field": "value"},
  "evidence_text": "short evidence phrase",
  "source_section": "section/table/figure when available",
  "source_table_or_figure": "table/figure id when available",
  "confidence": 0.0
}

Omit any update section that has no supported fields. If a value applies to all
records in the article, repeat it only for records where the corresponding field
is missing and the mapping is clear.

Article-level properties should capture supported characterization data that
cannot be confidently mapped to a single record. Keep each item short and do not
include a separate evidence index.
