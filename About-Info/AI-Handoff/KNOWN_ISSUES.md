# Known Issues

## KI-001 — Future modes remain outside the current scope

Reshape/Pivot and AQI are not implemented and have no reserved Home cards. Version 0.9.0 adds
the separate Data Splitter & Joiner. Reformat and Averaging include
working single/multi-file picker and drag/drop inspection, compatibility blocking, configuration,
bounded reference preview, batch/spill full-file review, per-source export/report/reopen
verification, templates, and a Process more similar files continuation path.

## KI-003 — Separate clean-Windows distribution verification remains

The PyInstaller portable package and current-user NSIS installer pass on the Windows build host,
including temporary silent install/application smoke/uninstall. Combination C must repeat build,
install, launch, and uninstall checks in a separate clean Windows environment. Artifacts are also
unsigned until the owner provides a code-signing identity and explicitly selects signing.
The current build host has no Windows Sandbox executable or alternate VM command, reports no
active hypervisor, and reports firmware virtualization disabled; Combination C therefore needs a
firmware/Windows-feature change or another clean Windows host.

Local C-lite now passes fresh extraction, minimal PATH/no inherited Python environment,
disposable settings/log paths, representative CSV/TSV/XLSX workflows, repository hygiene,
dependency inventory, installer lifecycle, source archive, and checksums. This reduces but does
not erase the separate-computer limitation.

## KI-004 — Git sandbox identity warning

The Codex sandbox runs under a different Windows identity than the workspace owner. Codex
uses a command-scoped `safe.directory` option for read-only Git inspection rather than
changing the owner's global Git configuration.

## KI-005 — Reference executor remains eager by design

Phases 3, 4, and 6 retain the immutable row table as the bounded semantic reference executor.
Production Reformat/Averaging, writers, and verification now use batch/spill contracts and no
longer apply the workflow-level 1 GB guard. A confirmed gap grid still blocks above 1,000,000
expected rows. Polars/PyArrow vectorization remains an optional future optimization behind
semantic-parity tests, not a current correctness dependency.
