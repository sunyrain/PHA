from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "processed" / "pha_extraction_1000_xhigh_fulltext_w8" / "codex_extraction_results.db"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "pha_external_descriptors"
DEFAULT_CACHE = DEFAULT_DB.parent / "entity_enrichment_cache.json"

MATERIAL_SKIP_RE = re.compile(
    r"hydrogel|polymer|copolymer|surface|matrix|membrane|serum|plasma|blood|cell|tissue|"
    r"buffer|solution|extract|column|bead|film|coating|composite|nanogel|microgel|cryogel",
    re.I,
)
PROTEIN_BROAD_RE = re.compile(r"\b(igg|immunoglobulin|globulin|albumin|antibody|enzyme|protein a|protein)\b", re.I)
NOISE_PROTEIN_RE = re.compile(r"serum|plasma|extract|lysate|mixture|unknown|protein mixture", re.I)

COMMON_ACCESSIONS = {
    ("bovine serum albumin", "bovine"): "P02769",
    ("bovine serum albumin", "bos taurus"): "P02769",
    ("human serum albumin", "human"): "P02768",
    ("human serum albumin", "homo sapiens"): "P02768",
    ("lysozyme", "chicken"): "P00698",
    ("lysozyme", "hen egg"): "P00698",
    ("lysozyme", "human"): "P61626",
    ("cytochrome c", "horse"): "P00004",
    ("myoglobin", "horse"): "P68082",
    ("ovalbumin", "chicken"): "P01012",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_payload(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": str(value)[:400]}


def material_query(row: dict[str, Any]) -> str:
    return str(row.get("pubchem_query") or row.get("name") or "").strip()


def material_is_queryable(row: dict[str, Any]) -> bool:
    query = material_query(row)
    if not query or len(query) > 80:
        return False
    if int(row.get("needs_manual_normalization") or 0):
        return False
    if MATERIAL_SKIP_RE.search(query):
        return False
    if len(re.findall(r"[A-Za-z][A-Za-z-]+", query)) > 8:
        return False
    return True


def protein_query(row: dict[str, Any]) -> str:
    parts = [row.get("uniprot_query") or row.get("name")]
    species = str(row.get("species_or_source") or "").strip()
    if species and species.lower() not in str(parts[0] or "").lower():
        parts.append(species)
    return " ".join(str(part or "").strip() for part in parts if part).strip()


def protein_is_queryable(row: dict[str, Any]) -> bool:
    query = protein_query(row)
    if not query or len(query) > 140:
        return False
    if NOISE_PROTEIN_RE.search(query):
        return False
    return True


def pubchem_lookup(query: str) -> dict[str, Any] | None:
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        + quote(query)
        + "/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChIKey,IUPACName/JSON"
    )
    response = requests.get(url, timeout=(5, 15))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    props = (response.json().get("PropertyTable") or {}).get("Properties") or []
    return props[0] if props else None


def uniprot_lookup(query: str) -> dict[str, Any] | None:
    params = {
        "query": f"({query}) AND (reviewed:true)",
        "fields": "accession,id,protein_name,organism_name,length,mass,sequence,reviewed,xref_pdb",
        "format": "json",
        "size": "5",
    }
    response = requests.get("https://rest.uniprot.org/uniprotkb/search", params=params, timeout=(5, 15))
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None
    first = results[0]
    return {
        "accession": first.get("primaryAccession"),
        "uniProtkbId": first.get("uniProtkbId"),
        "entryType": first.get("entryType"),
        "proteinDescription": first.get("proteinDescription"),
        "organism": first.get("organism"),
        "sequence": first.get("sequence"),
        "uniProtKBCrossReferences": first.get("uniProtKBCrossReferences") or [],
        "result_count": len(results),
    }


def rcsb_lookup_by_uniprot(accession: str) -> dict[str, Any] | None:
    if not accession:
        return None
    payload = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": accession,
            },
        },
        "return_type": "polymer_entity",
        "request_options": {"paginate": {"start": 0, "rows": 5}},
    }
    response = requests.post("https://search.rcsb.org/rcsbsearch/v2/query", json=payload, timeout=(5, 20))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    results = response.json().get("result_set") or []
    return {"result_count": len(results), "polymer_entity_ids": [item.get("identifier") for item in results if item.get("identifier")]}


