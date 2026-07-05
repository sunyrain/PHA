from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "processed" / "pha_extraction_1000_xhigh_fulltext_w8" / "codex_extraction_results.db"


def doi_hash(doi: str) -> str:
    return hashlib.sha1(doi.lower().encode("utf-8")).hexdigest()[:10]


def safe_id(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[<>:"/\\|?*\s]+', "_", text)
    text = re.sub(r"[^a-z0-9_.-]+", "_", text)
    return text[:80].strip("_") or "unknown"


def load_record_json(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def desired_record_ids(rows: list[sqlite3.Row]) -> dict[int, str]:
    seen: set[str] = set()
    per_doi_counts: dict[str, int] = defaultdict(int)
    mapping: dict[int, str] = {}
    for row in rows:
        doi = str(row["doi"] or "")
        prefix = f"PHA-{doi_hash(doi)}-"
        raw = str(row["record_id"] or "").strip()
        per_doi_counts[doi] += 1
        if raw.startswith(prefix) and raw not in seen:
            new_id = raw
        else:
            base = safe_id(raw) if raw and not raw.upper().startswith("PHA-") else f"{per_doi_counts[doi]:03d}"
            new_id = prefix + base
        suffix = 2
        candidate = new_id
        while candidate in seen:
            candidate = f"{new_id}-{suffix}"
            suffix += 1
        seen.add(candidate)
        mapping[int(row["id"])] = candidate
    return mapping


def normalize(db_path: Path, apply: bool) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute("select id, doi, record_id, record_json from adsorption_records order by doi, id").fetchall()
    mapping = desired_record_ids(rows)
    changes: list[dict[str, Any]] = []
    for row in rows:
        new_id = mapping[int(row["id"])]
        old_id = str(row["record_id"] or "")
        if old_id == new_id:
            continue
        rec = load_record_json(row["record_json"])
        rec["record_id"] = new_id
        changes.append({
            "id": int(row["id"]),
            "doi": row["doi"],
            "old_record_id": old_id,
            "new_record_id": new_id,
            "record_json": json.dumps(rec, ensure_ascii=False),
        })

    if apply and changes:
        with con:
            for item in changes:
                con.execute(
                    "update adsorption_records set record_id = ?, record_json = ? where id = ?",
                    (item["new_record_id"], item["record_json"], item["id"]),
                )
    con.close()
    return {
        "db_path": str(db_path),
        "apply": apply,
        "rows": len(rows),
        "changed": len(changes),
        "sample_changes": [
            {k: v for k, v in item.items() if k != "record_json"}
            for item in changes[:20]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize PHA extraction database IDs.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    report = normalize(args.db, args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
