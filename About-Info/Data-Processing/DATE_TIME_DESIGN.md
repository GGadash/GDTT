# Date and Time Design

Printed format and timestamp meaning are separate. A timestamp can be interval start, end,
midpoint, instantaneous, or unknown/custom and also carries a sampling duration.

Ambiguous regional dates require a preview of interpretations. Semantic end normalization
uses the confirmed interval rather than blindly rounding clock text. Start, mid, and end
fields are derivations with explicit names. Manual Time Shift changes timestamp values;
Timezone Conversion preserves the represented instant.

Phase 3 implements named ISO and regional profiles, distinct ambiguity interpretations,
milliseconds, parse/format separation, date-plus-time combination, DateTime splitting,
timestamp-role models, start/mid/end derivation, semantic inclusive-end normalization, and
manual shifts in `src/data_transform_tool/datetime/`.
