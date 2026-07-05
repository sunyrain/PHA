from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "databases" / "PHA-2026_articles.db"
DEFAULT_ARTICLE_DIR = ROOT / "data" / "article_data"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "pha_extraction"
DEFAULT_PROMPT = ROOT / "extraction" / "prompts" / "pha_codex_extraction_prompt_v3.md"
DEFAULT_SCHEMA = ROOT / "extraction" / "schemas" / "pha_codex_article_output.schema.json"

RELEVANCE_TERMS = [
    "adsorp", "sorption", "binding", "bind", "capture", "uptake", "removal",
    "fouling", "antifouling", "anti-fouling", "protein corona", "vroman",
    "separation", "purification", "imprint", "affinity", "selectiv",
    "albumin", "bsa", "hsa", "lysozyme", "fibrinogen", "hemoglobin", "igg",
    "immunoglobulin", "antibody", "enzyme", "serum", "plasma", "protein",
    "hydrogel", "nanogel", "microgel", "cryogel", "qmax", "isotherm",
    "kinetic", "capacity", "zeta", "swelling", "pore", "mesh"
]

ENTITY_SKIP_RE = re.compile(
    r"\b(hydrogel|gel|sample|buffer|solution|water|protein|serum|plasma)\b",
    re.I,
)
PUBCHEM_BULK_MATERIAL_RE = re.compile(
    r"\b(polymer|copolymer|hydrogel|nanogel|microgel|cryogel|membrane|bead|"
    r"resin|composite|network|monolith|scaffold|film|matrix|imprinted)\b",
    re.I,
)
UNIPROT_NOISE_RE = re.compile(
    r"\b(buffer|hydrogel|polymer|nanogel|microgel|membrane|bead|resin|matrix)\b",
    re.I,
)


