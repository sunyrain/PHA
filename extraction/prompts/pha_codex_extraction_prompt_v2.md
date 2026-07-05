# PHA Codex Extraction Prompt v2

You are extracting an auditable fact table for PHA: protein-hydrogel adsorption.

Return JSON only. The JSON must match the requested output shape. Never include prose outside JSON.

The most important unit is one measured observation:

hydrogel sample + protein or protein mixture + condition + measured outcome

Extract multiple records from one paper when the paper reports multiple hydrogels, proteins, pH values, temperatures, time points, columns, controls, or antifouling comparisons. If the context only supports a paper-level triage and no measured observation, return records [] and explain this in extraction_note.

Primary fields to protect from loss:
- hydrogel chemistry: backbone, monomers, crosslinker, functional groups, ligand, metal bridge, filler, format, synthesis method
- protein identity: name, abbreviation, species/source, target/template/competitor role, matrix, reported or inferable MW and pI
- experiment: batch/column/surface/QCM/SPR/flow, pH, buffer, salt, temperature, contact time, dose/area/volume, initial concentration
- outcome: raw metric, raw value, raw unit, capacity, removal, selectivity, recovery, fouling reduction, isotherm, kinetics, binding constants, regeneration
- mechanism: electrostatic, hydrophobic, hydrogen bonding, size exclusion, pore diffusion, imprinting, metal chelation, ion exchange, hydration layer, protein corona, Vroman competition, unfolding
- evidence: table/figure/section and a short quote or table-cell description from the context

Special extraction policy:
- Keep common adsorption fields in records.
- Put paper-specific but important fields in special_fields. Examples: protein corona composition profile, platelet/complement response, sensing limit of detection, enzyme activity retention, drug release confounder, cell adhesion side outcome, unusual material descriptor, high-throughput array layout, data-driven design feature.
- Put all enrichable materials in material_mentions, especially monomers, crosslinkers, ligands, metal ions, buffers, and fillers. Avoid sending generic "hydrogel" or broad polymer mixtures to PubChem unless a named small molecule is present.
- Put all enrichable proteins in protein_mentions. Prefer a UniProt query using full protein name plus species when known.

Output object:
- schema_version: "0.2.0"
- prompt_version: "v2"
- article: paper triage and metadata
- article_common_fields: compact paper-level summary of shared variables
- records: list of PHA adsorption records
- material_mentions: list of material entities for PubChem/manual enrichment
- protein_mentions: list of protein entities for UniProt/manual enrichment
- special_fields: list of unusual or paper-specific facts
- extraction_note: short note about confidence, gaps, and whether extraction is suitable for model training

Controlled labels:
- triage_label: include, maybe, exclude
- study_types: adsorption_capacity, separation_purification, antifouling_low_adsorption, imprinting_affinity, mechanism_property, screening_library, protein_immobilization, biocompatibility_fouling, biointerface_blood_contact, protein_corona_competition, formulation_process, ai_training_dataset
- hydrogel_format: bulk_gel, film, coating, bead, microgel, nanogel, cryogel, monolith, membrane, column_bed, scaffold, composite, other
- experiment_mode: batch, column, surface, qcm, spr, microarray, flow, implant, hemocompatibility, microscopy, other
- outcome_label: adsorbing, selective_adsorbing, weak_adsorbing, non_adsorbing, antifouling, protein_immobilization, ambiguous
- review_status: raw, needs_review, reviewed, rejected

Quality rules:
- Do not invent exact values. If a value is inferred, mark inferred_mechanism or needs_manual_review and explain.
- Use null for missing scalar values and [] for missing arrays.
- Use raw_metric_value and raw_metric_unit even when no normalized value is possible.
- For q_norm_mg_g, only fill when the raw metric is already mg/g dry gel or obviously equivalent.
- For surface adsorption, only fill surface_adsorption_ug_cm2 when the raw metric is a surface coverage or safely convertible.
- If the article is a sensor, drug-delivery, tissue-engineering, or diagnostic paper and protein adsorption is only incidental, mark triage maybe/exclude and use special_fields for relevant side facts.
- If the table reports multiple rows, extract the rows that contain protein adsorption/selectivity/antifouling outcomes. Do not summarize away the best or worst rows.

Required JSON skeleton:
{
  "schema_version": "0.2.0",
  "prompt_version": "v2",
  "article": {
    "doi": null,
    "title": "",
    "publisher": null,
    "journal": null,
    "year": null,
    "triage_label": "maybe",
    "triage_reason": "",
    "study_types": [],
    "has_quantitative_adsorption": false,
    "has_control_or_comparator": null,
    "is_review": null
  },
  "article_common_fields": {
    "main_hydrogel_families": [],
    "main_hydrogel_formats": [],
    "protein_panel": [],
    "condition_variables_scanned": [],
    "outcome_metrics_reported": [],
    "mechanism_tags_reported": [],
    "design_space_notes": null,
    "best_evidence_locations": []
  },
  "records": [],
  "material_mentions": [],
  "protein_mentions": [],
  "special_fields": [],
  "extraction_note": ""
}

For each record, include these nested objects:
provenance, triage, hydrogel, hydrogel_properties, protein, experiment, outcome, mechanism, biointerface_response, ai_modeling_labels, quality.

When uncertain, still return a structurally complete record if there is a measured hydrogel-protein outcome. Use nulls and needs_manual_review rather than dropping the record.
