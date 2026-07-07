# PHA Keywords and Extraction Strategy

Date: 2026-07-01

## Objective

PHA means **Protein-Hydrogel Adsorption** in this project. It does not refer to
polyhydroxyalkanoates.

Build a data-driven corpus for designing hydrogel systems that adsorb, weakly
adsorb, or resist adsorption of specified proteins. Following expert review,
the corpus must also support biointerface/blood-contacting materials,
multi-protein competitive adsorption, protein corona, process matching, and
AI-ready training labels. The database must support:

- hydrogel/protein pair screening;
- adsorption vs. low-adsorption classification;
- quantitative adsorption-capacity prediction;
- mechanism-aware design;
- preparation and physical-property reference lookup;
- multi-protein adsorb/reject design tasks;
- biointerface response and hemocompatibility interpretation;
- process-window and fabrication-route matching.

## Search Strategy

The search is intentionally split into ten query families. Each family is
kept separate so we can later audit which source contributed each paper.

The 2026-07-07 curation update integrates controlled fields into the current
release schema while preserving record granularity, output tables, and the
original Q1-Q7 retrieval meanings. Additional terms or fields should be logged
as additive expansion rather than as a replacement for prior query families.

| Family | Purpose | Positive/negative role |
| --- | --- | --- |
| Q1 quantitative adsorption | papers reporting capacity, kinetics, isotherms, or physical-property links | mostly positive adsorption |
| Q2 named target proteins | model-protein probes such as BSA, lysozyme, fibrinogen, hemoglobin, IgG | positive and weak adsorption |
| Q3 biointerface/blood-contacting | wound dressing, hemocompatibility, platelet/complement/cell response, blood-contacting hydrogel surfaces | positive, weak, and antifouling interface records |
| Q4 affinity/imprinted systems | imprinted, ion-exchange, boronate, chelating, aptamer, ligand hydrogels | selective adsorption |
| Q5 low-adsorption/antifouling | protein-resistant, zwitterionic, PEGylated, antifouling systems | negative or weak adsorption |
| Q6 multi-protein/protein corona | competitive adsorption, serum/plasma adsorption, protein exchange, Vroman effect, corona composition | multi-protein selectivity and reject-protein evidence |
| Q7 mechanism/property | electrostatic, hydrophobic, mesh-size, pore-size, pI, charge, conformation, unfolding, hydration layer, corona terms | mechanistic evidence |
| Q8 separation/purification | hydrogel adsorbents, columns, cryogels, monoliths, reusable capture systems | positive/selective adsorption and process records |
| Q9 formulation/process window | hydrogel formulation, fabrication, crosslinking, gelation, grafting, coating, elution, regeneration, scale-up | process matching and reproducibility |
| Q10 library/data-driven screening | high-throughput/combinatorial hydrogel arrays, hydrogel libraries, machine learning, inverse design, protein binding profile | design-oriented paired data |

Q3 and Q6 were redefined after expert review. Counts in earlier reports are
therefore historical and should not be reused for the new Q3/Q6 definitions.
The current `PHA/configs/config.yaml` contains Q1-Q10 and should be count-probed
again before a full harvest.

For compatibility with Q1-Q7 audit reporting, Q1-Q7 should remain
the primary audit families for Articles / Records / Model Ready / Comparable
Numeric summaries. Q8-Q10 may remain as extension families, but should not be
used to redefine the meaning of the earlier Q1-Q7 families.

## Inclusion Rules

Include a paper when it contains experimental evidence for interaction between
a hydrogel material and one or more proteins, including:

- adsorption, binding, uptake, fouling, capture, separation, purification, or
  recognition;
- low adsorption, protein resistance, antifouling behavior, or nonspecific
  adsorption suppression;
- multi-protein competition, serum/plasma protein adsorption, protein corona,
  Vroman-like exchange, or protein unfolding at the hydrogel interface;
- biointerface response linked to protein adsorption, such as platelet adhesion,
  complement activation, macrophage polarization, hemocompatibility, or foreign
  body response;
