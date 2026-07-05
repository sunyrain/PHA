from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import shutil
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "processed" / "pha_extraction_1000_xhigh_fulltext_w8" / "codex_extraction_results.db"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "curated"
DEFAULT_COMPLETION_DIR = ROOT / "data" / "processed" / "pha_field_completion_v4_targeted"
DEFAULT_EXTERNAL_DESCRIPTOR_DIR = ROOT / "data" / "processed" / "pha_external_descriptors"


MODEL_FIELDS = {
    "provenance.doi": "Source DOI.",
    "provenance.title": "Source article title.",
    "provenance.year": "Publication year if available.",
    "provenance.source_section": "Article section used as evidence.",
    "provenance.source_table_or_figure": "Source table or figure used as evidence.",
    "hydrogel.hydrogel_name": "Hydrogel or hydrogel-like material name.",
    "hydrogel.hydrogel_format": "Material format, such as bulk gel, coating, bead, cryogel, or nanogel.",
    "hydrogel.polymer_backbone": "Polymer backbone or family.",
    "hydrogel.monomers": "Reported monomers.",
    "hydrogel.monomer_ratios": "Reported monomer ratios.",
    "hydrogel.crosslinker": "Reported crosslinker(s).",
    "hydrogel.crosslinker_concentration": "Reported crosslinker concentration.",
    "hydrogel.initiator": "Reported initiator(s).",
    "hydrogel.synthesis_method": "Preparation or synthesis method.",
    "hydrogel.preparation_solvent": "Preparation solvent.",
    "hydrogel.preparation_pH": "Preparation pH.",
    "hydrogel.preparation_temp_C": "Preparation temperature in Celsius.",
    "hydrogel.gelation_time": "Gelation or curing time.",
    "hydrogel.functional_groups": "Functional groups.",
    "hydrogel.ligand_or_affinity_group": "Affinity ligands or recognition groups.",
    "hydrogel.filler_or_composite": "Composite fillers.",
    "hydrogel.substrate_or_support": "Substrate or support.",
    "hydrogel.post_treatment": "Post-treatment, washing, conditioning, or storage notes.",
    "hydrogel_properties.charge_class": "Material charge class.",
    "hydrogel_properties.swelling_ratio": "Swelling ratio.",
    "hydrogel_properties.water_content_pct": "Water content percentage.",
    "hydrogel_properties.porosity_pct": "Porosity percentage.",
    "hydrogel_properties.pore_size": "Pore size.",
    "hydrogel_properties.mesh_size": "Mesh size.",
    "hydrogel_properties.surface_area": "Surface area.",
    "hydrogel_properties.particle_size": "Particle size.",
    "hydrogel_properties.thickness": "Material thickness.",
    "hydrogel_properties.roughness": "Surface roughness.",
    "hydrogel_properties.zeta_potential_mV": "Zeta potential.",
    "hydrogel_properties.contact_angle_deg": "Water contact angle.",
    "hydrogel_properties.young_modulus": "Young's modulus or mechanical modulus.",
    "hydrogel_properties.responsive_type": "Stimuli-responsive behavior or class.",
    "hydrogel_properties.degradation_or_stability": "Degradation, reuse, storage, or stability notes.",
    "protein.protein_name": "Protein name.",
    "protein.protein_abbreviation": "Protein abbreviation.",
    "protein.protein_species_or_source": "Protein species or biological source.",
    "protein.protein_role": "Role of the protein in the experiment.",
    "protein.molecular_weight_kDa": "Protein molecular weight.",
    "protein.pI": "Protein isoelectric point.",
    "protein.charge_at_experiment_pH": "Reported or inferred protein charge at assay pH.",
    "protein.protein_initial_concentration": "Initial protein concentration.",
    "protein.protein_matrix": "Matrix, such as buffer, serum, plasma, or crude extract.",
    "protein.competitor_proteins": "Competitor proteins.",
    "experiment.experiment_mode": "Batch, surface, column, SPR/QCM, or other assay mode.",
    "experiment.hydrogel_dosage": "Hydrogel dosage.",
    "experiment.solution_volume": "Solution volume.",
    "experiment.pH": "Assay pH.",
    "experiment.buffer": "Assay buffer.",
    "experiment.ionic_strength": "Ionic strength.",
    "experiment.salt_type": "Salt type.",
    "experiment.salt_concentration": "Salt concentration.",
    "experiment.temperature_C": "Assay temperature.",
    "experiment.contact_time": "Contact or incubation time.",
    "experiment.flow_rate": "Flow rate.",
    "experiment.detection_method": "Detection or quantification method.",
    "experiment.replicate_count": "Replicate count.",
    "experiment.adsorption_type": "Endpoint, equilibrium, kinetic, dynamic, or unknown.",
    "experiment.competition_system": "Single protein, binary, serum, plasma, blood, or other competition context.",
    "outcome.outcome_label": "Qualitative outcome label.",
    "outcome.raw_metric_name": "Metric name as reported.",
    "outcome.raw_metric_value": "Metric value as reported.",
    "outcome.raw_metric_unit": "Metric unit as reported.",
    "outcome.q_norm_mg_g": "Normalized capacity in mg/g if extractable.",
    "outcome.q_norm_mg_mL_bed": "Normalized capacity in mg/mL bed if extractable.",
    "outcome.surface_adsorption_ug_cm2": "Surface adsorption in microgram per square centimeter.",
    "outcome.removal_efficiency_pct": "Removal efficiency percentage.",
    "outcome.binding_efficiency_pct": "Binding efficiency percentage.",
    "outcome.recovery_pct": "Recovery percentage.",
    "outcome.purity_pct": "Purity percentage.",
    "outcome.fouling_reduction_pct": "Fouling reduction percentage.",
    "outcome.retained_capacity_pct": "Retained capacity percentage.",
    "mechanism.mechanism_tags": "Mechanism tags extracted from the article.",
    "mechanism.control_type": "Control/comparator type.",
    "mechanism.control_material": "Control/comparator material.",
    "mechanism.fold_change_vs_control": "Fold change versus control.",
    "quality.unit_normalized": "Whether the outcome value was normalized.",
    "quality.source_quality_score": "Source quality score from 0 to 3.",
    "quality.needs_manual_review": "Whether the record should be manually reviewed.",
}


