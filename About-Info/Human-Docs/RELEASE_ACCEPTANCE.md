# Release Acceptance

GDTT release candidates must pass the local Combination C-lite gate. C-lite deliberately
uses a fresh portable extraction, a minimal runtime PATH, no inherited Python environment,
disposable settings/log directories, synthetic workflows, and a complete installer lifecycle.
It is strong build-host evidence, but it is not the same as a separate clean Windows computer.

For v0.10.1-rc.1, automated GitHub Windows/Linux CI and the Windows release pipeline also passed.
What remains is separate hands-on acceptance with published downloads and actual display scaling,
not an assertion that no independent automated Windows runner has tested the app. The current
EXE/installer are unsigned; hashes are not publisher signatures. Keep Windows security enabled.

## Verify the copied artifacts on another computer

No virtualization, Python, Git, or administrator permission is required for this artifact-only
check.

1. Download the matching release assets from GitHub (or copy the complete local candidate) to
   a suitable Windows x64 computer without GDTT's development environment. Another physical
   computer is enough; no Sandbox, VM, firmware change or operating-system reinstall is needed.
2. Open PowerShell in that directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_CHECKSUMS.ps1 -Directory .
```

3. Confirm that all checksums pass. Do not continue if any file is missing or has a different
   SHA-256.
4. Extract `GDTT-0.10.1-windows-x64-Portable.zip` into a new folder whose path contains a
   space. Launch `GDTT.exe`, open About, and confirm product version 0.10.1,
   license text, OpenAI Codex credit, and dependency versions.
5. Exercise Reformat with a small synthetic CSV selected through the file picker. Confirm the
   timestamp and interval, leave gap filling enabled, select True Null, export CSV plus
   plain/formatted XLSX, and require every post-export verification to pass.
6. Repeat source inspection by dragging and dropping a tab-delimited file or XLSX workbook.
   No operational or confidential monitoring data is needed.
7. Select two structurally identical synthetic files together. Confirm that GDTT identifies the
   first as the reference, exports each source with a collision-safe source-derived name, and
   displays a separate reopen-verification result for each file.
8. Add one file with a changed ordered schema or text delimiter. Confirm that GDTT explains the
   incompatibility and blocks configuration. After a successful export, use **Process more
   similar files** and confirm that the matching workflow returns to file selection.
9. Run `GDTT-0.10.1-windows-x64-installer.exe`. Confirm the license page, current-user
   installation, Start Menu entry, application launch, and About information. Uninstall it and
   confirm the application and Start Menu entry are removed.
10. Capture Light and Dark screenshots and record Windows edition/version/build. Note any
   SmartScreen or antivirus message exactly; the current release candidate is intentionally
   unsigned until the owner selects signing.
11. Exercise the ISO UTC/offset and compact formats, optional gap filling, averaging completeness,
    and all Split / Join operations. Check filenames and values, not only whether the app opens.
12. Test actual display scaling, resized field panels, font-size controls and theme palettes.

The small fixture `tests/fixtures/monitoring_gap.csv` inside the source archive is synthetic and
may be used for the manual workflow. It contains no operational measurements.

## Rebuild the complete candidate on another computer

This stronger check requires internet access for the locked Python environment and the
hash-verified NSIS bootstrap, but it does not require Git metadata.

1. Extract `GDTT-0.10.1-source.zip`.
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
3. Open PowerShell in the extracted source root and run:

```powershell
.\scripts\build_release_candidate.ps1
```

The command runs formatting, lint, strict typing, all automated tests, repository hygiene,
representative CSV/TSV/XLSX workflows, portable packaging, installer verification, source
archiving, local C-lite isolation, and checksum verification. Return these files to the owner:

- `BUILD_MANIFEST.json`
- `SHA256SUMS.txt`
- `LOCAL_C_LITE.json`
- `RELEASE_CANDIDATE.md`
- Light and Dark screenshots
- the PowerShell success output and Windows version/build

## Acceptance boundary

Local C-lite is complete. Final public-release acceptance still needs one artifact-only or full
rebuild pass on a separate Windows computer, an owner decision about code signing, owner review
of the artifacts, and explicit authorization for Git publication.
