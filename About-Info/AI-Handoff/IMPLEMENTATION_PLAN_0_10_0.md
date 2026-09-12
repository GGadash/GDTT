# GDTT 0.10.0 implementation plan

Prepared: 2026-09-10
Scope: PEND-001 through PEND-016 in PENDING_MODIFICATIONS.md.
Status: implemented and verified locally as 0.10.0 (2026-09-11): 191 tests, static checks,
portable package, installer lifecycle and C-lite pass. Generated release files carry final hashes.
The owner answered the format questions: round export values by default; optionally retain full
precision with Excel display formatting. Common mask is 0.00, grouping is #,##0.00, and input/output
dot/comma decimal separators are independent. No publication or shutdown is authorized.

## Release boundary

- Target version: 0.10.0, reflecting new formatting and appearance capabilities rather than
  only a patch fix. Keep the existing 0.9.0 release and its artifacts intact.
- Make and verify the modified version locally. No commit, push, release tag, publication,
  dependency upgrades, or computer shutdown is implied by this new request.
- Preserve existing processing, gap/null rules, aggregation, batch compatibility, timestamp
  semantics, and Split & Join behavior except for the explicitly requested format/zone controls.

## 1. Shared appearance and small fixes

PEND-001, 002, 010, 011, 012, 013, 014, 015.

- Update About's displayed copyright only; do not silently rewrite LICENSE or all source credits.
- Use one small local-processing footer; remove redundant prominent offline emphasis.
- Add shared Teal (default), Blue, Graphite, Violet, and Spectrum palette definitions to the
  existing theme layer. Preserve Light/Dark/Auto/System and meaningful status/focus colors.
- Provide compact font-size controls and a color selector near theme selection. Proposed default:
  resize overall UI text, retaining a slightly smaller monospaced font for displayed datasets.
  Persist appearance preferences only; never dataset transformation decisions.
- Prefer an installed monospace font with a system fallback; avoid adding a bundled font or
  new dependency unless needed. On-screen fonts must not change exported workbook styling.
- Remove the first card's explicit featured styling; add consistent hover styling without
  removing keyboard focus. Inspect the reported Prepare preview text artifact before fixing it.

## 2. Field editor layout and selection

PEND-003, 004, 008, 009.

- Replace the fixed mapping-pane layout with a real splitter; retain synchronized row scrolling
  and provide horizontal and vertical scroll access to both panes.
- Remove the editor's 560-pixel maximum-width restriction and horizontal-scroll prohibition.
  Make the editor resize sensibly and its Input/Output groups reachable at 1080p and scaling.
- Reorganize controls into modestly separated Input, Output, and relevant advanced groups.
  Add concise labels and explanatory tooltips without changing processing defaults.
- Reuse bulk-selection controls for actual checkbox lists/groups across workflows. Clearly label
  the affected scope; do not bulk-confirm safety/interpretation decisions. Single independent
  option toggles do not need redundant Select all buttons.

## 3. Type-aware profiles and timezone controls

PEND-005, 006, 007.

- Share type-aware profile controls between the selected-field editor and sequential wizard,
  avoiding duplicated option logic. Offer appropriate presets and Custom for every supported type.
- Keep parsing/formatting logic outside UI handlers. Extend the existing profile/recipe execution
  mechanisms narrowly, preserving old profile IDs, existing recipes, undo/redo, and templates.
- Distinguish input parsing, arithmetic transformations, and final output representation. Provide
  before/after samples and clear validation; unsupported custom tokens must not silently succeed.
- Support a documented practical set of Excel-style numeric/date/time patterns rather than
  claiming complete Excel-format-language compatibility without verification.
- Use one editable timezone control: UTC, Colombo, Custom, then half-hour fixed offsets and the
  complete named-zone list, including valid 45-minute regions. Source-column choices must remain
  column selectors when a timezone is read from data. Preserve DST ambiguity handling.
- A chosen type should update the available transformations and formatting options without
  silently applying a new conversion, discarding user input, or changing measurement values.

## 4. Efficient verification and local handoff

- Work locally in one task, reuse existing components/dependencies, and inspect targeted files.
- Run small focused tests per changed area: palettes/preferences, controls/splitters, format
  parsing/serialization, timezone choices, bulk scope, and old-recipe compatibility.
- Use small synthetic CSV/TSV/XLSX cases and boundary values. Avoid repeating unrelated
  million-row benchmarks or full Windows rebuilds during each UI iteration.
- Automate palette contrast checks and use a small native screenshot matrix for Home, selected
  field, and data preview in Light/Dark at 1080p and scaled/minimum sizes.
- Run the full lint/format/type/regression suite once after integration; rerun only affected
  checks for any fixes, followed by the final proportionate release gates.
- Update version/lock metadata, requirements, changelog, guide, and handoff. If producing local
  binaries, build the portable ZIP and existing EXE installer after source verification, using
  the established smoke, reopen-verification, C-lite, and checksum workflows.

## Original questions (answered above)

1. With output format `0.00` and source value `1.2345`, should CSV contain `1.23`, or retain
   `1.2345` while Excel/preview displays `1.23`? Calculations should retain precision until an
   explicitly selected arithmetic rounding operation, independently of this export choice.
2. Does the example `0,000.00` mean deliberate leading-zero padding, or was ordinary thousands
   grouping (`#,##0.00`) intended? Both can be offered, but presets/examples must state the effect.
