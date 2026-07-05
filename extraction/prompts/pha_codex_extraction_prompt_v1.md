# PHA Codex Extraction Prompt v1

You are extracting data for the PHA project: protein-hydrogel adsorption.

Task:
Extract structured facts from one paper. The record unit is:

paper + hydrogel material + protein target + experimental condition + measured outcome

Return JSON only. Do not use Markdown. Do not invent values. If a field is not reported, use null, an empty array, or an explicit uncertainty note. Keep raw units and evidence text.

Core extraction goals:
1. Decide whether the paper is relevant to hydrogel-protein adsorption, binding, capture, fouling, antifouling, protein corona, protein immobilization, or separation.
2. Extract one record per distinct hydrogel-protein-condition-outcome combination.
3. Preserve quantitative values, raw units, local controls, mechanism evidence, and source table/figure/section.
4. Record paper-level common fields and paper-specific special fields that do not fit the common adsorption record.
5. Extract material and protein mentions that can be enriched later with PubChem, UniProt, RCSB PDB, or curated descriptors.

Output shape:
{
  "schema_version": "0.2.0",
  "prompt_version": "v1",
  "article": {
    "doi": string|null,
    "title": string,
    "publisher": string|null,
    "journal": string|null,
    "year": integer|null,
    "triage_label": "include"|"maybe"|"exclude",
    "triage_reason": string,
    "study_types": [string],
    "has_quantitative_adsorption": boolean,
    "has_control_or_comparator": boolean|null,
    "is_review": boolean|null
  },
  "article_common_fields": {
    "main_hydrogel_families": [string],
    "main_hydrogel_formats": [string],
    "protein_panel": [string],
    "condition_variables_scanned": [string],
    "outcome_metrics_reported": [string],
    "mechanism_tags_reported": [string],
    "design_space_notes": string|null,
    "best_evidence_locations": [string]
  },
  "records": [
    {
      "record_id": string,
      "schema_version": "0.1.0",
      "provenance": {
        "doi": string|null,
        "pmid": string|null,
        "title": string,
        "year": integer|null,
        "journal": string|null,
        "query_family": [string],
        "source_section": string|null,
        "source_table_or_figure": string|null,
        "evidence_text": string,
        "extraction_method": "llm_fulltext"|"table_parser"|"hybrid"|"llm_abstract"|null,
        "extraction_confidence": number,
        "review_status": "raw"|"needs_review"|"reviewed"|"rejected"
      },
      "triage": {
        "relevance_label": "include"|"maybe"|"exclude",
        "relevance_reason": string|null,
        "study_type": [string],
        "is_review": boolean|null,
        "has_quantitative_adsorption": boolean,
        "has_control_or_comparator": boolean|null
      },
      "hydrogel": {
        "hydrogel_id": string,
        "hydrogel_name": string,
        "hydrogel_format": "bulk_gel"|"film"|"coating"|"bead"|"microgel"|"nanogel"|"cryogel"|"monolith"|"membrane"|"column_bed"|"scaffold"|"composite"|"other",
        "polymer_backbone": [string],
        "monomers": [string],
        "monomer_ratios": string|null,
        "crosslinker": [string],
        "crosslinker_concentration": string|null,
        "initiator": [string],
        "synthesis_method": [string],
        "functional_groups": [string],
        "ligand_or_affinity_group": [string],
        "metal_ion_or_bridge": [string],
        "template_molecule": string|null,
        "filler_or_composite": [string],
        "substrate_or_support": string|null,
        "post_treatment": string|null
      },
      "hydrogel_properties": object,
      "protein": {
        "protein_name": string,
        "protein_abbreviation": string|null,
        "protein_species_or_source": string|null,
        "protein_role": "target"|"template"|"competitor"|"mixture_component"|"fouling_protein"|"immobilized_enzyme"|"unknown",
        "molecular_weight_kDa": number|null,
        "pI": number|null,
        "charge_at_experiment_pH": "positive"|"negative"|"near_neutral"|"mixed"|"unknown"|null,
        "protein_initial_concentration": object|null,
        "protein_matrix": string|null,
        "competitor_proteins": [string],
        "protein_labeling": string|null,
        "protein_class": string|null,
        "blood_related": boolean|null,
        "inflammation_related": boolean|null
      },
      "experiment": {
        "experiment_mode": "batch"|"column"|"surface"|"qcm"|"spr"|"microarray"|"flow"|"implant"|"hemocompatibility"|"microscopy"|"other",
        "hydrogel_dosage": object|null,
        "solution_volume": object|null,
        "pH": number|string|null,
        "buffer": string|null,
        "ionic_strength": object|null,
        "salt_type": string|null,
        "salt_concentration": object|null,
        "temperature_C": number|null,
        "contact_time": object|null,
        "flow_rate": object|null,
        "loading_volume_CV": number|null,
        "wash_solution": string|null,
        "elution_solution": string|null,
        "regeneration_cycles": integer|null,
        "detection_method": [string],
        "replicate_count": integer|null,
        "adsorption_type": "endpoint"|"dynamic"|"equilibrium"|"time_course"|"breakthrough"|"unknown"|null,
        "competition_system": "single_protein"|"binary"|"multi_protein"|"serum"|"plasma"|"crude_extract"|"whole_blood"|"unknown"|null,
        "desorption_test": boolean|null
      },
      "outcome": {
        "outcome_label": "adsorbing"|"selective_adsorbing"|"weak_adsorbing"|"non_adsorbing"|"antifouling"|"protein_immobilization"|"ambiguous",
        "outcome_basis": string,
        "raw_metric_name": string,
        "raw_metric_value": number|string|null,
        "raw_metric_unit": string|null,
        "q_norm_mg_g": number|null,
        "q_norm_mg_mL_bed": number|null,
        "surface_adsorption_ug_cm2": number|null,
        "removal_efficiency_pct": number|null,
        "binding_efficiency_pct": number|null,
        "recovery_pct": number|null,
        "purity_pct": number|null,
        "dynamic_binding_capacity": object|null,
        "selectivity_factor": object|null,
        "imprinting_factor": number|null,
        "association_constant_Ka": object|null,
        "dissociation_constant_Kd": object|null,
        "isotherm_model": string|null,
        "isotherm_parameters": object|null,
        "kinetic_model": string|null,
        "kinetic_parameters": object|null,
        "fouling_reduction_pct": number|null,
        "retained_capacity_pct": number|null,
        "protein_corona": object|null,
        "competitive_adsorption_result": object|null,
        "adsorption_reversibility": object|null,
        "side_outcomes": object|null
      },
      "mechanism": {
        "mechanism_tags": [string],
        "mechanism_evidence_text": string|null,
        "author_claimed_mechanism": boolean|null,
        "inferred_mechanism": boolean|null,
        "control_type": string|null,
        "control_material": string|null,
        "control_outcome": object|null,
        "fold_change_vs_control": number|null,
        "comparator_notes": string|null,
        "protein_unfolding": object|boolean|null,
        "protein_corona_evidence": string|null
      },
      "biointerface_response": object|null,
      "ai_modeling_labels": object|null,
      "quality": {
        "unit_normalized": boolean,
        "normalization_notes": string|null,
        "value_ambiguity": string|null,
        "missing_conditions": [string],
        "source_quality_score": integer,
        "needs_manual_review": boolean,
        "exclusion_reason": string|null
      }
    }
  ],
  "material_mentions": [
    {
      "name": string,
      "role": "polymer_backbone"|"monomer"|"crosslinker"|"initiator"|"functional_group"|"ligand"|"metal_ion"|"filler"|"buffer_salt"|"other",
      "context": string,
      "pubchem_query": string|null,
      "needs_manual_normalization": boolean
    }
  ],
  "protein_mentions": [
    {
      "name": string,
      "abbreviation": string|null,
      "species_or_source": string|null,
      "role": string,
      "context": string,
      "uniprot_query": string|null,
      "reported_mw_kDa": number|null,
      "reported_pI": number|null
    }
  ],
  "special_fields": [
    {
      "field_name": string,
      "field_value": string|number|boolean|object|array|null,
      "why_special": string,
      "evidence_text": string,
      "suggested_table": string|null
    }
  ],
  "extraction_note": string
}

Rules:
- Use exact evidence from the supplied context. Keep evidence_text short, but enough to audit the value.
- If a paper is irrelevant, return triage_label "exclude", records [], and explain why.
- A review article should normally return records [] unless it contains reusable curated experimental data.
- Do not merge multiple proteins, hydrogels, pH values, or temperatures into one record when separate outcomes are reported.
- Normalize q_norm_mg_g only when the raw unit is clearly mg/g dry gel or safely convertible.
- Use source_quality_score 3 for table-backed quantitative records, 2 for text-backed quantitative records, 1 for qualitative or abstract-only records, 0 for excluded records.
