from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
import json
import math
import random
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "processed" / "pha_extraction_1000_xhigh_fulltext_w8" / "codex_extraction_results.db"


COVERAGE_GROUPS: dict[str, list[str]] = {
    "provenance": [
        "provenance.doi",
        "provenance.title",
        "provenance.source_section",
        "provenance.source_table_or_figure",
        "provenance.evidence_text",
        "provenance.extraction_confidence",
    ],
    "hydrogel_identity": [
        "hydrogel.hydrogel_name",
        "hydrogel.hydrogel_format",
        "hydrogel.polymer_backbone",
        "hydrogel.monomers",
        "hydrogel.functional_groups",
        "hydrogel.ligand_or_affinity_group",
        "hydrogel.filler_or_composite",
        "hydrogel.substrate_or_support",
    ],
    "preparation": [
        "hydrogel.monomer_ratios",
        "hydrogel.crosslinker",
        "hydrogel.crosslinker_concentration",
        "hydrogel.initiator",
        "hydrogel.synthesis_method",
        "hydrogel.preparation_solvent",
        "hydrogel.preparation_pH",
        "hydrogel.preparation_temp_C",
        "hydrogel.gelation_time",
        "hydrogel.post_treatment",
    ],
    "hydrogel_properties": [
        "hydrogel_properties.charge_class",
        "hydrogel_properties.swelling_ratio",
        "hydrogel_properties.water_content_pct",
        "hydrogel_properties.porosity_pct",
        "hydrogel_properties.pore_size",
        "hydrogel_properties.mesh_size",
        "hydrogel_properties.surface_area",
        "hydrogel_properties.particle_size",
        "hydrogel_properties.thickness",
        "hydrogel_properties.roughness",
        "hydrogel_properties.zeta_potential_mV",
        "hydrogel_properties.contact_angle_deg",
        "hydrogel_properties.young_modulus",
        "hydrogel_properties.responsive_type",
        "hydrogel_properties.degradation_or_stability",
    ],
    "protein": [
        "protein.protein_name",
        "protein.protein_abbreviation",
        "protein.protein_species_or_source",
        "protein.molecular_weight_kDa",
        "protein.pI",
        "protein.charge_at_experiment_pH",
        "protein.protein_initial_concentration",
        "protein.protein_matrix",
        "protein.competitor_proteins",
        "protein.protein_class",
    ],
    "experiment": [
        "experiment.experiment_mode",
        "experiment.hydrogel_dosage",
        "experiment.solution_volume",
        "experiment.pH",
        "experiment.buffer",
        "experiment.ionic_strength",
        "experiment.salt_type",
        "experiment.salt_concentration",
        "experiment.temperature_C",
        "experiment.contact_time",
        "experiment.flow_rate",
        "experiment.detection_method",
        "experiment.replicate_count",
        "experiment.adsorption_type",
        "experiment.competition_system",
    ],
    "outcome": [
        "outcome.outcome_label",
        "outcome.raw_metric_name",
        "outcome.raw_metric_value",
        "outcome.raw_metric_unit",
        "outcome.q_norm_mg_g",
        "outcome.q_norm_mg_mL_bed",
        "outcome.surface_adsorption_ug_cm2",
        "outcome.removal_efficiency_pct",
        "outcome.binding_efficiency_pct",
        "outcome.recovery_pct",
        "outcome.purity_pct",
        "outcome.dynamic_binding_capacity",
        "outcome.selectivity_factor",
        "outcome.imprinting_factor",
        "outcome.association_constant_Ka",
        "outcome.dissociation_constant_Kd",
        "outcome.isotherm_model",
        "outcome.kinetic_model",
        "outcome.fouling_reduction_pct",
        "outcome.retained_capacity_pct",
    ],
    "mechanism_quality": [
        "mechanism.mechanism_tags",
        "mechanism.mechanism_evidence_text",
        "mechanism.control_type",
        "mechanism.control_material",
        "mechanism.control_outcome",
        "mechanism.fold_change_vs_control",
        "quality.unit_normalized",
        "quality.source_quality_score",
        "quality.needs_manual_review",
        "quality.missing_conditions",
    ],
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
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def measured_value_number(value: Any) -> float | None:
    if isinstance(value, dict):
        return numeric(value.get("value"))
    return numeric(value)


def table_count(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return int(cur.execute("select count(*) from " + table).fetchone()[0])
    except Exception:
        return 0


def counter_from_records(records: list[dict[str, Any]], path: str, limit: int = 20) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for rec in records:
        value = get_path(rec, path)
        if isinstance(value, list):
            for item in value:
                if has_value(item):
                    counts[str(item)] += 1
        elif has_value(value):
            counts[str(value)] += 1
    return [{"value": key, "count": count} for key, count in counts.most_common(limit)]


def summarize_coverage(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    total = max(len(records), 1)
    field_coverage: dict[str, dict[str, Any]] = {}
    group_coverage: dict[str, dict[str, Any]] = {}
    for group, paths in COVERAGE_GROUPS.items():
        group_hits = 0
        group_possible = len(paths) * total
        for path in paths:
            count = sum(1 for rec in records if has_value(get_path(rec, path)))
            if count:
                group_hits += count
            field_coverage[path] = {
                "present": count,
                "total": len(records),
                "coverage_pct": round(count / total * 100, 2),
            }
        group_coverage[group] = {
            "present_cells": group_hits,
            "possible_cells": group_possible,
            "coverage_pct": round(group_hits / max(group_possible, 1) * 100, 2),
        }
    return field_coverage, group_coverage


def build_issues(rows: list[dict[str, Any]], records: list[dict[str, Any]], sample_limit: int) -> dict[str, list[dict[str, Any]]]:
    by_record_id: Counter[str] = Counter()
    for row in rows:
        if row.get("record_id"):
            by_record_id[str(row["record_id"])] += 1

    issue_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row, rec in zip(rows, records):
        quality = rec.get("quality") or {}
        provenance = rec.get("provenance") or {}
        outcome = rec.get("outcome") or {}
        experiment = rec.get("experiment") or {}
        hydrogel = rec.get("hydrogel") or {}
        protein = rec.get("protein") or {}

        base = {
            "record_id": row.get("record_id"),
            "doi": row.get("doi"),
            "title": row.get("title"),
            "hydrogel": hydrogel.get("hydrogel_name") or row.get("hydrogel_name"),
            "protein": protein.get("protein_name") or row.get("protein_name"),
        }
        confidence = numeric(provenance.get("extraction_confidence") or row.get("extraction_confidence"))
        score = numeric(quality.get("source_quality_score") if quality else row.get("source_quality_score"))
        p_h = numeric(experiment.get("pH") or row.get("pH"))
        temp = numeric(experiment.get("temperature_C"))
        q_norm = numeric(outcome.get("q_norm_mg_g") if outcome else row.get("q_norm_mg_g"))
        raw_value = outcome.get("raw_metric_value") if outcome else row.get("raw_metric_value")
        raw_unit = outcome.get("raw_metric_unit") if outcome else row.get("raw_metric_unit")
        evidence = str(provenance.get("evidence_text") or row.get("evidence_text") or "")

        if row.get("record_id") and by_record_id[str(row["record_id"])] > 1:
            issue_rows["duplicate_record_id"].append(base | {"issue": "duplicate record_id"})
        if quality.get("needs_manual_review") or row.get("needs_manual_review"):
            issue_rows["needs_manual_review"].append(base | {"issue": "marked for manual review"})
        if confidence is not None and confidence < 0.55:
            issue_rows["low_confidence"].append(base | {"issue": f"confidence={confidence}"})
        if score is not None and score <= 1:
            issue_rows["low_source_quality"].append(base | {"issue": f"source_quality_score={score}"})
        if p_h is not None and not (0 <= p_h <= 14):
            issue_rows["invalid_pH"].append(base | {"issue": f"pH={p_h}"})
        if temp is not None and not (-20 <= temp <= 150):
            issue_rows["suspicious_temperature"].append(base | {"issue": f"temperature_C={temp}"})
        if q_norm is not None and (q_norm < 0 or q_norm > 50000):
            issue_rows["suspicious_q_norm"].append(base | {"issue": f"q_norm_mg_g={q_norm}"})
        if has_value(raw_value) and not has_value(raw_unit):
            issue_rows["raw_value_missing_unit"].append(base | {"issue": "raw metric value has no unit"})
        if not has_value(raw_value) and not any(has_value(outcome.get(k)) for k in ["q_norm_mg_g", "surface_adsorption_ug_cm2", "removal_efficiency_pct", "binding_efficiency_pct", "fouling_reduction_pct"]):
            issue_rows["no_numeric_outcome"].append(base | {"issue": "no numeric outcome"})
        if len(evidence.strip()) < 30:
            issue_rows["weak_evidence_text"].append(base | {"issue": "evidence_text is short or absent"})

    random.seed(42)
    limited: dict[str, list[dict[str, Any]]] = {}
    for key, items in issue_rows.items():
        if len(items) > sample_limit:
            limited[key] = random.sample(items, sample_limit)
        else:
            limited[key] = items
    return limited


def audit(db_path: Path, target_articles: int | None, sample_limit: int) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    tables = [row[0] for row in cur.execute("select name from sqlite_master where type = 'table' order by name").fetchall()]
    article_rows = [dict(row) for row in cur.execute("select * from article_extractions order by updated_at").fetchall()]
    record_rows = [dict(row) for row in cur.execute("select * from adsorption_records order by doi, id").fetchall()]
    aux_counts = {
        "material_mentions": table_count(cur, "material_mentions"),
        "protein_mentions": table_count(cur, "protein_mentions"),
        "special_fields": table_count(cur, "special_fields"),
    }
    con.close()

    parsed_records = [load_json(row.get("record_json")) for row in record_rows]
    field_coverage, group_coverage = summarize_coverage(parsed_records)
    status_counts = Counter(str(row.get("status")) for row in article_rows)
    records_per_article = Counter(str(row.get("records_count")) for row in article_rows)

    usable_target_count = 0
    for rec in parsed_records:
        outcome = rec.get("outcome") or {}
        quality = rec.get("quality") or {}
        model_label = rec.get("ai_modeling_labels") or {}
        has_target = any(has_value(outcome.get(k)) for k in [
            "q_norm_mg_g",
            "q_norm_mg_mL_bed",
            "surface_adsorption_ug_cm2",
            "removal_efficiency_pct",
            "binding_efficiency_pct",
            "fouling_reduction_pct",
            "retained_capacity_pct",
            "raw_metric_value",
        ])
        if has_target and not quality.get("needs_manual_review") and model_label.get("usable_for_training") is not False:
            usable_target_count += 1

    report: dict[str, Any] = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "db_path": str(db_path),
        "target_articles": target_articles,
        "tables": tables,
        "counts": {
            "article_extractions": len(article_rows),
            "adsorption_records": len(record_rows),
            "material_mentions": aux_counts["material_mentions"],
            "protein_mentions": aux_counts["protein_mentions"],
            "special_fields": aux_counts["special_fields"],
        },
        "article_completion_pct": round(len(article_rows) / target_articles * 100, 2) if target_articles else None,
        "status_counts": dict(status_counts),
        "records_per_article_counts": dict(records_per_article),
        "top_values": {
            "triage_labels": counter_from_records(parsed_records, "triage.relevance_label"),
            "study_types": counter_from_records(parsed_records, "triage.study_type"),
            "hydrogel_formats": counter_from_records(parsed_records, "hydrogel.hydrogel_format"),
            "experiment_modes": counter_from_records(parsed_records, "experiment.experiment_mode"),
            "outcome_labels": counter_from_records(parsed_records, "outcome.outcome_label"),
            "raw_metric_names": counter_from_records(parsed_records, "outcome.raw_metric_name"),
            "mechanism_tags": counter_from_records(parsed_records, "mechanism.mechanism_tags"),
            "protein_names": counter_from_records(parsed_records, "protein.protein_name"),
        },
        "group_coverage": group_coverage,
        "field_coverage": field_coverage,
        "model_readiness": {
            "records_with_any_target_and_not_review": usable_target_count,
            "pct_of_records": round(usable_target_count / max(len(record_rows), 1) * 100, 2),
            "records_with_q_norm_mg_g": field_coverage["outcome.q_norm_mg_g"]["present"],
            "records_with_surface_adsorption_ug_cm2": field_coverage["outcome.surface_adsorption_ug_cm2"]["present"],
            "records_with_pH": field_coverage["experiment.pH"]["present"],
            "records_with_contact_time": field_coverage["experiment.contact_time"]["present"],
            "records_with_hydrogel_properties_any": group_coverage["hydrogel_properties"]["coverage_pct"],
            "records_with_preparation_any": group_coverage["preparation"]["coverage_pct"],
        },
        "issue_samples": build_issues(record_rows, parsed_records, sample_limit),
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    counts = report["counts"]
    lines = [
        "# PHA extraction quality audit",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Database: `{report['db_path']}`",
        f"- Articles: {counts['article_extractions']} / {report.get('target_articles') or 'unknown'}",
        f"- Records: {counts['adsorption_records']}",
        f"- Materials / proteins / special fields: {counts['material_mentions']} / {counts['protein_mentions']} / {counts['special_fields']}",
        "",
        "## Article status",
        "",
    ]
    for key, value in sorted(report["status_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Model readiness", ""])
    for key, value in report["model_readiness"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Coverage by group", ""])
    for group, item in report["group_coverage"].items():
        lines.append(f"- {group}: {item['coverage_pct']}% ({item['present_cells']}/{item['possible_cells']})")
    lines.extend(["", "## Key field coverage", ""])
    important = [
        "hydrogel.monomers",
        "hydrogel.crosslinker",
        "hydrogel.synthesis_method",
        "hydrogel_properties.swelling_ratio",
        "hydrogel_properties.pore_size",
        "hydrogel_properties.zeta_potential_mV",
        "hydrogel_properties.contact_angle_deg",
        "protein.molecular_weight_kDa",
        "protein.pI",
        "experiment.pH",
        "experiment.contact_time",
        "experiment.temperature_C",
        "outcome.raw_metric_value",
        "outcome.raw_metric_unit",
        "outcome.q_norm_mg_g",
        "outcome.surface_adsorption_ug_cm2",
        "mechanism.mechanism_tags",
        "quality.needs_manual_review",
    ]
    for key in important:
        item = report["field_coverage"].get(key)
        if item:
            lines.append(f"- {key}: {item['coverage_pct']}% ({item['present']}/{item['total']})")
    lines.extend(["", "## Top values", ""])
    for group, values in report["top_values"].items():
        compact = ", ".join(f"{v['value']} ({v['count']})" for v in values[:10])
        lines.append(f"- {group}: {compact}")
    lines.extend(["", "## Issue samples", ""])
    for issue, samples in report["issue_samples"].items():
        lines.append(f"### {issue} ({len(samples)} sampled)")
        if not samples:
            lines.append("")
            continue
        for sample in samples[:10]:
            lines.append(
                f"- {sample.get('record_id')} | {sample.get('doi')} | "
                f"{sample.get('hydrogel')} / {sample.get('protein')} | {sample.get('issue')}"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PHA Codex extraction quality.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--target-articles", type=int)
    parser.add_argument("--sample-limit", type=int, default=30)
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise FileNotFoundError(args.db)
    out_dir = args.output_dir or args.db.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    report = audit(args.db, args.target_articles, args.sample_limit)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"quality_audit_{stamp}.json"
    md_path = out_dir / f"QUALITY_AUDIT_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"Audit JSON: {json_path}")
    print(f"Audit MD: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
