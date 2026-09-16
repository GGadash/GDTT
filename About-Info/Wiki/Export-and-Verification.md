# Export and verification

## Summary

Inspect the full-file result before exporting, then read the verification outcome for every output. Preview success alone is not proof that a complete file or batch will export correctly.

## Full-file review

After configuration review, GDTT rereads complete Reformat/Averaging sources and executes the plan through private spill-backed batches. Compare input/output counts and first/middle/last records. Split / Join exports its reviewed complete-source snapshot.

Keep source backups. Export to a new folder whenever possible. Reformat/Averaging replaces an existing name only with explicit overwrite permission; Split / Join uses a new run folder.

## Formats and names

Select any combination of CSV, plain XLSX and formatted XLSX. Reformat/Averaging suggestions include source/time details and `RF` or `AVG`; plain/formatted Excel adds `P` or `F`. Batch names are source-derived and collision-safe. Split / Join uses operation-specific suffixes described in [its guide](https://github.com/GGadash/GDTT/wiki/Splitting-and-Joining).

CSV/TSV/TXT are supported input types; do not assume a dedicated TSV output selector exists. Current normal output choices are CSV and Excel. Choose CSV or split outputs when an Excel worksheet would exceed its row limit.

Formatted Excel supports Environmental Technical, Clean Laboratory and Minimal presets, plus font/color/AutoFilter/frozen-header controls. These are independent of the app's interface theme.

## Missing values and reports

Choose True Null, N/A, -999 or a custom sentinel. The writer applies the representation at the boundary; internal missing values remain canonical.

Reformat/Averaging can write transformation information, versioned recipe JSON, a concise summary and a conditional warning/error file. These sidecars are optional and enabled by default. Split / Join writes `SPLIT_JOIN_REPORT.json`.

Reports and recipes are designed not to store measurement rows, but can contain source names, field names and processing metadata. Review them before public sharing.

## What verification checks

The app reopens every data output and checks readability, expected filenames, rows, ordered columns, duplicate Index fields, values/null representation, timestamp boundaries and applicable formatted-sheet structure.

- **Passed:** the implemented checks passed.
- **Passed with Warnings:** inspect the warnings before using the result.
- **Failed:** investigate; do not treat that output as accepted.

In a batch, each source has independent results. One success does not hide another failure. Mechanical verification does not certify your choice of timezone, units, aggregation method or scientific interpretation.

## Templates and cancellation

Use **Save current** and **Manage** for local configuration/style templates. They contain configuration, not measurements. Matching can offer Apply, Review or Ignore; Apply requires exact schema compatibility, while likely matches remain review-only.

Templates support duplicate, rename, import/export and confirmed deletion. Keep backups of useful templates. Imported recipes are configuration to review, not a reason to skip validation.

Cancellable background work removes private workspaces and partial export files during normal cleanup. Atomic same-directory replacement prevents a partial file from masquerading as a finished output. A crash, disk failure or external lock can still require inspection; do not manually remove files while a job is active.

Source: [User guide](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/USER_GUIDE.md).
