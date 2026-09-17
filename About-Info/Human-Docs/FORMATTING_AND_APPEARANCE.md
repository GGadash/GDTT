# GDTT 0.10.1: formatting and appearance

GDTT — Data Transform Tool by Gadash (Akila DJ). Implemented with existing Python, PySide6,
XlsxWriter/openpyxl and Decimal components, with AI-assisted development using OpenAI Codex.
No new dependency or bundled font was added; existing third-party notices remain applicable.

## Input and output

Select a field in Reformat / Transform. Drag either divider to enlarge the mapping columns or
Selected field editor. Both directions can scroll; short windows may require vertical scrolling.
The sequential wizard offers the same profiles. Both input and output preset lists follow the
chosen field type; numeric/text lists do not include temporal presets. Custom is directly below
Auto / unchanged or As source, and opens an editable mask field. Changing type resets both profiles
to Auto / unchanged and As source, and removes incompatible numeric transforms.
Existing recipes/defaults do not acquire rounding
automatically: choose a numeric output mask when rounding is wanted.

### ISO date/time presets (0.10.1)

Select DateTime for the following input and output choices. Common extended forms appear first;
compact forms are lower in the list. Date-only and Time-only fields retain their own relevant
presets. Hover a preset for its descriptive name. Existing profile IDs/output defaults are retained.

| Meaning | Extended example | Compact example |
| --- | --- | --- |
| UTC datetime | 2026-09-15T01:02:03Z | 20260915T010203Z |
| Datetime with UTC offset | 2026-09-15T01:02:03+05:30 | 20260915T010203+0530 |
| Date with hour/minute | 2026-09-15T01:02 | 20260915T0102 |
| Date with full time | 2026-09-15T01:02:03 | 20260915T010203 |

Masks use GDTT's existing notation: yyyy = year, MM = month, dd = day, HH = 24-hour,
mm = minute, ss = second; quoted T/Z are shown explicitly. XX denotes compact offset,
XXX denotes colon-separated offset. Exact new ISO masks also work when typed into Custom.
UTC presets read Z as UTC and convert known source instants to UTC on output, including date
rollover. Offset output preserves the value's current timezone offset. UTC/offset output blocks
when the source timezone is unknown; for naive local inputs select the matching no-zone input
profile, configure the source timezone (for example Asia/Colombo), and a target timezone before
export. Do not merely append Z to local wall-clock times. No-zone/minute presets intentionally
omit timezone/seconds; they are explicit formatting choices, not lossless timestamp containers.

Saved older recipes retain their explicit profiles when opened, including a previously selected
cross-type input profile; it is not offered among new presets. Explicitly changing field type
resets profiles for review. New ISO profile IDs require GDTT 0.10.1 or newer. No recipe schema or
dependency changes are needed.

### Numeric input and output

- **Input profile** describes how existing values are read; it does not round input numbers.
- **Output format** describes the export. `0.00` is the first/common numeric preset: 1.2345 -> 1.23.
  By default this changes the stored exported number, not just its appearance. Less precision can
  reduce text size, but actual file-size savings depend on format/compression.
- **Keep full numeric precision**, off by default, preserves 1.2345 in CSV and numeric Excel
  cells while the preview and Excel mask show 1.23. Explicit arithmetic rounding/ppm transforms
  still act before export; this option cannot restore precision already removed by them.
- Independent **Input decimal separator** and **Output decimal separator** offer dot/comma.
  Choosing comma with an unchanged profile selects a numeric `0.00` profile explicitly.
  For French/EU `1.234,56` or `1 234,56` (also non-breaking spaces), select grouped input
  `#,##0.00` and comma decimal. Ungrouped `1,2345` needs `0.00` plus comma decimal.
  Separators are not guessed. CSV remains comma-delimited and quotes decimal-comma values.
