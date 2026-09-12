# Pending modification requirements

Recorded: 2026-09-10 (Asia/Colombo)

## Authorization and status: implemented locally in 0.10.0

The original notes-only hold was superseded on 2026-09-10 when the owner requested these changes,
an efficient implementation plan, and a suitably versioned modified app. The 15 original items
plus PEND-016 are implemented. The numeric questions were answered and incorporated; see
IMPLEMENTATION_PLAN_0_10_0.md and Human-Docs/FORMATTING_AND_APPEARANCE.md for the final scope.
Commit/push/tag/publication are not authorized by this request.

The bullets below retain the original requirement wording for traceability. PEND IDs are stable;
their implemented status and test references are in Machine-Readable/requirements_registry.json.
The published 0.9.0 release remains unchanged.

## PEND-001 — About copyright wording

- Location: the app's About section.
- Current wording supplied by the owner: `Copyright (c) 2026 Akila DJ +`
- Required replacement: `Copyright (c) 2026 Gadash +`
- Preserve the year and trailing plus sign. This request specifically names About; changes to
  the root license or other attribution text are not assumed from this item.

## PEND-002 — Clear local-processing footer

- Current footer: `Private by design • No dataset upload`.
- Owner request: explain its meaning and replace the vague wording with a clearer statement
  about local/offline processing and no cloud upload.
- Meaning under the existing specification: dataset processing takes place on the user's
  computer; the app does not upload datasets for cloud processing.
- Proposed wording, not yet applied or approved verbatim:
  `Processed locally on your computer • No cloud upload`
- Avoid implying that this label promises file encryption or controls other applications.
- Later refinement: keep this message small and unobtrusive; see PEND-015. Clear wording does
  not mean giving offline/local operation greater visual prominence.

## PEND-003 — Checkbox bulk-selection controls

- Owner request: include Check all / Select all and Deselect all capabilities wherever the
  app presents checkboxes.
- Cover relevant checkbox lists/groups throughout the app, not only the field-mapping screen.
- Clarification to resolve when planning implementation: the scope of each bulk action,
  including filtered/hidden items and standalone decision/confirmation checkboxes. Bulk
  selection should not silently acknowledge consequential confirmations.

## PEND-004 — Resizable Configure fields sections and scrolling

- Location: field mapping, Configure fields.
- First section described by the owner: row/index column, Export checkboxes, Input column,
  and related columns.
- Other section: Detected type and the remaining configuration columns.
- Reported issue: the divider between the two sections cannot be adjusted.
- Required behavior: make the divider draggable so the sections can be resized.
- Retain scrolling and provide both horizontal and vertical scrollbars for the mapping
  sections, with access to all rows/columns when content exceeds the available space.
- Preserve existing selection, mapping, and processing behavior; this is a layout/usability
  request, not a change to transformation rules.

## PEND-005 — Type-aware selected-field options

- Location: the modification/configuration workflow's selected-field/column editor.
- Reported issue: output formatting/transformation options remain the same when the selected
  type changes, including date, integer, and numeric types.
- Required behavior: present options appropriate to the chosen type. Numeric/integer/decimal
  types need suitable numeric options; date/time types need date/time options.
- Provide a Custom option for every type, not only numeric or date/time fields.

## PEND-006 — Common and custom input/output profiles

- Input profile choices must cover all supported types and include Custom.
- Both input and output sections must offer common numeric settings, common date/time settings,
  and custom settings where appropriate to the type.
- Permit typed custom format patterns using familiar Excel-style notation, including `0`, `#`,
  and date/time tokens. Owner examples, retained exactly: `0.00`, `0,000.00`, `yyyy-MM-dd`.
- Planning clarification for later: define the supported pattern syntax and demonstrate its
  effect. Do not silently replace the owner's `0,000.00` example with a different grouping mask.
  Distinguish input parsing rules from output display/serialization rules.

## PEND-007 — Editable timezone/source choices and ordered presets

- Owner request: timezone and source-value entries must allow custom typing as well as dropdown
  selection. Confirm the precise source-value controls during the later implementation review.
- Dropdown order: UTC first, Colombo second, Custom third, then the remaining list.
- Include the main zones and choices in 30-minute increments; retain access to the full list,
  rather than restricting users to a few presets.
- Planning clarification for later: distinguish named geographic zones from fixed UTC offsets,
  and retain valid non-half-hour zones when providing the full zone list.

