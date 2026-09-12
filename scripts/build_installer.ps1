# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param(
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "The GDTT installer must be built on Windows."
}

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$packagingRoot = [IO.Path]::GetFullPath((Join-Path $repository "packaging"))
$resolvedOutput = if ($OutputRoot) {
    [IO.Path]::GetFullPath($OutputRoot)
} else {
    [IO.Path]::GetFullPath((Join-Path $packagingRoot "output"))
}
$packagingPrefix = $packagingRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $resolvedOutput.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Installer output is restricted to the repository packaging directory."
}

function Find-MakeNsis {
    $command = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }
    $candidates = @(
        (Join-Path $packagingRoot "tools\nsis-3.12\makensis.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe"),
        (Join-Path $env:ProgramFiles "NSIS\makensis.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\NSIS\makensis.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    throw "NSIS makensis.exe was not found. Run: ./scripts/bootstrap_nsis.ps1"
}

Push-Location $repository
try {
    & (Join-Path $repository "scripts/verify_release.ps1") -OutputRoot $resolvedOutput
    $manifestPath = Join-Path $resolvedOutput "BUILD_MANIFEST.json"
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $version = [string]$manifest.version
    $versionParts = @($version.Split('.'))
    while ($versionParts.Count -lt 4) {
        $versionParts += "0"
    }
    $fileVersion = ($versionParts[0..3] -join ".")
    $bundle = [IO.Path]::GetFullPath((Join-Path $resolvedOutput "GDTT"))
    $installerName = "GDTT-$version-windows-x64-installer.exe"
    $installer = Join-Path $resolvedOutput $installerName
    if (Test-Path -LiteralPath $installer) {
        Remove-Item -LiteralPath $installer -Force
    }

    $makensis = Find-MakeNsis
    $installerScript = Join-Path $packagingRoot "data_transform_tool.nsi"
    & $makensis /V3 "/DAPP_VERSION=$version" "/DAPP_FILE_VERSION=$fileVersion" "/DBUNDLE_DIR=$bundle" "/DOUTPUT_DIR=$resolvedOutput" "/DOUTPUT_NAME=$installerName" $installerScript
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $installer -PathType Leaf)) {
        throw "NSIS did not create the expected installer: $installer"
    }

    $installerHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest | Add-Member -NotePropertyName installer -NotePropertyValue ([ordered]@{
        name = $installerName
        sha256 = $installerHash
        system = "NSIS"
        scope = "current-user"
    }) -Force
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

    $checksumsPath = Join-Path $resolvedOutput "SHA256SUMS.txt"
    $checksumLines = @(
        Get-Content -LiteralPath $checksumsPath | Where-Object { $_ -notmatch '-(setup|installer)\.exe$' }
        "$installerHash *$installerName"
    )
    [IO.File]::WriteAllLines($checksumsPath, $checksumLines)

    & (Join-Path $repository "scripts/verify_installer.ps1") -OutputRoot $resolvedOutput
    Write-Host "Windows installer ready: $installer"
}
finally {
    Pop-Location
}
