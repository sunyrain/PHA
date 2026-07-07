$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Package = Join-Path $Root 'data\curated\pha_scientific_dataset_20260705'
$DataDir = Join-Path $Package 'data'
$MetadataDir = Join-Path $Package 'metadata'
$ReportsDir = Join-Path $Package 'reports'
$RulesVersion = 'curated_release_20260707'

$StandardFields = @(
  'interaction_type',
  'is_covalent_binding',
  'experiment_mode_primary',
  'experiment_mode_detail',
  'application_context',
  'comparable_target_class',
  'model_ready',
  'model_ready_blocker',
  'manual_review_priority',
  'q5_protein_evidence_flag',
  'q5_triage_action',
  'standardization_rules_version'
)

$DeprecatedFields = @('model_ready_v2')

$StandardDescriptions = [ordered]@{
  interaction_type = 'Controlled interaction class: physical adsorption, nonspecific adsorption, selective adsorption, affinity binding, covalent immobilization, entrapment, antifouling low adsorption, protein fouling, or unknown.'
  is_covalent_binding = 'yes/no/unclear flag indicating whether protein binding or immobilization is covalent.'
  experiment_mode_primary = 'Coarse controlled assay mode derived from experiment_mode, adsorption_type, detection method, outcome, and evidence.'
  experiment_mode_detail = 'Fine controlled assay mode derived from the same fields while preserving the original experiment_mode text.'
  application_context = 'Controlled application context: biointerface adsorption, purification, antifouling, protein immobilization, hemocompatibility, screening library, mechanism study, or other.'
  comparable_target_class = 'Comparability tier for the selected target: strong, medium, weak, or not_comparable.'
  model_ready = 'Curated model-ready flag using standardized interaction/application/comparability fields.'
  model_ready_blocker = 'Semicolon-separated reasons preventing model_ready=true, or ready.'
  manual_review_priority = 'Rule-derived manual review priority: high, medium, or low.'
  q5_protein_evidence_flag = 'Whether an antifouling/low-adsorption candidate has protein, serum, plasma, albumin, fibrinogen, IgG, or total-protein evidence.'
  q5_triage_action = 'Q5 protein-antifouling rule action: keep, downweight, exclude_candidate, or not_applicable.'
  standardization_rules_version = 'Version identifier for the deterministic standardization rules.'
}

function Clean-Text {
  param([object]$Value)
  if ($null -eq $Value) { return '' }
  return ([string]$Value).Trim()
}

function Has-Value {
  param([object]$Value)
  $Text = (Clean-Text $Value).ToLowerInvariant()
  if (-not $Text) { return $false }
  return -not ($Text -in @('null', 'none', 'unknown', 'not reported', 'n/a', 'na', '[]', '{}'))
}

function As-Bool {
  param([object]$Value)
  $Text = (Clean-Text $Value).ToLowerInvariant()
  return $Text -in @('true', '1', 'yes')
}

function As-Number {
  param([object]$Value)
  $Text = Clean-Text $Value
  if (-not $Text) { return $null }
  $Out = 0.0
  if ([double]::TryParse($Text, [Globalization.NumberStyles]::Any, [Globalization.CultureInfo]::InvariantCulture, [ref]$Out)) {
    return $Out
  }
  return $null
}

function Text-Blob {
  param([pscustomobject]$Row)
  $Keys = @(
    'hydrogel__hydrogel_name', 'hydrogel__hydrogel_format', 'hydrogel__polymer_backbone',
    'hydrogel__monomers', 'hydrogel__crosslinker', 'hydrogel__functional_groups',
    'hydrogel__ligand_or_affinity_group', 'hydrogel__filler_or_composite',
    'protein__protein_name', 'protein__protein_abbreviation', 'protein__protein_species_or_source',
    'protein__protein_role', 'protein__protein_matrix', 'protein__competitor_proteins',
    'experiment__experiment_mode', 'experiment__adsorption_type', 'experiment__competition_system',
    'experiment__detection_method', 'outcome__outcome_label', 'outcome__raw_metric_name',
    'outcome__raw_metric_value', 'outcome__raw_metric_unit', 'mechanism__mechanism_tags',
    'mechanism__control_type', 'mechanism__control_material', 'evidence_text_db',
    'primary_target_name', 'primary_target_unit'
  )
  $Parts = foreach ($Key in $Keys) {
    if ($Row.PSObject.Properties[$Key]) { Clean-Text $Row.$Key }
  }
  return ($Parts -join ' ').ToLowerInvariant()
}

