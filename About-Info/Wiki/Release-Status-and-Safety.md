# Release status and safety

## Summary

**v0.10.2-rc.1 is an unsigned pre-release, not a fully accepted stable release.** Automated tests and packaging checks passed. Separate hands-on testing on a normal clean Windows computer, actual-DPI review and a signing decision remain pending.

Status reviewed **2026-09-17**. Read the evidence attached to the exact release you download.

## What passed for 0.10.2 RC1

| Check | Evidence/status |
| --- | --- |
| Automated tests | 226 passed |
| Formatting, lint and strict typing | Ruff and mypy passed |
| Windows/Linux CI | [Tagged CI](https://github.com/GGadash/GDTT/actions/runs/35235309166) passed |
| Portable packaging and installer lifecycle | [Windows build/release](https://github.com/GGadash/GDTT/actions/runs/35235309343) passed |
| Build-host C-lite | Fresh extraction, limited environment, isolated settings/logs, representative CSV/TSV/XLSX workflows and installer cleanup passed |
| Published files | Eight independently downloaded GitHub asset digests matched; six checksum entries passed |
| Manual clean-Windows acceptance | **Pending** |
| Trusted code signing | **Not applied** |
| Actual monitor/DPI owner acceptance | **Pending** |

Release source tag: `v0.10.2-rc.1` at `675f6647275b4921b01fc9b86b4e5bb9860e8404`. Later documentation commits do not change the tagged binaries. [Release downloads and evidence](https://github.com/GGadash/GDTT/releases/tag/v0.10.2-rc.1).

## What unsigned means

The EXE and installer have no trusted publisher code-signing signature. Windows may show unknown-publisher/SmartScreen warnings or enforce a block under local policy. Hashes identify exact bytes; they do not establish publisher identity or prove the absence of bugs/malware.

Keep Windows security enabled. Do not distribute a self-signed certificate as if it were universally trusted. If signing is adopted, verify and timestamp signatures before regenerating archives and checksums. Even trusted signatures do not automatically remove every reputation warning. [Microsoft's explanation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

## What clean-Windows testing means

This is **not** a claim that there has been no independent automated Windows run: GitHub Windows builds and tests did run. The remaining gate is a hands-on pass with published downloads on a normal Windows computer without GDTT's development setup.

Another suitable physical computer is enough. Windows Sandbox, VirtualBox, hardware virtualization, Python and Git are not required for artifact-only testing. A new user account on the development computer is useful isolation, but not equivalent to a separate clean computer.

1. Download the matching release assets and verify hashes.
2. Extract the entire portable folder into a path containing spaces and launch it.
3. Exercise browse/drag-drop, compatible/incompatible batches and all three workflows with synthetic data.
4. Check ISO UTC/offset output, previews, nulls, CSV and both Excel outputs.
5. Test the installer, Start Menu entry, app launch and uninstall.
6. Check Light/Dark, chosen colors, font sizing and real display scaling.
7. Record Windows version/build, warnings, screenshots and expected versus actual results.

Follow the [full acceptance checklist](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/RELEASE_ACCEPTANCE.md). Keep confidential datasets out of public evidence.

## Data-use and warranty boundaries

GDTT helps make transformations explicit and verifiable; it does not certify regulatory compliance or the scientific validity of your chosen rules. Confirm units, instrument metadata, timestamp roles, completeness standards and outputs independently before consequential use.

Back up inputs. Logs/reports may contain names and processing metadata; review before sharing. Temporary spill files can contain measurements and are private local processing data. Local operation is not a guarantee against every disclosure or operating-system failure.

The project is provided **as is**, without warranty, under its [license](https://github.com/GGadash/GDTT/wiki/License-Credits-and-Support). Third-party licenses remain separate. No signature, checksum, passing test or AI-assisted development claim replaces your own acceptance review.