def safe_id(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[<>:"/\\|?*\s]+', "_", text)
    return text[:180].strip("_") or "unknown"


def doi_hash(doi: str) -> str:
    return hashlib.sha1(doi.lower().encode("utf-8")).hexdigest()[:10]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def article_json_path(article_root: Path, article_path: str | None) -> Path | None:
    if not article_path:
        return None
    folder = article_root / article_path
    if not folder.exists():
        return None
    candidates = [
        p for p in folder.glob("*.json")
        if not p.name.endswith(".elsevier_api.json")
        and "debug" not in p.name.lower()
    ]
    if not candidates:
        candidates = list(folder.glob("*.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)


def html_to_text(html: str, max_chars: int = 8000) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" | ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:max_chars]


def flatten_full_text(article: dict[str, Any]) -> list[tuple[str, str]]:
    body = article.get("full_text") or article.get("body") or ""
    sections: list[tuple[str, str]] = []
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict):
                title = str(item.get("title") or "Section")
                text = str(item.get("text") or "")
                if text.strip():
                    sections.append((title, text))
                for sub in item.get("subsections") or []:
                    if isinstance(sub, dict):
                        st = str(sub.get("title") or f"{title} subsection")
                        sx = str(sub.get("text") or "")
                        if sx.strip():
                            sections.append((st, sx))
                    elif str(sub).strip():
                        sections.append((title, str(sub)))
            elif str(item).strip():
                sections.append(("Section", str(item)))
    elif isinstance(body, str) and body.strip():
        sections.append(("Article body", body))
    return sections


def score_text(text: str) -> int:
    lower = text.lower()
    return sum(lower.count(term) for term in RELEVANCE_TERMS)


def build_context(article: dict[str, Any], source_row: dict[str, Any], max_chars: int = 14000, full_context: bool = False) -> str:
    meta = article.get("metadata") or {}
    title = meta.get("title") or source_row.get("title") or ""
    abstract = meta.get("abstract") or ""
    if isinstance(abstract, list):
        abstract = " ".join(str(x) for x in abstract)

    header = {
        "doi": meta.get("doi") or source_row.get("doi"),
        "title": title,
        "publisher": meta.get("publisher") or article.get("publisher") or source_row.get("publisher"),
        "journal": meta.get("journal"),
        "publish_date": meta.get("publish_date") or source_row.get("publish_date"),
        "keywords": meta.get("keywords"),
        "source_json": str(source_row.get("json_path") or ""),
    }
    parts = ["[METADATA]\n" + json.dumps(header, ensure_ascii=False, indent=2)]
    if abstract:
        parts.append("[ABSTRACT]\n" + str(abstract)[:5000])

    tables = article.get("tables") or []
    table_blocks: list[tuple[int, str]] = []
    for idx, tbl in enumerate(tables):
        caption = tbl.get("title") or tbl.get("caption") or f"Table {idx + 1}"
        text = html_to_text(str(tbl.get("content") or ""), 50000 if full_context else 5000)
        footnote = html_to_text(str(tbl.get("footnote") or tbl.get("footnotes") or ""), 10000 if full_context else 2000)
        block = f"Table index: {idx}\nCaption: {caption}\nContent: {text}"
        if footnote:
            block += f"\nFootnote: {footnote}"
        table_blocks.append((score_text(block) + 5, block))
    table_blocks.sort(key=lambda x: x[0], reverse=True)
    for _, block in (table_blocks if full_context else table_blocks[:5]):
        parts.append("[TABLE]\n" + block)

    sections = flatten_full_text(article)
    scored_sections: list[tuple[int, str]] = []
    for title_s, text in sections:
        clean = re.sub(r"\s+", " ", str(text)).strip()
        if not clean:
            continue
        score = score_text(title_s + " " + clean)
        title_score = 8 if re.search(r"result|discussion|adsorp|binding|protein|method|experiment", title_s, re.I) else 0
        section_text = clean if full_context else clean[:3500]
        scored_sections.append((score + title_score, f"## {title_s}\n{section_text}"))
    scored_sections.sort(key=lambda x: x[0], reverse=True)
    for score, block in (scored_sections if full_context else scored_sections[:4]):
        if not full_context and score <= 0 and len(parts) > 3:
            continue
        parts.append("[TEXT_SECTION]\n" + block)

    figures = article.get("figures") or []
    fig_lines = []
    for fig in (figures if full_context else figures[:20]):
        if isinstance(fig, dict):
            caption = fig.get("caption") or fig.get("title") or ""
            fid = fig.get("id") or fig.get("label") or ""
            if caption:
                fig_lines.append(f"{fid}: {caption}")
    if fig_lines:
        fig_text = "\n".join(fig_lines)
        parts.append("[FIGURE_CAPTIONS]\n" + (fig_text if full_context else fig_text[:6000]))

    context = "\n\n".join(parts)
    if max_chars and max_chars > 0:
        return context[:max_chars]
    return context


def fetch_rows(db_path: Path, article_root: Path, limit: int) -> list[dict[str, Any]]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT id, doi, publisher, title, publish_date, article_path
        FROM articles
        WHERE success = 1 AND article_path IS NOT NULL
        ORDER BY id
        """
    ).fetchall()
    con.close()

    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        jpath = article_json_path(article_root, item.get("article_path"))
        if not jpath:
            continue
        item["json_path"] = str(jpath)
        text = " ".join(str(item.get(k) or "") for k in ("title", "doi", "publisher"))
        try:
            data = load_json(jpath)
            meta = data.get("metadata") or {}
            text += " " + str(meta.get("abstract") or "")[:3000]
            text += " " + " ".join(str((t.get("title") or t.get("caption") or "")) for t in (data.get("tables") or [])[:6] if isinstance(t, dict))
        except Exception:
            pass
        item["score"] = score_text(text)
        enriched.append(item)

    enriched.sort(key=lambda x: (x["score"], x["id"]), reverse=True)
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in enriched:
        buckets.setdefault(item.get("publisher") or "UNKNOWN", []).append(item)

    selected: list[dict[str, Any]] = []
    while len(selected) < limit and buckets:
        for pub in sorted(list(buckets), key=lambda p: len(buckets[p]), reverse=True):
            if buckets.get(pub):
                selected.append(buckets[pub].pop(0))
                if len(selected) >= limit:
                    break
            if not buckets.get(pub):
                buckets.pop(pub, None)
    return selected[:limit]


def extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def minimal_validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in [
        "schema_version", "prompt_version", "article", "article_common_fields",
        "records", "material_mentions", "protein_mentions", "special_fields",
        "extraction_note",
    ]:
        if key not in payload:
            errors.append(f"missing top-level key: {key}")
    if not isinstance(payload.get("records", []), list):
        errors.append("records is not a list")
    for i, rec in enumerate(payload.get("records") or []):
        if not isinstance(rec, dict):
            errors.append(f"record {i} is not an object")
            continue
        for key in ["provenance", "triage", "hydrogel", "protein", "experiment", "outcome", "mechanism", "quality"]:
            if key not in rec:
                errors.append(f"record {i} missing {key}")
    return errors


def ensure_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS article_extractions (
            doi TEXT PRIMARY KEY,
            title TEXT,
            publisher TEXT,
            source_json TEXT,
            status TEXT,
            prompt_version TEXT,
            model TEXT,
            reasoning_effort TEXT,
            records_count INTEGER DEFAULT 0,
            material_mentions_count INTEGER DEFAULT 0,
            protein_mentions_count INTEGER DEFAULT 0,
            special_fields_count INTEGER DEFAULT 0,
            output_json TEXT,
            validation_errors TEXT,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS adsorption_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            record_id TEXT,
            title TEXT,
            hydrogel_name TEXT,
            hydrogel_format TEXT,
            polymer_backbone TEXT,
            functional_groups TEXT,
            protein_name TEXT,
            protein_abbreviation TEXT,
            experiment_mode TEXT,
            pH TEXT,
            outcome_label TEXT,
            raw_metric_name TEXT,
            raw_metric_value TEXT,
            raw_metric_unit TEXT,
            q_norm_mg_g REAL,
            surface_adsorption_ug_cm2 REAL,
            evidence_text TEXT,
            extraction_confidence REAL,
            source_quality_score INTEGER,
            needs_manual_review INTEGER,
            record_json TEXT,
            UNIQUE(doi, record_id)
        );
        CREATE TABLE IF NOT EXISTS material_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            name TEXT,
            role TEXT,
            context TEXT,
            pubchem_query TEXT,
            needs_manual_normalization INTEGER,
            enrichment_json TEXT,
            UNIQUE(doi, name, role, context)
        );
        CREATE TABLE IF NOT EXISTS protein_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            name TEXT,
            abbreviation TEXT,
            species_or_source TEXT,
            role TEXT,
            context TEXT,
            uniprot_query TEXT,
            reported_mw_kDa REAL,
            reported_pI REAL,
            enrichment_json TEXT,
            UNIQUE(doi, name, role, context)
        );
        CREATE TABLE IF NOT EXISTS special_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT,
            field_name TEXT,
            field_value_json TEXT,
            why_special TEXT,
            evidence_text TEXT,
            suggested_table TEXT
        );
        """
    )
    return con


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def db_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return as_json(value)
    return str(value)


def db_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value)
        return float(match.group(0)) if match else None
    return None


def flatten_value(obj: Any, *path: str) -> Any:
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def upsert_payload(con: sqlite3.Connection, row: dict[str, Any], payload: dict[str, Any], status: str, meta: dict[str, str], errors: list[str] | None = None, error_message: str | None = None) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    doi = row["doi"]
    article = payload.get("article") or {}
    records = payload.get("records") or []
    materials = payload.get("material_mentions") or []
    proteins = payload.get("protein_mentions") or []
    special = payload.get("special_fields") or []
    con.execute(
        """
        INSERT INTO article_extractions
        (doi, title, publisher, source_json, status, prompt_version, model, reasoning_effort,
         records_count, material_mentions_count, protein_mentions_count, special_fields_count,
         output_json, validation_errors, error_message, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doi) DO UPDATE SET
          title=excluded.title,
          publisher=excluded.publisher,
          source_json=excluded.source_json,
          status=excluded.status,
          prompt_version=excluded.prompt_version,
          model=excluded.model,
          reasoning_effort=excluded.reasoning_effort,
          records_count=excluded.records_count,
          material_mentions_count=excluded.material_mentions_count,
          protein_mentions_count=excluded.protein_mentions_count,
          special_fields_count=excluded.special_fields_count,
          output_json=excluded.output_json,
          validation_errors=excluded.validation_errors,
          error_message=excluded.error_message,
          updated_at=excluded.updated_at
        """,
        (
            doi, article.get("title") or row.get("title"), row.get("publisher"),
            row.get("json_path"), status, payload.get("prompt_version") or meta["prompt_version"],
            meta["model"], meta["reasoning_effort"], len(records), len(materials), len(proteins),
            len(special), as_json(payload), as_json(errors or []), error_message, now, now,
        ),
    )
    con.execute("DELETE FROM adsorption_records WHERE doi = ?", (doi,))
    con.execute("DELETE FROM material_mentions WHERE doi = ?", (doi,))
    con.execute("DELETE FROM protein_mentions WHERE doi = ?", (doi,))
    con.execute("DELETE FROM special_fields WHERE doi = ?", (doi,))

    for idx, rec in enumerate(records):
        raw_rec_id = str(rec.get("record_id") or "").strip()
        if raw_rec_id.startswith(f"PHA-{doi_hash(doi)}-"):
            rec_id = raw_rec_id
        elif raw_rec_id and not raw_rec_id.upper().startswith("PHA-"):
            rec_id = f"PHA-{doi_hash(doi)}-{safe_id(raw_rec_id)[:40]}"
        else:
            rec_id = f"PHA-{doi_hash(doi)}-{idx + 1:03d}"
        rec["record_id"] = rec_id
        hydrogel = rec.get("hydrogel") or {}
        protein = rec.get("protein") or {}
        experiment = rec.get("experiment") or {}
        outcome = rec.get("outcome") or {}
        provenance = rec.get("provenance") or {}
        quality = rec.get("quality") or {}
        con.execute(
            """
            INSERT OR REPLACE INTO adsorption_records
            (doi, record_id, title, hydrogel_name, hydrogel_format, polymer_backbone,
             functional_groups, protein_name, protein_abbreviation, experiment_mode, pH,
             outcome_label, raw_metric_name, raw_metric_value, raw_metric_unit, q_norm_mg_g,
             surface_adsorption_ug_cm2, evidence_text, extraction_confidence,
             source_quality_score, needs_manual_review, record_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doi, rec_id, db_text(provenance.get("title") or row.get("title")),
                db_text(hydrogel.get("hydrogel_name")), db_text(hydrogel.get("hydrogel_format")),
                as_json(hydrogel.get("polymer_backbone") or []),
                as_json(hydrogel.get("functional_groups") or []),
                db_text(protein.get("protein_name")), db_text(protein.get("protein_abbreviation")),
                db_text(experiment.get("experiment_mode")), db_text(experiment.get("pH")),
                db_text(outcome.get("outcome_label")), db_text(outcome.get("raw_metric_name")),
                db_text(outcome.get("raw_metric_value")), db_text(outcome.get("raw_metric_unit")),
                db_float(outcome.get("q_norm_mg_g")), db_float(outcome.get("surface_adsorption_ug_cm2")),
                db_text(provenance.get("evidence_text")), db_float(provenance.get("extraction_confidence")),
                db_float(quality.get("source_quality_score")),
                1 if quality.get("needs_manual_review") else 0, as_json(rec),
            ),
        )

    for mat in materials:
        name = str(mat.get("name") or "").strip()
        if not name:
            continue
        con.execute(
            """
            INSERT OR IGNORE INTO material_mentions
            (doi, name, role, context, pubchem_query, needs_manual_normalization, enrichment_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doi, name, db_text(mat.get("role")), db_text(mat.get("context")), db_text(mat.get("pubchem_query")),
                1 if mat.get("needs_manual_normalization") else 0, None,
            ),
        )

    for prot in proteins:
        name = str(prot.get("name") or "").strip()
        if not name:
            continue
        con.execute(
            """
            INSERT OR IGNORE INTO protein_mentions
            (doi, name, abbreviation, species_or_source, role, context, uniprot_query,
             reported_mw_kDa, reported_pI, enrichment_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doi, name, db_text(prot.get("abbreviation")), db_text(prot.get("species_or_source")),
                db_text(prot.get("role")), db_text(prot.get("context")), db_text(prot.get("uniprot_query")),
                db_float(prot.get("reported_mw_kDa")), db_float(prot.get("reported_pI")), None,
            ),
        )

    for sp in special:
        con.execute(
            """
            INSERT INTO special_fields
            (doi, field_name, field_value_json, why_special, evidence_text, suggested_table)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                doi, db_text(sp.get("field_name")), as_json(sp.get("field_value")),
                db_text(sp.get("why_special")), db_text(sp.get("evidence_text")), db_text(sp.get("suggested_table")),
            ),
        )
    con.commit()


