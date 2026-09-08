# Data Splitter & Joiner — GDTT 0.9.0

This separate Home workflow reorganizes fields and rows without calculating statistics or
filling sampling gaps. Reformat and Averaging retain their existing processing behavior.

## Start a job

1. Open **Split / Join**. Browse or drag/drop local CSV, TSV, TXT, or XLSX files.
2. Select each source in the left list. Choose its worksheet, header, delimiter, or encoding
   if needed, then **Inspect / refresh columns**. Review the detected structure and sample.
3. Choose its timestamp column, input format, source timezone, and measurement fields.
   Each source may use its own timestamp column name, format, timezone, and Excel worksheet.
4. Choose the operation and review its options. Click **Prepare & preview**.
5. Review the complete-source output list and select each output for first/middle/last samples.
   Choose CSV, plain Excel, formatted Excel, or several formats, then the export parent folder.
6. Click **Export & verify all outputs**. GDTT creates a uniquely named run subfolder after
   every file passes reopen verification. The displayed folder includes `SPLIT_JOIN_REPORT.json`.
   Existing outputs and input files are never overwritten by this module.

## Operations

| Operation | Result and choices |
|---|---|
| Split by time period | One file per populated period per source: year, month, week, quarter, custom season, or day. |
| Split parameters / field groups | One file per selected parameter by default. To combine fields, load selected parameters into the group table, enable named groups, and give fields the same group name. Blank group names exclude fields. |
| Join time-series files | Concatenate and sort files with matching selected field names and order. Timestamp column names may differ. Optionally split the combined result into configured periods. |
| Join parameters by timestamp | Match exact instants across files. Choose all timestamps (outer), timestamps common to every file (inner), or the first file's timestamps (left). Missing matches use the selected output-null representation. |

For field splitting, optional shared metadata fields appear in every result alongside the
timestamp. All selected groups and shared fields must exist in each source. For field joining,
parameters receive stable `S1_`, `S2_`, etc. prefixes, corresponding to source order, so identical
field names cannot overwrite each other. This does not join different stations sharing one
timestamp as a composite key; prepare those sources separately if needed.

## Timezones, formats and period starts

- **UTC**, **Asia/Colombo** (currently UTC+05:30, or +5.5 hours), and **+05:30** are shortcuts.
  Type any IANA timezone or a fixed offset such as `-04:00` in either editable zone selector.
  An IANA region follows its historical/DST rules; a fixed offset stays constant.
- The source timezone applies to timestamps without an embedded offset. An embedded `Z`,
  `+05:30`, etc. already defines the instant and takes precedence. Sources are matched by that
  instant, including microseconds, rather than by their displayed local clock strings.
- The boundary/output timezone controls period membership and exported timestamp representation.
  Outputs always use ISO 8601 text with the explicit offset, including in Excel, to retain it.
- ISO input accepts dates, times with seconds or fractional seconds, and embedded offsets.
  For other formats choose a listed pattern or type a Python `strptime` pattern. For example,
  `%d/%m/%Y %H:%M` is day-first, and `%m/%d/%Y %H:%M` is month-first. Ambiguous dates are not guessed.
- Choose the local start time, including seconds. Weeks have a chosen weekday; months have a
  chosen start day; quarters have a first-quarter start month and day; years have a start month
  and valid day. Month/quarter start days are restricted to 1–28 to remain valid in every month.
  January 1 at 00:00 is the default calendar-year start.
- Define at least two unique named season starts by month/day. Each season ends at the next
  boundary, including across New Year. Seasonal and annual boundaries must be valid every year
  (February 29 cannot be an annually recurring start).
- Periods include their start and exclude their end. For example, `2025-12-31 18:30 UTC`
  belongs to the 2026 calendar-year file when the boundary timezone is Colombo.
- Ambiguous or nonexistent local source times or period boundaries at DST transitions block
  with an explanation. Supply offset-bearing input or choose an unambiguous boundary time.

## Duplicates, previews and verification

Joins stop on duplicate/overlapping timestamps by default. Keep-first/keep-last explicitly
resolve duplicates using input-file order, then original row order. Time joins additionally
offer keep-all; field joins require one chosen row per timestamp per source. Splits retain
duplicate rows. No measurement aggregation, interpolation, or gap insertion occurs here.

Preparation reads complete sources into private disk-backed snapshots and sorts by timestamp.
Export uses that reviewed snapshot. Changing input or operation controls invalidates the plan;
prepare again to apply them. Samples are bounded; row counts cover all source rows. An inner
join with no matches can produce a valid header-only joined table. Time splits create only
populated periods, not empty files for gaps. Up to 100 sources and 5,000 output tables are allowed
per UI run, with the usual Excel row limit applying to each output.

Every file is reopened and checked using the established GDTT verification engine. A failed or
cancelled export removes its temporary run folder. The JSON report records operation settings,
source names, row counts, period boundaries, formats, missing-value policy, and per-file check
results without copying measurement rows. True Null, N/A, -999, and a custom sentinel apply only
to output representation; existing source values are preserved.

## Local release status

Version 0.9.0 portable EXE/ZIP, current-user EXE installer, and audited source ZIP were built
and verified locally. All 162 automated tests and local C-lite acceptance passed. The owner
authorized a subsequent source commit/push; a new GitHub release tag is not part of this
instruction, so pushing source alone does not publish new binary downloads.
The Windows executable smoke test includes synthetic split-time, split-field, join-time, and
join-field operations with CSV and Excel export/reopen verification. The usual separate clean
Windows acceptance and code-signing decisions remain external gates.

## Automatic filenames

Each prepared output receives a descriptive name with a unique ordinal, source/group or joined
file count, relevant date range or period start, and a clear operation suffix:

- `_SPLIT_FIELDS` for parameter/group files;
- `_SPLIT_YEAR`, `_SPLIT_MONTH`, `_SPLIT_WEEK`, `_SPLIT_QUARTER`, `_SPLIT_SEASON`, or `_SPLIT_DAY`;
- `_JOIN_TIME` or `_JOIN_FIELDS` for combined files;
- `_JOIN_TIME_BY_MONTH`, for example, when a joined result is regrouped into monthly files.

CSV adds `.csv`; plain Excel adds `_P.xlsx`; formatted Excel adds `_F.xlsx`. The preview shows
the exact planned filenames for the selected output. Invalid Windows filename characters are
sanitized and long labels shortened while preserving the suffix. Stable ordinals prevent
collisions, and each export creates a new run folder, so repeating a job does not overwrite
earlier exports. Reformat/Averaging keep their existing RF/AVG naming conventions.
