# Null Handling

After user confirmation, blank text, N/A, NA, NULL, custom markers, or numeric sentinels
map to one canonical internal missing state. `-999` is never assumed missing without
confirmation. Invalid numeric text follows an explicit file-level decision and is counted.

Export applies one global measurement-missing policy. True Null is the default: consecutive
delimiters in CSV/TSV and a genuinely absent XLSX cell value. It is not an empty string.

Phase 3 implements confirmed input normalization with canonical Python `None`. Marker matching
can be scoped to selected columns and configured for case/whitespace behavior. Detection from
Phase 2 remains advisory; no marker, including `-999`, is transformed until explicitly listed.

Phase 4 adds invalid-numeric summaries with Null and Continue, Inspect, Stop, and Preserve
Source policies. Preserve Source copies only invalid raw values to a separate field before
placing canonical nulls in the numeric field. Row-removal rules can preview all-measurements,
all-selected, any-required, selected-subset, or present-value-threshold matches.

Only `None` is missing inside the engine. Empty text remains a real source value unless the
user explicitly confirms it as a missing marker. The strict delimited adapter therefore writes
`value1,,value3` for a canonical null but `value1,"",value3` for empty text; the XLSX adapter
passes `None` as a genuinely absent cell value. Full exporters and post-export reopening remain
Phase 8 CSV and XLSX writers now apply the selected representation only at the output boundary.
Post-export verification reopens outputs and checks the exact CSV lexical representation or XLSX
blank/value structure against the canonical result.

Phase 5 shows the global output policy early in the **Gaps & missing** configuration tab. The
choices are True Null / blank (default), N/A, -999, and Custom Sentinel; a custom choice is
invalid until a non-empty sentinel is supplied. The proposed-output preview renders that choice
without changing the immutable canonical-null recipe semantics. Detected source markers remain
separate checkboxes and are never confirmed merely by selecting an output representation.
