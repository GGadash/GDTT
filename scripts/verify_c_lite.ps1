# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param(
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$packagingRoot = [IO.Path]::GetFullPath((Join-Path $repository "packaging"))
$resolvedOutput = if ($OutputRoot) {
    [IO.Path]::GetFullPath($OutputRoot)
} else {
    [IO.Path]::GetFullPath((Join-Path $packagingRoot "output"))
}
$packagingPrefix = $packagingRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $resolvedOutput.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "C-lite verification is restricted to the repository packaging directory."
}

& (Join-Path $repository "scripts/verify_release.ps1") -OutputRoot $resolvedOutput
$manifestPath = Join-Path $resolvedOutput "BUILD_MANIFEST.json"
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($property in @("archive", "executable", "installer", "sourceArchive")) {
    if ($null -eq $manifest.$property) {
        throw "The build manifest has no $property entry."
    }
}

$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "temp/c-lite acceptance"))
$extractionRoot = Join-Path $temporaryRoot "fresh extraction"
$profileRoot = Join-Path $temporaryRoot "isolated profile"
$evidenceRoot = Join-Path $temporaryRoot "evidence"
if (-not $temporaryRoot.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe C-lite temporary path: $temporaryRoot"
}
if (Test-Path -LiteralPath $temporaryRoot) {
    Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $extractionRoot,$profileRoot,$evidenceRoot | Out-Null

$archivePath = Join-Path $resolvedOutput $manifest.archive.name
$sourceArchivePath = Join-Path $resolvedOutput $manifest.sourceArchive.name
$installerPath = Join-Path $resolvedOutput $manifest.installer.name
foreach ($artifact in @($archivePath, $sourceArchivePath, $installerPath)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "Release artifact is missing: $artifact"
    }
}
Expand-Archive -LiteralPath $archivePath -DestinationPath $extractionRoot
$executable = Join-Path $extractionRoot "GDTT/GDTT.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "The portable archive did not extract the expected executable."
}

$normalLog = Join-Path $env:LOCALAPPDATA "Gadash (Akila DJ)/GDTT/Logs/data-transform-tool.log"
$normalLogBefore = if (Test-Path -LiteralPath $normalLog -PathType Leaf) {
    (Get-FileHash -LiteralPath $normalLog -Algorithm SHA256).Hash
} else {
    $null
}
$trace = Join-Path $evidenceRoot "portable-smoke.log"
$isolatedLog = Join-Path $profileRoot "Logs/data-transform-tool.log"
$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $executable
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
foreach ($name in @("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")) {
    $null = $startInfo.Environment.Remove($name)
}
$startInfo.Environment["PATH"] = "$env:SystemRoot\System32;$env:SystemRoot"
$startInfo.Environment["APPDATA"] = (Join-Path $profileRoot "AppData/Roaming")
$startInfo.Environment["LOCALAPPDATA"] = (Join-Path $profileRoot "AppData/Local")
$startInfo.Environment["TEMP"] = (Join-Path $profileRoot "Temp")
$startInfo.Environment["TMP"] = (Join-Path $profileRoot "Temp")
$startInfo.Environment["DTT_DATA_DIRECTORY"] = (Join-Path $profileRoot "Data")
$startInfo.Environment["DTT_LOG_DIRECTORY"] = (Join-Path $profileRoot "Logs")
$startInfo.Environment["DTT_SMOKE_TRACE"] = $trace
$startInfo.Environment["QT_QPA_PLATFORM"] = "offscreen"
$startInfo.ArgumentList.Add("--smoke-test")
$startInfo.ArgumentList.Add("-platform")
$startInfo.ArgumentList.Add("offscreen")
New-Item -ItemType Directory -Path $startInfo.Environment["TEMP"] -Force | Out-Null
$process = [Diagnostics.Process]::Start($startInfo)
if ($null -eq $process -or -not $process.WaitForExit(90000) -or $process.ExitCode -ne 0) {
    $traceText = if (Test-Path -LiteralPath $trace) { Get-Content -LiteralPath $trace -Raw } else { "No trace." }
    throw "Fresh-extraction minimal-environment smoke failed. Trace: $traceText"
}
$traceText = Get-Content -LiteralPath $trace -Raw
if ($traceText -notmatch "imports-complete" -or $traceText -notmatch "smoke-result=0") {
    throw "Fresh-extraction smoke trace is incomplete."
}
if (-not (Test-Path -LiteralPath $isolatedLog -PathType Leaf)) {
    throw "The packaged application did not create its log inside the isolated profile."
}
$isolatedLogText = Get-Content -LiteralPath $isolatedLog -Raw
if ($isolatedLogText -match "SYNTHETIC-STATION") {
    throw "The isolated application log contains dataset row content."
}
$normalLogAfter = if (Test-Path -LiteralPath $normalLog -PathType Leaf) {
    (Get-FileHash -LiteralPath $normalLog -Algorithm SHA256).Hash
} else {
    $null
}
if ($normalLogBefore -ne $normalLogAfter) {
    throw "C-lite smoke changed the normal user application log."
}

