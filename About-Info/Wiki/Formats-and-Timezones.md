# Formats and timezones

## Summary

A format controls how a value is read or displayed; it is not the same as timestamp meaning or timezone conversion. Choose a field type first. Both input and output offer relevant presets plus an editable Custom choice near the top.

## Date/time and ISO presets

For **DateTime**, common extended forms appear before compact forms. Date-only and Time-only lists retain their own relevant presets; numeric/text lists do not offer date/time presets.

| Meaning | Extended example | Compact example |
| --- | --- | --- |
| UTC datetime | `2026-09-15T01:02:03Z` | `20260915T010203Z` |
| Datetime with offset | `2026-09-15T01:02:03+05:30` | `20260915T010203+0530` |
| Date with hour/minute | `2026-09-15T01:02` | `20260915T0102` |
| Date with full time | `2026-09-15T01:02:03` | `20260915T010203` |

GDTT masks use `yyyy` for year, `MM` for month, `dd` for day, `HH` for 24-hour, `mm` for minute and `ss` for second. Quoted `'T'`/`'Z'` are shown explicitly; `XX` is a compact offset and `XXX` is colon-separated. Exact new ISO masks also work in Custom. These new profiles require GDTT 0.10.1 or later.

**Z means actual UTC.** UTC output converts an aware instant, including any date rollover. Example: `2026-01-01T01:02:03+05:30` becomes `2025-12-31T19:32:03Z`. It never simply adds Z to an unknown local clock time. UTC/offset output blocks when the source timezone is unknown.

For naive local input, select its no-zone input format, configure the source timezone and a target timezone before exporting. Minute formats omit seconds; no-zone formats omit the offset. Choose those only when that information loss is intended. Existing millisecond and regional presets remain available.

## Numeric formatting and decimal separators

- `0.00` is the common preset: `1.2345` becomes stored/exported `1.23` by default.
- `#,##0.00` adds thousands grouping; `0`, `0.000`, `0.###` and supported custom masks are available.
- Input formatting parses values without rounding them.
- **Keep full numeric precision** preserves the underlying number; preview and Excel formatting can show fewer decimals. CSV retains the available number in this mode. Earlier arithmetic rounding cannot be undone.
- Input/output decimal separators are separate dot/comma choices. For `1.234,56`, use grouped input `#,##0.00` and comma decimal. Do not rely on guessing.
- CSV remains comma-delimited; decimal-comma values are quoted. Excel separators follow Excel/OS regional settings. Excel's native numeric precision limits still apply.

## Other Custom formats

Text supports `@` or `pre-{value}-post`. Boolean supports `True|False`, `Yes|No`, `1|0` or two custom labels. Date/time examples include `dd/MM/yyyy` and `yyyy-MM-dd HH:mm:ss`. Quote literal words.

Custom is a documented subset, not the complete Excel mask language: arbitrary currency/scientific/percentage, conditional-color, multi-section and custom fractional-second masks are not promised. Invalid masks are reported instead of executed.

## Timezone choices and meaning

Priority choices are UTC, Asia/Colombo (+05:30), Custom, half-hour offsets and the installed IANA list. Other valid minute offsets, such as +05:45, can be typed. Named regions retain historical/daylight-saving rules; fixed offsets never acquire DST rules.

Timezone conversion preserves an instant. **Time Shift** intentionally moves it and is a separate operation. Source timezone, reporting/boundary timezone and start/mid/end timestamp role are separate concepts. Ambiguous or nonexistent DST-local times require explicit handling or block.

Split / Join uses its own ISO or Python `strptime` input controls; do not paste Excel-style masks into a Python-pattern field. See [its guide](https://github.com/GGadash/GDTT/wiki/Splitting-and-Joining).

Source: [Formatting and appearance](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/FORMATTING_AND_APPEARANCE.md).
