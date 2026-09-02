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
    throw "Release-candidate finalization is restricted to the repository packaging directory."
}

$checksumsPath = Join-Path $resolvedOutput "SHA256SUMS.txt"
$manifestPath = Join-Path $resolvedOutput "BUILD_MANIFEST.json"
foreach ($required in @($checksumsPath, $manifestPath, (Join-Path $resolvedOutput "LOCAL_C_LITE.json"))) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Release-candidate prerequisite is missing: $required"
    }
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$portableVerifierPath = Join-Path $resolvedOutput "VERIFY_CHECKSUMS.ps1"
Copy-Item -LiteralPath (Join-Path $repository "scripts/verify_artifact_checksums.ps1") -Destination $portableVerifierPath -Force
$portableVerifierHash = (Get-FileHash -LiteralPath $portableVerifierPath -Algorithm SHA256).Hash.ToLowerInvariant()
$publicationItem = if (
    $env:GITHUB_REF_TYPE -eq "tag" -and
    $env:GITHUB_REF_NAME -like "v*"
) {
    "- [x] Explicit tag $($env:GITHUB_REF_NAME) triggered automatic GitHub Release publishing"
} else {
    "- [ ] Push a reviewed v* tag to authorize automatic GitHub Release publishing"
}
$checklist = @"
# GDTT $($manifest.version) Release Candidate

Generated: $([DateTime]::UtcNow.ToString("o"))

## Passed

- [x] Locked Python 3.13 development environment
- [x] Ruff formatting and lint
- [x] Strict mypy type checking
- [x] Complete automated test suite
- [x] Prospective-source audit for secrets, datasets, local paths, temporary/build files, and metadata
- [x] Synthetic CSV, TSV, and XLSX end-to-end workflows
- [x] CSV, plain XLSX, and formatted XLSX output reopen verification
- [x] Transformation reports, recipes, summaries, warnings, and log privacy checks
- [x] Fresh portable ZIP extraction with minimal PATH and no inherited Python environment
- [x] Disposable application data and log directories; normal user log unchanged
- [x] Bundled runtime dependency metadata inventory
- [x] Current-user installer install, registration, launch, uninstall, and cleanup
- [x] Audited source archive
- [x] BUILD_MANIFEST.json and SHA256SUMS.txt verification
- [x] Project license, third-party notices, product metadata, and OpenAI Codex credit included

## Pending owner/external gates

- [ ] Repeat the release build and installer lifecycle on a separate clean Windows machine
- [ ] Capture final Light and Dark release screenshots on that machine
- [ ] Select a code-signing identity or explicitly approve an unsigned public release
- [ ] Perform owner acceptance of the release-candidate artifacts
$publicationItem

Hyphenated tags such as v0.8.0-rc.1 publish as pre-releases. Stable tags such as v0.8.0 publish
as normal releases. A source push or manually dispatched package build never publishes.

This is a locally isolated release candidate, not a final public release. Windows Sandbox was
not used because it is unstable on the current host.
"@
$checklistPath = Join-Path $resolvedOutput "RELEASE_CANDIDATE.md"
[IO.File]::WriteAllText($checklistPath, $checklist, [Text.UTF8Encoding]::new($false))
$checklistHash = (Get-FileHash -LiteralPath $checklistPath -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | Add-Member -NotePropertyName releaseCandidate -NotePropertyValue ([ordered]@{
    name = "RELEASE_CANDIDATE.md"
    sha256 = $checklistHash
    checksumVerifier = "VERIFY_CHECKSUMS.ps1"
    checksumVerifierSha256 = $portableVerifierHash
    status = "local_acceptance_passed"
    finalCleanWindowsGate = "pending"
    signing = "not_signed"
}) -Force
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
$checksumLines = @(
    Get-Content -LiteralPath $checksumsPath | Where-Object {
        $_ -notmatch ' \*(RELEASE_CANDIDATE\.md|VERIFY_CHECKSUMS\.ps1)$' -and
        $_ -notmatch ' \*.*[/\\]'
    }
    "$checklistHash *RELEASE_CANDIDATE.md"
    "$portableVerifierHash *VERIFY_CHECKSUMS.ps1"
)
[IO.File]::WriteAllLines($checksumsPath, $checksumLines)

& $portableVerifierPath -Directory $resolvedOutput
Write-Host "GDTT $($manifest.version) release candidate finalized."
Write-Host "Checklist: $checklistPath"