def codex_extract(row: dict[str, Any], prompt_template: str, schema: Path, out_dir: Path, model: str, reasoning_effort: str, timeout: int, force: bool, use_output_schema: bool, context_chars: int, full_context: bool) -> tuple[dict[str, Any], list[str]]:
    doi = row["doi"]
    sid = safe_id(doi)
    raw_dir = out_dir / "raw_outputs"
    context_dir = out_dir / "input_contexts"
    json_dir = out_dir / "json_outputs"
    last_message = raw_dir / f"{sid}.last_message.txt"
    stdout_path = raw_dir / f"{sid}.stdout.txt"
    stderr_path = raw_dir / f"{sid}.stderr.txt"
    json_path = json_dir / f"{sid}.json"

    if json_path.exists() and not force:
        payload = load_json(json_path)
        return payload, minimal_validate(payload)

    article = load_json(Path(row["json_path"]))
    context = build_context(article, row, max_chars=context_chars, full_context=full_context)
    context_path = context_dir / f"{sid}.md"
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(context, encoding="utf-8")

    prompt = (
        prompt_template.rstrip()
        + "\n\n[ARTICLE_CONTEXT]\n"
        + context
        + "\n\nReturn JSON now."
    )
    raw_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

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
    if use_output_schema:
        insert_at = cmd.index("-o")
        cmd[insert_at:insert_at] = ["--output-schema", str(schema)]
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
        raise RuntimeError(f"codex failed with code {result.returncode}: {(result.stderr or result.stdout)[-1000:]}")

    raw_text = last_message.read_text(encoding="utf-8") if last_message.exists() else result.stdout
    payload = extract_json(raw_text)
    if isinstance(payload, list):
        payload = {
            "schema_version": "0.2.0",
            "prompt_version": "unknown",
            "article": {"title": row.get("title") or "", "triage_label": "maybe", "triage_reason": "model returned a list", "study_types": []},
            "article_common_fields": {},
            "records": payload,
            "material_mentions": [],
            "protein_mentions": [],
            "special_fields": [],
            "extraction_note": "Wrapped list output into article object.",
        }
    if not isinstance(payload, dict):
        raise ValueError("Codex output was not a JSON object")
    errors = minimal_validate(payload)
    write_json(json_path, payload)
    return payload, errors