$metadataRoot = Join-Path $extractionRoot "GDTT/_internal"
$bundledDistributions = @(
    Get-ChildItem -LiteralPath $metadataRoot -Directory -Filter "*.dist-info" |
        ForEach-Object { $_.Name.ToLowerInvariant() }
)
$expectedDistributions = @(
    "charset_normalizer-",
    "data_transform_tool-",
    "openpyxl-",
    "platformdirs-",
    "pydantic-",
    "pyside6-",
    "tzdata-",
    "xlsxwriter-"
)
foreach ($expected in $expectedDistributions) {
    if (-not ($bundledDistributions | Where-Object { $_.StartsWith($expected) })) {
        throw "Bundled dependency metadata is missing: $expected"
    }
}

$auditPath = Join-Path $evidenceRoot "REPOSITORY_AUDIT.json"
& (Get-Command uv -ErrorAction Stop).Source run python scripts/audit_release_tree.py --json-output $auditPath | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Repository release audit failed during C-lite."
}
$workflowRoot = Join-Path $evidenceRoot "representative-workflows"
& (Get-Command uv -ErrorAction Stop).Source run python scripts/run_representative_workflows.py --output-root $workflowRoot | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Representative CSV/TSV/XLSX workflows failed during C-lite."
}
$workflowEvidencePath = Join-Path $workflowRoot "REPRESENTATIVE_WORKFLOWS.json"
$workflowEvidence = Get-Content -LiteralPath $workflowEvidencePath -Raw | ConvertFrom-Json
if ($workflowEvidence.status -ne "passed" -or $workflowEvidence.workflows.Count -ne 3) {
    throw "Representative workflow evidence is incomplete."
}

& (Join-Path $repository "scripts/verify_installer.ps1") -OutputRoot $resolvedOutput

$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$sourceHash = (Get-FileHash -LiteralPath $sourceArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$installerHash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (
    $archiveHash -ne $manifest.archive.sha256 -or
    $sourceHash -ne $manifest.sourceArchive.sha256 -or
    $installerHash -ne $manifest.installer.sha256
) {
    throw "One or more release-candidate hashes do not match BUILD_MANIFEST.json."
}
$executableSignature = Get-AuthenticodeSignature -LiteralPath $executable
$installerSignature = Get-AuthenticodeSignature -LiteralPath $installerPath
$os = Get-CimInstance Win32_OperatingSystem
$report = [ordered]@{
    status = "passed"
    gate = "Combination C local C-lite"
    limitation = "Build-host isolation only; a separate clean Windows host remains the final distribution gate."
    product = $manifest.product
    version = $manifest.version
    verifiedAtUtc = [DateTime]::UtcNow.ToString("o")
    host = [ordered]@{
        os = $os.Caption
        version = $os.Version
        build = $os.BuildNumber
    }
    isolation = [ordered]@{
        freshArchiveExtraction = $true
        pathContainsSpaces = $true
        minimalPath = $true
        pythonEnvironmentRemoved = $true
        disposableDataDirectory = $true
        disposableLogDirectory = $true
        normalUserLogUnchanged = $true
    }
    workflows = [ordered]@{
        formats = @($workflowEvidence.workflows | ForEach-Object { $_.source_format })
        allPassed = $true
        evidenceSha256 = (Get-FileHash -LiteralPath $workflowEvidencePath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    repositoryAudit = [ordered]@{
        status = (Get-Content -LiteralPath $auditPath -Raw | ConvertFrom-Json).status
        sha256 = (Get-FileHash -LiteralPath $auditPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    bundledDistributions = $bundledDistributions
    artifacts = [ordered]@{
        portableZipSha256 = $archiveHash
        sourceZipSha256 = $sourceHash
        installerSha256 = $installerHash
        executableSignature = $executableSignature.Status.ToString()
        installerSignature = $installerSignature.Status.ToString()
    }
    installer = [ordered]@{
        currentUserNoAdmin = $true
        silentInstall = $true
        installedAppSmoke = $true
        registrationReadback = $true
        silentUninstall = $true
        cleanup = $true
    }
    logs = [ordered]@{
        isolatedLogSha256 = (Get-FileHash -LiteralPath $isolatedLog -Algorithm SHA256).Hash.ToLowerInvariant()
        containsDatasetRows = $false
    }
}
$reportPath = Join-Path $resolvedOutput "LOCAL_C_LITE.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding utf8NoBOM
$reportHash = (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | Add-Member -NotePropertyName localAcceptance -NotePropertyValue ([ordered]@{
    name = "LOCAL_C_LITE.json"
    sha256 = $reportHash
    status = "passed"
    cleanHostEquivalent = $false
}) -Force
$manifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

$checksumsPath = Join-Path $resolvedOutput "SHA256SUMS.txt"
$checksumLines = @(
    Get-Content -LiteralPath $checksumsPath | Where-Object { $_ -notmatch ' \*LOCAL_C_LITE\.json$' }
    "$reportHash *LOCAL_C_LITE.json"
)
[IO.File]::WriteAllLines($checksumsPath, $checksumLines)

foreach ($line in Get-Content -LiteralPath $checksumsPath) {
    if ($line -notmatch '^([0-9a-f]{64}) \*(.+)$') {
        throw "Invalid SHA256SUMS line: $line"
    }
    $expectedHash = $Matches[1]
    $relative = $Matches[2].Replace("/", [IO.Path]::DirectorySeparatorChar)
    $candidate = Join-Path $resolvedOutput $relative
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Checksummed file is missing: $candidate"
    }
    $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "Checksum mismatch: $relative"
    }
}

Write-Host "Combination C local C-lite verification passed."
Write-Host "Evidence: $reportPath"
Write-Host "Limitation: separate clean-Windows verification remains pending."