function Contains-Any {
  param(
    [string]$Text,
    [string[]]$Patterns
  )
  foreach ($Pattern in $Patterns) {
    if ($Text -match $Pattern) { return $true }
  }
  return $false
}

function Has-Any-Field {
  param(
    [pscustomobject]$Row,
    [string[]]$Fields
  )
  foreach ($Field in $Fields) {
    if ($Row.PSObject.Properties[$Field] -and (Has-Value $Row.$Field)) { return $true }
  }
  return $false
}

function Derive-ComparableClass {
  param([pscustomobject]$Row, [string]$Blob)
  $Strong = @(
    'outcome__q_norm_mg_g',
    'outcome__q_norm_mg_mL_bed',
    'outcome__surface_adsorption_ug_cm2',
    'outcome__association_constant_Ka',
    'outcome__dissociation_constant_Kd'
  )
  $Medium = @(
    'outcome__removal_efficiency_pct',
    'outcome__binding_efficiency_pct',
    'outcome__recovery_pct',
    'outcome__purity_pct',
    'outcome__fouling_reduction_pct',
    'outcome__retained_capacity_pct',
    'outcome__selectivity_factor',
    'outcome__imprinting_factor',
    'outcome__dynamic_binding_capacity'
  )
  $HasMaterial = Has-Any-Field $Row @('hydrogel__hydrogel_name', 'hydrogel__polymer_backbone', 'hydrogel__monomers')
  $HasProtein = Has-Any-Field $Row @('protein__protein_name', 'protein__protein_abbreviation', 'protein__protein_matrix')
  if (-not $HasMaterial -or -not $HasProtein) { return 'not_comparable' }
  if (Has-Any-Field $Row $Strong) { return 'strong' }
  if (Has-Any-Field $Row $Medium) { return 'medium' }
  $WeakPatterns = @(
    'fluorescence intensity', 'fluorescent intensity', 'relative signal', 'band intensity',
    'sds[- ]page', 'staining intensity', 'image[- ]derived', 'absorbance', '\bod\b',
    'arbitrary unit', '\ba\.?u\.?\b'
  )
  if (Contains-Any $Blob $WeakPatterns) { return 'weak' }
  if (-not (Has-Value $Row.primary_target_value) -or -not (Has-Value $Row.primary_target_unit)) { return 'not_comparable' }
  return 'weak'
}

function Derive-InteractionType {
  param([string]$Blob)
  if (Contains-Any $Blob @('covalent', 'glutaraldehyde', '\bedc\b', '\bnhs\b', 'schiff base', 'epoxy', 'glycidyl', 'aldehyde', 'amide bond', 'amine coupling')) {
    return 'covalent_immobilization'
  }
  if (Contains-Any $Blob @('entrap', 'entrapp', 'encapsulat', 'embedded', 'loaded', 'release', 'nanogel.*insulin', 'microgel.*loaded')) {
    return 'entrapment'
  }
  if (Contains-Any $Blob @('affinity', 'antibody[- ]antigen', 'antigen', 'aptamer', 'biotin', 'streptavidin', '\bni[- ]nta\b', 'his[- ]tag', 'immunoaffinity', 'affinity ligand')) {
    return 'affinity_binding'
  }
  if (Contains-Any $Blob @('imprint', 'molecularly imprinted', '\bmip\b', 'selectiv', 'template', 'chelat', 'ion exchange', 'anion exchange', 'cation exchange', 'metal[- ]ion')) {
    return 'selective_adsorption'
  }
  if (Contains-Any $Blob @('antifouling', 'anti[- ]fouling', 'low adsorption', 'low protein adsorption', 'reduced protein adsorption', 'nonfouling', 'non[- ]fouling', 'fouling reduction', 'zwitterionic', 'sulfobetaine', 'carboxybetaine', '\bmpc\b')) {
    return 'antifouling_low_adsorption'
  }
  if (Contains-Any $Blob @('protein fouling', 'biofouling', 'membrane fouling', 'foulant')) {
    return 'protein_fouling'
  }
  if (Contains-Any $Blob @('nonspecific', 'non[- ]specific', 'serum protein adsorption', 'plasma protein adsorption')) {
    return 'nonspecific_adsorption'
  }
  if (Contains-Any $Blob @('adsorption', 'adsorb', 'sorption', 'binding capacity', 'uptake', 'isotherm', 'kinetic')) {
    return 'physical_adsorption'
  }
  return 'unknown'
}