def pubchem_lookup(name: str) -> dict[str, Any] | None:
    if not name or ENTITY_SKIP_RE.search(name) or len(name) > 80:
        return None
    if PUBCHEM_BULK_MATERIAL_RE.search(name) and len(name) > 24:
        return None
    if len(re.findall(r"[A-Za-z][A-Za-z-]+", name)) > 8:
        return None
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        + quote(name)
        + "/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChIKey,IUPACName/JSON"
    )
    r = requests.get(url, timeout=(3, 8))
    if r.status_code != 200:
        return None
    data = r.json()
    props = (data.get("PropertyTable") or {}).get("Properties") or []
    return props[0] if props else None


def uniprot_lookup(query: str) -> dict[str, Any] | None:
    if not query or len(query) > 120 or UNIPROT_NOISE_RE.search(query):
        return None
    params = {
        "query": query,
        "fields": "accession,id,protein_name,organism_name,length,mass,sequence",
        "format": "json",
        "size": "3",
    }
    r = requests.get("https://rest.uniprot.org/uniprotkb/search", params=params, timeout=(3, 8))
    if r.status_code != 200:
        return None
    data = r.json()
    results = data.get("results") or []
    if not results:
        return None
    first = results[0]
    return {
        "accession": first.get("primaryAccession"),
        "uniProtkbId": first.get("uniProtkbId"),
        "proteinDescription": first.get("proteinDescription"),
        "organism": first.get("organism"),
        "sequence": first.get("sequence"),
        "result_count": len(results),
    }


