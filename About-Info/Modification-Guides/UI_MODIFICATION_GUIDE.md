# UI Modification Guide

Semantic colors live in `ui/theme.py`; reusable components in `ui/widgets/`; screens in
`ui/views/`; and global chrome/navigation in `ui/main_window.py`.

Preserve keyboard focus, accessible names, high contrast, large primary actions, progressive
disclosure, and System/Light/Dark behavior. Avoid fixed pixel layouts except bounded control
sizes, and test at minimum window size. UI handlers may construct/validate commands but do
not perform parsing, transformation, aggregation, or file export calculations.

For visual changes, capture light and dark screenshots after launch once screenshot tooling
is part of the workflow.