TARGET_PRIORITY = [
    ("q_norm_mg_g", "mg/g", "maximize", "outcome.q_norm_mg_g"),
    ("surface_adsorption_ug_cm2", "ug/cm2", "context_dependent", "outcome.surface_adsorption_ug_cm2"),
    ("removal_efficiency_pct", "%", "maximize", "outcome.removal_efficiency_pct"),
    ("binding_efficiency_pct", "%", "maximize", "outcome.binding_efficiency_pct"),
    ("recovery_pct", "%", "maximize", "outcome.recovery_pct"),
    ("purity_pct", "%", "maximize", "outcome.purity_pct"),
    ("fouling_reduction_pct", "%", "maximize", "outcome.fouling_reduction_pct"),
    ("retained_capacity_pct", "%", "maximize", "outcome.retained_capacity_pct"),
]

FIELD_COMPLETION_FIELDS = [
    "hydrogel__monomer_ratios",
    "hydrogel__crosslinker_concentration",
    "hydrogel__preparation_solvent",
    "hydrogel__preparation_pH",
    "hydrogel__preparation_temp_C",
    "hydrogel__gelation_time",
    "hydrogel__post_treatment",
    "hydrogel_properties__swelling_ratio",
    "hydrogel_properties__water_content_pct",
    "hydrogel_properties__porosity_pct",
    "hydrogel_properties__pore_size",
    "hydrogel_properties__mesh_size",
    "hydrogel_properties__surface_area",
    "hydrogel_properties__particle_size",
    "hydrogel_properties__thickness",
    "hydrogel_properties__roughness",
    "hydrogel_properties__zeta_potential_mV",
    "hydrogel_properties__contact_angle_deg",
    "hydrogel_properties__young_modulus",
    "hydrogel_properties__responsive_type",
    "hydrogel_properties__degradation_or_stability",
    "protein__molecular_weight_kDa",
    "protein__pI",
    "experiment__pH",
    "experiment__temperature_C",
    "experiment__contact_time",
]


FAILED_RELEVANCE_OVERRIDES = {
    "10.1016/s1381-1177(02)00232-1": (
        "relevant",
        "Glucose oxidase immobilization on poly(N-vinylimidazole) and metal-chelated hydrogels is a protein-hydrogel immobilization study.",
    ),
    "10.1016/j.aca.2013.11.052": (
        "relevant",
        "Hydrogel-based molecularly imprinted polymers and selectivity conditioning are directly relevant to protein/hydrogel binding.",
    ),
    "10.1016/j.biomaterials.2009.06.010": (
        "relevant",
        "Pullulan modified cholesteryl nanogels binding amyloid-beta oligomers is a hydrogel/nanogel-protein binding case.",
    ),
    "10.1016/j.colsurfb.2015.12.011": (
        "relevant",
        "Macroporous composite hydrogels and lysozyme controlled delivery are relevant to protein-hydrogel interactions.",
    ),
}


