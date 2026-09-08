# Project Overview

GDTT — Data Transform Tool by Gadash (Akila DJ) is a local Windows application for
environmental and generic time-series datasets, with initial emphasis on air quality,
meteorology, and noise.

It will transform and standardize columns, dates, timestamps, timezones, units, missing
values, and expected sampling grids; calculate completeness-aware aggregates; export CSV
and XLSX; and reopen outputs for verification. Every material inference is visible and
overridable. Source datasets are never overwritten by default or uploaded.

The product is being delivered in specification-defined phases. Version 0.9.0 provides working
source inspection; reversible Reformat and Averaging configuration/proposed-preview workspaces;
spill-backed full-file execution; CSV and plain/formatted XLSX output; reports and versioned
local templates; streamed post-export reopen verification; and build-host-verified portable and
installer artifacts. Single-file and compatible multi-file inputs can be browsed or dropped;
batch files are schema-checked against the first reference file and exported with independent
verification evidence. Separate clean-Windows release validation remains in Phase 9.

The separate Data Splitter & Joiner supports field groups, exact timestamp parameter joins,
chronological file joining, and calendar/season splitting. It has per-source formats/timezones,
explicit boundary times/zones, preview, background cancellation, and verified new-folder exports.
