from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "curated" / "pha_scientific_dataset_20260705"
DOCS = ROOT / "docs"

RECORD_COLUMNS = {
    "record_id": "record_id",
    "doi": "doi",
    "doi_split": "doi_split",
    "article_status": "article_status",
    "article_title": "article_title",
    "publisher": "publisher",
    "provenance__year": "year",
    "provenance__source_section": "source_section",
    "provenance__source_table_or_figure": "source_table_or_figure",
    "hydrogel__hydrogel_name": "hydrogel",
    "hydrogel__hydrogel_format": "format",
    "hydrogel__polymer_backbone": "backbone",
    "hydrogel__monomers": "monomers",
    "hydrogel__crosslinker": "crosslinker",
    "hydrogel__functional_groups": "functional_groups",
    "hydrogel__ligand_or_affinity_group": "ligand",
    "hydrogel__filler_or_composite": "filler",
    "hydrogel__substrate_or_support": "substrate_or_support",
    "hydrogel__preparation_solvent": "preparation_solvent",
    "hydrogel__preparation_pH": "preparation_pH",
    "hydrogel__preparation_temp_C": "preparation_temp_C",
    "hydrogel__gelation_time": "gelation_time",
    "hydrogel__post_treatment": "post_treatment",
    "hydrogel_properties__charge_class": "charge",
    "hydrogel_properties__swelling_ratio": "swelling_ratio",
    "hydrogel_properties__water_content_pct": "water_content_pct",
    "hydrogel_properties__porosity_pct": "porosity_pct",
    "hydrogel_properties__pore_size": "pore_size",
    "hydrogel_properties__mesh_size": "mesh_size",
    "hydrogel_properties__surface_area": "surface_area",
    "hydrogel_properties__particle_size": "particle_size",
    "hydrogel_properties__thickness": "thickness",
    "hydrogel_properties__roughness": "roughness",
    "hydrogel_properties__zeta_potential_mV": "zeta_potential_mV",
    "hydrogel_properties__contact_angle_deg": "contact_angle_deg",
    "hydrogel_properties__young_modulus": "young_modulus",
    "hydrogel_properties__responsive_type": "responsive_type",
    "hydrogel_properties__degradation_or_stability": "degradation_or_stability",
    "protein__protein_name": "protein",
    "protein__protein_abbreviation": "protein_abbreviation",
    "protein__protein_species_or_source": "protein_source",
    "protein__protein_role": "protein_role",
    "protein__molecular_weight_kDa": "protein_mw_kDa",
    "protein__pI": "protein_pI",
    "protein__charge_at_experiment_pH": "protein_charge_at_pH",
    "protein__protein_initial_concentration": "protein_initial_concentration",
    "protein__protein_matrix": "protein_matrix",
    "experiment__experiment_mode": "experiment_mode",
    "experiment__hydrogel_dosage": "hydrogel_dosage",
    "experiment__solution_volume": "solution_volume",
    "experiment__pH": "pH",
    "experiment__buffer": "buffer",
    "experiment__ionic_strength": "ionic_strength",
    "experiment__salt_type": "salt_type",
    "experiment__salt_concentration": "salt_concentration",
    "experiment__temperature_C": "temperature_C",
    "experiment__contact_time": "contact_time",
    "experiment__flow_rate": "flow_rate",
    "experiment__detection_method": "detection_method",
    "experiment__replicate_count": "replicate_count",
    "experiment__adsorption_type": "adsorption_type",
    "experiment__competition_system": "competition_system",
    "outcome__outcome_label": "outcome",
    "outcome__raw_metric_name": "metric",
    "outcome__raw_metric_value": "value",
    "outcome__raw_metric_unit": "unit",
    "outcome__q_norm_mg_g": "q_norm_mg_g",
    "outcome__q_norm_mg_mL_bed": "q_norm_mg_mL_bed",
    "outcome__surface_adsorption_ug_cm2": "surface_adsorption_ug_cm2",
    "outcome__removal_efficiency_pct": "removal_efficiency_pct",
    "outcome__binding_efficiency_pct": "binding_efficiency_pct",
    "outcome__recovery_pct": "recovery_pct",
    "outcome__purity_pct": "purity_pct",
    "outcome__fouling_reduction_pct": "fouling_reduction_pct",
    "outcome__retained_capacity_pct": "retained_capacity_pct",
    "outcome__dynamic_binding_capacity": "dynamic_binding_capacity",
    "outcome__selectivity_factor": "selectivity_factor",
    "outcome__imprinting_factor": "imprinting_factor",
    "outcome__association_constant_Ka": "association_constant_Ka",
    "outcome__dissociation_constant_Kd": "dissociation_constant_Kd",
    "outcome__isotherm_model": "isotherm_model",
    "outcome__kinetic_model": "kinetic_model",
    "mechanism__mechanism_tags": "mechanism_tags",
    "mechanism__control_type": "control_type",
    "mechanism__control_material": "control_material",
    "quality__source_quality_score": "quality_score",
    "quality__needs_manual_review": "needs_review",
    "primary_target_name": "target",
    "primary_target_value": "target_value",
    "primary_target_unit": "target_unit",
    "primary_target_direction": "target_direction",
    "model_ready": "model_ready",
    "model_ready_reason": "model_ready_reason",
    "interaction_type": "interaction_type",
    "is_covalent_binding": "is_covalent_binding",
    "experiment_mode_primary": "experiment_mode_primary",
    "experiment_mode_detail": "experiment_mode_detail",
    "application_context": "application_context",
    "comparable_target_class": "comparable_target_class",
    "model_ready_v2": "model_ready_v2",
    "model_ready_blocker": "model_ready_blocker",
    "manual_review_priority": "manual_review_priority",
    "q5_protein_evidence_flag": "q5_protein_evidence_flag",
    "q5_triage_action": "q5_triage_action",
    "extraction_confidence_db": "confidence",
    "evidence_text_db": "evidence",
}