- Excel numeric cells use Excel/OS regional separators. GDTT writes locale-neutral masks;
  the output separator directly controls previews and CSV, not the user's Excel settings.
  See [XlsxWriter's locale documentation](https://xlsxwriter.readthedocs.io/format.html#number-formats-in-different-locales).
  Excel's native numeric precision limit still applies; full-precision mode is not arbitrary-
  precision Excel storage. CSV preserves the available numeric value without that Excel limit.

## Custom patterns: a practical subset, not the complete Excel language

Choose Custom and type a mask, then leave the field to apply it. Invalid masks show a message.
Presets remain available. A mask is data, never executable code.

| Type | Examples and behavior |
| --- | --- |
| Numeric | `0`, `0.00`, `0.000`, `0.###`, `#,##0.00`, `0000.00`; up to 12 fractional positions. `0` requires a digit, trailing `#` hides optional zeroes. Rounding is half away from zero. |
| Date | `yyyy-MM-dd`, `dd/MM/yyyy`, `dd MMM yyyy`; month names use the runtime locale. |
| Time / DateTime | `HH:mm:ss`, `yyyy-MM-dd HH:mm:ss`, `hh:mm:ss AM/PM`, `yyyy-MM-dd HH:mm:ss XXX`; lowercase `mm` after hours/before seconds denotes minutes, `MM` denotes months. |
| Text / category / auto | `@` leaves text unchanged; `pre-{value}-post` adds affixes on output or removes matching affixes on input. |
| Boolean | `True\|False`, `Yes\|No`, `1\|0`, or custom `Oui\|Non`. First label is true, second false. |

Quote date/time literal words. Existing millisecond/date presets remain available. Unsupported
custom fractional-second tokens, percentage/scientific/currency masks, conditional colors and
multi-section Excel formats are not claimed as supported. Canonical nulls and selected missing-
value policies remain separate from formatting. Templates/recipes carry explicit custom-profile
strings without changing their existing schema; older GDTT versions cannot interpret new masks.

## Time zones

Dropdown priority is UTC, Asia/Colombo (+05:30), Custom, half-hour offsets from -12:00 through
+14:00, then the full installed IANA zone list. Type other valid minute offsets, such as +05:45,
or a zone name. Named zones retain historical/DST rules; fixed offsets never change for DST.
When reading source zones from a field, the source-value control remains a field selector.
Ambiguous/nonexistent named-zone times still follow the existing explicit DST handling.

## Appearance and selection

Teal is the original/default accent; Blue, Graphite, Violet and Spectrum are alternatives.
Use A-/A+ beside Theme to adjust interface sizes (10-20 px base). Tables use smaller Consolas
or an installed monospace fallback. These preferences persist and do not change exported styling.
Light/Dark/Auto retain the selected accent; System follows native system colors.

Select all/Deselect all affects only the adjacent field, marker, format, derived-field or report
group. It does not grant overwrite permission or bulk-confirm timestamp/completeness decisions.
About shows the new copyright wording; the existing root license has not been rewritten.

## About, links and optional support (0.10.2)

Open About from the app menu. Its scrollable overview groups the GitHub project, Wiki,
downloads, issue/feature reporting and release-safety links. A short license summary links the
online LICENSE; the full offline License and Components tabs remain available unchanged.
The Sponsor / Donate section, headed "Fuel the next transformation", contains the Ko-fi profile
and GDTT project support links. Donations are optional and do not unlock features or guarantee
support/delivery. Feedback and documentation improvements are welcome without donating.
Links open only when selected, in the default browser, and require internet access; dataset
processing remains local. The page retains copyright, Codex credit and unsigned/clean-Windows
limitations. It wraps and scrolls at the minimum dialog size with enlarged fonts in Light/Dark.

## Verification and release boundary

Focused tests cover locale parsing, numeric precision, CSV and both Excel outputs, stored masks,
recipe compatibility, type-aware controls, resize/scroll policies, selection scope, timezone
priority and ten light/dark palette contrast combinations. Native previews include 1920x1020,
1280x680 and 980x680 logical window sizes. Actual per-monitor 150% DPI remains an owner check.
Local binaries are unsigned; clean-computer acceptance and explicit Git publication remain separate.