- quantitative or semi-quantitative measurements such as capacity, removal,
  surface coverage, fluorescence intensity, elution yield, fouling reduction,
  or comparison against a control hydrogel.

Q5 antifouling/low-adsorption records must contain protein, serum, plasma,
albumin, fibrinogen, IgG, blood, or total-protein measurement evidence. Articles
with only antibacterial, cell-adhesion, marine-biofouling, or generic
antifouling claims and no protein/blood/plasma/serum fouling measurement should
be excluded or down-weighted.

## Exclusion Rules

Exclude or down-rank papers when the hydrogel is only used for:

- protein drug delivery/release without adsorption or binding data;
- tissue engineering/cell culture without protein adsorption measurement;
- pure synthesis/characterization with no protein interaction experiment;
- simulation-only work without experimental adsorption validation;
- review, perspective, patent, editorial, or bibliometric analysis.

## Record Granularity

One extracted record should represent:

`hydrogel material + protein target + experimental condition + measured outcome`

A single paper can therefore produce many records if it compares:

- multiple hydrogels;
- multiple proteins;
- multiple pH/ionic-strength/temperature conditions;
- different concentrations or contact times;
- adsorption and desorption/regeneration cycles.

## Core Fields

### Provenance

- DOI, title, journal, year, publisher
- source section/table/figure/supplement
- exact evidence text or table caption
- extraction confidence and review status

### Hydrogel Identity And Preparation

- hydrogel name or sample code
- polymer backbone and monomers
- crosslinker and crosslink density
- functional groups or ligands
- charge class: cationic, anionic, zwitterionic, neutral, amphiphilic
- composite filler: silica, graphene oxide, MOF, magnetic particle, clay,
  cellulose, chitosan, alginate, etc.
- synthesis/preparation method
- initiator, solvent, pH, temperature, gelation time when reported

### Hydrogel Physical Properties

- swelling ratio / water content
- pore size, mesh size, porosity, surface area
- particle size for beads, microgels, nanogels
- zeta potential or surface charge
- contact angle / hydrophilicity
- modulus/mechanical property
- degradation/stability
- responsive behavior: pH, temperature, ionic strength, redox, light

### Protein Target

- protein name and abbreviation
- source/species: BSA, HSA, lysozyme, fibrinogen, IgG, etc.
- molecular weight
- isoelectric point / pI
- charge state at experiment pH when inferable
- initial concentration and matrix: buffer, serum, plasma, mixture

### Adsorption Experiment

- batch, column, membrane, surface, coating, or flow mode
- hydrogel dosage, mass, area, or volume
- protein concentration before/after adsorption
- pH, buffer, ionic strength, salt, temperature
- contact/incubation time
- detection method: UV-vis, fluorescence, BCA/Bradford, QCM, SPR, ELISA,
  HPLC, electrophoresis, microscopy
- competing proteins or serum/plasma background

### Outcome Metrics

- adsorption capacity: raw value and normalized value
- surface adsorption/coverage when applicable
- removal or binding efficiency
- distribution coefficient / partition coefficient
- selectivity coefficient
- dynamic binding capacity for columns
- isotherm model and parameters: Langmuir, Freundlich, Sips, etc.
- kinetic model and parameters: pseudo-first-order, pseudo-second-order,
  intraparticle diffusion, etc.
- desorption efficiency, regeneration cycles, retained capacity
- antifouling or low-adsorption reduction percentage

### Curated Standardization Fields

These fields are deterministic post-processing labels. They do not replace raw
evidence fields and should not overwrite article-derived experimental values.

- `interaction_type`: `physical_adsorption`, `nonspecific_adsorption`,
  `selective_adsorption`, `affinity_binding`, `covalent_immobilization`,
  `entrapment`, `antifouling_low_adsorption`, `protein_fouling`, or `unknown`.
- `is_covalent_binding`: `yes`, `no`, or `unclear`.
- `experiment_mode_primary`: `batch`, `column`, `surface`, `flow`, `QCM_SPR`,
  `microarray`, `immobilization`, `hemocompatibility`, `biofouling`, or `other`.
