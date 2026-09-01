# Data Pipeline Specification

The planned pipeline is:

1. Probe file metadata without mutation.
2. Detect encoding/delimiter/worksheet/header and sample structure.
3. Profile types, missing markers, timestamps, interval, and empty columns.
4. Ask the user to confirm consequential ambiguity.
5. Build a validated, versioned transformation or aggregation recipe.
6. Compile the recipe into a readable execution plan.
7. Produce input and proposed-output previews.
8. Validate, execute with progress/cancellation, and export atomically.
9. Reopen the output and verify structure, nulls, timestamps, and row counts.
10. Present and optionally export the report and recipe.

Raw source values and parsed values remain conceptually distinct. Detection warnings and
invalid-value decisions carry counts into the final report.

The Phase 4 eager reference engine defines confirmed-interval grids, generated-row metadata
behavior, invalid-numeric decisions, canonical-null row removal, and strict true-null
serialization semantics. The Phase 5 UI composes those contracts without reimplementing their
calculations in signal handlers.

The Phase 6 eager aggregation reference engine defines timezone-aware reporting boundaries,
boundary-derived expected counts, Direct and visible Incremental execution, per-stage
completeness evidence, and isolated statistic strategies. The Phase 7 UI composes the same typed
recipes and bounded evidence previews without duplicating calculations; production large-file
execution must preserve these semantics.