def protein_full_name(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    desc = payload.get("proteinDescription") or {}
    rec = desc.get("recommendedName") if isinstance(desc, dict) else {}
    full = rec.get("fullName") if isinstance(rec, dict) else {}
    if isinstance(full, dict):
        return str(full.get("value") or "")
    return str(full or "")


def organism_name(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    org = payload.get("organism") or {}
    if isinstance(org, dict):
        return str(org.get("scientificName") or org.get("commonName") or "")
    return ""


def common_accession_for(row: dict[str, Any]) -> str:
    name = str(row.get("name") or "").lower()
    species = str(row.get("species_or_source") or "").lower()
    for (needle_name, needle_species), accession in COMMON_ACCESSIONS.items():
        if needle_name in name and needle_species in species:
            return accession
    return ""


def material_row(item: dict[str, Any], payload: Any, queryable: bool) -> dict[str, Any]:
    status = "skipped"
    qa_status = "skipped"
    qa_note = ""
    if queryable:
        status = "not_queried"
        qa_status = "not_queried"
    if payload == {}:
        status = "no_match"
        qa_status = "no_match"
    elif isinstance(payload, dict) and payload.get("error"):
        status = "error"
        qa_status = "error"
        qa_note = str(payload.get("error"))
    elif isinstance(payload, dict) and payload.get("CID"):
        status = "matched"
        qa_status = "usable"
    elif payload is not None:
        status = "unknown_payload"
        qa_status = "needs_review"
    return {
        "material_mention_id": item.get("id"),
        "doi": item.get("doi"),
        "name": item.get("name"),
        "role": item.get("role"),
        "query": material_query(item),
        "value_origin": "external_descriptor",
        "source_database": "PubChem",
        "match_status": status,
        "qa_status": qa_status,
        "qa_note": qa_note,
        "pubchem_cid": payload.get("CID") if isinstance(payload, dict) else None,
        "molecular_formula": payload.get("MolecularFormula") if isinstance(payload, dict) else None,
        "molecular_weight": payload.get("MolecularWeight") if isinstance(payload, dict) else None,
        "canonical_smiles": payload.get("ConnectivitySMILES") or payload.get("CanonicalSMILES") if isinstance(payload, dict) else None,
        "isomeric_smiles": payload.get("SMILES") or payload.get("IsomericSMILES") if isinstance(payload, dict) else None,
        "inchikey": payload.get("InChIKey") if isinstance(payload, dict) else None,
        "iupac_name": payload.get("IUPACName") if isinstance(payload, dict) else None,
    }


def protein_row(item: dict[str, Any], payload: Any, queryable: bool) -> dict[str, Any]:
    status = "skipped"
    qa_status = "skipped"
    notes: list[str] = []
    if queryable:
        status = "not_queried"
        qa_status = "not_queried"
    if payload == {}:
        status = "no_match"
        qa_status = "no_match"
    elif isinstance(payload, dict) and payload.get("error"):
        status = "error"
        qa_status = "error"
        notes.append(str(payload.get("error")))
    elif isinstance(payload, dict) and payload.get("accession"):
        status = "matched"
        qa_status = "usable"
        species = str(item.get("species_or_source") or "")
        organism = organism_name(payload)
        if PROTEIN_BROAD_RE.search(str(item.get("name") or "")) and not species:
            notes.append("broad_query_needs_accession_review")
        if species and organism and species.lower() not in organism.lower():
            notes.append("reported_species_not_in_uniprot_organism")
        expected = common_accession_for(item)
        if expected and expected != payload.get("accession"):
            notes.append(f"common_accession_mismatch_expected_{expected}")
        if notes:
            qa_status = "needs_review"
    elif payload is not None:
        status = "unknown_payload"
        qa_status = "needs_review"
    seq = payload.get("sequence") if isinstance(payload, dict) else {}
    pdb_refs = [
        ref.get("id")
        for ref in (payload.get("uniProtKBCrossReferences") or [])
        if isinstance(ref, dict) and str(ref.get("database") or "").upper() == "PDB" and ref.get("id")
    ] if isinstance(payload, dict) else []
    return {
        "protein_mention_id": item.get("id"),
        "doi": item.get("doi"),
        "name": item.get("name"),
        "abbreviation": item.get("abbreviation"),
        "species_or_source": item.get("species_or_source"),
        "role": item.get("role"),
        "query": protein_query(item),
        "value_origin": "external_descriptor",
        "source_database": "UniProt",
        "match_status": status,
        "qa_status": qa_status,
        "qa_note": ";".join(notes),
        "uniprot_accession": payload.get("accession") if isinstance(payload, dict) else None,
        "uniprot_id": payload.get("uniProtkbId") if isinstance(payload, dict) else None,
        "reviewed": "reviewed" in str(payload.get("entryType") or "").lower() if isinstance(payload, dict) else None,
        "protein_full_name": protein_full_name(payload),
        "organism": organism_name(payload),
        "sequence_length": seq.get("length") if isinstance(seq, dict) else None,
        "molecular_mass_Da": seq.get("molWeight") if isinstance(seq, dict) else None,
        "sequence_available": bool(seq.get("value")) if isinstance(seq, dict) else False,
        "pdb_cross_refs": ";".join(pdb_refs[:20]),
        "result_count": payload.get("result_count") if isinstance(payload, dict) else None,
    }


def audit_rows(materials: list[dict[str, Any]], proteins: list[dict[str, Any]], structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, entity_type, data in [
        ("PubChem", "material", materials),
        ("UniProt", "protein", proteins),
        ("RCSB PDB", "structure", structures),
    ]:
        status = Counter(str(row.get("match_status") or "unknown") for row in data)
        qa = Counter(str(row.get("qa_status") or "unknown") for row in data)
        rows.append(
            {
                "source_database": label,
                "entity_type": entity_type,
                "rows": len(data),
                "matched": status.get("matched", 0),
                "usable": qa.get("usable", 0),
                "needs_review": qa.get("needs_review", 0),
                "not_queried": status.get("not_queried", 0),
                "skipped": status.get("skipped", 0),
                "no_match": status.get("no_match", 0),
                "error": status.get("error", 0),
            }
        )
    return rows


def build_sidecars(db_path: Path, output_dir: Path, cache_path: Path, query_api: bool, limit: int, sleep_s: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = load_json(cache_path)
    cache.setdefault("pubchem", {})
    cache.setdefault("uniprot", {})
    cache.setdefault("rcsb", {})

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    materials = [dict(r) for r in con.execute("SELECT * FROM material_mentions ORDER BY doi, id").fetchall()]
    proteins = [dict(r) for r in con.execute("SELECT * FROM protein_mentions ORDER BY doi, id").fetchall()]
    con.close()

    query_budget = limit if limit > 0 else 10**9
    material_rows: list[dict[str, Any]] = []
    for item in materials:
        queryable = material_is_queryable(item)
        query = material_query(item)
        payload = parse_payload(item.get("enrichment_json"))
        if payload is None and queryable and query_api and query_budget > 0:
            if query not in cache["pubchem"]:
                try:
                    cache["pubchem"][query] = pubchem_lookup(query) or {}
                except Exception as exc:
                    cache["pubchem"][query] = {"error": str(exc)}
                time.sleep(sleep_s)
            payload = cache["pubchem"].get(query)
            query_budget -= 1
        material_rows.append(material_row(item, payload, queryable))

    protein_rows: list[dict[str, Any]] = []
    for item in proteins:
        queryable = protein_is_queryable(item)
        query = protein_query(item)
        payload = parse_payload(item.get("enrichment_json"))
        if payload is None and queryable and query_api and query_budget > 0:
            if query not in cache["uniprot"]:
                try:
                    cache["uniprot"][query] = uniprot_lookup(query) or {}
                except Exception as exc:
                    cache["uniprot"][query] = {"error": str(exc)}
                time.sleep(sleep_s)
            payload = cache["uniprot"].get(query)
            query_budget -= 1
        protein_rows.append(protein_row(item, payload, queryable))

    structure_rows: list[dict[str, Any]] = []
    for row in protein_rows:
        accession = str(row.get("uniprot_accession") or "")
        if not accession or row.get("qa_status") != "usable":
            continue
        payload = None
        if query_api and query_budget > 0:
            if accession not in cache["rcsb"]:
                try:
                    cache["rcsb"][accession] = rcsb_lookup_by_uniprot(accession) or {}
                except Exception as exc:
                    cache["rcsb"][accession] = {"error": str(exc)}
                time.sleep(sleep_s)
            payload = cache["rcsb"].get(accession)
            query_budget -= 1
        status = "not_queried" if payload is None else ("matched" if isinstance(payload, dict) and payload.get("polymer_entity_ids") else "no_match")
        qa_status = "usable" if status == "matched" else status
        if isinstance(payload, dict) and payload.get("error"):
            status = "error"
            qa_status = "error"
        structure_rows.append(
            {
                "protein_mention_id": row.get("protein_mention_id"),
                "doi": row.get("doi"),
                "name": row.get("name"),
                "uniprot_accession": accession,
                "value_origin": "external_descriptor",
                "source_database": "RCSB PDB",
                "match_status": status,
                "qa_status": qa_status,
                "qa_note": payload.get("error") if isinstance(payload, dict) and payload.get("error") else "",
                "rcsb_polymer_entity_ids": ";".join(payload.get("polymer_entity_ids") or []) if isinstance(payload, dict) else "",
                "result_count": payload.get("result_count") if isinstance(payload, dict) else None,
            }
        )

    pd.DataFrame(material_rows).to_csv(output_dir / "external_material_descriptors.csv", index=False, encoding="utf-8")
    pd.DataFrame(protein_rows).to_csv(output_dir / "external_protein_descriptors.csv", index=False, encoding="utf-8")
    pd.DataFrame(structure_rows).to_csv(output_dir / "external_structure_descriptors.csv", index=False, encoding="utf-8")
    audit = audit_rows(material_rows, protein_rows, structure_rows)
    pd.DataFrame(audit).to_csv(output_dir / "external_descriptor_audit.csv", index=False, encoding="utf-8")
    write_json(cache_path, cache)

    lines = [
        "# PHA external descriptor sidecar report",
        "",
        f"- Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Source DB: `{db_path}`",
        f"- Query API: {query_api}",
        f"- Output dir: `{output_dir}`",
        "",
        "## Audit",
        "",
    ]
    for row in audit:
        lines.append(
            f"- {row['source_database']} {row['entity_type']}: rows={row['rows']}, "
            f"matched={row['matched']}, usable={row['usable']}, needs_review={row['needs_review']}, "
            f"not_queried={row['not_queried']}, skipped={row['skipped']}, errors={row['error']}"
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "External descriptors are sidecar features only. They must not overwrite observed experimental fields in adsorption records.",
        ]
    )
    (output_dir / "external_descriptor_report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PHA external descriptor sidecars without mutating experimental records.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--query-api", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Maximum API lookups across PubChem, UniProt, and RCSB; 0 means no cap.")
    parser.add_argument("--sleep-s", type=float, default=0.2)
    args = parser.parse_args(argv)
    build_sidecars(args.db, args.output_dir, args.cache, args.query_api, args.limit, args.sleep_s)
    print(f"External descriptor sidecars written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
