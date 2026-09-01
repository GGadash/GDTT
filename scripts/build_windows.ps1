# Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "The GDTT Windows package must be built on Windows."
}

$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$packagingRoot = [IO.Path]::GetFullPath((Join-Path $repository "packaging"))
$outputRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "output"))
$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "temp"))
$repositoryPrefix = $repository.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

function Assert-WorkspacePath {
    param([Parameter(Mandatory)][string]$Path)
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing a packaging operation outside the repository: $resolved"
    }
}

function Get-HermeticPackagingPath {
    $systemDirectory = [IO.Path]::GetFullPath([Environment]::SystemDirectory)
    $retained = foreach ($entry in ($env:Path -split [IO.Path]::PathSeparator)) {
        $trimmed = $entry.Trim().Trim('"')
        if (-not $trimmed) {
            continue
        }
        try {
            $resolvedEntry = [IO.Path]::GetFullPath($trimmed)
        }
        catch {
            $trimmed
            continue
        }
        $externalIcu = Join-Path $resolvedEntry "icuuc.dll"
        if (
            (Test-Path -LiteralPath $externalIcu -PathType Leaf) -and
            -not $resolvedEntry.Equals($systemDirectory, [StringComparison]::OrdinalIgnoreCase)
        ) {
            Write-Host "Excluding external ICU directory from the PyInstaller PATH: $resolvedEntry"
            continue
        }
        $trimmed
    }
    return $retained -join [IO.Path]::PathSeparator
}

foreach ($generatedRoot in @($outputRoot, $temporaryRoot)) {
    Assert-WorkspacePath -Path $generatedRoot
    if (Test-Path -LiteralPath $generatedRoot) {
        Remove-Item -LiteralPath $generatedRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $generatedRoot | Out-Null
}

Push-Location $repository
try {
    $uv = (Get-Command uv -ErrorAction Stop).Source
    & $uv sync --locked --extra dev --extra packaging
    if (-not $SkipTests) {
        & (Join-Path $repository "scripts/test.ps1")
    }
    & $uv run python scripts/generate_icons.py
    & $uv run python scripts/generate_windows_version.py --output packaging/temp/windows_version_info.txt
    $originalPath = $env:Path
    try {
        $env:Path = Get-HermeticPackagingPath
        & $uv run pyinstaller --noconfirm --clean --distpath packaging/output --workpath packaging/temp packaging/data_transform_tool.spec
    }
    finally {
        $env:Path = $originalPath
    }

    $version = (& $uv run python -c "from data_transform_tool import __version__; print(__version__)").Trim()
    $bundle = Join-Path $outputRoot "GDTT"
    $executable = Join-Path $bundle "GDTT.exe"
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "PyInstaller did not create the expected executable: $executable"
    }

    $archiveName = "GDTT-$version-windows-x64.zip"
    $archive = Join-Path $outputRoot $archiveName
    Compress-Archive -LiteralPath $bundle -DestinationPath $archive -CompressionLevel Optimal

    $executableHash = (Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash.ToLowerInvariant()
    $archiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    # SHA256SUMS is a self-contained public-release checksum set. The unpacked executable
    # remains integrity-recorded in BUILD_MANIFEST.json and is verified before archiving.
    $checksumLines = @("$archiveHash *$archiveName")
    [IO.File]::WriteAllLines((Join-Path $outputRoot "SHA256SUMS.txt"), $checksumLines)

    $manifest = [ordered]@{
        product = "GDTT"
        description = "GDTT — Data Transform Tool by Gadash (Akila DJ)"
        version = $version
        platform = "windows-x64"
        packageType = "PyInstaller onedir"
        python = (& $uv run python -c "import platform; print(platform.python_version())").Trim()
        pyinstaller = (& $uv run pyinstaller --version).Trim()
        builtAtUtc = [DateTime]::UtcNow.ToString("o")
        archive = [ordered]@{ name = $archiveName; sha256 = $archiveHash }
        executable = [ordered]@{
            name = "GDTT/GDTT.exe"
            sha256 = $executableHash
        }
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outputRoot "BUILD_MANIFEST.json") -Encoding utf8NoBOM

    & (Join-Path $repository "scripts/verify_release.ps1") -OutputRoot $outputRoot
    Write-Host "Windows package ready: $archive"
    Write-Host "Checksums: $(Join-Path $outputRoot 'SHA256SUMS.txt')"
}
finally {
    Pop-Location
}