def load_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def compact_json(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_enrichment(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": str(value)[:500]}


def get_path(obj: dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return not (isinstance(value, float) and math.isnan(value))
    if isinstance(value, str):
        stripped = value.strip().lower()
        return bool(stripped) and stripped not in {"null", "none", "unknown", "not reported", "n/a", "na"}
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    if isinstance(value, dict):
        return any(has_value(v) for v in value.values())
    return True


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def measured_value(value: Any) -> tuple[Any, Any, Any]:
    if isinstance(value, dict):
        return value.get("value"), value.get("unit"), value.get("raw_text") or value.get("condition")
    return value, None, None


def article_decision(row: dict[str, Any]) -> tuple[str, str]:
    status = str(row.get("status") or "")
    doi = str(row.get("doi") or "").lower()
    title = str(row.get("title") or "")
    if status == "failed":
        relevance, reason = FAILED_RELEVANCE_OVERRIDES.get(doi, infer_relevance(title))
        if relevance == "irrelevant":
            return "exclude_irrelevant_failed", reason
        return "retain_failed_relevant_needs_manual_or_retry", reason
    if status == "partial":
        return "exclude_no_records", "No adsorption records were extracted; retain source metadata for traceability."
    return "include_records", "Article yielded one or more extracted records."


def infer_relevance(title: str) -> tuple[str, str]:
    low = title.lower()
    relevant_terms = ["hydrogel", "nanogel", "microgel", "cryogel", "protein", "enzyme", "albumin", "lysozyme", "antibody", "imprinted"]
    if any(term in low for term in relevant_terms):
        return "relevant", "Title contains protein/hydrogel interaction terms; retain for manual review."
    return "irrelevant", "No protein/hydrogel interaction signal in the title."


def record_flat_row(row: dict[str, Any], article_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rec = load_json(row.get("record_json"))
    doi = str(row.get("doi") or get_path(rec, "provenance.doi") or "")
    article = article_lookup.get(doi.lower(), {})
    out: dict[str, Any] = {
        "record_id": row.get("record_id"),
        "doi": doi,
        "doi_split": doi_split(doi),
        "article_status": article.get("status"),
        "article_title": article.get("title") or row.get("title"),
        "publisher": article.get("publisher"),
        "source_json": article.get("source_json"),
    }
    for field in MODEL_FIELDS:
        value = get_path(rec, field)
        if isinstance(value, (list, dict)):
            out[field.replace(".", "__")] = compact_json(value)
        else:
            out[field.replace(".", "__")] = value
        if isinstance(value, dict):
            v, unit, note = measured_value(value)
            prefix = field.replace(".", "__")
            out[f"{prefix}__value"] = v
            out[f"{prefix}__unit"] = unit
            out[f"{prefix}__note"] = note
    quality = rec.get("quality") or {}
    outcome = rec.get("outcome") or {}
    target_name, target_value, target_unit, target_direction = primary_target(outcome)
    out.update(
        {
            "primary_target_name": target_name,
            "primary_target_value": target_value,
            "primary_target_unit": target_unit,
            "primary_target_direction": target_direction,
            "model_ready": is_model_ready(rec, row, article, target_value),
            "model_ready_reason": model_ready_reason(rec, row, article, target_value),
            "needs_manual_review_db": int(row.get("needs_manual_review") or 0),
            "source_quality_score_db": row.get("source_quality_score"),
            "extraction_confidence_db": row.get("extraction_confidence"),
            "evidence_text_db": row.get("evidence_text"),
            "record_json": compact_json(rec),
            "quality_missing_conditions": compact_json(quality.get("missing_conditions") or []),
        }
    )
    return out


def primary_target(outcome: dict[str, Any]) -> tuple[str | None, float | None, str | None, str | None]:
    for name, unit, direction, path in TARGET_PRIORITY:
        value = numeric(get_path({"outcome": outcome}, path))
        if value is not None:
            return name, value, unit, direction
    raw = numeric(outcome.get("raw_metric_value"))
    if raw is not None and has_value(outcome.get("raw_metric_unit")):
        return str(outcome.get("raw_metric_name") or "raw_metric"), raw, str(outcome.get("raw_metric_unit")), "context_dependent"
    return None, None, None, None


def is_model_ready(rec: dict[str, Any], row: dict[str, Any], article: dict[str, Any], target_value: float | None) -> bool:
    if article.get("status") != "success":
        return False
    if target_value is None:
        return False
    if int(row.get("needs_manual_review") or 0):
        return False
    if numeric(row.get("source_quality_score")) is not None and numeric(row.get("source_quality_score")) < 2:
        return False
    if not has_value(get_path(rec, "hydrogel.hydrogel_name")):
        return False
    if not has_value(get_path(rec, "protein.protein_name")):
        return False
    return True


def model_ready_reason(rec: dict[str, Any], row: dict[str, Any], article: dict[str, Any], target_value: float | None) -> str:
    reasons: list[str] = []
    if article.get("status") != "success":
        reasons.append("article_not_success")
    if target_value is None:
        reasons.append("missing_numeric_target")
    if int(row.get("needs_manual_review") or 0):
        reasons.append("needs_manual_review")
    score = numeric(row.get("source_quality_score"))
    if score is not None and score < 2:
        reasons.append("low_source_quality")
    if not has_value(get_path(rec, "hydrogel.hydrogel_name")):
        reasons.append("missing_hydrogel_name")
    if not has_value(get_path(rec, "protein.protein_name")):
        reasons.append("missing_protein_name")
    return ";".join(reasons) if reasons else "ready"


def inverse_design_row(flat: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": flat.get("record_id"),
        "doi": flat.get("doi"),
        "doi_split": flat.get("doi_split"),
        "hydrogel_name": flat.get("hydrogel__hydrogel_name"),
        "hydrogel_format": flat.get("hydrogel__hydrogel_format"),
        "polymer_backbone": flat.get("hydrogel__polymer_backbone"),
        "monomers": flat.get("hydrogel__monomers"),
        "monomer_ratios": flat.get("hydrogel__monomer_ratios"),
        "crosslinker": flat.get("hydrogel__crosslinker"),
        "crosslinker_concentration": flat.get("hydrogel__crosslinker_concentration"),
        "synthesis_method": flat.get("hydrogel__synthesis_method"),
        "preparation_solvent": flat.get("hydrogel__preparation_solvent"),
        "preparation_pH": flat.get("hydrogel__preparation_pH"),
        "preparation_temp_C": flat.get("hydrogel__preparation_temp_C"),
        "gelation_time": flat.get("hydrogel__gelation_time"),
        "post_treatment": flat.get("hydrogel__post_treatment"),
        "functional_groups": flat.get("hydrogel__functional_groups"),
        "ligand_or_affinity_group": flat.get("hydrogel__ligand_or_affinity_group"),
        "filler_or_composite": flat.get("hydrogel__filler_or_composite"),
        "charge_class": flat.get("hydrogel_properties__charge_class"),
        "responsive_type": flat.get("hydrogel_properties__responsive_type"),
        "swelling_ratio": flat.get("hydrogel_properties__swelling_ratio__value") or flat.get("hydrogel_properties__swelling_ratio"),
        "water_content_pct": flat.get("hydrogel_properties__water_content_pct"),
        "porosity_pct": flat.get("hydrogel_properties__porosity_pct"),
        "pore_size_value": flat.get("hydrogel_properties__pore_size__value"),
        "pore_size_unit": flat.get("hydrogel_properties__pore_size__unit"),
        "mesh_size": flat.get("hydrogel_properties__mesh_size__value") or flat.get("hydrogel_properties__mesh_size"),
        "surface_area": flat.get("hydrogel_properties__surface_area__value") or flat.get("hydrogel_properties__surface_area"),
        "particle_size": flat.get("hydrogel_properties__particle_size__value") or flat.get("hydrogel_properties__particle_size"),
        "thickness": flat.get("hydrogel_properties__thickness__value") or flat.get("hydrogel_properties__thickness"),
        "roughness": flat.get("hydrogel_properties__roughness__value") or flat.get("hydrogel_properties__roughness"),
        "zeta_potential_mV": flat.get("hydrogel_properties__zeta_potential_mV__value") or flat.get("hydrogel_properties__zeta_potential_mV"),
        "contact_angle_deg": flat.get("hydrogel_properties__contact_angle_deg__value") or flat.get("hydrogel_properties__contact_angle_deg"),
        "young_modulus": flat.get("hydrogel_properties__young_modulus__value") or flat.get("hydrogel_properties__young_modulus"),
        "degradation_or_stability": flat.get("hydrogel_properties__degradation_or_stability"),
        "protein_name": flat.get("protein__protein_name"),
        "protein_abbreviation": flat.get("protein__protein_abbreviation"),
        "protein_species_or_source": flat.get("protein__protein_species_or_source"),
        "protein_mw_kDa": flat.get("protein__molecular_weight_kDa"),
        "protein_pI": flat.get("protein__pI"),
        "protein_charge_at_pH": flat.get("protein__charge_at_experiment_pH"),
        "experiment_mode": flat.get("experiment__experiment_mode"),
        "pH": flat.get("experiment__pH"),
        "temperature_C": flat.get("experiment__temperature_C"),
        "contact_time": flat.get("experiment__contact_time__value") or flat.get("experiment__contact_time"),
        "contact_time_unit": flat.get("experiment__contact_time__unit"),
        "buffer": flat.get("experiment__buffer"),
        "salt_type": flat.get("experiment__salt_type"),
        "salt_concentration": flat.get("experiment__salt_concentration__value") or flat.get("experiment__salt_concentration"),
        "hydrogel_dosage": flat.get("experiment__hydrogel_dosage__value") or flat.get("experiment__hydrogel_dosage"),
        "solution_volume": flat.get("experiment__solution_volume__value") or flat.get("experiment__solution_volume"),
        "flow_rate": flat.get("experiment__flow_rate__value") or flat.get("experiment__flow_rate"),
        "detection_method": flat.get("experiment__detection_method"),
        "replicate_count": flat.get("experiment__replicate_count"),
        "target_name": flat.get("primary_target_name"),
        "target_value": flat.get("primary_target_value"),
        "target_unit": flat.get("primary_target_unit"),
        "target_direction": flat.get("primary_target_direction"),
        "outcome_label": flat.get("outcome__outcome_label"),
        "mechanism_tags": flat.get("mechanism__mechanism_tags"),
        "source_quality_score": flat.get("source_quality_score_db"),
        "extraction_confidence": flat.get("extraction_confidence_db"),
        "article_title": flat.get("article_title"),
    }


def doi_split(doi: str) -> str:
    digest = hashlib.sha1(doi.lower().encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def read_table(con: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {table}", con)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames or list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def material_descriptor_rows(materials: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in materials.to_dict("records"):
        payload = parse_enrichment(item.get("enrichment_json"))
        status = "not_queried"
        if payload is None:
            status = "not_queried"
        elif payload == {}:
            status = "no_match"
        elif isinstance(payload, dict) and payload.get("error"):
            status = "error"
        elif isinstance(payload, dict) and payload.get("CID"):
            status = "matched"
        else:
            status = "unknown_payload"
        rows.append(
            {
                "material_mention_id": item.get("id"),
                "doi": item.get("doi"),
                "name": item.get("name"),
                "role": item.get("role"),
                "pubchem_query": item.get("pubchem_query"),
                "needs_manual_normalization": item.get("needs_manual_normalization"),
                "value_origin": "external_descriptor",
                "source_database": "PubChem",
                "match_status": status,
                "pubchem_cid": payload.get("CID") if isinstance(payload, dict) else None,
                "molecular_formula": payload.get("MolecularFormula") if isinstance(payload, dict) else None,
                "molecular_weight": payload.get("MolecularWeight") if isinstance(payload, dict) else None,
                "canonical_smiles": payload.get("ConnectivitySMILES") if isinstance(payload, dict) else None,
                "isomeric_smiles": payload.get("SMILES") if isinstance(payload, dict) else None,
                "inchikey": payload.get("InChIKey") if isinstance(payload, dict) else None,
                "iupac_name": payload.get("IUPACName") if isinstance(payload, dict) else None,
                "qa_note": payload.get("error") if isinstance(payload, dict) and payload.get("error") else "",
            }
        )
    return rows


def protein_name_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    desc = payload.get("proteinDescription") or {}
    rec = desc.get("recommendedName") if isinstance(desc, dict) else {}
    if isinstance(rec, dict):
        full = rec.get("fullName")
        if isinstance(full, dict):
            return str(full.get("value") or "")
        if isinstance(full, str):
            return full
    return ""


def organism_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    org = payload.get("organism") or {}
    if isinstance(org, dict):
        return str(org.get("scientificName") or org.get("commonName") or "")
    return ""


def broad_protein_query(name: str, species: str | None) -> bool:
    text = f"{name} {species or ''}".strip().lower()
    broad_terms = [
        "immunoglobulin",
        "igg",
        "albumin",
        "serum protein",
        "protein a",
        "antibody",
        "enzyme",
        "plasma protein",
    ]
    if any(term in text for term in broad_terms) and not species:
        return True
    return len(text.split()) <= 2 and any(term in text for term in ["protein", "enzyme", "albumin"])


def protein_descriptor_rows(proteins: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in proteins.to_dict("records"):
        payload = parse_enrichment(item.get("enrichment_json"))
        status = "not_queried"
        qa_notes: list[str] = []
        if payload is None:
            status = "not_queried"
        elif payload == {}:
            status = "no_match"
        elif isinstance(payload, dict) and payload.get("error"):
            status = "error"
            qa_notes.append(str(payload.get("error")))
        elif isinstance(payload, dict) and payload.get("accession"):
            status = "matched"
        else:
            status = "unknown_payload"
        name = str(item.get("name") or "")
        species = item.get("species_or_source")
        if status == "matched" and broad_protein_query(name, str(species) if species else None):
            qa_notes.append("broad_query_needs_accession_review")
        organism = organism_from_payload(payload)
        if status == "matched" and species and organism and str(species).lower() not in organism.lower():
            qa_notes.append("reported_species_not_in_uniprot_organism")
        sequence = payload.get("sequence") if isinstance(payload, dict) else {}
        rows.append(
            {
                "protein_mention_id": item.get("id"),
                "doi": item.get("doi"),
                "name": item.get("name"),
                "abbreviation": item.get("abbreviation"),
                "species_or_source": species,
                "role": item.get("role"),
                "uniprot_query": item.get("uniprot_query"),
                "reported_mw_kDa": item.get("reported_mw_kDa"),
                "reported_pI": item.get("reported_pI"),
                "value_origin": "external_descriptor",
                "source_database": "UniProt",
                "match_status": status,
                "qa_status": "needs_review" if qa_notes else ("usable" if status == "matched" else status),
                "qa_note": ";".join(qa_notes),
                "uniprot_accession": payload.get("accession") if isinstance(payload, dict) else None,
                "uniprot_id": payload.get("uniProtkbId") if isinstance(payload, dict) else None,
                "protein_full_name": protein_name_from_payload(payload),
                "organism": organism,
                "sequence_length": sequence.get("length") if isinstance(sequence, dict) else None,
                "molecular_mass_Da": sequence.get("molWeight") if isinstance(sequence, dict) else None,
                "sequence_available": bool(sequence.get("value")) if isinstance(sequence, dict) else False,
                "result_count": payload.get("result_count") if isinstance(payload, dict) else None,
            }
        )
    return rows


def field_coverage(flat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = max(len(flat_rows), 1)
    rows: list[dict[str, Any]] = []
    for field, description in MODEL_FIELDS.items():
        col = field.replace(".", "__")
        present = sum(1 for row in flat_rows if has_value(row.get(col)))
        rows.append(
            {
                "field": field,
                "column": col,
                "description": description,
                "present": present,
                "total": len(flat_rows),
                "coverage_pct": round(present / total * 100, 2),
            }
        )
    return rows


def field_completion_candidates(flat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_doi: dict[str, list[dict[str, Any]]] = {}
    for row in flat_rows:
        by_doi.setdefault(str(row.get("doi") or ""), []).append(row)
    candidates: list[dict[str, Any]] = []
    for doi, rows in by_doi.items():
        if not doi:
            continue
        model_ready_count = sum(1 for row in rows if row.get("model_ready"))
        records_count = len(rows)
        missing_counts = {field: sum(1 for row in rows if not has_value(row.get(field))) for field in FIELD_COMPLETION_FIELDS}
        missing_cells = sum(missing_counts.values())
        possible_cells = max(records_count * len(FIELD_COMPLETION_FIELDS), 1)
        if model_ready_count == 0 and records_count < 3:
            continue
        missing_fields = [field for field, count in missing_counts.items() if count == records_count]
        score = model_ready_count * 5 + records_count + round(missing_cells / possible_cells * 10, 2)
        first = rows[0]
        candidates.append(
            {
                "doi": doi,
                "article_title": first.get("article_title"),
                "article_status": first.get("article_status"),
                "records_count": records_count,
                "model_ready_count": model_ready_count,
                "missing_completion_cells": missing_cells,
                "possible_completion_cells": possible_cells,
                "missing_completion_pct": round(missing_cells / possible_cells * 100, 2),
                "priority_score": score,
                "fully_missing_fields": ";".join(missing_fields),
                "source_json": first.get("source_json"),
            }
        )
    candidates.sort(key=lambda row: (row["priority_score"], row["model_ready_count"], row["records_count"]), reverse=True)
    return candidates


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def copy_or_empty_csv(src: Path, dst: Path, columns: list[str]) -> pd.DataFrame:
    df = read_csv_if_exists(src)
    if df.empty:
        df = pd.DataFrame(columns=columns)
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False, encoding="utf-8")
    return df


def descriptor_audit_rows(material_descriptor: list[dict[str, Any]], protein_descriptor: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, entity_type, data in [
        ("PubChem", "material", material_descriptor),
        ("UniProt", "protein", protein_descriptor),
    ]:
        status_counts: dict[str, int] = {}
        qa_counts: dict[str, int] = {}
        for row in data:
            status = str(row.get("match_status") or "unknown")
            qa = str(row.get("qa_status") or ("usable" if status == "matched" else status))
            status_counts[status] = status_counts.get(status, 0) + 1
            qa_counts[qa] = qa_counts.get(qa, 0) + 1
        rows.append(
            {
                "source_database": source,
                "entity_type": entity_type,
                "rows": len(data),
                "matched": status_counts.get("matched", 0),
                "usable": qa_counts.get("usable", 0),
                "needs_review": qa_counts.get("needs_review", 0),
                "not_queried": status_counts.get("not_queried", 0),
                "skipped": status_counts.get("skipped", 0),
                "no_match": status_counts.get("no_match", 0),
                "error": status_counts.get("error", 0),
            }
        )
    return rows


def integrate_completion_outputs(output_dir: Path, completion_dir: Path | None) -> None:
    metadata_dir = output_dir / "metadata"
    report_dir = output_dir / "reports"
    columns_patch = [
        "doi",
        "record_id",
        "matched_record_id",
        "target_path",
        "value_json",
        "value_origin",
        "evidence_text",
        "source_section",
        "source_table_or_figure",
        "confidence",
        "prompt_version",
        "article_type",
        "apply_status",
        "qa_note",
    ]
    columns_article_level = [
        "doi",
        "field_name",
        "value_json",
        "value_origin",
        "evidence_text",
        "source_section",
        "source_table_or_figure",
        "confidence",
        "prompt_version",
        "article_type",
        "qa_note",
    ]
    columns_coverage = [
        "field",
        "before_present",
        "after_present",
        "delta_present",
        "total",
        "before_coverage_pct",
        "after_coverage_pct",
        "delta_coverage_pct",
    ]
    columns_audit = ["target_path", "apply_status", "patches", "unique_dois", "unique_records"]
    if completion_dir and completion_dir.exists():
        copy_or_empty_csv(completion_dir / "completion_patches.csv", metadata_dir / "completion_patches.csv", columns_patch)
        copy_or_empty_csv(completion_dir / "article_level_properties.csv", metadata_dir / "article_level_properties.csv", columns_article_level)
        copy_or_empty_csv(completion_dir / "completion_coverage_before_after.csv", metadata_dir / "completion_coverage_before_after.csv", columns_coverage)
        copy_or_empty_csv(completion_dir / "completion_patch_audit.csv", metadata_dir / "completion_patch_audit.csv", columns_audit)
        report = completion_dir / "completion_run_report.md"
        if report.exists():
            shutil.copy2(report, report_dir / report.name)
            return
    copy_or_empty_csv(Path("__missing_completion_patches__.csv"), metadata_dir / "completion_patches.csv", columns_patch)
    copy_or_empty_csv(Path("__missing_article_level_properties__.csv"), metadata_dir / "article_level_properties.csv", columns_article_level)
    copy_or_empty_csv(Path("__missing_completion_coverage__.csv"), metadata_dir / "completion_coverage_before_after.csv", columns_coverage)
    copy_or_empty_csv(Path("__missing_completion_audit__.csv"), metadata_dir / "completion_patch_audit.csv", columns_audit)
    (report_dir / "completion_run_report.md").write_text(
        "# PHA field completion run report\n\nNo v4 field-completion output directory was provided or found during packaging.\n",
        encoding="utf-8",
    )


def integrate_external_descriptor_outputs(
    output_dir: Path,
    external_dir: Path | None,
    material_descriptor: list[dict[str, Any]],
    protein_descriptor: list[dict[str, Any]],
) -> None:
    data_dir = output_dir / "data"
    metadata_dir = output_dir / "metadata"
    report_dir = output_dir / "reports"
    material_cols = [
        "material_mention_id",
        "doi",
        "name",
        "role",
        "query",
        "value_origin",
        "source_database",
        "match_status",
        "qa_status",
        "qa_note",
        "pubchem_cid",
        "molecular_formula",
        "molecular_weight",
        "canonical_smiles",
        "isomeric_smiles",
        "inchikey",
        "iupac_name",
    ]
    protein_cols = [
        "protein_mention_id",
        "doi",
        "name",
        "abbreviation",
        "species_or_source",
        "role",
        "query",
        "value_origin",
        "source_database",
        "match_status",
        "qa_status",
        "qa_note",
        "uniprot_accession",
        "uniprot_id",
        "reviewed",
        "protein_full_name",
        "organism",
        "sequence_length",
        "molecular_mass_Da",
        "sequence_available",
        "pdb_cross_refs",
        "result_count",
    ]
    structure_cols = [
        "protein_mention_id",
        "doi",
        "name",
        "uniprot_accession",
        "value_origin",
        "source_database",
        "match_status",
        "qa_status",
        "qa_note",
        "rcsb_polymer_entity_ids",
        "result_count",
    ]
    audit_cols = ["source_database", "entity_type", "rows", "matched", "usable", "needs_review", "not_queried", "skipped", "no_match", "error"]
    copied_audit = False
    if external_dir and external_dir.exists():
        copy_or_empty_csv(external_dir / "external_material_descriptors.csv", data_dir / "external_material_descriptors.csv", material_cols)
        copy_or_empty_csv(external_dir / "external_protein_descriptors.csv", data_dir / "external_protein_descriptors.csv", protein_cols)
        copy_or_empty_csv(external_dir / "external_structure_descriptors.csv", data_dir / "external_structure_descriptors.csv", structure_cols)
        audit = read_csv_if_exists(external_dir / "external_descriptor_audit.csv")
        if not audit.empty:
            audit.to_csv(metadata_dir / "external_descriptor_audit.csv", index=False, encoding="utf-8")
            copied_audit = True
        report = external_dir / "external_descriptor_report.md"
        if report.exists():
            shutil.copy2(report, report_dir / report.name)
    else:
        copy_or_empty_csv(Path("__missing_external_materials__.csv"), data_dir / "external_material_descriptors.csv", material_cols)
        copy_or_empty_csv(Path("__missing_external_proteins__.csv"), data_dir / "external_protein_descriptors.csv", protein_cols)
        copy_or_empty_csv(Path("__missing_external_structures__.csv"), data_dir / "external_structure_descriptors.csv", structure_cols)
    if not copied_audit:
        write_csv(metadata_dir / "external_descriptor_audit.csv", descriptor_audit_rows(material_descriptor, protein_descriptor), audit_cols)
    if not (report_dir / "external_descriptor_report.md").exists():
        (report_dir / "external_descriptor_report.md").write_text(
            "# PHA external descriptor sidecar report\n\nGenerated from existing material/protein descriptor tables during packaging.\n",
            encoding="utf-8",
        )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# PHA Protein-Hydrogel Adsorption Dataset

Generated: {summary['generated_at']}

## Scope

This curated package organizes literature-derived protein-hydrogel adsorption, binding, immobilization, antifouling, and related biointerface records extracted from the local PHA corpus.

The primary unit is one record:

`paper + hydrogel/sample + protein/mixture + experimental condition + measured outcome`

## Contents

- `data/sources.csv`: article-level metadata, extraction status, and curation decision.
- `data/records_flat.csv`: flattened record-level table with provenance, hydrogel, protein, condition, outcome, mechanism, and quality fields.
- `data/records_raw.jsonl`: raw nested record JSON for lossless downstream parsing.
- `data/model_records.csv`: conservative model-ready subset.
- `data/inverse_design_seed.csv`: compact table for inverse-design and generative-model experiments.
- `data/materials.csv`: material, monomer, crosslinker, ligand, filler, and related mentions.
- `data/proteins.csv`: protein mentions and reported protein properties.
- `data/material_descriptors.csv`: flattened PubChem descriptors with match status.
- `data/protein_descriptors.csv`: flattened UniProt descriptors with QA status.
- `data/special_fields.csv`: article-specific fields outside the common schema.
- `metadata/field_coverage.csv`: coverage audit for common fields.
- `metadata/field_completion_candidates.csv`: DOI-level priority queue for second-pass preparation/property completion.
- `metadata/completion_patches.csv`: patch-first second-pass field-completion proposals and apply status.
- `metadata/article_level_properties.csv`: observed article-level values that could not be safely mapped to exact records.
- `metadata/completion_coverage_before_after.csv`: coverage deltas from the latest completion run.
- `metadata/completion_patch_audit.csv`: patch status counts by target path.
- `metadata/external_descriptor_audit.csv`: PubChem/UniProt/RCSB sidecar descriptor QA summary.
- `metadata/data_dictionary.csv`: table and column descriptions.
- `metadata/failed_articles.csv`: failed DOI audit and relevance decision.
- `metadata/partial_articles.csv`: article-level no-record exclusions.
- `metadata/checksums_sha256.csv`: file checksums.

## Summary

- Articles: {summary['articles_total']}
- Success / partial / failed: {summary['success']} / {summary['partial']} / {summary['failed']}
- Records: {summary['records_total']}
- Model-ready records: {summary['model_ready_records']}
- Inverse-design seed rows: {summary['inverse_design_rows']}
- Completion patches: {summary.get('completion_patches', 0)}

## Curation Rules

Records are marked model-ready only when they come from a successful article extraction, have a numeric target, are not marked for manual review, have source quality score >= 2, and include hydrogel and protein identity.

Failed but relevant articles are retained in `sources.csv` and `failed_articles.csv` for traceability. They are excluded from record-level and model-ready training tables until manually extracted or successfully retried.

Second-pass completion uses a patch-first workflow. Only `observed_fulltext` patches with exact record IDs, non-empty evidence, source section, empty target fields, and whitelisted target paths may be applied to nested records. External descriptors are exported as sidecar features and must not overwrite observed experimental fields.

## Known Limitations

The dataset is literature-mined and not manually verified end-to-end. Preparation and hydrogel physical-property coverage are much lower than identity and outcome coverage. Use `field_coverage.csv`, `completion_patch_audit.csv`, `external_descriptor_audit.csv`, `model_ready_reason`, and provenance/evidence columns when building predictive or generative models.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_datasheet(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# Datasheet

## Motivation

The dataset is intended to support protein-hydrogel adsorption analysis, tabular predictive modeling, and inverse design of hydrogel materials.

## Composition

The package contains article-level source metadata, record-level structured facts, raw nested JSON, material/protein entity tables, special article-specific fields, and conservative model-ready subsets.

## Collection Process

Records were mined from locally stored article JSON files using a Codex extraction prompt and then audited for status, field coverage, quality flags, and model readiness.

## Preprocessing

The curated export flattens nested JSON into CSV, preserves raw JSONL, assigns curation decisions to sources, normalizes record IDs, and computes model-ready flags. It keeps second-pass field completion as auditable patches and keeps PubChem/UniProt/RCSB values as external descriptor sidecars.

## Recommended Uses

- Exploratory analysis of protein-hydrogel adsorption and antifouling literature.
- Baseline tabular models using high-confidence model-ready records.
- Descriptor enrichment through PubChem and UniProt before deep learning.
- Candidate generation and inverse design using `inverse_design_seed.csv`.

## Discouraged Uses

- Treating all raw records as ground truth without manual verification.
- Training high-stakes models without checking source evidence and missingness.
- Comparing incompatible targets without unit normalization and assay-mode stratification.

## Maintenance

Regenerate this package from the SQLite extraction database after new extraction, manual review, enrichment, or schema changes.

Generated: {summary['generated_at']}
"""
    metadata_dir = out_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "datasheet.md").write_text(text, encoding="utf-8")


def write_data_dictionary(out_dir: Path) -> None:
    rows = [
        {"table": "sources.csv", "column": "curation_decision", "description": "Article-level inclusion/exclusion decision for curated exports."},
        {"table": "records_flat.csv", "column": "model_ready", "description": "Boolean flag for conservative model-ready rows."},
        {"table": "records_flat.csv", "column": "model_ready_reason", "description": "Semicolon-separated reasons why a row is not model-ready, or ready."},
        {"table": "records_flat.csv", "column": "primary_target_name", "description": "Selected primary target according to target priority."},
        {"table": "records_flat.csv", "column": "primary_target_value", "description": "Numeric value of the selected primary target."},
        {"table": "records_flat.csv", "column": "primary_target_unit", "description": "Unit of the selected primary target."},
        {"table": "records_flat.csv", "column": "doi_split", "description": "Deterministic DOI-level train/validation/test split."},
        {"table": "model_records.csv", "column": "doi_split", "description": "Deterministic DOI-level train/validation/test split."},
        {"table": "inverse_design_seed.csv", "column": "target_direction", "description": "Suggested optimization direction for the target."},
        {"table": "inverse_design_seed.csv", "column": "doi_split", "description": "Deterministic DOI-level train/validation/test split."},
        {"table": "material_descriptors.csv", "column": "match_status", "description": "PubChem enrichment status: matched, no_match, error, not_queried, or unknown_payload."},
        {"table": "material_descriptors.csv", "column": "canonical_smiles", "description": "PubChem canonical/connectivity SMILES for descriptor generation when available."},
        {"table": "material_descriptors.csv", "column": "pubchem_cid", "description": "PubChem compound identifier for matched small molecules."},
        {"table": "protein_descriptors.csv", "column": "match_status", "description": "UniProt enrichment status: matched, no_match, error, not_queried, or unknown_payload."},
        {"table": "protein_descriptors.csv", "column": "qa_status", "description": "Whether the UniProt match is directly usable or needs accession/species review."},
        {"table": "protein_descriptors.csv", "column": "uniprot_accession", "description": "UniProt accession for matched protein query."},
        {"table": "protein_descriptors.csv", "column": "sequence_available", "description": "Whether a protein sequence was returned and can be used for sequence embeddings."},
        {"table": "completion_patches.csv", "column": "target_path", "description": "Whitelisted nested record path proposed for second-pass completion."},
        {"table": "completion_patches.csv", "column": "value_origin", "description": "Origin of the patch value; only observed_fulltext patches may be applied to experimental records."},
        {"table": "completion_patches.csv", "column": "apply_status", "description": "Patch validation/application result such as applied, eligible_not_applied, or rejected_existing_value."},
        {"table": "article_level_properties.csv", "column": "field_name", "description": "Observed article-level field that could not be safely mapped to one exact record."},
        {"table": "external_material_descriptors.csv", "column": "value_origin", "description": "Always external_descriptor; sidecar chemistry feature, not an observed experiment field."},
        {"table": "external_protein_descriptors.csv", "column": "value_origin", "description": "Always external_descriptor; sidecar protein feature, not an observed experiment field."},
        {"table": "external_structure_descriptors.csv", "column": "rcsb_polymer_entity_ids", "description": "RCSB PDB polymer entity identifiers linked from a QA-usable UniProt accession."},
        {"table": "external_descriptor_audit.csv", "column": "usable", "description": "Sidecar descriptor rows considered usable after source-specific QA."},
    ]
    for field, description in MODEL_FIELDS.items():
        rows.append({"table": "records_flat.csv", "column": field.replace(".", "__"), "description": description})
    write_csv(out_dir / "metadata" / "data_dictionary.csv", rows)


def build_package(
    db_path: Path,
    output_dir: Path,
    audit_md: Path | None,
    completion_dir: Path | None = DEFAULT_COMPLETION_DIR,
    external_descriptor_dir: Path | None = DEFAULT_EXTERNAL_DESCRIPTOR_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    metadata_dir = output_dir / "metadata"
    report_dir = output_dir / "reports"
    for d in [data_dir, metadata_dir, report_dir]:
        d.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    articles = [dict(r) for r in con.execute("SELECT * FROM article_extractions ORDER BY doi").fetchall()]
    records = [dict(r) for r in con.execute("SELECT * FROM adsorption_records ORDER BY doi, id").fetchall()]
    materials = read_table(con, "material_mentions")
    proteins = read_table(con, "protein_mentions")
    special = read_table(con, "special_fields")
    con.close()

    article_lookup = {str(row.get("doi") or "").lower(): row for row in articles}
    source_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    partial_rows: list[dict[str, Any]] = []
    source_fieldnames = [
        "doi",
        "title",
        "publisher",
        "status",
        "records_count",
        "material_mentions_count",
        "protein_mentions_count",
        "special_fields_count",
        "source_json",
        "curation_decision",
        "curation_reason",
        "error_message",
    ]
    for row in articles:
        decision, reason = article_decision(row)
        src = {
            "doi": row.get("doi"),
            "title": row.get("title"),
            "publisher": row.get("publisher"),
            "status": row.get("status"),
            "records_count": row.get("records_count"),
            "material_mentions_count": row.get("material_mentions_count"),
            "protein_mentions_count": row.get("protein_mentions_count"),
            "special_fields_count": row.get("special_fields_count"),
            "source_json": row.get("source_json"),
            "curation_decision": decision,
            "curation_reason": reason,
            "error_message": row.get("error_message"),
        }
        source_rows.append(src)
        if row.get("status") == "failed":
            failed_rows.append(src)
        if row.get("status") == "partial":
            partial_rows.append(src)

    flat_rows = [record_flat_row(row, article_lookup) for row in records]
    model_rows = [row for row in flat_rows if row.get("model_ready")]
    inverse_rows = [inverse_design_row(row) for row in model_rows]
    material_descriptor = material_descriptor_rows(materials)
    protein_descriptor = protein_descriptor_rows(proteins)

    write_csv(data_dir / "sources.csv", source_rows)
    write_csv(data_dir / "records_flat.csv", flat_rows)
    write_jsonl(data_dir / "records_raw.jsonl", [load_json(row.get("record_json")) for row in records])
    write_csv(data_dir / "model_records.csv", model_rows)
    write_csv(data_dir / "inverse_design_seed.csv", inverse_rows)
    materials.to_csv(data_dir / "materials.csv", index=False, encoding="utf-8")
    proteins.to_csv(data_dir / "proteins.csv", index=False, encoding="utf-8")
    write_csv(data_dir / "material_descriptors.csv", material_descriptor)
    write_csv(data_dir / "protein_descriptors.csv", protein_descriptor)
    special.to_csv(data_dir / "special_fields.csv", index=False, encoding="utf-8")
    write_csv(metadata_dir / "failed_articles.csv", failed_rows, source_fieldnames)
    write_csv(metadata_dir / "partial_articles.csv", partial_rows, source_fieldnames)
    write_csv(metadata_dir / "field_coverage.csv", field_coverage(flat_rows))
    write_csv(metadata_dir / "field_completion_candidates.csv", field_completion_candidates(flat_rows))
    write_data_dictionary(output_dir)
    integrate_completion_outputs(output_dir, completion_dir)
    integrate_external_descriptor_outputs(output_dir, external_descriptor_dir, material_descriptor, protein_descriptor)
    if audit_md and audit_md.exists():
        shutil.copy2(audit_md, report_dir / audit_md.name)
    for report in sorted((ROOT / "reports").glob("PHA_*_20260705.md")):
        shutil.copy2(report, report_dir / report.name)

    status_counts = {row["status"]: 0 for row in articles}
    for row in articles:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    summary = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "db_path": str(db_path),
        "articles_total": len(articles),
        "success": status_counts.get("success", 0),
        "partial": status_counts.get("partial", 0),
        "failed": status_counts.get("failed", 0),
        "records_total": len(records),
        "model_ready_records": len(model_rows),
        "inverse_design_rows": len(inverse_rows),
        "materials": len(materials),
        "proteins": len(proteins),
        "material_descriptor_matches": sum(1 for row in material_descriptor if row.get("match_status") == "matched"),
        "protein_descriptor_matches": sum(1 for row in protein_descriptor if row.get("match_status") == "matched"),
        "protein_descriptor_needs_review": sum(1 for row in protein_descriptor if row.get("qa_status") == "needs_review"),
        "special_fields": len(special),
        "completion_patches": len(read_csv_if_exists(metadata_dir / "completion_patches.csv")),
        "external_material_descriptor_rows": len(read_csv_if_exists(data_dir / "external_material_descriptors.csv")),
        "external_protein_descriptor_rows": len(read_csv_if_exists(data_dir / "external_protein_descriptors.csv")),
    }
    (metadata_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(output_dir, summary)
    write_datasheet(output_dir, summary)

    checksum_rows = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "checksums_sha256.csv":
            checksum_rows.append({"path": str(path.relative_to(output_dir)).replace("\\", "/"), "sha256": sha256(path), "bytes": path.stat().st_size})
    write_csv(metadata_dir / "checksums_sha256.csv", checksum_rows)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Scientific Data style PHA curated dataset package.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--audit-md", type=Path)
    parser.add_argument("--completion-dir", type=Path, default=DEFAULT_COMPLETION_DIR)
    parser.add_argument("--external-descriptor-dir", type=Path, default=DEFAULT_EXTERNAL_DESCRIPTOR_DIR)
    args = parser.parse_args(argv)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT / f"pha_scientific_dataset_{stamp}"
    summary = build_package(args.db, output_dir, args.audit_md, args.completion_dir, args.external_descriptor_dir)
    print(json.dumps({"output_dir": str(output_dir), **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
