# PHA Scope and Data Plan

## Goal

Build a literature-mined database for protein adsorption by hydrogel materials,
covering adsorbent composition, protein targets, adsorption conditions,
capacity, kinetics, isotherms, selectivity, regeneration, and provenance.

## Working Scope

- Hydrogel adsorbents used to bind, capture, separate, purify, enrich, remove,
  or resist proteins.
- Protein-imprinted, affinity, ion-exchange, zwitterionic, charged, cryogel,
  nanogel, microgel, and composite hydrogel systems.
- Model proteins such as albumin/BSA, lysozyme, hemoglobin, immunoglobulins,
  antibodies, enzymes, cytokines, and serum proteins.
- Experimental adsorption records with quantitative or semi-quantitative
  readouts.

## Out of Scope For The First Pass

- General tissue engineering, wound dressing, and drug delivery papers unless
  protein adsorption/binding is measured.
- Pure synthesis papers without adsorption or binding results.
- Reviews, perspectives, patents, editorials, and bibliometric analyses.
- Molecular simulation-only studies unless paired with experimental adsorption
  data.

## Core Schema Groups

- Provenance: DOI, title, journal, publication year, publisher, source table or
  text, extraction time, confidence, and curation status.
- Hydrogel material: polymer/backbone, monomers, crosslinker, functional groups,
  charge type, porosity, swelling ratio, mesh size, morphology, and composite
  fillers.
- Protein target: protein name, source/species, molecular weight, pI, charge
  state, concentration, and matrix/sample context.
- Adsorption experiment: pH, buffer, ionic strength, temperature, contact time,
  dosage, initial/final concentration, batch/column mode, and competing solutes.
- Performance: adsorption capacity, removal/binding efficiency, distribution
  coefficient, selectivity, kinetic model, isotherm model, fitted parameters,
  regeneration, reuse, and desorption conditions.
- Quality flags: unit normalization status, missing-condition flags, duplicate
  DOI/record flags, and out-of-range numeric checks.

## Initial Literature Search Strategy

The updated metadata pass uses seven query families, documented in
`PHA_KEYWORDS_AND_EXTRACTION_STRATEGY.md`:

- quantitative adsorption and physical-property records;
- named model protein probes;
- separation, purification, and reusable hydrogel adsorbents;
- imprinted, affinity, chelating, boronate, aptamer, and ion-exchange systems;
- low-adsorption and antifouling systems for weak/negative labels;
- hydrogel libraries and high-throughput screening records;
- mechanism-centered adsorption papers.

## Operational Workflow

1. Harvest literature metadata into `PHA/data/databases/PHA-2026_articles.db`.
2. Export the filtered DOI queue to `PHA/data/raw/article_pending_download.json`
   and `PHA/data/processed/article_pending_download.xlsx`.
3. Download publisher article assets into `PHA/data/article_data`.
4. Develop a PHA extractor after the first corpus audit confirms the dominant
   article types and data fields.
5. Run quality checks for DOI deduplication, field coverage, unit normalization,
   and topic relevance before building a public release.
