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
    throw "Release verification is restricted to the repository packaging directory."
}

$bundle = Join-Path $resolvedOutput "GDTT"
$executable = Join-Path $bundle "GDTT.exe"
$internal = Join-Path $bundle "_internal"
foreach ($required in @(
    $executable,
    (Join-Path $internal "LICENSE"),
    (Join-Path $internal "THIRD_PARTY_NOTICES.md"),
    (Join-Path $internal "data_transform_tool/resources/icons/data-transform-tool.svg")
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Packaged file is missing: $required"
    }
}

$versionInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($executable)
if ($versionInfo.ProductName -ne "GDTT") {
    throw "Unexpected executable product name: $($versionInfo.ProductName)"
}
if (-not $versionInfo.ProductVersion) {
    throw "The executable has no product version metadata."
}

$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $executable
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.ArgumentList.Add("--smoke-test")
$startInfo.ArgumentList.Add("-platform")
$startInfo.ArgumentList.Add("offscreen")
$smokeTrace = Join-Path $packagingRoot "temp/release-smoke.log"
$profileRoot = Join-Path $packagingRoot "temp/release-profile"
if (Test-Path -LiteralPath $smokeTrace) {
    Remove-Item -LiteralPath $smokeTrace -Force
}
if (Test-Path -LiteralPath $profileRoot) {
    Remove-Item -LiteralPath $profileRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $profileRoot | Out-Null
$startInfo.Environment["DTT_SMOKE_TRACE"] = $smokeTrace
$startInfo.Environment["DTT_DATA_DIRECTORY"] = (Join-Path $profileRoot "Data")
$startInfo.Environment["DTT_LOG_DIRECTORY"] = (Join-Path $profileRoot "Logs")
$process = [Diagnostics.Process]::Start($startInfo)
if ($null -eq $process) {
    throw "The packaged executable could not be started."
}
if (-not $process.WaitForExit(90000)) {
    $process.Kill($true)
    $traceText = if (Test-Path -LiteralPath $smokeTrace) {
        (Get-Content -LiteralPath $smokeTrace -Raw).Trim()
    } else {
        "No smoke trace was written."
    }
    throw "The packaged smoke test did not finish within 90 seconds. Trace: $traceText"
}
if ($process.ExitCode -ne 0) {
    $traceText = if (Test-Path -LiteralPath $smokeTrace) {
        (Get-Content -LiteralPath $smokeTrace -Raw).Trim()
    } else {
        "No smoke trace was written."
    }
    throw "The packaged smoke test failed with exit code $($process.ExitCode). Trace: $traceText"
}
if (Test-Path -LiteralPath $smokeTrace) {
    Remove-Item -LiteralPath $smokeTrace -Force
}
if (Test-Path -LiteralPath $profileRoot) {
    Remove-Item -LiteralPath $profileRoot -Recurse -Force
}

$manifestPath = Join-Path $resolvedOutput "BUILD_MANIFEST.json"
$checksumsPath = Join-Path $resolvedOutput "SHA256SUMS.txt"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or -not (Test-Path -LiteralPath $checksumsPath -PathType Leaf)) {
    throw "Build manifest or checksum file is missing."
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$archive = Join-Path $resolvedOutput $manifest.archive.name
if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
    throw "Packaged archive is missing: $archive"
}
$actualArchiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
$actualExecutableHash = (Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualArchiveHash -ne $manifest.archive.sha256 -or $actualExecutableHash -ne $manifest.executable.sha256) {
    throw "Packaged artifact hashes do not match the build manifest."
}

Write-Host "Verified GDTT $($manifest.version) PyInstaller onedir package."
Write-Host "Packaged smoke, metadata, required files, archive, and SHA-256 hashes passed."
