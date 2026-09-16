# Project Overview

GDTT — Data Transform Tool by Gadash (Akila DJ) is a local Windows application for
environmental and generic time-series datasets, with initial emphasis on air quality,
meteorology, and noise.

It transforms and standardizes columns, dates, timestamps, timezones, units, missing
values, and expected sampling grids; calculates completeness-aware aggregates; exports CSV
and XLSX; and reopens outputs for verification. Every material inference is visible and
overridable. Source datasets are never overwritten by default or uploaded.

The product is being delivered in specification-defined phases. Version 0.10.1 provides working
source inspection; reversible Reformat and Averaging configuration/proposed-preview workspaces;
spill-backed full-file execution; CSV and plain/formatted XLSX output; reports and versioned
local templates; streamed post-export reopen verification; and build-host-verified portable and
installer artifacts. Single-file and compatible multi-file inputs can be browsed or dropped;
batch files are schema-checked against the first reference file and exported with independent
verification evidence. It also includes type-scoped Custom/numeric/date-time profiles, extended
and compact ISO presets, explicit decimal separators, palettes, font sizing and resizable editors.

The public v0.10.1-rc.1 release remains unsigned. Automated Windows/Linux CI and local C-lite
passed, but separate hands-on clean-Windows acceptance and actual-DPI owner review remain pending.
It is supplied as is, without warranty under the root LICENSE; validate your outputs independently.
See the [wiki](../Wiki/Home.md), [release safety](../Wiki/Release-Status-and-Safety.md) and
[license/credits](../Wiki/License-Credits-and-Support.md).

The separate Data Splitter & Joiner supports field groups, exact timestamp parameter joins,
chronological file joining, and calendar/season splitting. It has per-source formats/timezones,
explicit boundary times/zones, preview, background cancellation, and verified new-folder exports.
