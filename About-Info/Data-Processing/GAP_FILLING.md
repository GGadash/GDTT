# Gap Filling

Gap reconstruction starts only after the user confirms a primary timestamp and expected
interval. It creates the exact expected grid, identifies duplicates/disorder separately,
and inserts rows without interpolating measurements.

Generated rows populate timestamps, derived time fields, and indexes. Each other field
uses an explicit Null, Carry Stable Metadata, Fixed Value, or Derived from Timestamp policy.
Pollutant and sensor values are never forward-filled merely because neighbors exist.

Phase 4 implements this as an immutable reference engine in `gaps/`. Interval detection is
advisory; generation requires a positive confirmed interval. Timezone-aware grids advance by
elapsed time in UTC and render back into the source zone, including across daylight-saving
boundaries. Mixed aware/naive timestamps are blocked.

Analysis reports duplicates, chronological breaks, invalid timestamps, and off-grid rows as
separate conditions. Generation blocks duplicates, invalid timestamps, and off-grid values;
chronological reordering requires an explicit option. Measurement columns are always canonical
null in generated rows, regardless of metadata configuration. Carry Stable Metadata succeeds
only when all non-null source values have the same scalar type and value.

Phase 5 exposes **Insert Missing Time Rows** as a default-on option that the user may
deselect. When selected, the primary timestamp and interval must still be explicitly
confirmed before a recipe can be reviewed. The interface also exposes Null, Carry Stable,
Fixed Value, and Derived from Timestamp behavior for non-measurement fields.

The nearby True Null / N/A / -999 / Custom Sentinel control is the one global output missing
representation. It affects proposed-output display and future serialization, not internal gap
generation: generated measurements always remain canonical `None`, and no measurement is
interpolated or forward-filled.
