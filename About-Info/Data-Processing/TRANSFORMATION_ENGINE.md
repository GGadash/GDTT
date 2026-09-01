# Transformation Engine

Phase 3 implements a UI-independent semantic reference engine. `DataTable` is immutable;
each `TransformationOperation` returns a new table plus counted diagnostics, and
`TransformationPlan` records an audit entry for every step. Recipes are frozen, versioned
Pydantic models and contain configuration only—never measurement rows or executable code.

## Implemented operation families

- columns: rename, reorder, select/remove from output, add empty, duplicate, one-based Index,
  and deselect entirely empty fields;
- numeric: arithmetic rounding, ppm to ppb, ppb to ppm, explicit invalid-value policies;
- calculated fields: nested source/constant arithmetic expression trees and linear formulas,
  without Python `eval`;
- date/time: named parse/format profiles, ambiguity previews, combine/split, timestamp roles,
  duration, start/mid/end derivation, inclusive-end normalization, and manual time shifts;
- timezone: embedded, fixed IANA, timezone-column, and manual-offset sources; conversion to a
  target IANA zone preserves the instant and surfaces ambiguous/nonexistent DST local times;
- nulls: only user-confirmed markers become the one canonical internal null value, `None`.

## Execution boundary

The immutable row table is the correctness/reference executor for domain tests and bounded
previews. It is not the final large-file backend. Later phases must compile the same explicit
operations to a benchmarked lazy/chunked backend without changing their semantics, diagnostics,
or recipe representation.

## Phase 5 configuration workflow

`ReformatDraft` is an immutable application-layer configuration model. The mapping grid,
selected-column editor, sequential wizard, and global gap/missing controls all update the same
draft through an undoable `ConfigurationSession`. Validation converts a ready draft into the
existing typed version-1 `TransformationRecipe`; UI signal handlers do not perform data
calculations.

The proposed-output preview is bounded by the inspected source slice and composes the tested
Phase 3 and Phase 4 operations. It is a decision aid, not a separate transformation engine or a
large-file execution path.
