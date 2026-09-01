# Timezone Design

Use timezone-aware standard-library datetimes and IANA `zoneinfo` keys. Bundle `tzdata`
because Windows may not provide the IANA database. UTC and Asia/Colombo are prominent,
while all IANA zones remain searchable.

Naive input requires an explicit source zone or offset. A numeric offset is not a timezone
and does not supply daylight-saving rules. Ambiguous and nonexistent DST-local times must
be surfaced rather than silently corrected.

Phase 3 supports embedded offsets, a fixed IANA zone, an IANA zone column, and a manual UTC
offset as separate source modes. Aware inputs cannot have their embedded offset silently
overridden. Ambiguous DST times require first/second-occurrence selection; nonexistent local
times are blocking errors. Conversion always targets an IANA zone and preserves the instant.
