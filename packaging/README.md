# Windows Packaging

Combination B provides a maintained PyInstaller `onedir` specification, canonical application
icon, generated Windows version metadata, local build/verification scripts, SHA-256 checksums,
and a Windows build workflow. Combination D wraps the verified bundle in a current-user NSIS
installer. Generated `output/`, `temp/`, and workspace-local `tools/` directories remain ignored.

Build and verify locally on Windows:

```powershell
./scripts/build_windows.ps1
```

Then bootstrap the pinned, hash-verified NSIS 3.12 portable compiler and build the installer:

```powershell
./scripts/bootstrap_nsis.ps1
./scripts/build_installer.ps1
```

Or build the complete local release candidate in one command:

```powershell
./scripts/build_release_candidate.ps1
```

The portable archive, current-user installer, `BUILD_MANIFEST.json`, and `SHA256SUMS.txt` are
written under `packaging/output/`. The release-candidate command also adds the audited source
archive, C-lite JSON evidence, acceptance checklist, and portable checksum verifier. The installer displays the project license, installs under the
current user's local Programs directory, registers Start Menu and uninstall entries, offers an
optional desktop shortcut, and preserves settings/log data on uninstall. Verification performs a
silent temporary install, installed-app offscreen smoke, registration readback, silent uninstall,
and cleanup check. Combination A is integrated in the current artifacts. They remain development
artifacts until Combination C passes on a separate clean Windows environment.

The PyInstaller step removes non-system PATH directories exposing a private `icuuc.dll` while it
freezes the app, then restores PATH. This prevents unrelated developer tools from shadowing the
Windows ICU implementation used by Qt.

## Combination C clean-Windows gate

Use a separate clean Windows 11/10 x64 host or a disposable VM snapshot with no prior Data
Transform Tool installation. Install `uv`, transfer a clean source tree, and run:

```powershell
./scripts/build_windows.ps1
./scripts/bootstrap_nsis.ps1
./scripts/build_installer.ps1
```

Record the OS build, Python/PyInstaller/NSIS versions, `BUILD_MANIFEST.json`,
`SHA256SUMS.txt`, test output, portable smoke result, installer registration, installed-app
smoke, uninstall cleanup, and Light/Dark screenshots. Confirm the executable and installer
signature state explicitly; do not claim signing without the owner's selected certificate.

Windows Sandbox is acceptable as the disposable host only when virtualization is enabled in
firmware and the Windows Sandbox optional feature is installed. Microsoft documents the
prerequisites and setup in
[Install Windows Sandbox](https://learn.microsoft.com/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install).
Closing Sandbox destroys its state, so copy the evidence to an explicitly mapped result folder
before closing it.

Windows Sandbox is optional. Artifact-only and full source-rebuild instructions for another
physical or cloud Windows computer are in
`About-Info/Human-Docs/RELEASE_ACCEPTANCE.md`; neither route requires hardware virtualization
on the current computer.

## Automatic GitHub Releases

The Windows workflow publishes only for an explicitly pushed `v*` tag. It first completes the
portable package, installer, source archive, and C-lite gates; downloads that exact verified
Actions artifact into a separate least-privilege release job; validates the tag's base version
against `BUILD_MANIFEST.json`; and verifies the self-contained release checksums before calling
GitHub CLI.

- `v0.8.0-rc.1` creates a pre-release and does not mark it Latest.
- `v0.8.0` creates a normal release.
- Branch pushes, pull requests, and manual workflow runs build temporary Actions artifacts but
  never publish a Release.
- An existing Release is left unchanged on a workflow rerun.

The release job alone receives `contents: write`; the Windows build job and ordinary CI retain
read-only repository permissions. Do not push a release tag until the owner has reviewed the
candidate and explicitly accepted the applicable external/signing gates.
