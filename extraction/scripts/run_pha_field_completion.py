from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
from typing import Any

import pandas as pd

from run_codex_pha_extraction import build_context, extract_json, flatten_full_text, html_to_text, load_json, safe_id


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTRACTION_DB = ROOT / "data" / "processed" / "pha_extraction_1000_xhigh_fulltext_w8" / "codex_extraction_results.db"
DEFAULT_CANDIDATES = ROOT / "data" / "curated" / "pha_scientific_dataset_20260705" / "metadata" / "field_completion_candidates.csv"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "pha_field_completion"
DEFAULT_PROMPT = ROOT / "extraction" / "prompts" / "pha_field_completion_prompt_v4_targeted.md"

TARGETED_ARTICLE_TYPES = [
    "cryogel_column",
    "mip_imprinting",
    "antifouling_surface",
    "enzyme_immobilization",
    "micro_nanogel",
    "general_batch_adsorption",
]

FIELD_CONTEXT_TERMS = [
    "adsorption", "adsorb", "binding", "bind", "immobilization", "immobilized",
    "protein concentration", "initial concentration", "contact time", "incubation",
    "equilibration", "kinetic", "isotherm", "buffer", "ph", "temperature",
    "ionic strength", "salt", "flow rate", "solution volume", "dosage",
    "preparation", "prepared", "synthesis", "synthesized", "polymerization",
    "monomer", "crosslink", "cross-link", "initiator", "gelation", "washing",
    "conditioning", "swelling", "water content", "porosity", "pore", "mesh",
    "surface area", "particle size", "thickness", "roughness", "zeta",
    "contact angle", "modulus", "rheology", "mechanical", "sem", "dls",
    "characterization", "isoelectric", "molecular weight", "molecular mass",
    "cryogel", "cryogelation", "freezing", "thawing", "bed volume",
    "breakthrough", "dynamic binding capacity", "dbc", "imprinting factor",
    "molecularly imprinted", "non-specific adsorption", "protein fouling",
    "surface coverage", "contact angle", "roughness", "thickness",
]

FIELD_TITLE_RE = re.compile(
    r"method|material|experiment|synth|prepar|character|adsorp|bind|immobil|"
    r"swelling|kinetic|isotherm|result|discussion|table",
    re.I,
)


UPDATE_SECTIONS = {
    "preparation_update": {
        "monomer_ratios": ("hydrogel", "monomer_ratios"),
        "crosslinker_concentration": ("hydrogel", "crosslinker_concentration"),
        "initiator": ("hydrogel", "initiator"),
        "synthesis_method": ("hydrogel", "synthesis_method"),
        "preparation_solvent": ("hydrogel", "preparation_solvent"),
        "preparation_pH": ("hydrogel", "preparation_pH"),
        "preparation_temp_C": ("hydrogel", "preparation_temp_C"),
        "gelation_time": ("hydrogel", "gelation_time"),
        "post_treatment": ("hydrogel", "post_treatment"),
        "washing_or_conditioning": ("hydrogel", "post_treatment"),
        "storage_condition": ("hydrogel", "post_treatment"),
    },
    "hydrogel_property_update": {
        "swelling_ratio": ("hydrogel_properties", "swelling_ratio"),
        "water_content_pct": ("hydrogel_properties", "water_content_pct"),
        "porosity_pct": ("hydrogel_properties", "porosity_pct"),
        "pore_size": ("hydrogel_properties", "pore_size"),
        "mesh_size": ("hydrogel_properties", "mesh_size"),
        "surface_area": ("hydrogel_properties", "surface_area"),
        "particle_size": ("hydrogel_properties", "particle_size"),
        "thickness": ("hydrogel_properties", "thickness"),
        "roughness": ("hydrogel_properties", "roughness"),
        "zeta_potential_mV": ("hydrogel_properties", "zeta_potential_mV"),
        "contact_angle_deg": ("hydrogel_properties", "contact_angle_deg"),
        "young_modulus": ("hydrogel_properties", "young_modulus"),
        "mechanical_modulus": ("hydrogel_properties", "young_modulus"),
        "responsive_type": ("hydrogel_properties", "responsive_type"),
        "degradation_or_stability": ("hydrogel_properties", "degradation_or_stability"),
    },
    "protein_property_update": {
        "molecular_weight_kDa": ("protein", "molecular_weight_kDa"),
        "pI": ("protein", "pI"),
        "charge_at_experiment_pH": ("protein", "charge_at_experiment_pH"),
        "protein_initial_concentration": ("protein", "protein_initial_concentration"),
        "protein_matrix": ("protein", "protein_matrix"),
        "competitor_proteins": ("protein", "competitor_proteins"),
    },
    "assay_condition_update": {
        "experiment_mode": ("experiment", "experiment_mode"),
        "pH": ("experiment", "pH"),
        "buffer": ("experiment", "buffer"),
        "ionic_strength": ("experiment", "ionic_strength"),
        "salt_type": ("experiment", "salt_type"),
        "salt_concentration": ("experiment", "salt_concentration"),
        "temperature_C": ("experiment", "temperature_C"),
        "contact_time": ("experiment", "contact_time"),
        "hydrogel_dosage": ("experiment", "hydrogel_dosage"),
        "solution_volume": ("experiment", "solution_volume"),
        "flow_rate": ("experiment", "flow_rate"),
        "detection_method": ("experiment", "detection_method"),
        "replicate_count": ("experiment", "replicate_count"),
        "protein_initial_concentration": ("protein", "protein_initial_concentration"),
    },
    "outcome_update": {
        "q_norm_mg_g": ("outcome", "q_norm_mg_g"),
        "q_norm_mg_mL_bed": ("outcome", "q_norm_mg_mL_bed"),
        "surface_adsorption_ug_cm2": ("outcome", "surface_adsorption_ug_cm2"),
        "removal_efficiency_pct": ("outcome", "removal_efficiency_pct"),
        "binding_efficiency_pct": ("outcome", "binding_efficiency_pct"),
        "recovery_pct": ("outcome", "recovery_pct"),
        "purity_pct": ("outcome", "purity_pct"),
        "dynamic_binding_capacity": ("outcome", "dynamic_binding_capacity"),
        "selectivity_factor": ("outcome", "selectivity_factor"),
        "imprinting_factor": ("outcome", "imprinting_factor"),
        "association_constant_Ka": ("outcome", "association_constant_Ka"),
        "dissociation_constant_Kd": ("outcome", "dissociation_constant_Kd"),
        "fouling_reduction_pct": ("outcome", "fouling_reduction_pct"),
        "retained_capacity_pct": ("outcome", "retained_capacity_pct"),
        "raw_metric_value": ("outcome", "raw_metric_value"),
        "raw_metric_unit": ("outcome", "raw_metric_unit"),
    },
}

