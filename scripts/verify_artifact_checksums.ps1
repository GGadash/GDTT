# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param(
    [string]$Directory = "."
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = [IO.Path]::GetFullPath($Directory)
$rootPrefix = $root.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
$checksumsPath = Join-Path $root "SHA256SUMS.txt"
if (-not (Test-Path -LiteralPath $checksumsPath -PathType Leaf)) {
    throw "SHA256SUMS.txt is missing from $root."
}

$verified = 0
foreach ($line in Get-Content -LiteralPath $checksumsPath) {
    if ($line -notmatch '^([0-9a-f]{64}) \*(.+)$') {
        throw "Invalid SHA256SUMS line: $line"
    }
    $expected = $Matches[1]
    $relative = $Matches[2].Replace("/", [IO.Path]::DirectorySeparatorChar)
    $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $target.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Checksummed path escapes the artifact directory: $relative"
    }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Checksummed artifact is missing: $relative"
    }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "SHA-256 mismatch: $relative"
    }
    $verified += 1
}

Write-Host "Verified $verified GDTT release-candidate checksums."
