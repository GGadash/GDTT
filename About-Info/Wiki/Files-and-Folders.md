# Files and folders

## Summary

The downloaded application, your exported datasets, per-user settings and the source repository are different locations. Do not put private monitoring data into the public Git repository.

## For application users

| Item | Default location or rule |
| --- | --- |
| Portable executable | Extracted `GDTT/GDTT.exe`, with its adjacent support files |
| Installed application | Destination selected in the current-user installer |
| Input datasets | Wherever you keep them; retain original backups |
| Reformat/Averaging outputs | The export folder you select |
| Split / Join outputs | A uniquely named run subfolder under the selected parent folder |
| Settings | `%LOCALAPPDATA%/Gadash (Akila DJ)/GDTT/settings.json` |
| Recipe templates | `%LOCALAPPDATA%/Gadash (Akila DJ)/GDTT/templates/` |
| Excel styles | `%LOCALAPPDATA%/Gadash (Akila DJ)/GDTT/xlsx-styles/` |
| Logs | `%LOCALAPPDATA%/Gadash (Akila DJ)/GDTT/Logs/data-transform-tool.log` |

`%LOCALAPPDATA%` means the current Windows user's local application-data directory. Paths follow `platformdirs`, and controlled deployments/tests can override data/log roots using `DTT_DATA_DIRECTORY` and `DTT_LOG_DIRECTORY`. Templates/styles then follow the data root.

Logs rotate at roughly 2 MB with three backups. They are designed not to record dataset rows; still inspect filenames, paths and metadata before sharing logs or reports. Uninstall intentionally retains user settings/logs.

## Temporary processing data

Large-file execution uses private temporary disk-backed spill workspaces rather than keeping everything in memory. Temporary processing storage may contain dataset values and must be treated as private.

Normal reset/navigation/cancellation cleans up owned workspaces; export uses temporary files or run folders before finalization. Do not delete active processing folders. Abrupt crashes or operating-system failures can leave residue requiring careful inspection.

## Source repository map

```text
README.md                  Product introduction and download links
LICENSE                    Authoritative project permission/warranty text
THIRD_PARTY_NOTICES.md      Dependency licenses and development credits
CHANGELOG.md               Versioned changes
src/data_transform_tool/   Application source
tests/                     Synthetic fixtures and automated checks
config/                    Versioned configuration assets
scripts/                   Test, audit, build and release commands
packaging/                 PyInstaller/NSIS definitions
About-Info/
  Wiki/                    Reviewed source for this public wiki
  Human-Docs/               Detailed user/release guides
  Data-Processing/          Timestamp, null, gap and aggregation rules
  Architecture/             Design and module map
  Machine-Readable/         Requirements and schemas
  Diagrams/                 Editable Mermaid diagrams
  AI-Handoff/               Current state, decisions and remaining work
.github/                   CI, release workflows and issue templates
```

## Generated and private folders

`packaging/output/` holds locally built binaries and evidence; `packaging/temp/` holds disposable build/verification work; `packaging/tools/` contains local build tooling. `exports/` includes local evidence and recoverable historical archives. These are ignored by Git, along with environments, caches, logs, previews and `data/input`, `data/output`, `data/private`.

Historical local artifacts are not downloadable repository files. Public binaries belong under [GitHub Releases](https://github.com/GGadash/GDTT/releases). Never force-add private datasets or generated installers to the source repository.

Sources: [Storage implementation](https://github.com/GGadash/GDTT/blob/main/src/data_transform_tool/settings/paths.py) · [Repository map](https://github.com/GGadash/GDTT/blob/main/About-Info/README.md) · [Artifact retention](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/ARTIFACT_RETENTION.md).
