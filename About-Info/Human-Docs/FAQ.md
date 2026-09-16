# Frequently Asked Questions

Current guide: GDTT 0.10.1 / v0.10.1-rc.1, reviewed 2026-09-16.
See the [public wiki](https://github.com/GGadash/GDTT/wiki) or its
[versioned source](../Wiki/Home.md) for detailed instructions.

## Does the application upload datasets?

Normal dataset processing is local and does not require a cloud account. Downloads, repository
access and optional external links are separate online activities. Review logs, reports and
recipes for private names/metadata before sharing them; temporary spill data can contain values.

## Which workflows work?

Reformat / Transform, Average / Aggregate and the separate Data Splitter & Joiner are implemented.
Reformat/Averaging include compatible batch input and per-file export verification. AQI and
Reshape/Pivot are not implemented. Older phase descriptions are historical, not current availability.

## What does unsigned mean?

The current EXE and installer have no trusted publisher code-signing signature. Windows may
warn or block according to local policy. Checksums detect file changes but are not signatures
or a guarantee of safety. Keep Windows security enabled and verify the official release source.

## Has it been tested on Windows?

Automated tests, GitHub Windows/Linux CI, local packaging/installer checks and C-lite acceptance
passed for RC1. Separate hands-on acceptance on an ordinary clean Windows computer and actual
monitor/DPI review remain pending. Another physical computer is sufficient; no Windows Sandbox,
VirtualBox, Python, Git or hardware virtualization is required for the artifact-only test.
See [Release acceptance](RELEASE_ACCEPTANCE.md).

## Is a blank cell the same as an empty string?

No. Only canonical None is internally missing. Empty text is retained unless explicitly confirmed
as a missing marker. True Null produces an unquoted empty CSV field or genuinely blank XLSX cell.

## Does changing a timezone shift the instant?

Timezone conversion preserves the instant; Time Shift is a separate transformation. UTC Z output
requires a known source timezone and converts to UTC. It does not label unknown local time as UTC.

## Why are formats different between field types?

Both input and output presets follow the selected type. Choose DateTime for ISO formats,
Decimal/Numeric for numeric masks, or Custom for the supported type-specific mask subset.
Changing field type resets profiles for review. See [Formatting](FORMATTING_AND_APPEARANCE.md).

## Where are binaries and reports?

Download binaries from [GitHub Releases](https://github.com/GGadash/GDTT/releases), not the source
file listing. Exported datasets use your selected folder; settings, templates and logs use
per-user paths. See [Files and folders](../Wiki/Files-and-Folders.md).

## Can I use the public release?

The source and release downloads are public. RC1 is an unsigned pre-release; it is not a completed
stable-release acceptance claim. Back up inputs, test your workflow and independently validate
consequential outputs. The software is provided as is, without warranty under [LICENSE](../../LICENSE).
Dependency licenses remain separate; see [credits](../../THIRD_PARTY_NOTICES.md).
