# Appearance and accessibility

## Summary

Interface preferences change the app's presentation, not your dataset or exported spreadsheet styling. Resize panels and adjust the font before assuming controls are missing.

## Themes and colors

- **Light** and **Dark** use the app's respective palettes.
- **Auto** follows the operating-system color preference and is the clean-install default.
- **System** delegates its palette to Qt's native platform style.
- **Teal** is the original accent; Blue, Graphite, Violet and Spectrum are alternatives.

Palette preferences persist. System styling can differ from the app's custom light/dark palettes.

## Text and data tables

Use the small **A- / A+** header controls beside Theme to adjust the base interface font between 10 and 20 pixels. Data tables use a smaller monospaced font, normally Consolas or an installed monospace fallback. GDTT does not bundle a new proprietary font.

## Mapping/editor space

Drag the mapping divider and selected-field editor divider to resize them. Both horizontal and vertical scrolling are available; short windows can require scrolling down to additional controls. The sequential wizard is an alternative for reviewing one field at a time.

Home workflow cards use consistent styling and highlight on hover. Complex controls have tooltips where provided. Select all/Deselect all controls affect only their adjacent group, not safety decisions or overwrite permission.

## What still needs owner review

Automated light/dark contrast checks and native layout previews passed for the documented release work. Real per-monitor scaling, particularly an owner's actual 1080p/150% DPI combination, still needs hands-on review; this is not a claim of formal accessibility certification.

Report Windows scaling percentage, display resolution, chosen theme/font size and a sanitized screenshot if something is clipped. Excel export styling is configured separately on the export screen.

Source: [Formatting and appearance](https://github.com/GGadash/GDTT/blob/main/About-Info/Human-Docs/FORMATTING_AND_APPEARANCE.md).
