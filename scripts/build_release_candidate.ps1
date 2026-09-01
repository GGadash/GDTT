# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$outputRoot = [IO.Path]::GetFullPath((Join-Path $repository "packaging/output"))
$checksumsPath = Join-Path $outputRoot "SHA256SUMS.txt"
$manifestPath = Join-Path $outputRoot "BUILD_MANIFEST.json"

Push-Location $repository
try {
    & (Join-Path $repository "scripts/build_windows.ps1")
    & (Join-Path $repository "scripts/bootstrap_nsis.ps1")
    & (Join-Path $repository "scripts/build_installer.ps1")
    & (Join-Path $repository "scripts/build_source_archive.ps1")
    & (Join-Path $repository "scripts/verify_c_lite.ps1")

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $portableVerifierPath = Join-Path $outputRoot "VERIFY_CHECKSUMS.ps1"
    Copy-Item -LiteralPath (Join-Path $repository "scripts/verify_artifact_checksums.ps1") -Destination $portableVerifierPath
    $portableVerifierHash = (Get-FileHash -LiteralPath $portableVerifierPath -Algorithm SHA256).Hash.ToLowerInvariant()
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
- [ ] Push a reviewed `v*` tag to authorize automatic GitHub Release publishing

Hyphenated tags such as `v0.8.0-rc.1` publish as pre-releases. Stable tags such as `v0.8.0`
publish as normal releases. A source push or manually dispatched package build never publishes.

This is a locally isolated release candidate, not a final public release. Windows Sandbox was
not used because it is unstable on the current host.
"@
    $checklistPath = Join-Path $outputRoot "RELEASE_CANDIDATE.md"
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
            $_ -notmatch ' \*(RELEASE_CANDIDATE\.md|VERIFY_CHECKSUMS\.ps1)$'
        }
        "$checklistHash *RELEASE_CANDIDATE.md"
        "$portableVerifierHash *VERIFY_CHECKSUMS.ps1"
    )
    [IO.File]::WriteAllLines($checksumsPath, $checksumLines)

    foreach ($line in Get-Content -LiteralPath $checksumsPath) {
        if ($line -notmatch '^([0-9a-f]{64}) \*(.+)$') {
            throw "Invalid SHA256SUMS line: $line"
        }
        $candidate = Join-Path $outputRoot $Matches[2].Replace("/", [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Release-candidate file is missing: $candidate"
        }
        $actual = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $Matches[1]) {
            throw "Release-candidate checksum failed: $candidate"
        }
    }
    & $portableVerifierPath -Directory $outputRoot
    Write-Host "GDTT $($manifest.version) local release candidate passed."
    Write-Host "Checklist: $checklistPath"
}
finally {
    Pop-Location
}