function Derive-CovalentFlag {
  param([string]$Interaction, [string]$Blob)
  if ($Interaction -eq 'covalent_immobilization') { return 'yes' }
  if (Contains-Any $Blob @('unclear.*covalent', 'whether.*covalent', 'covalent.*unclear')) { return 'unclear' }
  if ($Interaction -eq 'unknown') { return 'unclear' }
  return 'no'
}

function Derive-ExperimentPrimary {
  param([string]$Blob)
  if (Contains-Any $Blob @('\bqcm\b', 'qcm[- ]d', 'quartz crystal microbalance', '\bspr\b', 'surface plasmon resonance')) { return 'QCM_SPR' }
  if (Contains-Any $Blob @('column', 'breakthrough', 'dynamic binding', 'packed bed', 'monolith', 'bed volume', 'chromatograph')) { return 'column' }
  if (Contains-Any $Blob @('microfluidic', 'flow[- ]focusing', 'continuous flow', 'flow assay', 'perfusion', 'shear flow')) { return 'flow' }
  if (Contains-Any $Blob @('microarray', 'hydrogel array', 'array', 'library', 'high[- ]throughput', 'combinatorial')) { return 'microarray' }
  if (Contains-Any $Blob @('\bblood\b', '\bserum(?! albumin)\b', '\bplasma\b', 'platelet', 'complement', 'coagulation', 'hemocompat')) { return 'hemocompatibility' }
  if (Contains-Any $Blob @('antifouling', 'anti[- ]fouling', 'biofouling', 'fouling reduction', 'protein fouling')) { return 'biofouling' }
  if (Contains-Any $Blob @('immobilization', 'immobilized', 'enzyme activity', 'covalent_immobilization')) { return 'immobilization' }
  if (Contains-Any $Blob @('surface', 'coating', 'film', 'membrane', 'plate', 'slide', 'contact angle')) { return 'surface' }
  if (Contains-Any $Blob @('batch', 'static incubation', 'incubation', 'isotherm', 'kinetic', 'equilibrium', 'adsorption assay')) { return 'batch' }
  return 'other'
}

function Derive-ExperimentDetail {
  param([string]$Blob, [string]$Primary)
  if (Contains-Any $Blob @('qcm[- ]d', '\bqcm\b', 'quartz crystal microbalance')) { return 'QCM_D' }
  if (Contains-Any $Blob @('\bspr\b', 'surface plasmon resonance')) { return 'SPR_binding' }
  if (Contains-Any $Blob @('breakthrough')) { return 'column_breakthrough' }
  if (Contains-Any $Blob @('dynamic binding', 'dbc', 'q_norm_mg_ml_bed')) { return 'column_dynamic_binding' }
  if (Contains-Any $Blob @('surface fouling', 'fouling reduction', 'low protein adsorption', 'antifouling', 'anti[- ]fouling')) { return 'surface_fouling_assay' }
  if (Contains-Any $Blob @('fluorescence', 'fluorescent', 'confocal', 'image[- ]derived')) { return 'fluorescence_surface_quantification' }
  if (Contains-Any $Blob @('enzyme activity', 'immobilization activity', 'retained activity')) { return 'protein_immobilization_activity' }
  if (Contains-Any $Blob @('isotherm')) { return 'batch_adsorption_isotherm' }
  if (Contains-Any $Blob @('kinetic')) { return 'batch_adsorption_kinetics' }
  if (Contains-Any $Blob @('equilibrium')) { return 'batch_adsorption_equilibrium' }
  if (Contains-Any $Blob @('static incubation', 'incubation')) { return 'static_incubation' }
  if ($Primary -eq 'batch') { return 'batch_adsorption_equilibrium' }
  return 'other'
}