NUMERIC_FIELDS = {
    "year",
    "protein_mw_kDa",
    "protein_pI",
    "pH",
    "preparation_pH",
    "preparation_temp_C",
    "water_content_pct",
    "porosity_pct",
    "zeta_potential_mV",
    "contact_angle_deg",
    "temperature_C",
    "q_norm_mg_g",
    "q_norm_mg_mL_bed",
    "surface_adsorption_ug_cm2",
    "removal_efficiency_pct",
    "binding_efficiency_pct",
    "recovery_pct",
    "purity_pct",
    "fouling_reduction_pct",
    "retained_capacity_pct",
    "selectivity_factor",
    "imprinting_factor",
    "association_constant_Ka",
    "dissociation_constant_Kd",
    "replicate_count",
    "quality_score",
    "target_value",
    "confidence",
}

BOOL_FIELDS = {"model_ready", "model_ready_v2", "needs_review", "q5_protein_evidence_flag"}


def clean_value(key: str, value: str) -> Any:
    value = value.strip() if isinstance(value, str) else value
    if value == "":
        return None
    if key in BOOL_FIELDS:
        return str(value).lower() in {"true", "1", "yes"}
    if key in NUMERIC_FIELDS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def read_records() -> list[dict[str, Any]]:
    records = []
    with (PACKAGE / "data" / "records_flat.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            item = {
                out_key: clean_value(out_key, row.get(in_key, ""))
                for in_key, out_key in RECORD_COLUMNS.items()
            }
            records.append(item)
    return records


def counter_payload(records: list[dict[str, Any]], key: str, limit: int = 12) -> list[dict[str, Any]]:
    values = Counter(str(r.get(key)).strip() for r in records if r.get(key))
    return [{"name": name, "count": count} for name, count in values.most_common(limit)]


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    records = read_records()
    summary = json.loads((PACKAGE / "metadata" / "summary.json").read_text(encoding="utf-8"))
    browser_summary = {
        **summary,
        "top_proteins": counter_payload(records, "protein"),
        "top_hydrogels": counter_payload(records, "hydrogel"),
        "top_targets": counter_payload(records, "target"),
        "top_experiment_modes": counter_payload(records, "experiment_mode"),
        "top_experiment_mode_primary": counter_payload(records, "experiment_mode_primary"),
        "top_interaction_types": counter_payload(records, "interaction_type"),
        "top_application_contexts": counter_payload(records, "application_context"),
        "top_comparable_target_classes": counter_payload(records, "comparable_target_class"),
        "top_manual_review_priorities": counter_payload(records, "manual_review_priority"),
        "year_min": min((r["year"] for r in records if isinstance(r.get("year"), float)), default=None),
        "year_max": max((r["year"] for r in records if isinstance(r.get("year"), float)), default=None),
    }
    (DOCS / "pha_records_browser.json").write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (DOCS / "pha_summary.json").write_text(
        json.dumps(browser_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
