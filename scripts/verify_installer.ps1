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
    throw "Installer verification is restricted to the repository packaging directory."
}

& (Join-Path $repository "scripts/verify_release.ps1") -OutputRoot $resolvedOutput
$manifest = Get-Content -LiteralPath (Join-Path $resolvedOutput "BUILD_MANIFEST.json") -Raw | ConvertFrom-Json
if ($null -eq $manifest.installer) {
    throw "The build manifest has no installer entry."
}
$installer = [IO.Path]::GetFullPath((Join-Path $resolvedOutput $manifest.installer.name))
if (-not $installer.StartsWith($packagingPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "The manifest installer path escapes the packaging directory."
}
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Installer is missing: $installer"
}
$actualHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $manifest.installer.sha256) {
    throw "Installer hash does not match BUILD_MANIFEST.json."
}
$versionInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($installer)
if ($versionInfo.ProductName -ne "GDTT" -or $versionInfo.ProductVersion -ne $manifest.version) {
    throw "Installer version metadata is not canonical."
}

$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $packagingRoot "temp"))
$installRoot = [IO.Path]::GetFullPath((Join-Path $temporaryRoot "installer-smoke"))
$temporaryPrefix = $temporaryRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $installRoot.StartsWith($temporaryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe installer smoke target: $installRoot"
}
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\GDTT"
$applicationRegistryPath = "HKCU:\Software\Gadash (Akila DJ)\GDTT"
$startMenuDirectory = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\GDTT"
$smokeTrace = Join-Path $temporaryRoot "installer-smoke.log"
$profileRoot = Join-Path $temporaryRoot "installer-profile"
$verificationError = $null

try {
    if (Test-Path -LiteralPath $installRoot) {
        Remove-Item -LiteralPath $installRoot -Recurse -Force
    }
    $installInfo = [Diagnostics.ProcessStartInfo]::new()
    $installInfo.FileName = $installer
    $installInfo.UseShellExecute = $false
    $installInfo.CreateNoWindow = $true
    $installInfo.ArgumentList.Add("/S")
    $installInfo.ArgumentList.Add("/D=$installRoot")
    $installProcess = [Diagnostics.Process]::Start($installInfo)
    if ($null -eq $installProcess -or -not $installProcess.WaitForExit(120000) -or $installProcess.ExitCode -ne 0) {
        throw "Silent installer execution failed or timed out."
    }

    $installedExecutable = Join-Path $installRoot "GDTT.exe"
    $uninstaller = Join-Path $installRoot "Uninstall.exe"
    $startMenuShortcut = Join-Path $startMenuDirectory "GDTT.lnk"
    foreach ($required in @($installedExecutable, $uninstaller, $startMenuShortcut)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Installed file or shortcut is missing: $required"
        }
    }
    if (-not (Test-Path -LiteralPath $registryPath)) {
        throw "The current-user uninstall registry entry is missing."
    }
    $uninstallRegistration = Get-ItemProperty -LiteralPath $registryPath
    if (
        $uninstallRegistration.UninstallString -notlike '*Uninstall.exe*' -or
        $uninstallRegistration.QuietUninstallString -notlike '*Uninstall.exe* /S'
    ) {
        throw "The current-user uninstall commands are invalid."
    }

    if (Test-Path -LiteralPath $smokeTrace) {
        Remove-Item -LiteralPath $smokeTrace -Force
    }
    if (Test-Path -LiteralPath $profileRoot) {
        Remove-Item -LiteralPath $profileRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $profileRoot | Out-Null
    $smokeInfo = [Diagnostics.ProcessStartInfo]::new()
    $smokeInfo.FileName = $installedExecutable
    $smokeInfo.UseShellExecute = $false
    $smokeInfo.CreateNoWindow = $true
    $smokeInfo.Environment["DTT_SMOKE_TRACE"] = $smokeTrace
    $smokeInfo.Environment["DTT_DATA_DIRECTORY"] = (Join-Path $profileRoot "Data")
    $smokeInfo.Environment["DTT_LOG_DIRECTORY"] = (Join-Path $profileRoot "Logs")
    $smokeInfo.ArgumentList.Add("--smoke-test")
    $smokeInfo.ArgumentList.Add("-platform")
    $smokeInfo.ArgumentList.Add("offscreen")
    $smokeProcess = [Diagnostics.Process]::Start($smokeInfo)
    if ($null -eq $smokeProcess -or -not $smokeProcess.WaitForExit(90000) -or $smokeProcess.ExitCode -ne 0) {
        $traceText = if (Test-Path -LiteralPath $smokeTrace) { (Get-Content -LiteralPath $smokeTrace -Raw).Trim() } else { "No smoke trace was written." }
        throw "Installed application smoke failed or timed out. Trace: $traceText"
    }

    $uninstallInfo = [Diagnostics.ProcessStartInfo]::new()
    $uninstallInfo.FileName = $uninstaller
    $uninstallInfo.UseShellExecute = $false
    $uninstallInfo.CreateNoWindow = $true
    $uninstallInfo.ArgumentList.Add("/S")
    $uninstallProcess = [Diagnostics.Process]::Start($uninstallInfo)
    if ($null -eq $uninstallProcess -or -not $uninstallProcess.WaitForExit(120000)) {
        throw "Silent uninstaller execution failed or timed out."
    }
    for ($attempt = 0; $attempt -lt 60 -and (Test-Path -LiteralPath $installRoot); $attempt++) {
        Start-Sleep -Milliseconds 500
    }
    if ((Test-Path -LiteralPath $installRoot) -or (Test-Path -LiteralPath $registryPath) -or (Test-Path -LiteralPath $startMenuShortcut)) {
        throw "Uninstaller did not remove the application, registry entry, and Start Menu shortcut."
    }
}
catch {
    $verificationError = $_
}
finally {
    if (Test-Path -LiteralPath $installRoot) {
        Remove-Item -LiteralPath $installRoot -Recurse -Force
    }
    if (Test-Path -LiteralPath $startMenuDirectory) {
        Remove-Item -LiteralPath $startMenuDirectory -Recurse -Force
    }
    Remove-Item -LiteralPath $registryPath -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $applicationRegistryPath -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $smokeTrace -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $profileRoot) {
        Remove-Item -LiteralPath $profileRoot -Recurse -Force
    }
}

if ($null -ne $verificationError) {
    throw $verificationError
}
Write-Host "Verified GDTT $($manifest.version) current-user NSIS installer."
Write-Host "Silent install, installed-app smoke, Start Menu/uninstall registration, and uninstall cleanup passed."
