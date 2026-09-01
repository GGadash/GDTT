# Averaging Design

Direct aggregation calculates each target period from valid source observations.
Incremental aggregation uses a visible configurable chain and applies completeness at each
selected stage. Expected counts derive from timezone-aware boundaries and configured input
intervals, not from rows that happen to exist.

Arithmetic mean is the default. Min, max, sum, median, standard deviation, count, Leq
energy average, rainfall accumulation, and rain-rate mean are separate strategies. Leq is
never arithmetic-averaged. Reporting boundaries honor the chosen timezone, local day start,
week start, calendar/fixed periods, seasons, and DST.

Phase 6 implements these rules as an immutable eager reference executor in `aggregation/`.
`AggregationConfig` separates the confirmed input interval, reporting timezone, field
strategies, and visible stages. Direct requires exactly one target stage; Incremental requires
two or more stages and retains the table, report, and per-field completeness records from every
stage.

Clock periods divide a 24-hour wall-clock day exactly. Day, week, calendar month, quarter,
season, and reporting-year boundaries use local wall time in the selected IANA timezone. Fixed
30-day and fixed one-year periods use explicit anchors and remain distinct from calendar
periods. DST days derive 23 or 25 hourly expectations from boundary instants. Repeated fall-back
hours remain one wall-clock period with two elapsed input slots; skipped spring-forward slots
have no fabricated observations.

Completeness defaults to 75% and uses valid expected observations divided by boundary-derived
expected observations. The 2-of-3 exception is permitted only on an explicitly configured
Incremental stage with exactly three expected components. An incompatible stage chain is a
blocking configuration error rather than being silently truncated or reweighted. Insufficient
periods output canonical `None` and contribute counted diagnostics for later reports.

The arithmetic statistics use finite numeric values; standard deviation is the population
standard deviation. Equal-duration Leq uses energy averaging, and an optional positive duration
field enables duration-weighted energy averaging. Rainfall accumulation and rain-rate mean are
separate strategy identities even though they reuse sum and arithmetic-mean mathematics.

Aggregation instructions are frozen typed recipe models and are also represented in
`About-Info/Machine-Readable/transformation_recipe_schema.json`. The Phase 7 application layer
builds and previews these contracts; Qt handlers only edit immutable drafts and do not duplicate
period, completeness, or statistic calculations.

## Phase 7 configuration and preview

`AveragingDraft` keeps detected timestamp, source timezone, reporting-boundary timezone,
interval, missing-marker, and field-statistic
suggestions separate from explicit confirmations. Potential missing markers require a reviewed
decision before a preview is ready, preventing values such as `-999` from being silently treated
as measurements. Source timestamp localization remains separate from the reporting timezone so
UTC observations are not relabeled when another reporting calendar is selected. Name-based
Leq/rainfall/rain-rate suggestions likewise remain overridable and
must be confirmed for selected fields.

The visible stage list is the configured runtime chain, not decorative UI state. Each stage owns
its `PeriodSpec`, threshold, optional Incremental-only 2-of-3 rule, and label. The configuration
view exposes clock and custom-clock targets, day/week/month/fixed-30-day/quarter/season/year
alignment, editable season boundaries, and fixed anchors. Bounded previews use the first
inspection slice and the Phase 6 executor, retaining the final table, every stage table, and
every completeness record. They are evidence previews only; full-file execution begins in Phase
8.