def enrich_entities(con: sqlite3.Connection, cache_path: Path) -> None:
    cache = load_json(cache_path) if cache_path.exists() else {"pubchem": {}, "uniprot": {}}

    materials = con.execute(
        "SELECT id, name, COALESCE(pubchem_query, name) AS q FROM material_mentions WHERE enrichment_json IS NULL"
    ).fetchall()
    for mid, name, query in materials:
        key = query or name
        if key not in cache["pubchem"]:
            try:
                cache["pubchem"][key] = pubchem_lookup(key)
                time.sleep(0.2)
            except Exception as exc:
                cache["pubchem"][key] = {"error": str(exc)}
        con.execute("UPDATE material_mentions SET enrichment_json = ? WHERE id = ?", (as_json(cache["pubchem"][key]), mid))
        con.commit()
        write_json(cache_path, cache)

    proteins = con.execute(
        "SELECT id, name, abbreviation, species_or_source, uniprot_query FROM protein_mentions WHERE enrichment_json IS NULL"
    ).fetchall()
    for pid, name, abbr, species, query in proteins:
        q = query or " ".join(x for x in [name, species] if x)
        if q not in cache["uniprot"]:
            try:
                cache["uniprot"][q] = uniprot_lookup(q)
                time.sleep(0.2)
            except Exception as exc:
                cache["uniprot"][q] = {"error": str(exc)}
        con.execute("UPDATE protein_mentions SET enrichment_json = ? WHERE id = ?", (as_json(cache["uniprot"][q]), pid))
        con.commit()
        write_json(cache_path, cache)


