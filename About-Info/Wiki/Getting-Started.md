# Getting started

## Summary

Download the Windows x64 portable ZIP or installer from the official release. No Python, Git, cloud account or hardware virtualization is required to use these binaries. Start with a copy of a small, non-sensitive dataset.

## 1. Choose the download

Open [GDTT v0.10.2-rc.1 Assets](https://github.com/GGadash/GDTT/releases/tag/v0.10.2-rc.1).

| File | Use |
| --- | --- |
| `GDTT-0.10.2-windows-x64-Portable.zip` | Run without installing. Extract the complete folder, not just the EXE. |
| `GDTT-0.10.2-windows-x64-installer.exe` | Install for the current Windows user, with Start Menu/uninstall entries. |
| `GDTT-0.10.2-source.zip` | Developers or people rebuilding the app; not the ready-to-run download. |
| `SHA256SUMS.txt` and `VERIFY_CHECKSUMS.ps1` | Integrity checks for the matching release files. |
| `BUILD_MANIFEST.json`, `LOCAL_C_LITE.json`, `RELEASE_CANDIDATE.md` | Build provenance, acceptance results and remaining limitations. |

Use the verifier/checksums from the **same release** as the files. Do not mix locally built and GitHub-built assets; build timestamps can change hashes.

## 2. Check the download

For an individual file, PowerShell can calculate a hash without launching the app:

```powershell
Get-FileHash -Algorithm SHA256 .\GDTT-0.10.2-windows-x64-Portable.zip
```

Compare it with the corresponding entry in the official `SHA256SUMS.txt`. For the complete flat set of release assets, review the supplied verifier and follow [release acceptance instructions](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/RELEASE_ACCEPTANCE.md). A checksum detects a changed file; it is not a trusted publisher signature or proof that software is harmless.

## 3. Start the app

**Portable:** extract the ZIP to a writable folder, then run `GDTT/GDTT.exe`. Keep the supporting files beside it. User preferences and logs still use the per-user locations described in [Files and folders](https://github.com/GGadash/GDTT/wiki/Files-and-Folders); “portable” does not mean every file stays beside the EXE.

**Installer:** run the installer, review the license, choose the destination and optional desktop shortcut, then start GDTT from the Start Menu. Installation is per user and normally needs no administrator permission. Uninstall preserves settings/log data.

**Security warning:** these files are unsigned. Windows may display an unknown-publisher/SmartScreen warning or block execution under local policy. Keep security protections enabled; verify the official source and consult your administrator where required. See [Release status and safety](https://github.com/GGadash/GDTT/wiki/Release-Status-and-Safety).

## 4. Try a small first job

1. Choose **Reformat / Transform**.
2. Browse for, or drag in, a small CSV/TSV/TXT/XLSX file. Choose a worksheet for XLSX.
3. Inspect the detected fields, formats, header and missing markers.
4. Open **Configure fields**. Leave only the intended fields selected and choose explicit formats.
5. For a formatting-only trial, deselect **Insert Missing Time Rows**. Otherwise confirm its timestamp and interval.
6. Review the proposed output and configuration, then export to a new folder.
7. Check the reopened export's verification results and inspect the output yourself.

The repository's [monitoring_gap.csv](https://github.com/GGadash/GDTT/blob/main/tests/fixtures/monitoring_gap.csv) is synthetic test data, not operational measurements.

Next: [Reformat and batch](https://github.com/GGadash/GDTT/wiki/Reformat-and-Batch) or [choose another workflow](https://github.com/GGadash/GDTT/wiki/Home).
