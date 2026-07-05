from __future__ import annotations

from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_external_descriptor_sidecars import material_row, protein_row  # noqa: E402


class ExternalDescriptorSidecarTest(unittest.TestCase):
    def test_pubchem_exact_match_is_usable_sidecar(self) -> None:
        item = {
            "id": 1,
            "doi": "10.test/example",
            "name": "acrylic acid",
            "role": "monomer",
            "pubchem_query": "acrylic acid",
            "needs_manual_normalization": 0,
        }
        payload = {
            "CID": 6581,
            "MolecularFormula": "C3H4O2",
            "MolecularWeight": 72.06,
            "ConnectivitySMILES": "C=CC(=O)O",
            "InChIKey": "NIXOWILDQLNWCW-UHFFFAOYSA-N",
            "IUPACName": "prop-2-enoic acid",
        }
        row = material_row(item, payload, queryable=True)
        self.assertEqual(row["value_origin"], "external_descriptor")
        self.assertEqual(row["match_status"], "matched")
        self.assertEqual(row["qa_status"], "usable")
        self.assertEqual(row["pubchem_cid"], 6581)

    def test_uniprot_species_mismatch_needs_review(self) -> None:
        item = {
            "id": 1,
            "doi": "10.test/example",
            "name": "bovine serum albumin",
            "abbreviation": "BSA",
            "species_or_source": "bovine",
            "role": "target",
            "uniprot_query": "bovine serum albumin",
        }
        payload = {
            "accession": "P02768",
            "uniProtkbId": "ALBU_HUMAN",
            "entryType": "UniProtKB reviewed (Swiss-Prot)",
            "organism": {"scientificName": "Homo sapiens"},
            "sequence": {"length": 609, "molWeight": 69367, "value": "MKWVTFISLL"},
            "proteinDescription": {"recommendedName": {"fullName": {"value": "Albumin"}}},
            "result_count": 1,
        }
        row = protein_row(item, payload, queryable=True)
        self.assertEqual(row["match_status"], "matched")
        self.assertEqual(row["qa_status"], "needs_review")
        self.assertIn("reported_species_not_in_uniprot_organism", row["qa_note"])
        self.assertIn("common_accession_mismatch", row["qa_note"])

    def test_no_match_and_error_are_preserved(self) -> None:
        material = material_row({"id": 1, "name": "acrylic acid", "needs_manual_normalization": 0}, {}, queryable=True)
        protein = protein_row({"id": 2, "name": "lysozyme"}, {"error": "timeout"}, queryable=True)
        self.assertEqual(material["match_status"], "no_match")
        self.assertEqual(material["qa_status"], "no_match")
        self.assertEqual(protein["match_status"], "error")
        self.assertEqual(protein["qa_status"], "error")


if __name__ == "__main__":
    unittest.main()