- `experiment_mode_detail`: `batch_adsorption_equilibrium`,
  `batch_adsorption_kinetics`, `batch_adsorption_isotherm`,
  `static_incubation`, `column_dynamic_binding`, `column_breakthrough`,
  `surface_fouling_assay`, `QCM_D`, `SPR_binding`,
  `fluorescence_surface_quantification`, `protein_immobilization_activity`, or
  `other`.
- `application_context`: `biointerface_adsorption`, `purification`,
  `antifouling`, `protein_immobilization`, `hemocompatibility`,
  `screening_library`, `mechanism_study`, or `other`.
- `comparable_target_class`: `strong`, `medium`, `weak`, or `not_comparable`.
  Strong targets include normalized capacity, bed capacity, surface adsorption,
  Ka, and Kd. Medium targets include efficiency/recovery/purity/fouling
  percentages, selectivity factors, and imprinting factors. Fluorescence,
  absorbance, relative signal, SDS-PAGE band intensity, image-derived coverage,
  and qualitative staining intensity are weak unless separately normalized.
- `model_ready`, `model_ready_blocker`, and `manual_review_priority`: derived
  audit fields used for modeling subset selection and manual review ordering.

The original free-text `experiment_mode` and the controlled
`experiment_mode_primary/detail` fields should both be retained: the former
preserves evidence language, while the latter supports filtering and modeling.

## Mechanism Tags

Extract explicit mechanism labels and supporting evidence. Allowed tags:

- electrostatic attraction/repulsion
- hydrophobic interaction
- hydrogen bonding
- van der Waals interaction
- steric hindrance / hydration layer
- size exclusion / mesh-size sieving
- pore diffusion / mass transfer
- molecular imprinting
- affinity ligand recognition
- boronate affinity
- metal chelation / coordination
- ion exchange
- pH-responsive binding
- temperature-responsive binding
- protein conformational change
- competitive adsorption / Vroman-like effect

Mechanism tags should not be inferred unless the article gives direct evidence
or a clear author interpretation. Inferred tags must be marked as inferred.

## Positive And Negative Labels

Keep continuous outcome values as the primary target. Classification labels are
derived later from normalized outcomes and author claims.

Suggested raw labels:

- `adsorbing`: measurable binding/capture/removal or author-reported adsorption.
- `selective_adsorbing`: stronger adsorption for one protein over competitors.
- `weak_adsorbing`: measurable but low adsorption, or much weaker than control.
- `non_adsorbing`: no significant adsorption or explicitly protein-resistant.
- `antifouling`: designed to suppress nonspecific adsorption/fouling.

Do not force a global threshold during extraction. Store the local control,
unit, and context so thresholds can be changed during modeling.

## Extraction Workflow

1. Metadata triage:
   classify each article as `include`, `exclude`, or `maybe` based on title,
   abstract, document type, and query family.
2. Full-text triage:
   confirm whether the paper contains hydrogel-protein adsorption, binding,
   fouling, capture, or anti-adsorption data.
3. Record extraction:
   extract one record per hydrogel-protein-condition-outcome combination.
4. Unit normalization:
   preserve raw values, then normalize into common units where possible.
5. Mechanism extraction:
   attach explicit mechanism tags and evidence text to each record.
6. Quality scoring:
   score records by provenance clarity, unit completeness, condition coverage,
   and whether a control/comparator is present.
7. Modeling view:
   create derived tables for classification, regression, and retrieval:
   hydrogel features, protein features, condition features, and outcome labels.

## Priority For First Corpus Pass

Prioritize papers that report at least one of:

- adsorption capacity or binding capacity;
- adsorption isotherm or kinetic model;
- pH/ionic-strength/temperature dependence;
- comparison across multiple hydrogels or multiple proteins;
- selectivity against competing proteins;
- antifouling/low-adsorption comparison to a control;
- regeneration/desorption/reuse.
