from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from run_pha_field_completion import apply_patches, payload_to_patches  # noqa: E402


def make_db(record_json: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    db = Path(tmp.name)
    con = sqlite3.connect(db)
    con.execute(
        """
        CREATE TABLE adsorption_records (
            id INTEGER PRIMARY KEY,
            doi TEXT,
            record_id TEXT,
            record_json TEXT
        )
        """
    )
    con.execute(
        "INSERT INTO adsorption_records (doi, record_id, record_json) VALUES (?, ?, ?)",
        ("10.test/example", "PHA-test-001", json.dumps(record_json)),
    )
    con.commit()
    con.close()
    return db


def read_record(db: Path) -> dict:
    con = sqlite3.connect(db)
    raw = con.execute("SELECT record_json FROM adsorption_records").fetchone()[0]
    con.close()
    return json.loads(raw)


class FieldCompletionPatchFlowTest(unittest.TestCase):
    def tearDown(self) -> None:
        db = getattr(self, "db", None)
        if db:
            Path(db).unlink(missing_ok=True)

    def test_patch_does_not_overwrite_existing_value(self) -> None:
        self.db = make_db({"hydrogel": {"monomer_ratios": "old ratio"}})
        patches = [
            {
                "doi": "10.test/example",
                "record_id": "PHA-test-001",
                "target_path": "hydrogel.monomer_ratios",
                "value": "new ratio",
                "value_json": json.dumps("new ratio"),
                "value_origin": "observed_fulltext",
                "evidence_text": "Table 1 reports new ratio",
                "source_section": "Table 1",
                "source_table_or_figure": "Table 1",
                "confidence": 0.9,
                "prompt_version": "test",
                "article_type": "general_batch_adsorption",
                "qa_note": "",
            }
        ]
        applied, reports = apply_patches(self.db, "10.test/example", patches, apply=True)
        self.assertEqual(applied, 0)
        self.assertEqual(reports[0]["apply_status"], "rejected_existing_value")
        self.assertEqual(read_record(self.db)["hydrogel"]["monomer_ratios"], "old ratio")

    def test_unmatched_record_id_is_rejected(self) -> None:
        self.db = make_db({"hydrogel": {}})
        patches = [
            {
                "doi": "10.test/example",
                "record_id": "missing-record",
                "target_path": "hydrogel.monomer_ratios",
                "value": "1:2",
                "value_json": json.dumps("1:2"),
                "value_origin": "observed_fulltext",
                "evidence_text": "Table 1 reports 1:2",
                "source_section": "Table 1",
                "source_table_or_figure": "Table 1",
                "confidence": 0.9,
                "prompt_version": "test",
                "article_type": "general_batch_adsorption",
                "qa_note": "",
            }
        ]
        applied, reports = apply_patches(self.db, "10.test/example", patches, apply=True)
        self.assertEqual(applied, 0)
        self.assertEqual(reports[0]["apply_status"], "rejected_unmatched_record")

    def test_missing_evidence_or_source_is_rejected(self) -> None:
        self.db = make_db({"hydrogel": {}})
        patches = [
            {
                "doi": "10.test/example",
                "record_id": "PHA-test-001",
                "target_path": "hydrogel.monomer_ratios",
                "value": "1:2",
                "value_json": json.dumps("1:2"),
                "value_origin": "observed_fulltext",
                "evidence_text": "",
                "source_section": "Table 1",
                "source_table_or_figure": "Table 1",
                "confidence": 0.9,
                "prompt_version": "test",
                "article_type": "general_batch_adsorption",
                "qa_note": "",
            },
            {
                "doi": "10.test/example",
                "record_id": "PHA-test-001",
                "target_path": "hydrogel.crosslinker_concentration",
                "value": "5 mol%",
                "value_json": json.dumps("5 mol%"),
                "value_origin": "observed_fulltext",
                "evidence_text": "MBAAm 5 mol%",
                "source_section": "",
                "source_table_or_figure": "Table 1",
                "confidence": 0.9,
                "prompt_version": "test",
                "article_type": "general_batch_adsorption",
                "qa_note": "",
            },
        ]
        applied, reports = apply_patches(self.db, "10.test/example", patches, apply=True)
        self.assertEqual(applied, 0)
        self.assertEqual(reports[0]["apply_status"], "rejected_missing_evidence")
        self.assertEqual(reports[1]["apply_status"], "rejected_missing_source")

    def test_external_descriptor_origin_never_writes_record(self) -> None:
        self.db = make_db({"protein": {}})
        patches = [
            {
                "doi": "10.test/example",
                "record_id": "PHA-test-001",
                "target_path": "protein.molecular_weight_kDa",
                "value": 66.5,
                "value_json": json.dumps(66.5),
                "value_origin": "external_descriptor",
                "evidence_text": "UniProt P02769",
                "source_section": "UniProt",
                "source_table_or_figure": "",
                "confidence": 0.9,
                "prompt_version": "test",
                "article_type": "general_batch_adsorption",
                "qa_note": "",
            }
        ]
        applied, reports = apply_patches(self.db, "10.test/example", patches, apply=True)
        self.assertEqual(applied, 0)
        self.assertEqual(reports[0]["apply_status"], "rejected_origin")
        self.assertNotIn("molecular_weight_kDa", read_record(self.db)["protein"])

    def test_v2_payload_converts_to_patch(self) -> None:
        payload = {
            "article": {"article_type": "general_batch_adsorption"},
            "record_updates": [
                {
                    "record_id_hint": "PHA-test-001",
                    "preparation_update": {"monomer_ratios": "AAm:MBAAm 95:5"},
                    "evidence_text": "AAm:MBAAm 95:5",
                    "source_section": "Methods",
                    "source_table_or_figure": "",
                    "confidence": 0.8,
                }
            ],
        }
        patches = payload_to_patches("10.test/example", payload, "test")
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["target_path"], "hydrogel.monomer_ratios")
        self.assertEqual(patches[0]["value_origin"], "observed_fulltext")


if __name__ == "__main__":
    unittest.main()
