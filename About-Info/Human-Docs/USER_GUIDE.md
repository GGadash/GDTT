# User Guide

## Phase 2 source inspection

Run `uv run gdtt` (the compatibility command `uv run data-transform-tool` also works). Choose
Dark, Light, Auto, or System in the header; Auto is the clean-install default and follows the
operating-system color preference. Select **Start reformatting**, then browse for or drag and
drop one or more CSV, TSV, delimited TXT, or XLSX files.

With multiple files, the first file is the reference. GDTT inspects every file locally and
requires the same file type, ordered column names, header decision, delimiter/quote behavior,
and—when applicable—worksheet name. Row counts and measurement values may differ. Compatible
files are listed explicitly; an incompatible file shows its reasons and blocks configuration
until it is removed or corrected. A single file follows the same workflow without batch steps.

For XLSX, select one worksheet. Expand **Detection overrides** only when encoding, delimiter,
or header detection needs correction. Select **Inspect file** to profile the source locally.
The Overview, Columns, and First/Middle/Last tabs expose every advisory inference before any
future transformation is applied. Potential missing markers and ambiguous dates are prompts
for confirmation, never automatic mutations.

## Phase 5 reformat configuration

After inspection, select **Configure fields**. The mapping grid lets you include or exclude
fields and edit output names in place; search and grouped filters keep large schemas manageable.
Choose a row to configure its type, format profile, timestamp role, timezone behavior,
transformation, and generated-row behavior, or use **Sequential wizard** for one field at a
time. The Proposed output preview and live samples update from the same reversible draft.

**Insert Missing Time Rows** is selected by default and can be deselected. When it is selected,
confirm the primary timestamp and interval before review. Generated measurement cells stay
internally missing and are never interpolated. Select their global proposed/export appearance as
True Null / blank (default), N/A, -999, or a custom sentinel. This output choice is separate from
the checkboxes that confirm source missing markers. Use Undo, Redo, Reset, or Back freely; no
source file is changed.

## End-user workflow

1. Choose Reformat or Averaging.
2. Select or drop one file, or a compatible batch, and choose a worksheet where applicable.
3. Review detected schema, null markers, timestamps, and interval.
4. Configure explicit transformations or aggregation rules.
5. Compare input and proposed output previews.
6. Review the readable plan and warnings.
7. Export to a new file.
8. Review post-export verification and the processing report.

The tested configuration and domain engines continue into the Phase 8 review/export screen.
No operational file should be copied into the repository for normal use.

## Phase 7 averaging configuration

Choose **Average / Aggregate**, select and inspect a source, then choose **Configure averaging**.
The workspace starts from detected suggestions, but it does not silently approve them. Confirm
the timestamp, input parser profile, source timestamp timezone, reporting-boundary IANA timezone,
and input interval. Keeping these zones separate allows aware source instants to use another
reporting calendar; incompatible interval/boundary grids remain blocking preview errors. Review
the detected missing-marker list: checked markers become canonical nulls; unchecked markers are
deliberately retained after selecting **Marker decisions reviewed**.

Numeric fields are selected by default. Each field has an advisory statistic and output name.
Name-based Leq, rainfall, and rain-rate suggestions must be confirmed or overridden. Leq can
optionally name a duration field; all other statistics ignore duration weighting.

Choose **Direct** for source rows to one target or **Incremental** for a visible multi-stage
chain. Add, remove, or select stages to configure their period, threshold, and valid 2-of-3
exception. Period choices include common/custom clock intervals, configurable start-of-day,
week start, calendar month, anchored fixed 30 days, quarter start, editable season boundaries,
reporting-year start, and anchored fixed year. The default completeness threshold is 75%.

Use **Proposed output** for the bounded final table and **Stage completeness** for every retained
stage table plus valid/expected counts, availability, accepted/missing state, and 2-of-3 use.
Rejected values remain canonical null internally; True Null, N/A, -999, or Custom controls only
their proposed/output representation. Reset, Undo, Redo, and Back are safe and do not modify the
source.

## Phase 8 review, export, and verification

Select **Review configuration** or **Review averaging plan** after all required confirmations.
GDTT then reads the complete source locally into private bounded-memory spill
batches and executes the confirmed plan independently of the bounded preview. Review complete
input/output counts and the first, middle, and last five records before choosing outputs.

Choose any combination of CSV, plain XLSX, and formatted XLSX. The suggested Windows-safe name
includes the source, detected timestamp range, and RF or AVG; XLSX variants add P or F. You may
override it. Existing files are never replaced unless **Allow replacing files with the same
names** is selected.

Choose True blank/null, N/A, -999, or a custom output sentinel. Canonical null remains internal;
CSV true null is an unquoted empty field and XLSX true null is a genuinely blank cell. Formatted
XLSX offers Environmental Technical, Clean Laboratory, and Minimal presets plus font, color,
AutoFilter, and frozen-header controls.

Transformation information, versioned recipe JSON, a concise summary, and a conditional
warning/error file are optional and enabled by default. After writing, the app reopens every
data output and verifies readability, filename, rows, ordered columns, duplicate Index fields,
timestamp boundaries, null representation, values, and formatted-sheet structure. Review
Passed, Passed with Warnings, or Failed; failures are never hidden.

For a compatible batch, the pre-export tables are clearly labelled as the reference-file
preview. GDTT then prepares, writes, reopens, and verifies each source independently. Output
names are derived from each source (`source_RF` or `source_AVG`) and de-duplicated safely.
The Verification tab groups artifacts, warnings, and failures by source; one failed source does
not hide successful results for other files. Select **Process more similar files** after export
to return directly to file selection for another single file or batch.

Use **Save current** and **Manage** for local templates. Templates store configuration and style,
never measurements, and support schema-count matching, review, duplicate, rename, import,
export, and confirmed deletion. For a match, choose Apply to return its choices to the reversible
configuration draft, Review to inspect JSON without changing anything, or Ignore for the current
session. Apply requires an exact schema; likely matches remain review-only. Private spill files
are deleted after reset/navigation and cancellation; same-directory partial export files are
removed before a failed or cancelled atomic replacement.