function Derive-ApplicationContext {
  param([string]$Blob, [string]$Interaction, [string]$Primary)
  if (Contains-Any $Blob @('purification', 'separation', 'chromatograph', 'elution', 'recovery', 'purity', 'capture', 'dynamic binding', 'breakthrough')) { return 'purification' }
  if ($Interaction -eq 'antifouling_low_adsorption' -or $Primary -eq 'biofouling') { return 'antifouling' }
  if ($Interaction -in @('covalent_immobilization', 'entrapment') -or $Primary -eq 'immobilization') { return 'protein_immobilization' }
  if ($Primary -eq 'hemocompatibility') { return 'hemocompatibility' }
  if ($Primary -eq 'microarray' -or (Contains-Any $Blob @('screening', 'library', 'high[- ]throughput', 'combinatorial'))) { return 'screening_library' }
  if (Contains-Any $Blob @('mechanism', 'isotherm', 'kinetic', 'zeta potential', 'swelling', 'mesh size', 'pore size', 'contact angle')) { return 'mechanism_study' }
  if (Contains-Any $Blob @('adsorption', 'adsorb', 'binding', 'biointerface')) { return 'biointerface_adsorption' }
  return 'other'
}

function Derive-Q5ProteinFlag {
  param([string]$Blob)
  return Contains-Any $Blob @(
    '\bprotein\b', 'serum', 'plasma', 'albumin', '\bbsa\b', '\bhsa\b',
    'fibrinogen', '\bigg\b', 'immunoglobulin', 'total protein', 'blood'
  )
}

function Derive-ModelReady {
  param([pscustomobject]$Row, [string]$ComparableClass, [string]$Interaction)
  $Blockers = New-Object System.Collections.Generic.List[string]
  if (-not (Has-Any-Field $Row @('hydrogel__hydrogel_name', 'hydrogel__polymer_backbone', 'hydrogel__monomers'))) {
    $Blockers.Add('missing_material_identity')
  }
  if (-not (Has-Any-Field $Row @('protein__protein_name', 'protein__protein_abbreviation', 'protein__protein_matrix'))) {
    $Blockers.Add('missing_protein_target_or_mixture')
  }
  if (-not (Has-Any-Field $Row @('experiment__pH', 'experiment__contact_time', 'protein__protein_initial_concentration', 'experiment__temperature_C', 'experiment__flow_rate'))) {
    $Blockers.Add('missing_key_experiment_condition')
  }
  if ($ComparableClass -notin @('strong', 'medium')) {
    $Blockers.Add('not_strong_or_medium_comparable')
  }
  if (-not (Has-Any-Field $Row @('primary_target_unit', 'outcome__raw_metric_unit')) -and -not (As-Bool $Row.quality__unit_normalized)) {
    $Blockers.Add('missing_or_unnormalizable_unit')
  }
  $Score = As-Number $Row.quality__source_quality_score
  if ($null -eq $Score -or $Score -lt 2) {
    $Blockers.Add('low_source_quality')
  }
  if ($Interaction -eq 'unknown' -and -not (Has-Value $Row.record_json)) {
    $Blockers.Add('unknown_interaction_type')
  }
  if (Contains-Any ((Clean-Text $Row.article_title).ToLowerInvariant()) @('\breview\b')) {
    $Blockers.Add('review_or_nonexperimental_article')
  }
  if ($Blockers.Count -eq 0) { return @($true, 'ready') }
  return @($false, ($Blockers -join ';'))
}

