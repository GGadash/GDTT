# Gaps and missing values

## Summary

A missing timestamp row, a missing cell and an empty text value are different things. Confirm source missing markers explicitly. Gap filling adds expected rows with missing measurements; it does not invent observations.

## Confirm input markers

Potential markers such as N/A, NA, NULL, blank text or -999 are suggestions. Confirm the appropriate source markers before normalization. In particular, -999 is not automatically assumed missing.

The internal missing state is canonical `None`. Empty text remains a real value unless confirmed as missing. Invalid numeric values follow an explicit policy and are counted; review the diagnostics rather than silently treating all invalid values as measurements.

## Optional sampling-grid rows

**Insert Missing Time Rows** is enabled by default and can be deselected. When enabled:

1. Confirm the timestamp column.
2. Confirm a positive sampling interval.
3. Review duplicates, chronological breaks, invalid/off-grid timestamps and gap spans.
4. Resolve blocking ambiguity or explicitly allow supported reordering.
5. Review generated rows and per-field behavior.

Timezone-aware grids use elapsed-time arithmetic. The current confirmed grid limit is 1,000,000 expected rows. This is separate from the large-file spill-processing mechanism.

Generated measurements stay missing. Other fields can use explicit policies such as fixed values, stable metadata or timestamp-derived values. Do not describe this as interpolation.

## Output appearance

| Choice | Meaning at export |
| --- | --- |
| True Null / blank | CSV unquoted empty field; XLSX genuinely blank cell |
| N/A | Chosen textual missing marker |
| -999 | Chosen sentinel |
| Custom | Your non-empty sentinel |

These choices change representation, not the engine's internal null meaning. Choosing -999 as the output sentinel does not confirm -999 in the input as missing. Pick a sentinel that cannot be confused with legitimate observations.

CSV empty text can be written as `""` while null is an unquoted empty field; some other programs may collapse that distinction when reading. GDTT's verification checks its own defined representation.

## Aggregation and splitting

Insufficient aggregation completeness produces missing results, not guessed means. Split / Join reorganizes data without adding sampling-grid rows or aggregating measurements.

Sources: [Null handling](https://github.com/GGadash/GDTT/blob/main/About-Info/Data-Processing/NULL_HANDLING.md) · [Gap filling](https://github.com/GGadash/GDTT/blob/main/About-Info/Data-Processing/GAP_FILLING.md).
