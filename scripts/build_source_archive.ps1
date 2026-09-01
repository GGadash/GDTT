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
$repositoryPrefix = $repository.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $resolvedOutput.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Source archive output is restricted to the repository packaging directory."
}

$manifestPath = Join-Path $resolvedOutput "BUILD_MANIFEST.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Build the Windows package before creating the source archive."
}
$auditPath = Join-Path $packagingRoot "temp/repository-audit.json"
$sourceListPath = Join-Path $packagingRoot "temp/release-source-files.txt"
& (Get-Command uv -ErrorAction Stop).Source run python scripts/audit_release_tree.py --json-output $auditPath --list-output $sourceListPath
if ($LASTEXITCODE -ne 0) {
    throw "Repository release-hygiene audit failed."
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$version = [string]$manifest.version
$archiveName = "GDTT-$version-source.zip"
$archivePath = Join-Path $resolvedOutput $archiveName
$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "temp/source-archive"))
$stagingRoot = [IO.Path]::GetFullPath((Join-Path $temporaryRoot "GDTT-$version-source"))
foreach ($path in @($temporaryRoot, $stagingRoot, $archivePath)) {
    if (-not $path.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe source archive path: $path"
    }
}
if (Test-Path -LiteralPath $temporaryRoot) {
    Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
}
if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}
New-Item -ItemType Directory -Path $stagingRoot | Out-Null

$sourceFiles = @(Get-Content -LiteralPath $sourceListPath | Where-Object { $_ })
if (-not $sourceFiles) {
    throw "The release audit did not return a prospective source file set."
}
foreach ($relative in $sourceFiles) {
    $source = [IO.Path]::GetFullPath((Join-Path $repository $relative))
    if (-not $source.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Source path escapes the repository: $source"
    }
    $destination = [IO.Path]::GetFullPath((Join-Path $stagingRoot $relative))
    $stagingPrefix = $stagingRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $destination.StartsWith($stagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Source archive destination escapes staging: $destination"
    }
    $parent = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $destination
}

Compress-Archive -LiteralPath $stagingRoot -DestinationPath $archivePath -CompressionLevel Optimal
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | Add-Member -NotePropertyName sourceArchive -NotePropertyValue ([ordered]@{
    name = $archiveName
    sha256 = $archiveHash
    fileCount = $sourceFiles.Count
}) -Force
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

$checksumsPath = Join-Path $resolvedOutput "SHA256SUMS.txt"
$checksumLines = @(
    Get-Content -LiteralPath $checksumsPath | Where-Object { $_ -notmatch '-source\.zip$' }
    "$archiveHash *$archiveName"
)
[IO.File]::WriteAllLines($checksumsPath, $checksumLines)

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $unsafe = @(
        $archive.Entries | Where-Object {
            $_.FullName -match '(^|/)(\.git|\.venv|__pycache__|packaging/(output|temp|tools)|logs|exports)(/|$)'
        }
    )
    if ($unsafe) {
        throw "Source archive contains ignored runtime, Git, environment, or build content."
    }
    if ($archive.Entries.Count -lt $sourceFiles.Count) {
        throw "Source archive entry count is unexpectedly smaller than the source file set."
    }
}
finally {
    $archive.Dispose()
}

Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
Write-Host "Source archive ready: $archivePath"
Write-Host "Source files: $($sourceFiles.Count); SHA-256: $archiveHash"