function Derive-ManualReviewPriority {
  param(
    [pscustomobject]$Row,
    [string]$Blob,
    [string]$ComparableClass,
    [bool]$ModelReady,
    [string]$Interaction,
    [int]$DoiRecordCount
  )
  $Score = As-Number $Row.quality__source_quality_score
  $HighMaterial = Contains-Any $Blob @('\bpva\b', 'poly\(vinyl alcohol\)', '\bpeg\b', 'poly\(ethylene glycol\)', 'zwitterionic', 'cryogel', 'hydrogel coating', 'sulfobetaine', 'carboxybetaine')
  $HighProtein = Contains-Any $Blob @('fibrinogen', '\bigg\b', '\bserum(?! albumin)\b', '\bplasma\b', '\bblood\b')
  $UnitConverted = As-Bool $Row.quality__unit_normalized
  $ComparableForReview = $ComparableClass -in @('strong', 'medium')
  if (($ModelReady -and $Score -ge 2) -or $UnitConverted -or $ComparableClass -eq 'strong' -or ($HighProtein -and $Score -ge 2) -or ($HighMaterial -and $ComparableForReview) -or ($DoiRecordCount -gt 4 -and $ComparableForReview)) {
    return 'high'
  }
  if ((Has-Value $Row.primary_target_value) -or (Has-Value $Row.outcome__raw_metric_value) -or $ComparableClass -eq 'medium' -or $Interaction -in @('affinity_binding', 'covalent_immobilization', 'entrapment')) {
    return 'medium'
  }
  return 'low'
}

function Set-Prop {
  param(
    [pscustomobject]$Row,
    [string]$Name,
    [object]$Value
  )
  if ($Row.PSObject.Properties[$Name]) {
    $Row.$Name = $Value
  } else {
    $Row | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
  }
}

