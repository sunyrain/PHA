# PHA Expert Review Draft: Search Keywords And Extraction Fields

Date: 2026-07-01

Project: PHA, Protein Hydrogel Adsorption. Objective: build a literature-derived dataset for hydrogel systems that adsorb, selectively adsorb, weakly adsorb, or resist adsorption of target proteins, with enough material, protein, condition, outcome, and mechanism information to support data-driven hydrogel design.

## 1. Search Scope

| Item | Current Setting |
| --- | --- |
| Time span | 2000-2026 |
| Document type | Research articles |
| Databases | Web of Science Starter API, Elsevier Scopus API |
| Core material scope | Hydrogel, polymer gel, cryogel, nanogel, microgel, hydrogel bead, hydrogel membrane, hydrogel coating, hydrogel column, hydrogel monolith, porous gel |
| Core interaction scope | Protein adsorption, protein binding, protein uptake, protein capture, protein fouling, antifouling, protein separation, protein purification |
| Target use | Adsorption / non-adsorption classification, adsorption-capacity prediction, mechanism-aware material design, preparation and property reference |

## 2. Search Keyword Groups

| Query | Purpose | Material Terms | Protein / Interaction Terms | Quantitative, Functional, Or Mechanistic Terms |
| --- | --- | --- | --- | --- |
| Q1 Quantitative adsorption and property links | Capture papers reporting capacity, kinetics, isotherms, or material-property links. | `hydrogel*`, `"polymer gel*"`, `cryogel*`, `nanogel*`, `microgel*`, `"hydrogel bead*"`, `"hydrogel microsphere*"`, `"hydrogel membrane*"` | `"protein adsorption"`, `"protein adsorb*"`, `"protein sorption"`, `"protein binding"`, `"protein uptake"`, `"nonspecific protein adsorption"`, `"protein fouling"` | `"adsorption capacity"`, `"binding capacity"`, `isotherm*`, `kinetic*`, `Qmax`, `"distribution coefficient"`, `"adsorption mechanism"`, `"surface charge"`, `"charge density"`, `"zeta potential"`, `"swelling ratio"`, `"water content"`, `porosity`, `"pore size"`, `"mesh size"`, `modulus`, `"contact angle"`, `hydrophilic*`, `hydrophobic*`, `"functional group*"` |
| Q2 Named model proteins | Capture common model-protein and competitor-protein studies. | `hydrogel*`, `"polymer gel*"`, `cryogel*`, `nanogel*`, `microgel*`, `"hydrogel bead*"`, `"hydrogel microsphere*"`, `"hydrogel membrane*"` | `"bovine serum albumin"`, `BSA`, `"human serum albumin"`, `HSA`, `albumin`, `lysozyme`, `fibrinogen`, `hemoglobin`, `"cytochrome c"`, `myoglobin`, `ovalbumin`, `trypsin`, `pepsin`, `insulin`, `immunoglobulin*`, `IgG`, `antibody`, `antibodies`, `transferrin`, `ferritin`, `lactoferrin` | `adsorp*`, `sorption`, `bind*`, `uptake`, `capture`, `removal`, `"fouling resistance"`, `antifouling`, `"anti-fouling"` |
| Q3 Separation, purification, and reusable adsorbents | Capture hydrogel adsorbents, cryogels, columns, monoliths, and reusable capture systems. | `hydrogel*`, `cryogel*`, `"hydrogel bead*"`, `"hydrogel column*"`, `"hydrogel monolith*"`, `"hydrogel adsorbent*"`, `"porous gel*"` | `"protein separation"`, `"protein purification"`, `"protein capture"`, `"protein adsorption"`, `"affinity chromatography"`, `"ion exchange chromatography"`, `"binding capacity"`, `"dynamic binding capacity"` | `adsorp*`, `bind*`, `capture`, `selectivity`, `regeneration`, `elution` |
| Q4 Selective affinity, imprinted, chelating, aptamer, and ion-exchange hydrogels | Capture systems with explicit selective-recognition mechanisms. | `"molecularly imprinted hydrogel*"`, `"protein imprinted hydrogel*"`, `"protein-imprinted hydrogel*"`, `"affinity hydrogel*"`, `"ion-exchange hydrogel*"`, `"ion exchange hydrogel*"`, `"boronate affinity hydrogel*"`, `"metal chelate hydrogel*"`, `"chelating hydrogel*"`, `"Ni-NTA hydrogel*"`, `"aptamer hydrogel*"`, `"cryogel column*"`, `"hydrogel adsorbent*"` | `protein`, `peptide`, `albumin`, `lysozyme`, `hemoglobin`, `immunoglobulin*`, `IgG`, `antibody`, `enzyme` | `adsorp*`, `bind*`, `capture`, `recognition`, `selectiv*`, `separation` |
| Q5 Low-adsorption and antifouling hydrogels | Capture weak-binding and negative examples for non-adsorption design. | `hydrogel*`, `"polymer gel*"`, `cryogel*`, `nanogel*`, `microgel*`, `"hydrogel coating*"`, `"hydrogel surface*"`, `"hydrogel membrane*"` | `protein`, `serum`, `plasma`, `albumin`, `fibrinogen`, `lysozyme`, `immunoglobulin*`, `antibody` | `"low protein adsorption"`, `"reduced protein adsorption"`, `"minimal protein adsorption"`, `"resist protein adsorption"`, `"protein resistant"`, `protein-resistant`, `"protein repellent"`, `"fouling resistance"`, `"protein fouling"`, `biofouling`, `antifouling`, `"anti-fouling"`, `zwitterionic`, `PEGylated`, `"poly(ethylene glycol)"`, `"polyethylene glycol"` |
| Q6 Hydrogel libraries and high-throughput screening | Capture grouped material-protein adsorption data for model training. | `"hydrogel library"`, `"hydrogel libraries"`, `"combinatorial hydrogel*"`, `"high-throughput hydrogel*"`, `"hydrogel array*"`, `"hydrogel microarray*"`, `"microgel library"`, `"polymer hydrogel library"` | `"protein adsorption"`, `"protein binding"`, `"serum protein"`, `"protein fouling"`, `"nonspecific protein adsorption"`, `biofouling` | Library, screening, array, microarray, high-throughput context |
| Q7 Mechanism and property-centered adsorption | Capture papers discussing physical origin of adsorption or resistance. | `hydrogel*`, `"polymer gel*"`, `cryogel*`, `nanogel*`, `microgel*` | `protein`, `albumin`, `lysozyme`, `fibrinogen`, `hemoglobin`, `immunoglobulin*`, `antibody`; `adsorp*`, `sorption`, `bind*`, `fouling` | `electrostatic*`, `hydrophobic*`, `hydrophilic*`, `"hydrogen bonding"`, `"van der Waals"`, `"size exclusion"`, `"mesh size"`, `porosity`, `"pore size"`, `"charge density"`, `"surface charge"`, `"isoelectric point"`, `pI`, `"molecular imprinting"`, `"affinity ligand"`, `"conformation change"` |

