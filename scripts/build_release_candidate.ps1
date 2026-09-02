# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))

Push-Location $repository
try {
    & (Join-Path $repository "scripts/build_windows.ps1")
    & (Join-Path $repository "scripts/bootstrap_nsis.ps1")
    & (Join-Path $repository "scripts/build_installer.ps1")
    & (Join-Path $repository "scripts/build_source_archive.ps1")
    & (Join-Path $repository "scripts/verify_c_lite.ps1")
    & (Join-Path $repository "scripts/finalize_release_candidate.ps1")
}
finally {
    Pop-Location
}
