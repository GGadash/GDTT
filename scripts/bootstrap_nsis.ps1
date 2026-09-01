# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$version = "3.12"
$expectedSha256 = "56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f"
$downloadUrl = "https://downloads.sourceforge.net/project/nsis/NSIS%203/$version/nsis-$version.zip?download"
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$packagingRoot = [IO.Path]::GetFullPath((Join-Path $repository "packaging"))
$toolsRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "tools"))
$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "temp"))
$archive = [IO.Path]::GetFullPath((Join-Path $temporaryRoot "nsis-$version.zip"))
$target = [IO.Path]::GetFullPath((Join-Path $toolsRoot "nsis-$version"))
$compiler = Join-Path $target "makensis.exe"
$packagingPrefix = $packagingRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
foreach ($path in @($toolsRoot, $temporaryRoot, $archive, $target, $compiler)) {
    if (-not $path.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing an NSIS bootstrap operation outside packaging/: $path"
    }
}

if (Test-Path -LiteralPath $compiler -PathType Leaf) {
    $installedVersion = (& $compiler /VERSION).TrimStart('v')
    if ($installedVersion -eq $version) {
        Write-Host "Workspace NSIS $version is ready: $compiler"
        exit 0
    }
}

New-Item -ItemType Directory -Path $toolsRoot,$temporaryRoot -Force | Out-Null
$curl = (Get-Command curl.exe -ErrorAction Stop).Source
& $curl --fail --location --silent --show-error --output $archive $downloadUrl
if ($LASTEXITCODE -ne 0) {
    throw "The NSIS archive download failed with curl exit code $LASTEXITCODE."
}
$actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedSha256) {
    Remove-Item -LiteralPath $archive -Force
    throw "NSIS archive SHA-256 verification failed."
}
if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}
Expand-Archive -LiteralPath $archive -DestinationPath $toolsRoot -Force
Remove-Item -LiteralPath $archive -Force
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) {
    throw "The verified NSIS archive did not contain the expected compiler: $compiler"
}
$installedVersion = (& $compiler /VERSION).TrimStart('v')
if ($installedVersion -ne $version) {
    throw "Unexpected NSIS compiler version: $installedVersion"
}
Write-Host "Workspace NSIS $version is ready: $compiler"