## PEND-008 — Clear Input and Output subsections

- Reorder the selected-field editor into clearly identifiable Input and Output subsections.
- Use modest visual separation, without excessive spacing or unnecessarily large sections.
- Use concise, self-descriptive labels for entries, options, and buttons.
- Add tooltips for complex controls/buttons and settings whose purpose needs explanation.
- Keep the common/custom profile and timezone controls organized consistently with their
  input or output purpose.

## PEND-009 — Accessible, resizable selected-field editor

- Reported issue: on a 1080p display, this editor is partly hidden and dropdown controls/options
  cannot be seen properly because too little space is available.
- Make the selected-field editor more discoverable and allow its available space to be resized.
- Add scrolling so all configuration controls remain reachable in constrained layouts, and
  ensure dropdowns can be opened and their options read without clipping.
- Cover the editor as well as the mapping-table divider recorded in PEND-004; improving one
  must not leave the other inaccessible.
- Later acceptance should include a 1920 x 1080 display and relevant Windows display scaling.

## PEND-010 — Compact monospaced data-display font

- Use a small, readable monospaced font in Proposed output and other views displaying data.
- Owner preference: Consolas or a similar attractive free alternative. Font choice/fallback
  and any redistribution requirements are to be checked during later implementation planning.
- This concerns on-screen data presentation, not changes to exported file content or formatting.
- Keep values legible and aligned, including dates, numbers, null markers, and long text.

## PEND-011 — Compact font-size controls

- Add small font-size decrease/increase buttons in the top section, near the Dark/Light theme
  selector (the owner's "darl/light" wording is understood as Dark/Light).
- Keep these controls compact; use clear symbols/labels and explanatory tooltips.
- Later planning should define whether resizing applies to all UI text or only data views,
  while retaining monospaced data text and keeping controls accessible at 1080p.

## PEND-012 — Simple selectable color palettes

- Add a small theme-color button/control near the existing theme and font-size controls.
- Keep the current greenish palette as the default and give it a recognizable name.
- Add blue, grey, another single-color palette, and a multicolor palette.
- Proposed names for later review: Teal (current/default), Blue, Graphite (grey), Violet
  (additional single-color choice), and Spectrum (multicolor). These are proposals, not applied.
- Limit the change to coordinated text, background, border, and accent colors; avoid a major
  redesign or unrelated layout changes. Reusing palette/RGB values is acceptable where suitable.
- Check each palette in Dark mode as well as Light mode. Maintain readable contrast and
  recognizable selected, hovered, disabled, warning, and error states rather than relying on
  an unchecked RGB substitution. Keep existing Dark/Light/Auto/System behavior available.

## PEND-013 — Consistent Home workflow cards and hover emphasis

- Reported issue: the first Home workflow card looks selected because its border differs from
  those of the other two cards.
- Make all three cards visually consistent in their resting state, without an apparently
  preselected first card.
- Highlight the card under the mouse pointer; remove that hover emphasis when the pointer leaves.
- Preserve usable keyboard-focus indication while avoiding a misleading persistent selection.

## PEND-014 — Split & Join Prepare preview text artifact

- Reported issue: the Prepare preview button in Split & Join appears to contain additional or
  overlapping text.
- Investigate the actual rendering after implementation is authorized; the cause is not yet
  established. Ensure the button displays a single clear, readable Prepare preview label.
- Later verification should include relevant display scaling, resized layouts, and themes.

## PEND-015 — Subtle offline/local-operation messaging

- Do not repeatedly or prominently emphasize that the application is offline/local.
- Use small text or a small button/badge for this information.
- Coordinate this with PEND-002: explain local processing clearly but keep it visually secondary
  to workflow and data controls. This is a presentation change, not a change to offline behavior.

## Further requirements

### PEND-016 — Confirmed numeric export and decimal separators

Owner clarification: the main behavior rounds 1.2345 to 1.23 for an output mask of 0.00.
An optional mode preserves 1.2345 and uses Excel formatting to display 1.23. Grouping means
`#,##0.00`; common `0.00`, grouped and custom options are required. Independent input/output
dot or comma decimal separators support EU/French data. Implemented locally in 0.10.0;
see `About-Info/Human-Docs/FORMATTING_AND_APPEARANCE.md` for exact scope and limits.

Append subsequent owner requests with new pending IDs. Do not assume new items beyond the
currently approved PEND-001 through PEND-016 scope are authorized merely because they are noted.