## 3. Preliminary Scale Probe

| Query | Theme | Web of Science Count | Scopus Count | Notes |
| ---: | --- | ---: | ---: | --- |
| Q1 | Quantitative adsorption and property links | 902 | 878 | High priority for quantitative modeling. |
| Q2 | Named model proteins | 3,169 | 3,099 | Broad by design; useful for multi-protein comparison. |
| Q3 | Separation, purification, and reusable adsorbents | 1,871 | 1,375 | Narrowed to require separation/capture/capacity and adsorption/reuse/elution terms. |
| Q4 | Imprinted, affinity, chelating, aptamer, ion-exchange hydrogels | 141 | 135 | Smaller but high mechanistic value. |
| Q5 | Low-adsorption and antifouling hydrogels | 3,831 | 4,283 | Important source of weak-binding and negative labels. |
| Q6 | Hydrogel libraries and high-throughput screening | 3 | 3 | Low-yield but likely high-value when relevant. |
| Q7 | Mechanism and property-centered adsorption | 1,956 | 1,919 | Useful but needs triage for false positives. |

## 4. Inclusion And Exclusion Rules

| Category | Rule |
| --- | --- |
| Include | Experimental evidence for hydrogel-protein adsorption, binding, uptake, fouling, capture, separation, purification, recognition, low adsorption, or antifouling. |
| Include | Quantitative or semi-quantitative outcomes such as adsorption capacity, removal, surface coverage, fluorescence intensity, recovery, purity, fouling reduction, or comparison against a control. |
| Include | Reported hydrogel properties, protein properties, pH, salt, temperature, time, flow rate, or other conditions that support mechanism analysis or modeling. |
| Exclude / down-rank | Protein drug delivery or release only, with no adsorption or binding data. |
| Exclude / down-rank | Tissue engineering or cell culture only, with no protein adsorption measurement. |
| Exclude / down-rank | Synthesis/characterization only, simulation-only work, reviews, perspectives, editorials, patents, or bibliometric papers. |

## 5. Data Record Granularity

