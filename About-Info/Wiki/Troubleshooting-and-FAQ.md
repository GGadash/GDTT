# Troubleshooting and FAQ

## Summary

Most blocked previews require an explicit data decision, not reinstalling the app. Read the displayed reason and check the selected type, profile, timezone, markers and interval. Start with a small sanitized sample.

## Windows says “Unknown publisher” or blocks the app

The current release is unsigned. Verify the official release and hashes; keep security protections enabled and follow your organization's policy. See [Release status and safety](https://github.com/GGadash/GDTT/wiki/Release-Status-and-Safety). Do not assume every security warning is a harmless false positive.

## The portable EXE cannot find components

Extract the **whole** ZIP and retain the support files beside `GDTT.exe`. Do not run only an EXE copied out of the bundle, or run it directly inside the ZIP. Record the exact error if a complete extraction still fails.

## I cannot see a field control

Enlarge the selected-field panel using its divider, scroll horizontally/vertically or use the sequential wizard. Try a smaller interface font. Include Windows scaling percentage and resolution in a clipping report.

## Numeric fields show unexpected formats

Both input/output lists follow the selected type. Choose Decimal/Numeric for numeric masks or DateTime for ISO timestamps. Explicit type changes reset profiles. Custom is near the top and accepts the documented mask subset, not arbitrary Excel syntax.

## UTC output says the source timezone is unknown

A naive local timestamp is not automatically UTC. Select its actual input format, configure the source timezone and a target timezone, then review the converted sample. An embedded Z/offset already defines an instant. Do not add a literal Z to disguise an unknown zone.

## My decimal-comma values fail parsing

Choose comma as the **input** decimal separator. For thousands grouping, select a grouped input mask such as `#,##0.00`. Decimal-comma CSV fields remain quoted in comma-delimited exports. Excel displays separators according to regional settings.

## Why does a batch refuse one file?

Batch Reformat/Averaging requires matching file type, ordered field names, header/delimiter/quote choices and relevant worksheet name. Compare the mismatch explanation with the first reference file. Split / Join may fit intentionally different field structures.

## Why are there new rows or missing aggregate results?

Gap rows appear only when enabled and configured; measurements are not interpolated. Aggregate results can be missing because completeness did not meet the selected threshold. Review missing markers, input interval, boundaries and valid/expected counts rather than lowering a threshold blindly.

## Why did Split / Join create fewer files or no joined rows?

Time splits write only populated periods. Inner joins keep only instants common to every source; an empty match can be a valid header-only table. Check source zones, timestamp precision, selected fields and duplicate policy.

## Does GDTT upload my datasets?

Normal dataset processing is local and requires no cloud account. Downloading releases/dependencies, visiting links, filing issues or making donations are separate online actions. Logs, recipes and reports still require privacy review before you share them.

## Can I use this for compliance reporting?

Do not infer regulatory certification from an exported file or a Passed verification result. Independently validate the required method and dataset. The app is an unsigned pre-release with explicit remaining acceptance gates.

## Report a reproducible problem

Use [GitHub Issues](https://github.com/GGadash/GDTT/issues/new/choose). Include app version, Windows build/scaling, workflow, exact steps, expected result and actual result. Prefer synthetic examples showing the problem, plus sanitized error text/screenshots.

Never post credentials, private monitoring datasets or unreviewed logs publicly. If a problem may expose sensitive information, report only a non-sensitive summary and request an appropriate private reporting route before sharing details.

Useful references: [Current known issues](https://github.com/GGadash/GDTT/blob/main/About-Info/AI-Handoff/KNOWN_ISSUES.md) · [Release acceptance](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/RELEASE_ACCEPTANCE.md).
