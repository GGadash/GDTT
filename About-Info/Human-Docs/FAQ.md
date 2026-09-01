# Frequently Asked Questions

## Does the application upload datasets?

No. Dataset processing is local and offline-first.

## Why are the workflow buttons not processing files yet?

Version 0.1.0 is the Phase 1 repository and desktop foundation. File ingestion begins in
Phase 2.

## Is a blank cell the same as an empty string?

No. The processing engine will maintain a canonical missing state and export genuinely
blank CSV fields or XLSX cells when True Null is selected.

## Does changing a timezone shift the represented instant?

No. Timezone conversion preserves the instant; Time Shift is a separate transformation.

## Can I publish the project now?

Not yet. Complete implementation, license inventory, clean-data review, CI, packaging, and
release verification first. GitHub credentials are requested only after owner approval.