| Principle | Description |
| --- | --- |
| Record unit | One record = paper + hydrogel material + protein target + experimental condition + measured outcome. |
| Split records when | The same paper compares different hydrogels, proteins, pH values, salt concentrations, temperatures, contact times, concentrations, cycles, flow rates, or elution conditions. |
| Do not force thresholds during extraction | Store raw measurements and local controls first; derive adsorption/non-adsorption labels later under task-specific thresholds. |

## 6. Extraction Field List

| Module | Fields |
| --- | --- |
| A. Provenance and evidence | `record_id`, `schema_version`, `doi`, `pmid`, `title`, `year`, `journal`, `query_family`, `source_section`, `source_table_or_figure`, `evidence_text`, `extraction_method`, `extraction_confidence`, `review_status` |
| B. Article relevance and study type | `relevance_label` include/maybe/exclude, `relevance_reason`, `study_type` adsorption_capacity/separation_purification/antifouling_low_adsorption/imprinting_affinity/mechanism_property/screening_library/protein_immobilization/biocompatibility_fouling, `is_review`, `has_quantitative_adsorption`, `has_control_or_comparator` |
| C. Hydrogel identity and preparation | `hydrogel_id`, `hydrogel_name`, `hydrogel_format` bulk_gel/film/coating/bead/microgel/nanogel/cryogel/monolith/membrane/column_bed/scaffold/composite/other, `polymer_backbone`, `monomers`, `monomer_ratios`, `crosslinker`, `crosslinker_concentration`, `initiator`, `synthesis_method`, `preparation_solvent`, `preparation_pH`, `preparation_temp_C`, `gelation_time`, `functional_groups`, `ligand_or_affinity_group`, `metal_ion_or_bridge`, `template_molecule`, `filler_or_composite`, `substrate_or_support`, `post_treatment` |
| D. Hydrogel properties | `charge_class` cationic/anionic/zwitterionic/mixed_charge/neutral/amphiphilic/unknown, `net_charge_condition`, `responsive_type`, `lcst_C`, `swelling_ratio`, `water_content_pct`, `porosity_pct`, `pore_size`, `mesh_size`, `surface_area`, `particle_size`, `zeta_potential_mV`, `contact_angle_deg`, `young_modulus`, `adhesion_energy`, `permeability`, `thermal_stability`, `cycle_stability`, `morphology_method` |
| E. Protein target and protein properties | `protein_name`, `protein_abbreviation`, `protein_species_or_source`, `protein_role` target/template/competitor/mixture_component/fouling_protein/immobilized_enzyme/unknown, `molecular_weight_kDa`, `pI`, `charge_at_experiment_pH` positive/negative/near_neutral/mixed/unknown, `protein_initial_concentration`, `protein_matrix`, `competitor_proteins`, `protein_labeling` |
| F. Experimental conditions | `experiment_mode` batch/column/surface/QCM/SPR/microarray/flow/implant/hemocompatibility/microscopy/other, `hydrogel_dosage`, `solution_volume`, `pH`, `buffer`, `ionic_strength`, `salt_type`, `salt_concentration`, `temperature_C`, `contact_time`, `flow_rate`, `loading_volume_CV`, `wash_solution`, `elution_solution`, `regeneration_cycles`, `detection_method`, `replicate_count` |
| G. Adsorption, separation, and antifouling outcomes | `outcome_label` adsorbing/selective_adsorbing/weak_adsorbing/non_adsorbing/antifouling/protein_immobilization/ambiguous, `outcome_basis`, `raw_metric_name`, `raw_metric_value`, `raw_metric_unit`, `q_norm_mg_g`, `q_norm_mg_mL_bed`, `surface_adsorption_ug_cm2`, `removal_efficiency_pct`, `binding_efficiency_pct`, `recovery_pct`, `purity_pct`, `dynamic_binding_capacity`, `selectivity_factor`, `imprinting_factor`, `association_constant_Ka`, `dissociation_constant_Kd`, `isotherm_model`, `isotherm_parameters`, `kinetic_model`, `kinetic_parameters`, `fouling_reduction_pct`, `retained_capacity_pct`, `side_outcomes` |
| H. Mechanism, controls, and comparators | `mechanism_tags` electrostatic_attraction/electrostatic_repulsion/hydrophobic_interaction/hydrogen_bonding/van_der_waals/steric_hindrance/hydration_layer/size_exclusion/pore_diffusion/molecular_imprinting/shape_memory/coordination_metal_bridge/ion_exchange/boronate_affinity/ligand_affinity/aptamer_recognition/pH_responsive/temperature_responsive/salt_responsive/protein_conformation_change/competitive_adsorption/unknown, `mechanism_evidence_text`, `author_claimed_mechanism`, `inferred_mechanism`, `control_type`, `control_material`, `control_outcome`, `fold_change_vs_control`, `comparator_notes` |
| I. Normalization and quality control | `unit_normalized`, `normalization_notes`, `value_ambiguity`, `missing_conditions`, `source_quality_score` 0-3, `needs_manual_review`, `exclusion_reason` |