def export_excel(con: sqlite3.Connection, output_xlsx: Path) -> None:
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    queries = {
        "articles": "SELECT * FROM article_extractions ORDER BY updated_at DESC",
        "records": "SELECT * FROM adsorption_records ORDER BY doi, id",
        "materials": "SELECT * FROM material_mentions ORDER BY doi, name",
        "proteins": "SELECT * FROM protein_mentions ORDER BY doi, name",
        "special_fields": "SELECT * FROM special_fields ORDER BY doi, id",
    }
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        for sheet, sql in queries.items():
            pd.read_sql_query(sql, con).to_excel(writer, sheet_name=sheet, index=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Codex medium extraction for PHA articles.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--article-dir", type=Path, default=DEFAULT_ARTICLE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--skip-enrich", action="store_true")
    parser.add_argument("--enrich-only", action="store_true")
    parser.add_argument("--use-output-schema", action="store_true")
    parser.add_argument("--context-chars", type=int, default=10000)
    parser.add_argument("--full-context", action="store_true", help="Include all extracted tables, sections, and figure captions instead of ranked snippets.")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent Codex extraction workers.")
    parser.add_argument("--cache-only", action="store_true", help="Only ingest existing json_outputs; do not launch Codex.")
    parser.add_argument("--retry-failed", action="store_true", help="Only process DOI rows currently marked failed in the output database.")
    parser.add_argument("--only-doi", action="append", default=[], help="Only process this DOI. Can be supplied multiple times.")
    parser.add_argument("--only-doi-file", type=Path, help="Text file with one DOI per line to process.")
    args = parser.parse_args(argv)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_template = args.prompt.read_text(encoding="utf-8")
    prompt_version = re.search(r"Prompt v(\d+)", prompt_template)
    meta = {
        "prompt_version": f"v{prompt_version.group(1)}" if prompt_version else args.prompt.stem,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
    }

    con = ensure_db(out_dir / "codex_extraction_results.db")
    if args.enrich_only:
        enrich_entities(con, out_dir / "entity_enrichment_cache.json")
        export_excel(con, out_dir / "pha_codex_extraction.xlsx")
        print(f"Enrichment complete. SQLite: {out_dir / 'codex_extraction_results.db'}")
        print(f"Excel: {out_dir / 'pha_codex_extraction.xlsx'}")
        return 0

    rows = fetch_rows(args.db, args.article_dir, args.limit)
    only_dois = {doi.strip().lower() for doi in (args.only_doi or []) if doi.strip()}
    if args.only_doi_file:
        for line in args.only_doi_file.read_text(encoding="utf-8").splitlines():
            doi = line.strip()
            if doi and not doi.startswith("#"):
                only_dois.add(doi.lower())
    if args.retry_failed:
        failed_dois = {
            str(row[0]).lower()
            for row in con.execute("SELECT doi FROM article_extractions WHERE status = 'failed'").fetchall()
        }
        only_dois = failed_dois if not only_dois else only_dois & failed_dois
    if only_dois:
        rows = [row for row in rows if str(row.get("doi") or "").lower() in only_dois]
    manifest = out_dir / "codex_sample_manifest.json"
    write_json(manifest, rows)
    print(f"Prepared {len(rows)} article contexts. Manifest: {manifest}")
    if args.prepare_only:
        return 0

    pending: list[tuple[int, dict[str, Any]]] = []
    for idx, row in enumerate(rows, start=1):
        existing = None if args.force else con.execute(
            "SELECT status FROM article_extractions WHERE doi = ?", (row["doi"],)
        ).fetchone()
        if existing and existing[0] in {"success", "partial"}:
            print(f"[{idx}/{len(rows)}] skip {row['doi']} ({existing[0]})")
            continue
        if args.cache_only:
            cached_json = out_dir / "json_outputs" / f"{safe_id(row['doi'])}.json"
            if not cached_json.exists():
                print(f"[{idx}/{len(rows)}] skip {row['doi']} (no cached json)")
                continue
        pending.append((idx, row))

    done = 0
    failed = 0

    def run_one(idx: int, row: dict[str, Any]) -> tuple[int, dict[str, Any], dict[str, Any] | None, list[str], Exception | None]:
        try:
            payload, errors = codex_extract(
                row, prompt_template, args.schema, out_dir, args.model,
                args.reasoning_effort, args.timeout, args.force,
                args.use_output_schema, args.context_chars, args.full_context,
            )
            return idx, row, payload, errors, None
        except Exception as exc:
            return idx, row, None, ["codex_failed"], exc

    def record_result(idx: int, row: dict[str, Any], payload: dict[str, Any] | None, errors: list[str], exc: Exception | None) -> None:
        nonlocal done, failed
        if payload is not None and exc is None:
            status = "success" if payload.get("records") else "partial"
            if errors:
                status = "partial"
            try:
                upsert_payload(con, row, payload, status, meta, errors)
                done += 1
                print(f"[{idx}/{len(rows)}] -> {status} {row['doi']}, records={len(payload.get('records') or [])}, validation_errors={len(errors)}")
                return
            except Exception as upsert_exc:
                con.rollback()
                errors = [*errors, f"upsert_failed: {upsert_exc}"]
                exc = upsert_exc

        failed_payload = {
            "schema_version": "0.2.0",
            "prompt_version": meta["prompt_version"],
            "article": {
                "doi": row.get("doi"),
                "title": row.get("title") or "",
                "triage_label": "maybe",
                "triage_reason": "Codex extraction failed",
                "study_types": [],
            },
            "article_common_fields": {},
            "records": [],
            "material_mentions": [],
            "protein_mentions": [],
            "special_fields": [],
            "extraction_note": str(exc),
        }
        try:
            upsert_payload(con, row, failed_payload, "failed", meta, errors, str(exc))
        except Exception as fallback_exc:
            con.rollback()
            print(f"[{idx}/{len(rows)}] -> failed {row['doi']}: {exc}; fallback_upsert_failed={fallback_exc}")
        else:
            print(f"[{idx}/{len(rows)}] -> failed {row['doi']}: {exc}")
        failed += 1

    if args.workers > 1 and pending:
        worker_count = max(1, args.workers)
        print(f"Running {len(pending)} pending articles with {worker_count} Codex workers.")
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {
                pool.submit(run_one, idx, row): (idx, row)
                for idx, row in pending
            }
            for future in as_completed(futures):
                try:
                    idx, row, payload, errors, exc = future.result()
                except Exception as exc:
                    idx, row = futures[future]
                    payload = None
                    errors = ["worker_failed"]
                record_result(idx, row, payload, errors, exc)
    else:
        for idx, row in pending:
            print(f"[{idx}/{len(rows)}] codex {row['doi']} {row.get('publisher')} score={row.get('score')}")
            idx, row, payload, errors, exc = run_one(idx, row)
            record_result(idx, row, payload, errors, exc)

    if not args.skip_enrich:
        print("Enriching material/protein mentions with PubChem and UniProt...")
        enrich_entities(con, out_dir / "entity_enrichment_cache.json")

    export_excel(con, out_dir / "pha_codex_extraction.xlsx")
    print(f"Extraction complete. done={done}, failed={failed}")
    print(f"SQLite: {out_dir / 'codex_extraction_results.db'}")
    print(f"Excel: {out_dir / 'pha_codex_extraction.xlsx'}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
