# Splitting and joining

## Summary

The separate Split / Join module reorganizes parameters and time-series files. It does not aggregate measurements, interpolate, or fill gaps. Sources may have different timestamp names, formats, zones and worksheets when the chosen operation permits it.

## Choose an operation

| Operation | Result |
| --- | --- |
| Split by time period | One file per populated day/week/month/quarter/season/year per source |
| Split parameters / field groups | One file per parameter, or per explicitly named group |
| Join time-series files | Concatenate and sort matching selected fields; optionally split the result into periods |
| Join parameters by timestamp | Combine fields at exact matching instants with outer, inner or first-source/left matching |

For field groups, enable named groups and give related fields the same group name; blank groups exclude fields. Optional shared metadata accompanies each output. Field joins use stable `S1_`, `S2_`, etc. prefixes to prevent overlapping names from overwriting each other.

Joins match exact instants, including microseconds. They do not automatically join by a station-plus-time composite key. Process separate stations appropriately.

## Step by step

1. Open **Split / Join** and browse or drag in sources.
2. Select each source, choose worksheet/header/delimiter/encoding if needed, and **Inspect / refresh columns**.
3. Choose its timestamp field, input format, source timezone and measurement fields.
4. Choose the operation, groups/periods, duplicate policy and output-null representation.
5. Click **Prepare & preview**. Review the full-source output list and first/middle/last samples.
6. Select CSV/plain Excel/formatted Excel and an export parent folder.
7. Click **Export & verify all outputs**.

Preparation snapshots complete sources into private disk-backed storage. Changing controls invalidates the plan, so prepare again. Counts cover all source rows; displayed samples are bounded.

## Timezones and boundaries

Embedded Z/offsets define the instant and take precedence over a source zone for naive values. Boundary/output timezone determines period membership and the exported ISO timestamp offset.

Choose UTC, Asia/Colombo, a fixed offset or another IANA zone. Input controls accept ISO or Python `strptime` patterns such as `%d/%m/%Y %H:%M`; these are different from Reformat's Excel-style Custom masks.

Periods include their start and exclude their end. Choose start time, weekday and relevant month/day anchors. Month/quarter day starts are limited to 1–28. Annual and seasonal boundaries must recur every year, so February 29 is not a recurring start. Define at least two unique named season starts.

For a Colombo calendar year, `2025-12-31 18:30 UTC` belongs to 2026. DST-ambiguous/nonexistent local inputs or boundaries block with an explanation.

## Duplicates, filenames and limits

Joins stop on duplicates by default. Explicit keep-first/keep-last uses source order then original row order. Time joins also offer keep-all; field joins need one selected row per instant per source. Splits retain duplicate rows.

Names include stable ordinals, source/group/time labels and suffixes such as `_SPLIT_FIELDS`, `_SPLIT_MONTH`, `_JOIN_TIME` or `_JOIN_FIELDS`. Plain/formatted Excel adds `_P.xlsx`/`_F.xlsx`. Each export uses a unique run folder; existing results are not overwritten.

Only populated periods are written. A valid inner join with no matches can be header-only. UI runs allow up to 100 sources and 5,000 output tables; each Excel output must fit its worksheet limit.

A final run folder is published only after all files pass reopening verification. Failures/cancellation remove the temporary run folder. `SPLIT_JOIN_REPORT.json` records settings and verification without measurement rows.

Source: [Detailed Split & Join guide](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/SPLIT_JOIN.md).