## 7. Additions For Inverse Design

| Item | Required Change |
| --- | --- |
| Design-space framing | Treat the design space as material backbone x functionalization x network structure x format x fabrication process x operating condition x protein panel, not as a flat list of hydrogels. |
| Multi-protein objective | Add explicit support for target adsorbed protein sets and target rejected protein sets. The model should learn a protein-response vector under a given condition. |
| Process matching | Promote fabrication method, crosslinking/grafting/coating conditions, elution, regeneration, sterilization, storage, and scale-up notes from optional notes to design-relevant fields. |
| Tunable variables | Mark which variables were actively changed in a paper, such as pH, salt, temperature, ligand density, monomer ratio, crosslink density, pore size, or hydrogel format. |
| Negative examples | Keep low-adsorption and antifouling hydrogels in scope because they supply non-adsorption labels for reject-protein constraints. |

| New Search Direction | Purpose | Candidate Terms |
| --- | --- | --- |
| Q8 Multi-protein competition and selectivity | Find data close to "adsorb these proteins, reject those proteins." | `competitive protein adsorption`, `selective protein adsorption`, `protein adsorption selectivity`, `protein mixture`, `serum protein adsorption`, `plasma protein adsorption`, `protein corona`, `Vroman effect` |
| Q9 Formulation, fabrication, and process window | Extract reproducible recipes and process constraints. | `hydrogel formulation`, `hydrogel fabrication`, `crosslinking density`, `gelation`, `cryopolymerization`, `grafting`, `coating`, `regeneration`, `elution`, `scale-up` |
| Q10 Data-driven design and screening | Find design-oriented datasets and hydrogel panels. | `machine learning`, `data-driven`, `inverse design`, `screening`, `combinatorial`, `high-throughput`, `hydrogel array`, `protein binding profile` |

| Additional Field Module | Fields |
| --- | --- |
| Design-space position | Application scenario, material family, format family, functionalization strategy, network-structure level, tunable variables, whether the paper systematically scanned variables. |
| Protein-panel outcome | Target protein set, reject protein set, competitor protein set, mixture matrix, panel size, adsorption vector, selectivity ranking. |
| Design constraints | Required adsorbed proteins, required rejected proteins, minimum adsorption threshold, maximum reject-protein adsorption threshold, selectivity threshold, allowed operating window. |
| Process matching | Recommended fabrication method, key formulation ratio, crosslinking/grafting/coating conditions, washing, elution, regeneration, sterilization, storage, scale-up risks. |
| Feasibility assessment | Precursor availability, synthesis complexity, aqueous or mild preparation, toxic monomer/metal concerns, reusability, application fit. |
| Inverse-design output | Candidate hydrogel, matched process, expected adsorbed proteins, expected rejected proteins, supporting literature, extrapolation risk, confidence, validation experiments. |

## 8. Questions For Expert Review

| No. | Question |
| ---: | --- |
| 1 | Are important target proteins missing, especially in coagulation, plasma, enzymes, antibodies, food proteins, or bioprocessing systems? |
| 2 | Should the hydrogel material terms include additional natural polymers, synthetic polymers, commercial adsorbents, or common product names? |
| 3 | Should low-adsorption and antifouling hydrogels remain in scope as negative examples for non-adsorption design? |
| 4 | Should we split sub-domains such as blood-contacting materials, food protein purification, biomedical surfaces, environmental separation, or bioprocess purification? |
| 5 | Are the fields sufficient to capture preparation parameters, physical properties, adsorption mechanisms, reproducible experimental conditions, and application performance? |
| 6 | Should side outcomes such as cell adhesion, platelet adhesion, bacterial adhesion, and thrombosis be retained as auxiliary fields, or should the dataset be restricted to protein adsorption only? |
| 7 | For inverse design, what should be the first practical application scenario: purification, depletion, antifouling coating, blood-contacting material, sensor enrichment, or another use case? |
| 8 | What thresholds should define "adsorb" and "reject" for expert review: absolute capacity, percent removal, surface coverage, selectivity factor, or task-specific ranking? |
| 9 | Which process constraints should be hard filters, such as water-phase synthesis, biocompatibility, no toxic metal, reusable column, sterilizable coating, or low-cost precursor? |
