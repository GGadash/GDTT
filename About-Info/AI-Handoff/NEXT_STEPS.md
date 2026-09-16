# Next Steps

## Current owner instruction — public repository and wiki (2026-09-16)

Complete: repository is public and the live wiki is published at https://github.com/GGadash/GDTT/wiki
(wiki master 2d23538233ce4e6fd6662662110156258bc956d3). Fourteen guide pages, sidebar/footer and
the retained initial landing link are present. Source navigation/license validation and anonymous
live content/footer checks passed. Reviewed sources are under About-Info/Wiki; CI runs
scripts/verify_wiki_docs.py. Follow WIKI_MAINTENANCE.md and reconcile any future web edits.
Next optional owner review: read the live wiki/diagrams in a browser and report wording/layout
preferences. Separate hands-on clean-Windows/DPI acceptance and signing remain unchanged.
No new release, binary rebuild, signing, shutdown or history rewriting is part of this docs task.

## Current owner instruction — ISO update and publication (2026-09-15)

Complete: PEND-017 shipped as v0.10.1-rc.1 from 3f33567. All 224 tests, local binary/installer
verification, C-lite, Windows/Linux CI and tagged Windows build/release passed. Eight published
assets were independently downloaded; six release checksums and all eight GitHub digests matched.
Older local output/evidence is recoverable under exports/archive/2026-09-15-pre-0.10.1/.
Next: owner review of ISO selections and actual DPI, separate clean-Windows acceptance, then a
signing decision before stable promotion. Keep historical releases/tags untouched; no shutdown.

## Current owner instruction — publication (2026-09-12)

Complete: source commit `4789a83` and tag `v0.10.0-rc.1` are pushed; Windows/Linux CI and Windows
build/release all passed. Eight correctly named assets are published and independently verified
(six checksum entries plus eight GitHub digests). Older local builds/evidence are preserved in
`exports/archive/2026-09-12-pre-release/`; generated artifacts and private data remain outside Git.
Next: owner review at actual monitor DPI/scaling, separate clean-Windows acceptance, and a signing
decision before promotion to stable. Keep existing historical tags/assets unchanged. No shutdown.

## Current owner instruction — 0.10.0 update (2026-09-10)

PEND-001 through PEND-016 are implemented locally as 0.10.0. Numeric questions were answered:
round export values by default, optional Excel display-only precision, and independent dot/comma
input/output separators. Local tests, portable/installer and C-lite acceptance passed. Review
the generated `packaging/output/RELEASE_CANDIDATE.md` and `LOCAL_C_LITE.json` for final evidence.
Owner review of actual monitor scaling and separate clean-host/unsigned-artifact acceptance
remain external. Test the local 0.10.0 build, then authorize publication separately if satisfied.
Publication was subsequently authorized on 2026-09-12; no shutdown is requested.

## Current owner request: 0.9.0 Split & Join

Local 0.9.0 tests, layout checks, portable/installer verification, automatic output names, and
C-lite acceptance are complete. `v0.9.0-rc.1` is published with all eight assets; Windows/Linux CI,
the Windows release workflow, six downloaded content checksums, and eight asset digests passed.
Next, test the downloaded portable/installer builds on a separate Windows computer. Keep this a
pre-release until the external acceptance gates below are completed.

## Existing external acceptance gates

1. Combination A, Combination B, and optional Combination D are complete on this Windows build
   host.
2. Local Combination C-lite is complete. Combination C's remaining external gate is to use a
   separate clean Windows computer and verify install/launch/uninstall.
   - The current host cannot provide that environment because Windows Sandbox is absent and
     firmware virtualization is disabled.
   - Enable firmware virtualization and install Windows Sandbox, or use another clean Windows
     VM/host, or use another physical computer. Follow
     `About-Info/Human-Docs/RELEASE_ACCEPTANCE.md`; Windows Sandbox is not required.
3. On that clean computer, include single-file picker, drag/drop, compatible multi-file batch,
   incompatible-batch blocking, per-file reopen verification, and Process more similar files in
   the manual acceptance pass.
4. Record Light/Dark release screenshots from the clean environment.
5. Decide code signing only after the owner provides or selects a signing identity; unsigned
   development artifacts remain valid for testing.
6. Review the generated release-candidate artifacts and complete the clean-host evidence.
7. `v0.8.0-rc.3` completed CI, the Windows package/installer/source/C-lite gates, shared
   finalization, artifact upload, and automatic GitHub pre-release publication. All eight
   published assets were downloaded independently and their six content checksums passed the
   included verifier. Preserve RC1 and RC2 as historical failure evidence; do not rewrite them.
8. The source is published at `GGadash/GDTT`; keep GitHub CI green and continue to require
   explicit owner authorization for future commits, pushes, tags, and releases.
