# Modification Prompt Patterns

## Small change

`Read AGENTS.md and handoff files. Modify only <specific behavior>. Preserve <related
behavior>. Add/update focused tests and update the requirement registry, changelog, and
CURRENT_STATE.md.`

## Bug fix

`Investigate before changing code. Reproduce <symptom> with a test, identify the responsible
module, fix the smallest component, run regressions, and document the cause and fix.`

## New feature

`Add <feature> through the relevant domain strategy/registry, not directly in UI handlers.
Expose it through the application/UI layers, add tests and documentation, and preserve
unrelated workflows.`

## UI-only

`Change only presentation/layout/theme behavior. Do not alter parsing, transformations,
recipe semantics, or exports. Verify Light/Dark, keyboard focus, and minimum window size.`

## Engine / averaging / import / export

Name the exact requirement, input/output examples, null/timezone/completeness expectations,
and modules allowed to change. Require headless tests before GUI integration.

## Refactor / performance

State behavior that must remain identical. Require benchmark evidence for optimization and
avoid mixing cleanup with feature changes.

## Packaging/release

Require locked dependencies, clean-Windows verification, license inventory, changelog,
checksums, and explicit approval before commits/tags/pushes.
