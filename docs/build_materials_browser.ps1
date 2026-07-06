$ErrorActionPreference = 'Stop'

$DocsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Resolve-Path (Join-Path $DocsDir '..\data\curated\pha_scientific_dataset_20260705\data')

function Clean-Text {
  param([object]$Value)
  if ($null -eq $Value) { return '' }
  return ([string]$Value).Trim()
}

function Short-Text {
  param(
    [string]$Value,
    [int]$MaxLength = 240
  )
  $Text = Clean-Text $Value
  if ($Text.Length -le $MaxLength) { return $Text }
  return $Text.Substring(0, $MaxLength - 3) + '...'
}

function Add-Count {
  param(
    [hashtable]$Table,
    [string]$Key
  )
  $CleanKey = Clean-Text $Key
  if (-not $CleanKey) { return }
  if (-not $Table.ContainsKey($CleanKey)) { $Table[$CleanKey] = 0 }
  $Table[$CleanKey] += 1
}

function Top-Counts {
  param(
    [hashtable]$Table,
    [int]$Limit = 6
  )
  @($Table.GetEnumerator() |
    Sort-Object @{ Expression = 'Value'; Descending = $true }, @{ Expression = 'Key'; Descending = $false } |
    Select-Object -First $Limit |
    ForEach-Object { [ordered]@{ name = $_.Key; count = $_.Value } })
}

$Materials = Import-Csv (Join-Path $DataDir 'materials.csv')
$Descriptors = Import-Csv (Join-Path $DataDir 'material_descriptors.csv')

$DescriptorByMentionId = @{}
foreach ($Descriptor in $Descriptors) {
  $DescriptorByMentionId[(Clean-Text $Descriptor.material_mention_id)] = $Descriptor
}

$Groups = @{}
foreach ($Material in $Materials) {
  $Name = Clean-Text $Material.name
  if (-not $Name) { continue }
  $Key = $Name.ToLowerInvariant()
  if (-not $Groups.ContainsKey($Key)) {
    $Groups[$Key] = [ordered]@{
      name                 = $Name
      mention_count        = 0
      doi_set              = @{}
      role_counts          = @{}
      status_counts        = @{}
      query_counts         = @{}
      needs_review_count   = 0
      descriptor_mentions  = 0
      pubchem_cid          = ''
      molecular_formula    = ''
      molecular_weight     = ''
      canonical_smiles     = ''
      inchikey             = ''
      iupac_name           = ''
      examples             = @()
    }
  }

  $Group = $Groups[$Key]
  $Group.mention_count += 1
  $Doi = Clean-Text $Material.doi
  if ($Doi) { $Group.doi_set[$Doi] = $true }
  Add-Count $Group.role_counts $Material.role
  Add-Count $Group.query_counts $Material.pubchem_query
  if ((Clean-Text $Material.needs_manual_normalization) -eq '1') {
    $Group.needs_review_count += 1
  }

  $Descriptor = $DescriptorByMentionId[(Clean-Text $Material.id)]
  if ($Descriptor) {
    $Status = Clean-Text $Descriptor.match_status
    Add-Count $Group.status_counts $Status
    if ($Status -eq 'matched') { $Group.descriptor_mentions += 1 }

    if (-not $Group.pubchem_cid -and (Clean-Text $Descriptor.pubchem_cid)) { $Group.pubchem_cid = Clean-Text $Descriptor.pubchem_cid }
    if (-not $Group.molecular_formula -and (Clean-Text $Descriptor.molecular_formula)) { $Group.molecular_formula = Clean-Text $Descriptor.molecular_formula }
    if (-not $Group.molecular_weight -and (Clean-Text $Descriptor.molecular_weight)) { $Group.molecular_weight = Clean-Text $Descriptor.molecular_weight }
    if (-not $Group.canonical_smiles -and (Clean-Text $Descriptor.canonical_smiles)) { $Group.canonical_smiles = Clean-Text $Descriptor.canonical_smiles }
    if (-not $Group.inchikey -and (Clean-Text $Descriptor.inchikey)) { $Group.inchikey = Clean-Text $Descriptor.inchikey }
    if (-not $Group.iupac_name -and (Clean-Text $Descriptor.iupac_name)) { $Group.iupac_name = Clean-Text $Descriptor.iupac_name }
  }

  if ($Group.examples.Count -lt 4) {
    $Context = Short-Text $Material.context 260
    if ($Context) {
      $Group.examples += [ordered]@{
        doi     = $Doi
        role    = Clean-Text $Material.role
        context = $Context
      }
    }
  }
}

$Rows = foreach ($Entry in $Groups.GetEnumerator()) {
  $Group = $Entry.Value
  $TopRoles = @(Top-Counts $Group.role_counts 6)
  $StatusCounts = @(Top-Counts $Group.status_counts 6)
  $QueryCounts = @(Top-Counts $Group.query_counts 4)
  $PrimaryRole = if ($TopRoles.Count) { $TopRoles[0]['name'] } else { '' }
  $PrimaryStatus = if ($Group.descriptor_mentions -gt 0) {
    'matched'
  } elseif ($StatusCounts.Count) {
    $StatusCounts[0]['name']
  } else {
    'no_descriptor'
  }
  [ordered]@{
    name                 = $Group.name
    primary_role         = $PrimaryRole
    mention_count        = $Group.mention_count
    doi_count            = $Group.doi_set.Count
    descriptor_status    = $PrimaryStatus
    descriptor_mentions  = $Group.descriptor_mentions
    needs_review_count   = $Group.needs_review_count
    pubchem_cid          = $Group.pubchem_cid
    molecular_formula    = $Group.molecular_formula
    molecular_weight     = $Group.molecular_weight
    canonical_smiles     = $Group.canonical_smiles
    inchikey             = $Group.inchikey
    iupac_name           = $Group.iupac_name
    top_roles            = $TopRoles
    match_status_counts  = $StatusCounts
    pubchem_queries      = $QueryCounts
    examples             = $Group.examples
  }
}

$Rows = @($Rows | Sort-Object @{ Expression = { $_['mention_count'] }; Descending = $true }, @{ Expression = { $_['doi_count'] }; Descending = $true }, @{ Expression = { $_['name'] }; Descending = $false })

$TopRolesGlobal = @{}
$TopStatusGlobal = @{}
foreach ($Row in $Rows) {
  Add-Count $TopRolesGlobal $Row['primary_role']
  Add-Count $TopStatusGlobal $Row['descriptor_status']
}

$Summary = [ordered]@{
  generated_at                  = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
  material_mentions             = $Materials.Count
  unique_materials              = $Rows.Count
  descriptor_matched_materials  = @($Rows | Where-Object { $_['descriptor_status'] -eq 'matched' }).Count
  descriptor_matched_mentions   = @($Materials | Where-Object {
    $Descriptor = $DescriptorByMentionId[(Clean-Text $_.id)]
    $Descriptor -and (Clean-Text $Descriptor.match_status) -eq 'matched'
  }).Count
  needs_review_materials        = @($Rows | Where-Object { $_['needs_review_count'] -gt 0 }).Count
  top_roles                     = Top-Counts $TopRolesGlobal 10
  descriptor_statuses           = Top-Counts $TopStatusGlobal 10
}

$Rows | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $DocsDir 'pha_materials_browser.json') -Encoding UTF8
$Summary | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $DocsDir 'pha_materials_summary.json') -Encoding UTF8

Write-Host "materials=$($Materials.Count) unique=$($Rows.Count) matched_materials=$($Summary.descriptor_matched_materials)"