ALLOWED_TARGET_PATHS = {
    ".".join(target_path): target_path
    for section in UPDATE_SECTIONS.values()
    for target_path in section.values()
}

PATCH_FIELDNAMES = [
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

ARTICLE_LEVEL_FIELDNAMES = [
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


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        stripped = value.strip().lower()
        return bool(stripped) and stripped not in {"null", "none", "unknown", "not reported", "n/a", "na"}
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    if isinstance(value, dict):
        return any(has_value(v) for v in value.values())
    return True


def ensure_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS field_completion_articles (
            doi TEXT PRIMARY KEY,
            status TEXT,
            source_json TEXT,
            prompt_version TEXT,
            model TEXT,
            reasoning_effort TEXT,
            updates_count INTEGER,
            applied_updates_count INTEGER DEFAULT 0,
            output_json TEXT,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS field_completion_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            record_id_hint TEXT,
            matched_record_id TEXT,
            update_json TEXT,
            applied_fields_json TEXT,
            evidence_text TEXT,
            confidence REAL
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS field_completion_patches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            record_id TEXT,
            matched_record_id TEXT,
            target_path TEXT,
            value_json TEXT,
            value_origin TEXT,
            evidence_text TEXT,
            source_section TEXT,
            source_table_or_figure TEXT,
            confidence REAL,
            prompt_version TEXT,
            article_type TEXT,
            apply_status TEXT,
            qa_note TEXT,
            created_at TEXT
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS article_level_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            field_name TEXT,
            value_json TEXT,
            value_origin TEXT,
            evidence_text TEXT,
            source_section TEXT,
            source_table_or_figure TEXT,
            confidence REAL,
            prompt_version TEXT,
            article_type TEXT,
            qa_note TEXT,
            created_at TEXT
        )
        """
    )
    con.commit()
    return con


def extraction_article_rows(db: Path) -> dict[str, dict[str, Any]]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = {str(r["doi"]).lower(): dict(r) for r in con.execute("SELECT * FROM article_extractions").fetchall()}
    con.close()
    return rows


def record_summary(db: Path, doi: str, max_records: int = 80) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT id, record_id, hydrogel_name, protein_name, experiment_mode, pH, raw_metric_name, raw_metric_value, raw_metric_unit, record_json FROM adsorption_records WHERE lower(doi)=lower(?) ORDER BY id", (doi,)).fetchall()]
    con.close()
    summaries: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows[:max_records]:
        rec = json.loads(row.get("record_json") or "{}")
        rid = str(row.get("record_id") or "")
        by_id[rid] = rec
        summaries.append(
            {
                "record_id": rid,
                "hydrogel_name": row.get("hydrogel_name"),
                "protein_name": row.get("protein_name"),
                "experiment_mode": row.get("experiment_mode"),
                "pH": row.get("pH"),
                "raw_metric": f"{row.get('raw_metric_name')}: {row.get('raw_metric_value')} {row.get('raw_metric_unit')}",
                "missing_focus": missing_focus(rec),
            }
        )
    return summaries, by_id


def missing_focus(rec: dict[str, Any]) -> list[str]:
    focus: list[str] = []
    checks = {
        "monomer_ratios": ("hydrogel", "monomer_ratios"),
        "crosslinker_concentration": ("hydrogel", "crosslinker_concentration"),
        "preparation_temp_C": ("hydrogel", "preparation_temp_C"),
        "swelling_ratio": ("hydrogel_properties", "swelling_ratio"),
        "pore_size": ("hydrogel_properties", "pore_size"),
        "zeta_potential_mV": ("hydrogel_properties", "zeta_potential_mV"),
        "contact_angle_deg": ("hydrogel_properties", "contact_angle_deg"),
        "protein_mw": ("protein", "molecular_weight_kDa"),
        "protein_pI": ("protein", "pI"),
        "temperature_C": ("experiment", "temperature_C"),
    }
    for label, path in checks.items():
        if not has_value(get_nested(rec, path)):
            focus.append(label)
    return focus


def get_nested(obj: dict[str, Any], path: tuple[str, str]) -> Any:
    first, second = path
    value = obj.get(first)
    if not isinstance(value, dict):
        return None
    return value.get(second)


def set_if_missing(rec: dict[str, Any], path: tuple[str, str], value: Any) -> bool:
    if not has_value(value):
        return False
    section, field = path
    target = rec.setdefault(section, {})
    if not isinstance(target, dict):
        return False
    if has_value(target.get(field)):
        return False
    target[field] = value
    return True


def normalize_target_path(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("__", ".")


def parse_value_json(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and stripped[0] in "[{\"" or stripped in {"null", "true", "false"}:
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def patch_row(
    doi: str,
    record_id: str,
    target_path: str,
    value: Any,
    origin: str,
    evidence_text: Any,
    source_section: Any,
    source_table_or_figure: Any,
    confidence: Any,
    prompt_version: str,
    article_type: str,
    qa_note: str = "",
) -> dict[str, Any]:
    return {
        "doi": doi,
        "record_id": str(record_id or "").strip(),
        "matched_record_id": "",
        "target_path": normalize_target_path(target_path),
        "value": parse_value_json(value),
        "value_json": as_json(parse_value_json(value)),
        "value_origin": str(origin or "observed_fulltext").strip() or "observed_fulltext",
        "evidence_text": str(evidence_text or "").strip(),
        "source_section": str(source_section or "").strip(),
        "source_table_or_figure": str(source_table_or_figure or "").strip(),
        "confidence": confidence,
        "prompt_version": prompt_version,
        "article_type": str(article_type or "").strip(),
        "apply_status": "pending",
        "qa_note": qa_note,
    }


def payload_to_patches(doi: str, payload: dict[str, Any], prompt_version: str) -> list[dict[str, Any]]:
    article = payload.get("article") or {}
    article_type = str(article.get("article_type") or payload.get("article_type") or "")
    patches: list[dict[str, Any]] = []

    explicit = payload.get("record_patches") or payload.get("patches") or []
    for item in explicit:
        if not isinstance(item, dict):
            continue
        target_path = normalize_target_path(item.get("target_path") or item.get("path") or item.get("field"))
        value = item.get("value") if "value" in item else item.get("value_json")
        patches.append(
            patch_row(
                doi=doi,
                record_id=str(item.get("record_id") or item.get("record_id_hint") or ""),
                target_path=target_path,
                value=value,
                origin=str(item.get("value_origin") or "observed_fulltext"),
                evidence_text=item.get("evidence_text"),
                source_section=item.get("source_section"),
                source_table_or_figure=item.get("source_table_or_figure"),
                confidence=item.get("confidence"),
                prompt_version=prompt_version,
                article_type=str(item.get("article_type") or article_type),
                qa_note=str(item.get("qa_note") or item.get("field_rationale") or ""),
            )
        )

    for update in payload.get("record_updates") or []:
        if not isinstance(update, dict):
            continue
        rid = str(update.get("record_id_hint") or update.get("record_id") or "").strip()
        local_article_type = str(update.get("article_type") or article_type)
        for update_section, mapping in UPDATE_SECTIONS.items():
            section_value = update.get(update_section) or {}
            if not isinstance(section_value, dict):
                continue
            for source_field, target_tuple in mapping.items():
                if source_field not in section_value:
                    continue
                value = section_value.get(source_field)
                patches.append(
                    patch_row(
                        doi=doi,
                        record_id=rid,
                        target_path=".".join(target_tuple),
                        value=value,
                        origin=str(update.get("value_origin") or "observed_fulltext"),
                        evidence_text=update.get("evidence_text"),
                        source_section=update.get("source_section"),
                        source_table_or_figure=update.get("source_table_or_figure"),
                        confidence=update.get("confidence"),
                        prompt_version=prompt_version,
                        article_type=local_article_type,
                        qa_note=f"converted_from_{update_section}.{source_field}",
                    )
                )
    return patches


def payload_to_article_level_rows(doi: str, payload: dict[str, Any], prompt_version: str) -> list[dict[str, Any]]:
    article = payload.get("article") or {}
    article_type = str(article.get("article_type") or payload.get("article_type") or "")
    rows: list[dict[str, Any]] = []
    values = payload.get("article_level_properties") or []
    if isinstance(values, dict):
        values = [{"field_name": key, "value": value} for key, value in values.items()]
    for item in values:
        if not isinstance(item, dict):
            continue
        value = item.get("value") if "value" in item else item.get("value_json")
        rows.append(
            {
                "doi": doi,
                "field_name": str(item.get("field_name") or item.get("target_path") or item.get("path") or "").strip(),
                "value": parse_value_json(value),
                "value_json": as_json(parse_value_json(value)),
                "value_origin": str(item.get("value_origin") or "observed_fulltext").strip() or "observed_fulltext",
                "evidence_text": str(item.get("evidence_text") or "").strip(),
                "source_section": str(item.get("source_section") or "").strip(),
                "source_table_or_figure": str(item.get("source_table_or_figure") or "").strip(),
                "confidence": item.get("confidence"),
                "prompt_version": prompt_version,
                "article_type": str(item.get("article_type") or article_type).strip(),
                "qa_note": str(item.get("qa_note") or item.get("why_article_level") or "").strip(),
            }
        )
    return rows


def patch_apply_status(rec_rows: dict[str, dict[str, Any]], patch: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    target_path = normalize_target_path(patch.get("target_path"))
    if target_path not in ALLOWED_TARGET_PATHS:
        return "rejected_unsupported_path", "target_path is not in the allowed patch whitelist", None
    if str(patch.get("value_origin") or "") != "observed_fulltext":
        return "rejected_origin", "only observed_fulltext patches may be applied to experimental records", None
    if not has_value(patch.get("value")):
        return "rejected_empty_value", "patch value is empty", None
    if not str(patch.get("evidence_text") or "").strip():
        return "rejected_missing_evidence", "observed patch requires evidence_text", None
    if not str(patch.get("source_section") or "").strip():
        return "rejected_missing_source", "observed patch requires source_section", None
    rid = str(patch.get("record_id") or "").strip()
    row = rec_rows.get(rid)
    if not row:
        return "rejected_unmatched_record", "record_id did not match an existing adsorption record", None
    rec = json.loads(row.get("record_json") or "{}")
    if has_value(get_nested(rec, ALLOWED_TARGET_PATHS[target_path])):
        return "rejected_existing_value", "target field already has a value", rec
    return "eligible", "", rec


def apply_patches(extraction_db: Path, doi: str, patches: list[dict[str, Any]], apply: bool) -> tuple[int, list[dict[str, Any]]]:
    con = sqlite3.connect(extraction_db)
    con.row_factory = sqlite3.Row
    rows = {
        str(r["record_id"]): dict(r)
        for r in con.execute(
            "SELECT id, record_id, record_json FROM adsorption_records WHERE lower(doi)=lower(?)",
            (doi,),
        ).fetchall()
    }
    applied_total = 0
    reports: list[dict[str, Any]] = []
    with con:
        for patch in patches:
            status, qa_note, rec = patch_apply_status(rows, patch)
            rid = str(patch.get("record_id") or "").strip()
            row = rows.get(rid)
            if status == "eligible" and apply and row and rec is not None:
                target_path = ALLOWED_TARGET_PATHS[normalize_target_path(patch.get("target_path"))]
                section, field = target_path
                rec.setdefault(section, {})[field] = patch.get("value")
                con.execute(
                    "UPDATE adsorption_records SET record_json=? WHERE id=?",
                    (json.dumps(rec, ensure_ascii=False), row["id"]),
                )
                rows[rid]["record_json"] = json.dumps(rec, ensure_ascii=False)
                status = "applied"
                applied_total += 1
            elif status == "eligible":
                status = "eligible_not_applied"
            patch["matched_record_id"] = rid if row else ""
            patch["apply_status"] = status
            patch["qa_note"] = ";".join(part for part in [str(patch.get("qa_note") or ""), qa_note] if part)
            reports.append(patch)
    con.close()
    return applied_total, reports


def score_field_context(text: str, record_terms: list[str]) -> int:
    lower = text.lower()
    score = 0
    for term in FIELD_CONTEXT_TERMS:
        score += lower.count(term)
    for term in record_terms:
        clean = term.strip().lower()
        if len(clean) >= 3:
            score += 2 * lower.count(clean)
    return score


def compact_record_terms(records: list[dict[str, Any]], limit: int = 80) -> list[str]:
    terms: list[str] = []
    for rec in records[:limit]:
        for key in ("hydrogel_name", "protein_name", "experiment_mode"):
            value = rec.get(key)
            if value and isinstance(value, str):
                terms.append(value)
    seen: set[str] = set()
    uniq: list[str] = []
    for term in terms:
        normalized = re.sub(r"\s+", " ", term).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            uniq.append(normalized)
    return uniq[:limit]


def infer_article_type(row: dict[str, Any] | None = None, text: str = "") -> str:
    haystack = " ".join(
        str(x or "")
        for x in [
            text,
            row.get("article_title") if row else "",
            row.get("fully_missing_fields") if row else "",
        ]
    ).lower()
    if any(term in haystack for term in ["imprinted", "imprinting", "mip", "template molecule", "recognition"]):
        return "mip_imprinting"
    if any(term in haystack for term in ["enzyme", "immobilized", "immobilization", "biocatalyst", "trypsin", "lipase"]):
        return "enzyme_immobilization"
    if any(term in haystack for term in ["nanogel", "microgel", "microparticle", "nanoparticle", "particle size", "dls"]):
        return "micro_nanogel"
    if any(term in haystack for term in ["cryogel", "supermacroporous", "monolith", "column", "bed volume", "breakthrough"]):
        return "cryogel_column"
    if any(term in haystack for term in ["antifouling", "fouling", "non-specific", "nonspecific", "contact angle", "protein adsorption resistance", "biofouling"]):
        return "antifouling_surface"
    return "general_batch_adsorption"


def build_field_context(
    article: dict[str, Any],
    source_row: dict[str, Any],
    records: list[dict[str, Any]],
    max_chars: int,
    table_limit: int,
    section_limit: int,
    per_table_chars: int,
    per_section_chars: int,
) -> str:
    meta = article.get("metadata") or {}
    abstract = meta.get("abstract") or ""
    if isinstance(abstract, list):
        abstract = " ".join(str(x) for x in abstract)

    header = {
        "doi": meta.get("doi") or source_row.get("doi"),
        "title": meta.get("title") or source_row.get("title") or "",
        "publisher": meta.get("publisher") or article.get("publisher") or source_row.get("publisher"),
        "journal": meta.get("journal"),
        "publish_date": meta.get("publish_date") or source_row.get("publish_date"),
        "source_json": str(source_row.get("source_json") or source_row.get("json_path") or ""),
    }
    parts = ["[METADATA]\n" + json.dumps(header, ensure_ascii=False, indent=2)]
    if abstract:
        parts.append("[ABSTRACT]\n" + str(abstract)[:2500])

    record_terms = compact_record_terms(records)

    table_blocks: list[tuple[int, str]] = []
    for idx, tbl in enumerate(article.get("tables") or []):
        if not isinstance(tbl, dict):
            continue
        caption = str(tbl.get("title") or tbl.get("caption") or f"Table {idx + 1}")
        text = html_to_text(str(tbl.get("content") or ""), per_table_chars)
        footnote = html_to_text(str(tbl.get("footnote") or tbl.get("footnotes") or ""), 1200)
        block = f"Table index: {idx}\nCaption: {caption}\nContent: {text}"
        if footnote:
            block += f"\nFootnote: {footnote}"
        score = score_field_context(caption + " " + text + " " + footnote, record_terms)
        if FIELD_TITLE_RE.search(caption):
            score += 12
        table_blocks.append((score + 4, block))
    table_blocks.sort(key=lambda item: item[0], reverse=True)
    for score, block in table_blocks[:table_limit]:
        if score > 0:
            parts.append("[FIELD_RELEVANT_TABLE]\n" + block)

    section_blocks: list[tuple[int, str]] = []
    for title, text in flatten_full_text(article):
        clean = re.sub(r"\s+", " ", str(text)).strip()
        if not clean:
            continue
        score = score_field_context(title + " " + clean, record_terms)
        if FIELD_TITLE_RE.search(title):
            score += 10
        section_blocks.append((score, f"## {title}\n{clean[:per_section_chars]}"))
    section_blocks.sort(key=lambda item: item[0], reverse=True)
    for score, block in section_blocks[:section_limit]:
        if score > 0:
            parts.append("[FIELD_RELEVANT_TEXT]\n" + block)

    fig_lines: list[tuple[int, str]] = []
    for fig in article.get("figures") or []:
        if not isinstance(fig, dict):
            continue
        caption = str(fig.get("caption") or fig.get("title") or fig.get("description") or "")
        fid = str(fig.get("id") or fig.get("label") or "")
        if caption:
            fig_lines.append((score_field_context(caption, record_terms), f"{fid}: {caption}"))
    fig_lines.sort(key=lambda item: item[0], reverse=True)
    useful_figures = [line for score, line in fig_lines[:10] if score > 0]
    if useful_figures:
        parts.append("[FIELD_RELEVANT_FIGURES]\n" + "\n".join(useful_figures)[:2500])

    context = "\n\n".join(parts)
    if max_chars and max_chars > 0:
        return context[:max_chars]
    return context


def build_prompt(
    prompt_template: str,
    article: dict[str, Any],
    row: dict[str, Any],
    records: list[dict[str, Any]],
    context_chars: int,
    full_context: bool,
    context_mode: str,
    table_limit: int,
    section_limit: int,
    per_table_chars: int,
    per_section_chars: int,
    article_type_hint: str,
) -> str:
    if context_mode == "field" and not full_context:
        context = build_field_context(
            article,
            row,
            records,
            max_chars=context_chars,
            table_limit=table_limit,
            section_limit=section_limit,
            per_table_chars=per_table_chars,
            per_section_chars=per_section_chars,
        )
    else:
        context = build_context(article, row, max_chars=context_chars, full_context=full_context)
    record_block = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    return (
        prompt_template.rstrip()
        + "\n\n[EXISTING_RECORDS_WITH_MISSING_FOCUS]\n"
        + record_block
        + "\n\n[ARTICLE_TYPE_HINT]\n"
        + article_type_hint
        + "\n\n[ARTICLE_CONTEXT]\n"
        + context
        + "\n\nReturn JSON now."
    )


def run_codex(prompt: str, out_dir: Path, sid: str, model: str, reasoning_effort: str, timeout: int) -> dict[str, Any]:
    raw_dir = out_dir / "raw_outputs"
    json_dir = out_dir / "json_outputs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    last_message = raw_dir / f"{sid}.last_message.txt"
    stdout_path = raw_dir / f"{sid}.stdout.txt"
    stderr_path = raw_dir / f"{sid}.stderr.txt"
    cmd = [
        "codex", "--disable", "plugins", "--ask-for-approval", "never", "exec",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning_effort}"',
        "--sandbox", "read-only",
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-rules",
        "-o", str(last_message),
        "--color", "never",
        "-",
    ]
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT.parent),
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    stdout_path.write_text(result.stdout or "", encoding="utf-8")
    stderr_path.write_text(result.stderr or "", encoding="utf-8")
    if result.returncode != 0 and not last_message.exists():
        raise RuntimeError(f"codex failed with code {result.returncode}: {(result.stderr or result.stdout)[-1200:]}")
    raw_text = last_message.read_text(encoding="utf-8") if last_message.exists() else result.stdout
    payload = extract_json(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("field completion output was not a JSON object")
    (json_dir / f"{sid}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def apply_completion(extraction_db: Path, doi: str, payload: dict[str, Any], prompt_version: str = "legacy") -> tuple[int, list[dict[str, Any]]]:
    patches = payload_to_patches(doi, payload, prompt_version)
    return apply_patches(extraction_db, doi, patches, apply=True)


def save_result(
    con: sqlite3.Connection,
    doi: str,
    row: dict[str, Any],
    payload: dict[str, Any] | None,
    status: str,
    meta: dict[str, str],
    patches: list[dict[str, Any]],
    applied_count: int,
    article_level_rows: list[dict[str, Any]] | None = None,
    error: str | None = None,
) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    article_level_rows = article_level_rows or []
    with con:
        con.execute(
            """
            INSERT INTO field_completion_articles
            (doi, status, source_json, prompt_version, model, reasoning_effort, updates_count, applied_updates_count, output_json, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doi) DO UPDATE SET
              status=excluded.status,
              source_json=excluded.source_json,
              prompt_version=excluded.prompt_version,
              model=excluded.model,
              reasoning_effort=excluded.reasoning_effort,
              updates_count=excluded.updates_count,
              applied_updates_count=excluded.applied_updates_count,
              output_json=excluded.output_json,
              error_message=excluded.error_message,
              updated_at=excluded.updated_at
            """,
            (
                doi,
                status,
                row.get("source_json"),
                meta["prompt_version"],
                meta["model"],
                meta["reasoning_effort"],
                len(patches),
                applied_count,
                json.dumps(payload, ensure_ascii=False) if payload else None,
                error,
                now,
                now,
            ),
        )
        con.execute("DELETE FROM field_completion_updates WHERE doi=?", (doi,))
        con.execute("DELETE FROM field_completion_patches WHERE doi=?", (doi,))
        con.execute("DELETE FROM article_level_properties WHERE doi=?", (doi,))
        for patch in patches:
            con.execute(
                """
                INSERT INTO field_completion_updates
                (doi, record_id_hint, matched_record_id, update_json, applied_fields_json, evidence_text, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doi,
                    patch.get("record_id"),
                    patch.get("matched_record_id"),
                    json.dumps(patch, ensure_ascii=False),
                    json.dumps([patch.get("target_path")] if patch.get("apply_status") == "applied" else [], ensure_ascii=False),
                    patch.get("evidence_text"),
                    patch.get("confidence"),
                ),
            )
            con.execute(
                """
                INSERT INTO field_completion_patches
                (doi, record_id, matched_record_id, target_path, value_json, value_origin,
                 evidence_text, source_section, source_table_or_figure, confidence,
                 prompt_version, article_type, apply_status, qa_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doi,
                    patch.get("record_id"),
                    patch.get("matched_record_id"),
                    patch.get("target_path"),
                    patch.get("value_json"),
                    patch.get("value_origin"),
                    patch.get("evidence_text"),
                    patch.get("source_section"),
                    patch.get("source_table_or_figure"),
                    patch.get("confidence"),
                    patch.get("prompt_version"),
                    patch.get("article_type"),
                    patch.get("apply_status"),
                    patch.get("qa_note"),
                    now,
                ),
            )
        for item in article_level_rows:
            con.execute(
                """
                INSERT INTO article_level_properties
                (doi, field_name, value_json, value_origin, evidence_text, source_section,
                 source_table_or_figure, confidence, prompt_version, article_type, qa_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doi,
                    item.get("field_name"),
                    item.get("value_json"),
                    item.get("value_origin"),
                    item.get("evidence_text"),
                    item.get("source_section"),
                    item.get("source_table_or_figure"),
                    item.get("confidence"),
                    item.get("prompt_version"),
                    item.get("article_type"),
                    item.get("qa_note"),
                    now,
                ),
            )


def load_candidates(
    path: Path,
    limit: int,
    min_model_ready: int,
    only_dois: set[str],
    sample_mode: str,
    pilot_per_type: int,
) -> list[dict[str, Any]]:
    df = pd.read_csv(path)
    if min_model_ready:
        df = df[df["model_ready_count"] >= min_model_ready]
    if only_dois:
        df = df[df["doi"].str.lower().isin(only_dois)]
    df = df.sort_values(["priority_score", "model_ready_count", "records_count"], ascending=False)
    if limit == 0:
        return []
    if sample_mode == "targeted-pilot" and not only_dois:
        rows = df.to_dict("records")
        chosen: list[dict[str, Any]] = []
        seen: set[str] = set()
        for article_type in TARGETED_ARTICLE_TYPES:
            group = [row for row in rows if infer_article_type(row) == article_type]
            for row in group[:pilot_per_type]:
                doi = str(row.get("doi") or "").lower()
                if doi and doi not in seen:
                    row["article_type_hint"] = article_type
                    chosen.append(row)
                    seen.add(doi)
        if limit and len(chosen) < limit:
            for row in rows:
                doi = str(row.get("doi") or "").lower()
                if doi and doi not in seen:
                    row["article_type_hint"] = infer_article_type(row)
                    chosen.append(row)
                    seen.add(doi)
                if len(chosen) >= limit:
                    break
        return chosen[:limit]
    df = df.head(limit)
    rows = df.to_dict("records")
    for row in rows:
        row["article_type_hint"] = infer_article_type(row)
    return rows


def completed_dois_from_results(paths: list[Path]) -> set[str]:
    completed: set[str] = set()
    for path in paths:
        if path.is_dir():
            path = path / "field_completion_results.db"
        if not path.exists():
            continue
        try:
            con = sqlite3.connect(path)
            rows = con.execute("SELECT doi FROM field_completion_articles WHERE status='success'").fetchall()
            completed.update(str(row[0]).lower() for row in rows if row and row[0])
            con.close()
        except sqlite3.Error:
            continue
    return completed


def load_success_payloads(paths: list[Path]) -> list[tuple[str, dict[str, Any]]]:
    payloads: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        if path.is_dir():
            path = path / "field_completion_results.db"
        if not path.exists():
            continue
        con = sqlite3.connect(path)
        rows = con.execute(
            "SELECT doi, output_json FROM field_completion_articles WHERE status='success' AND output_json IS NOT NULL"
        ).fetchall()
        con.close()
        for doi, output_json in rows:
            try:
                payload = json.loads(output_json)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                payloads.append((str(doi), payload))
    return payloads


def coverage_snapshot(extraction_db: Path, fields: list[str]) -> dict[str, dict[str, Any]]:
    con = sqlite3.connect(extraction_db)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT record_json FROM adsorption_records").fetchall()]
    con.close()
    total = len(rows)
    parsed = [json.loads(row.get("record_json") or "{}") for row in rows]
    out: dict[str, dict[str, Any]] = {}
    for field in fields:
        path = tuple(field.split(".", 1))
        if len(path) != 2:
            continue
        present = sum(1 for rec in parsed if has_value(get_nested(rec, path)))  # type: ignore[arg-type]
        out[field] = {
            "present": present,
            "total": total,
            "coverage_pct": round(present / max(total, 1) * 100, 2),
        }
    return out


def coverage_before_after_rows(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in sorted(set(before) | set(after)):
        b = before.get(field, {"present": 0, "total": 0, "coverage_pct": 0})
        a = after.get(field, {"present": 0, "total": b.get("total", 0), "coverage_pct": 0})
        rows.append(
            {
                "field": field,
                "before_present": b.get("present"),
                "after_present": a.get("present"),
                "delta_present": int(a.get("present") or 0) - int(b.get("present") or 0),
                "total": a.get("total") or b.get("total"),
                "before_coverage_pct": b.get("coverage_pct"),
                "after_coverage_pct": a.get("coverage_pct"),
                "delta_coverage_pct": round(float(a.get("coverage_pct") or 0) - float(b.get("coverage_pct") or 0), 2),
            }
        )
    return rows


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if rows:
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    else:
        pd.DataFrame(columns=fieldnames or []).to_csv(path, index=False, encoding="utf-8")


def write_completion_exports(
    result_db: sqlite3.Connection,
    output_dir: Path,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    meta: dict[str, str],
    failures: int,
) -> None:
    articles = pd.read_sql_query("SELECT * FROM field_completion_articles ORDER BY updated_at DESC", result_db)
    updates = pd.read_sql_query("SELECT * FROM field_completion_updates ORDER BY doi, id", result_db)
    patches = pd.read_sql_query("SELECT * FROM field_completion_patches ORDER BY doi, id", result_db)
    article_props = pd.read_sql_query("SELECT * FROM article_level_properties ORDER BY doi, id", result_db)
    articles.to_csv(output_dir / "field_completion_articles.csv", index=False, encoding="utf-8")
    updates.to_csv(output_dir / "field_completion_updates.csv", index=False, encoding="utf-8")
    patches.to_csv(output_dir / "completion_patches.csv", index=False, encoding="utf-8")
    article_props.to_csv(output_dir / "article_level_properties.csv", index=False, encoding="utf-8")
    write_rows(output_dir / "completion_coverage_before_after.csv", coverage_before_after_rows(before, after))

    audit_rows: list[dict[str, Any]] = []
    if not patches.empty:
        for (target_path, apply_status), group in patches.groupby(["target_path", "apply_status"], dropna=False):
            audit_rows.append(
                {
                    "target_path": target_path,
                    "apply_status": apply_status,
                    "patches": int(len(group)),
                    "unique_dois": int(group["doi"].nunique()),
                    "unique_records": int(group["record_id"].nunique()),
                }
            )
    write_rows(
        output_dir / "completion_patch_audit.csv",
        audit_rows,
        ["target_path", "apply_status", "patches", "unique_dois", "unique_records"],
    )

    status_counts = Counter(str(x) for x in patches["apply_status"]) if not patches.empty else Counter()
    lines = [
        "# PHA field completion run report",
        "",
        f"- Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Prompt version: {meta.get('prompt_version')}",
        f"- Model: {meta.get('model')}",
        f"- Reasoning effort: {meta.get('reasoning_effort')}",
        f"- Articles tracked: {len(articles)}",
        f"- Patches: {len(patches)}",
        f"- Article-level properties: {len(article_props)}",
        f"- Failures: {failures}",
        "",
        "## Patch status",
        "",
    ]
    if status_counts:
        for key, value in sorted(status_counts.items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- no patches generated")
    lines.extend(["", "## Largest coverage deltas", ""])
    coverage_rows = coverage_before_after_rows(before, after)
    coverage_rows.sort(key=lambda row: row["delta_present"], reverse=True)
    for row in coverage_rows[:20]:
        if row["delta_present"]:
            lines.append(
                f"- {row['field']}: +{row['delta_present']} rows "
                f"({row['before_coverage_pct']}% -> {row['after_coverage_pct']}%)"
            )
    if not any(row["delta_present"] for row in coverage_rows):
        lines.append("- no fields changed in the extraction DB during this run")
    (output_dir / "completion_run_report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run second-pass PHA field completion for preparation/property gaps.")
    parser.add_argument("--extraction-db", type=Path, default=DEFAULT_EXTRACTION_DB)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="xhigh")
    parser.add_argument("--timeout", type=int, default=2400)
    parser.add_argument("--context-chars", type=int, default=12000)
    parser.add_argument("--context-mode", choices=["field", "extraction"], default="field")
    parser.add_argument("--table-limit", type=int, default=8)
    parser.add_argument("--section-limit", type=int, default=6)
    parser.add_argument("--per-table-chars", type=int, default=3000)
    parser.add_argument("--per-section-chars", type=int, default=1800)
    parser.add_argument("--full-context", action="store_true")
    parser.add_argument("--min-model-ready", type=int, default=1)
    parser.add_argument("--sample-mode", choices=["priority", "targeted-pilot"], default="priority")
    parser.add_argument("--pilot-per-type", type=int, default=5)
    parser.add_argument("--only-doi", action="append", default=[])
    parser.add_argument("--skip-completed-db", type=Path, action="append", default=[])
    parser.add_argument("--reapply-results-db", type=Path, action="append", default=[], help="Apply successful stored completion payloads without invoking Codex.")
    parser.add_argument("--apply", action="store_true", help="Apply non-conflicting missing-field updates into adsorption_records.record_json.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tracked_fields = sorted(ALLOWED_TARGET_PATHS)
    before_coverage = coverage_snapshot(args.extraction_db, tracked_fields)
    prompt_version = (
        "field_completion_v4_targeted_patch"
        if "v4" in args.prompt.stem
        else ("field_completion_v2_compact_patch" if "v2" in args.prompt.stem else "field_completion_v1")
    )
    meta = {
        "prompt_version": prompt_version,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
    }
    if args.reapply_results_db:
        result_db = ensure_db(args.output_dir / "field_completion_results.db")
        rows: list[dict[str, Any]] = []
        total_fields = 0
        for doi, payload in load_success_payloads(args.reapply_results_db):
            patches = payload_to_patches(doi, payload, prompt_version)
            applied_count, patch_reports = apply_patches(args.extraction_db, doi, patches, apply=args.apply)
            article_rows = payload_to_article_level_rows(doi, payload, prompt_version)
            save_result(result_db, doi, {"source_json": None}, payload, "success", meta, patch_reports, applied_count, article_rows)
            total_fields += applied_count
            rows.append(
                {
                    "doi": doi,
                    "patches_count": len(patch_reports),
                    "applied_fields": applied_count,
                    "matched_patches": sum(1 for report in patch_reports if report.get("matched_record_id")),
                }
            )
            print(f"reapplied {doi}: patches={rows[-1]['patches_count']}, applied_fields={applied_count}")
        pd.DataFrame(rows).to_csv(args.output_dir / "field_completion_reapply_report.csv", index=False, encoding="utf-8")
        after_coverage = coverage_snapshot(args.extraction_db, tracked_fields)
        write_completion_exports(result_db, args.output_dir, before_coverage, after_coverage, meta, failures=0)
        print(f"Reapply done. dois={len(rows)}; applied_fields={total_fields}; report={args.output_dir / 'field_completion_reapply_report.csv'}")
        return 0

    prompt_template = args.prompt.read_text(encoding="utf-8")
    candidates = load_candidates(
        args.candidates,
        args.limit,
        args.min_model_ready,
        {d.lower() for d in args.only_doi},
        args.sample_mode,
        args.pilot_per_type,
    )
    skip_completed = completed_dois_from_results(args.skip_completed_db)
    if skip_completed:
        before_count = len(candidates)
        candidates = [cand for cand in candidates if str(cand["doi"]).lower() not in skip_completed]
        print(f"Skipped {before_count - len(candidates)} completed field-completion candidates from prior result DBs.")
    articles = extraction_article_rows(args.extraction_db)
    result_db = ensure_db(args.output_dir / "field_completion_results.db")

    tasks: list[dict[str, Any]] = []
    for cand in candidates:
        doi = str(cand["doi"])
        existing = None if args.force else result_db.execute("SELECT status FROM field_completion_articles WHERE doi=?", (doi,)).fetchone()
        if existing and existing[0] == "success":
            print(f"skip {doi} ({existing[0]})")
            continue
        article_row = articles.get(doi.lower())
        if not article_row or not article_row.get("source_json") or not Path(str(article_row["source_json"])).exists():
            save_result(result_db, doi, {"source_json": None}, None, "missing_source", meta, [], 0, "source_json missing")
            continue
        summaries, _ = record_summary(args.extraction_db, doi)
        article = load_json(Path(str(article_row["source_json"])))
        prompt = build_prompt(
            prompt_template,
            article,
            article_row,
            summaries,
            args.context_chars,
            args.full_context,
            args.context_mode,
            args.table_limit,
            args.section_limit,
            args.per_table_chars,
            args.per_section_chars,
            str(cand.get("article_type_hint") or infer_article_type(cand)),
        )
        tasks.append({"doi": doi, "row": article_row, "prompt": prompt, "sid": safe_id(doi)})

    print(f"Prepared {len(tasks)} field completion tasks.")

    def run_one(task: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, Exception | None]:
        try:
            payload = run_codex(task["prompt"], args.output_dir, task["sid"], args.model, args.reasoning_effort, args.timeout)
            return task, payload, None
        except Exception as exc:
            return task, None, exc

    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_one, task) for task in tasks]
        for future in as_completed(futures):
            task, payload, exc = future.result()
            doi = task["doi"]
            if exc or payload is None:
                failures += 1
                save_result(result_db, doi, task["row"], None, "failed", meta, [], 0, [], str(exc))
                print(f"failed {doi}: {exc}")
                continue
            patches = payload_to_patches(doi, payload, prompt_version)
            applied_count, patch_reports = apply_patches(args.extraction_db, doi, patches, apply=args.apply)
            article_rows = payload_to_article_level_rows(doi, payload, prompt_version)
            save_result(result_db, doi, task["row"], payload, "success", meta, patch_reports, applied_count, article_rows)
            print(f"success {doi}: patches={len(patch_reports)}, applied_fields={applied_count}")

    after_coverage = coverage_snapshot(args.extraction_db, tracked_fields)
    write_completion_exports(result_db, args.output_dir, before_coverage, after_coverage, meta, failures)
    print(f"Field completion done. failures={failures}; db={args.output_dir / 'field_completion_results.db'}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
