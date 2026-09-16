# Reformat and batch processing

## Summary

Use this workflow to inspect files, select and rename fields, apply explicit transformations, and export independently verified results. Undoable configuration and bounded previews let you review choices before full-file execution.

## Select and inspect input

Choose **Start reformatting** and browse or drag/drop CSV, TSV, delimited TXT or XLSX. Select one worksheet for XLSX. Use detection overrides only when encoding, delimiter, quote/header handling or worksheet selection needs correction.

Inspect Overview, Columns and First/Middle/Last samples. Confirm ambiguous dates and potential missing markers rather than assuming a detection is correct. Keep an untouched source copy outside the repository.

## Configure fields

Open **Configure fields**. Use the mapping grid to include/exclude fields, edit output names and review column order. Search/filter a large schema; choose a row for its detailed controls or open **Sequential wizard**.

For each field review:

- chosen type and its matching input/output profile;
- Custom format, when a preset is unsuitable;
- timestamp role and sampling duration where applicable;
- source and target timezone, separately from manual time shifts;
- numeric transforms and generated-row behavior.

Both profile lists follow the selected type. Custom sits near the top. Changing type resets profiles for review and clears incompatible numeric transforms. Saved older recipes retain their explicit profiles when opened.

Drag panel dividers to give the mapping grid or editor more room; horizontal and vertical scrollbars remain available. Select all/Deselect all applies only to its adjacent group, not safety confirmations or overwrite permission.

## Gaps and missing values

**Insert Missing Time Rows** is enabled by default but optional. It requires a confirmed timestamp and positive interval. Generated measurements are missing, not interpolated. Input missing markers and output null appearance are separate decisions. Read [Gaps and missing values](https://github.com/GGadash/GDTT/wiki/Gaps-and-Missing-Values).

## Compatible batches

The first file is the reference. Shared configuration requires the same file kind, ordered column names, header decision, delimiter/quote behavior and, for XLSX, worksheet name. Row counts and measured values may differ.

An incompatible input blocks the batch with reasons. Correct or remove it; do not force a shared recipe onto different structures. For files with deliberately different fields, consider [Split / Join](https://github.com/GGadash/GDTT/wiki/Splitting-and-Joining) instead.

Configuration previews are reference-file evidence only. Each source is later read completely, transformed, exported and reopened independently. Results and failures are grouped by source; a successful first file does not prove the rest passed. Names are source-derived and collision-safe. **Process more similar files** returns to source selection after export.

## Review and finish

Use Back, Reset, Undo and Redo to revise the draft. Select **Review configuration** after required decisions are confirmed, compare full-file counts and samples, then choose outputs and inspect the verification report.

Next: [Formats and timezones](https://github.com/GGadash/GDTT/wiki/Formats-and-Timezones) · [Export and verification](https://github.com/GGadash/GDTT/wiki/Export-and-Verification)

Source: [User guide](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/USER_GUIDE.md).