function Write-Csv {
  param(
    [string]$Path,
    [object[]]$Rows
  )
  $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function Merge-Standardization {
  param(
    [string]$Path,
    [hashtable]$ByRecordId
  )
  $Rows = @(Import-Csv -LiteralPath $Path)
  foreach ($Row in $Rows) {
    $Std = $ByRecordId[$Row.record_id]
    if ($null -eq $Std) { continue }
    foreach ($Field in $DeprecatedFields) {
      if ($Row.PSObject.Properties[$Field]) {
        $Row.PSObject.Properties.Remove($Field)
      }
    }
    foreach ($Field in $StandardFields) {
      Set-Prop $Row $Field $Std.$Field
    }
    if ($Row.PSObject.Properties['model_ready_reason']) {
      $Row.model_ready_reason = $Std.model_ready_blocker
    }
  }
  Write-Csv $Path $Rows
}

function Add-FieldCoverageRows {
  param(
    [string]$Path,
    [object[]]$Rows
  )
  $Existing = @(Import-Csv -LiteralPath $Path | Where-Object { $_.field -notlike 'standardization.*' })
  $Total = $Rows.Count
  $NewRows = foreach ($Field in $StandardFields) {
    $Present = @($Rows | Where-Object { Has-Value $_.$Field }).Count
    [pscustomobject][ordered]@{
      field = "standardization.$Field"
      column = $Field
      description = $StandardDescriptions[$Field]
      present = $Present
      total = $Total
      coverage_pct = if ($Total) { [Math]::Round($Present * 100.0 / $Total, 2) } else { 0 }
    }
  }
  Write-Csv $Path @($Existing + $NewRows)
}

function Add-DataDictionaryRows {
  param([string]$Path)
  $KnownFields = @($StandardFields + $DeprecatedFields)
  $Existing = @(Import-Csv -LiteralPath $Path | Where-Object { $_.column -notin $KnownFields -and $_.table -ne 'model_records_v2.csv' })
  $NewRows = New-Object System.Collections.Generic.List[object]
  $Tables = @('records_flat.csv', 'records_core.csv', 'model_records.csv', 'inverse_design_seed.csv', 'record_standardization.csv')
  foreach ($Table in $Tables) {
    foreach ($Field in $StandardFields) {
      $NewRows.Add([pscustomobject][ordered]@{ table = $Table; column = $Field; description = $StandardDescriptions[$Field] })
    }
  }
  Write-Csv $Path @($Existing + $NewRows)
}

function Add-FieldTierRows {
  param(
    [string]$Path,
    [object[]]$Rows
  )
  $Existing = @(Import-Csv -LiteralPath $Path | Where-Object { $_.field -notlike 'standardization.*' })
  $Total = $Rows.Count
  $NewRows = foreach ($Field in $StandardFields) {
    $Present = @($Rows | Where-Object { Has-Value $_.$Field }).Count
    $Coverage = if ($Total) { [Math]::Round($Present * 100.0 / $Total, 2) } else { 0 }
    [pscustomobject][ordered]@{
      field = "standardization.$Field"
      column = $Field
      display_label = ($Field -replace '_', ' ')
      disposition = 'main_field'
      tier = 'standardization'
      present = $Present
      missing = $Total - $Present
      total = $Total
      coverage_pct = $Coverage
      effective_present = $Present
      effective_missing = $Total - $Present
      effective_coverage_pct = ('{0:N2}' -f $Coverage)
      coverage_delta_pp = '0.00'
      description = $StandardDescriptions[$Field]
    }
  }
  Write-Csv $Path @($Existing + $NewRows)
}

function Write-RunComparison {
  param(
    [object[]]$FlatRows,
    [object[]]$StandardRows,
    [string]$MetadataDir,
    [int]$PreviousModelReady
  )
  $SummaryPath = Join-Path $MetadataDir 'summary.json'
  $Summary = Get-Content -LiteralPath $SummaryPath -Raw | ConvertFrom-Json
  foreach ($OldName in @('run_comparison_summary_20260707.csv', 'run_comparison_summary_20260707.md')) {
    $OldPath = Join-Path $MetadataDir $OldName
    if (Test-Path -LiteralPath $OldPath) {
      Remove-Item -LiteralPath $OldPath -Force
    }
  }
  $ModelReady = @($StandardRows | Where-Object { As-Bool $_.model_ready }).Count
  $ComparableNumeric = @($FlatRows | Where-Object { Has-Value $_.primary_target_value }).Count
  $StrongMedium = @($StandardRows | Where-Object { $_.comparable_target_class -in @('strong', 'medium') }).Count

  $MetricRows = New-Object System.Collections.Generic.List[object]
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'articles_count'; category = 'current_release'; count = $Summary.articles_total })
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'records_count'; category = 'current_release'; count = $FlatRows.Count })
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'model_ready_count'; category = 'current_curated_model_ready'; count = $ModelReady })
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'model_ready_count'; category = 'pre_integration_conservative_subset'; count = $PreviousModelReady })
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'comparable_count'; category = 'strong_or_medium'; count = $StrongMedium })
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'numeric_target_count'; category = 'primary_target_numeric'; count = $ComparableNumeric })
  foreach ($Field in @('interaction_type', 'experiment_mode_primary', 'application_context', 'comparable_target_class', 'manual_review_priority')) {
    $StandardRows | Group-Object $Field | Sort-Object Count -Descending | ForEach-Object {
      $MetricRows.Add([pscustomobject][ordered]@{ metric = "${Field}_distribution"; category = $_.Name; count = $_.Count })
    }
  }
  $FlatRows | Group-Object quality__source_quality_score | Sort-Object Name | ForEach-Object {
    $MetricRows.Add([pscustomobject][ordered]@{ metric = 'source_quality_score_distribution'; category = $_.Name; count = $_.Count })
  }
  $FlatRows | Group-Object protein__protein_name | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object {
    $MetricRows.Add([pscustomobject][ordered]@{ metric = 'protein_distribution_top20'; category = $_.Name; count = $_.Count })
  }
  $FlatRows | Group-Object hydrogel__hydrogel_name | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object {
    $MetricRows.Add([pscustomobject][ordered]@{ metric = 'hydrogel_distribution_top20'; category = $_.Name; count = $_.Count })
  }
  $MetricRows.Add([pscustomobject][ordered]@{ metric = 'q1_q7_query_family_contribution'; category = 'not_available_in_public_release_metadata'; count = '' })
  Write-Csv (Join-Path $MetadataDir 'curation_summary_20260707.csv') $MetricRows.ToArray()

  $Lines = New-Object System.Collections.Generic.List[string]
  $Lines.Add('# PHA Curation Summary')
  $Lines.Add('')
  $Lines.Add("Generated: $((Get-Date).ToString('yyyy-MM-ddTHH:mm:ss'))")
  $Lines.Add('')
  $Lines.Add('This summary describes the current integrated PHA = Protein-Hydrogel Adsorption release. The controlled curation fields are part of the main public schema.')
  $Lines.Add('')
  $Lines.Add('## Core Counts')
  $Lines.Add('')
  $Lines.Add("| Metric | Count |")
  $Lines.Add("|---|---:|")
  $Lines.Add("| Articles | $($Summary.articles_total) |")
  $Lines.Add("| Records | $($FlatRows.Count) |")
  $Lines.Add("| Model-ready records | $ModelReady |")
  $Lines.Add("| Strong/medium comparable records | $StrongMedium |")
  $Lines.Add("| Numeric primary-target records | $ComparableNumeric |")
  $Lines.Add('')
  foreach ($Field in @('comparable_target_class', 'interaction_type', 'experiment_mode_primary', 'application_context', 'manual_review_priority')) {
    $Lines.Add("## $Field")
    $Lines.Add('')
    $Lines.Add('| Category | Count |')
    $Lines.Add('|---|---:|')
    $StandardRows | Group-Object $Field | Sort-Object Count -Descending | ForEach-Object {
      $Lines.Add("| $($_.Name) | $($_.Count) |")
    }
    $Lines.Add('')
  }
  $Lines.Add('## Q1-Q7 Query Family Contribution')
  $Lines.Add('')
  $Lines.Add('Query-family contribution is not available in the current public release metadata. The next retrieval run should retain per-article Q1-Q7 family hits so this comparison can be populated without changing record granularity.')
  $Lines.Add('')
  $Lines.Add('## Curation Fields')
  $Lines.Add('')
  foreach ($Field in $StandardFields) {
    $Lines.Add('- `' + $Field + '`: ' + $StandardDescriptions[$Field])
  }
  $Lines.Add('')
  $Lines.Add('## Compatibility Note')
  $Lines.Add('')
  $Lines.Add("A prior conservative model-ready subset contained $PreviousModelReady records. The current release uses the integrated `model_ready` field as the single public model-ready flag.")
  Set-Content -LiteralPath (Join-Path $MetadataDir 'curation_summary_20260707.md') -Value $Lines -Encoding UTF8
}

