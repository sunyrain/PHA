from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "curated" / "pha_scientific_dataset_20260705"
CHECKSUMS = PACKAGE / "metadata" / "checksums_sha256.csv"

LOCAL_PREFIXES = tuple(
    prefix for prefix in os.environ.get("PHA_PUBLIC_SANITIZE_PREFIXES", "").split(";") if prefix
)

TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".cff"}


def public_source_path(value: str) -> str:
    if not value:
        return value
    normalized = value.replace("\\", "/")
    marker = "/PHA/data/article_data/"
    if marker in normalized:
        return "local_article_corpus/" + normalized.split(marker, 1)[1]
    marker = "PHA/data/article_data/"
    if marker in normalized:
        return "local_article_corpus/" + normalized.split(marker, 1)[1]
    if ":/" in normalized:
        return "local_article_corpus/" + Path(normalized).name
    return normalized


def sanitize_text(text: str) -> str:
    out = text
    for prefix in LOCAL_PREFIXES:
        replacement = "PHA/" if prefix.rstrip("\\/").endswith("PHA") else ""
        out = out.replace(prefix, replacement)
    return out


def sanitize_csv(path: Path) -> None:
    csv.field_size_limit(1024 * 1024 * 1024)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return
        rows = []
        changed = False
        for row in reader:
            for field in reader.fieldnames:
                value = row.get(field)
                if value is None:
                    continue
                new_value = public_source_path(value) if field == "source_json" else sanitize_text(value)
                if new_value != value:
                    row[field] = new_value
                    changed = True
            rows.append(row)
    if not changed:
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def sanitize_plain_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    new_text = sanitize_text(text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rewrite_checksums() -> None:
    files = []
    for path in PACKAGE.rglob("*"):
        if not path.is_file() or path == CHECKSUMS:
            continue
        rel = path.relative_to(PACKAGE).as_posix()
        files.append((rel, sha256(path), path.stat().st_size))
    CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    with CHECKSUMS.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "sha256", "bytes"])
        writer.writerows(sorted(files))


def main() -> None:
    self_path = Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() == self_path:
            continue
        if path.suffix.lower() == ".csv":
            sanitize_csv(path)
        elif path.suffix.lower() in TEXT_SUFFIXES:
            sanitize_plain_text(path)
    rewrite_checksums()


if __name__ == "__main__":
    main()