function Update-SummaryJson {
  param(
    [string]$Path,
    [object[]]$StandardRows
  )
  $Summary = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
  foreach ($Name in @('model_ready_v2_records')) {
    if ($Summary.PSObject.Properties[$Name]) {
      $Summary.PSObject.Properties.Remove($Name)
    }
  }
  $Summary | Add-Member -NotePropertyName standardization_rules_version -NotePropertyValue $RulesVersion -Force
  $Summary | Add-Member -NotePropertyName standardization_generated_at -NotePropertyValue ((Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')) -Force
  $Summary | Add-Member -NotePropertyName model_ready_records -NotePropertyValue (@($StandardRows | Where-Object { As-Bool $_.model_ready }).Count) -Force
  $Summary | Add-Member -NotePropertyName strong_comparable_records -NotePropertyValue (@($StandardRows | Where-Object { $_.comparable_target_class -eq 'strong' }).Count) -Force
  $Summary | Add-Member -NotePropertyName medium_comparable_records -NotePropertyValue (@($StandardRows | Where-Object { $_.comparable_target_class -eq 'medium' }).Count) -Force
  $Summary | Add-Member -NotePropertyName high_review_priority_records -NotePropertyValue (@($StandardRows | Where-Object { $_.manual_review_priority -eq 'high' }).Count) -Force
  $Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Update-Checksums {
  param([string]$Package)
  $Rows = Get-ChildItem -LiteralPath $Package -Recurse -File |
    Where-Object { $_.FullName -notlike '*\metadata\checksums_sha256.csv' } |
    Sort-Object FullName |
    ForEach-Object {
      $Relative = $_.FullName.Substring($Package.Length + 1).Replace('\', '/')
      [pscustomobject][ordered]@{
        path = $Relative
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes = $_.Length
      }
    }
  Write-Csv (Join-Path $Package 'metadata\checksums_sha256.csv') @($Rows)
}

$FlatPath = Join-Path $DataDir 'records_flat.csv'
$CorePath = Join-Path $DataDir 'records_core.csv'
$ModelPath = Join-Path $DataDir 'model_records.csv'
$DesignPath = Join-Path $DataDir 'inverse_design_seed.csv'

$FlatRows = @(Import-Csv -LiteralPath $FlatPath)
$PreviousModelReady = @($FlatRows | Where-Object { As-Bool $_.model_ready }).Count
$DoiCounts = @{}
$FlatRows | Group-Object doi | ForEach-Object { $DoiCounts[$_.Name] = $_.Count }

$StandardRows = foreach ($Row in $FlatRows) {
  $Blob = Text-Blob $Row
  $ComparableClass = Derive-ComparableClass $Row $Blob
  $InteractionType = Derive-InteractionType $Blob
  $CovalentFlag = Derive-CovalentFlag $InteractionType $Blob
  $PrimaryMode = Derive-ExperimentPrimary $Blob
  $DetailMode = Derive-ExperimentDetail $Blob $PrimaryMode
  $Application = Derive-ApplicationContext $Blob $InteractionType $PrimaryMode
  $Q5Flag = Derive-Q5ProteinFlag $Blob
  $Q5Action = if ($Application -eq 'antifouling') {
    if ($Q5Flag) { 'keep' } elseif (Contains-Any $Blob @('antibacterial', 'cell adhesion', 'marine biofouling', 'general antifouling')) { 'exclude_candidate' } else { 'downweight' }
  } else {
    'not_applicable'
  }
  $ModelReadyResult = Derive-ModelReady $Row $ComparableClass $InteractionType
  $ModelReady = [bool]$ModelReadyResult[0]
  $ModelReadyBlocker = [string]$ModelReadyResult[1]
  $Priority = Derive-ManualReviewPriority $Row $Blob $ComparableClass $ModelReady $InteractionType ([int]$DoiCounts[$Row.doi])

  [pscustomobject][ordered]@{
    record_id = $Row.record_id
    doi = $Row.doi
    interaction_type = $InteractionType
    is_covalent_binding = $CovalentFlag
    experiment_mode_primary = $PrimaryMode
    experiment_mode_detail = $DetailMode
    application_context = $Application
    comparable_target_class = $ComparableClass
    model_ready = $ModelReady
    model_ready_blocker = $ModelReadyBlocker
    manual_review_priority = $Priority
    q5_protein_evidence_flag = $Q5Flag
    q5_triage_action = $Q5Action
    standardization_rules_version = $RulesVersion
  }
}

$StandardByRecordId = @{}
foreach ($Std in $StandardRows) {
  $StandardByRecordId[$Std.record_id] = [pscustomobject]$Std
}

Write-Csv (Join-Path $DataDir 'record_standardization.csv') @($StandardRows)
Merge-Standardization $FlatPath $StandardByRecordId
Merge-Standardization $CorePath $StandardByRecordId
Merge-Standardization $DesignPath $StandardByRecordId

$FlatRows = @(Import-Csv -LiteralPath $FlatPath)
$ModelRows = @($FlatRows | Where-Object { As-Bool $_.model_ready })
Write-Csv $ModelPath $ModelRows
$ModelV2Path = Join-Path $DataDir 'model_records_v2.csv'
if (Test-Path -LiteralPath $ModelV2Path) {
  Remove-Item -LiteralPath $ModelV2Path -Force
}

Add-FieldCoverageRows (Join-Path $MetadataDir 'field_coverage.csv') @($StandardRows)
Add-DataDictionaryRows (Join-Path $MetadataDir 'data_dictionary.csv')
Add-FieldTierRows (Join-Path $DataDir 'field_tiers.csv') @($StandardRows)
Write-RunComparison $FlatRows @($StandardRows) $MetadataDir $PreviousModelReady
Update-SummaryJson (Join-Path $MetadataDir 'summary.json') @($StandardRows)
Update-Checksums $Package

Write-Host "records=$($FlatRows.Count) model_ready=$($ModelRows.Count) strong=$(@($StandardRows | Where-Object { $_.comparable_target_class -eq 'strong' }).Count) medium=$(@($StandardRows | Where-Object { $_.comparable_target_class -eq 'medium' }).Count)"
