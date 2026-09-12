# Next Steps

## Current owner instruction — publication (2026-09-12)

Commit and push reviewed 0.10.0 sources, create/push the unused `v0.10.0-rc.1` tag, and confirm
Windows/Linux CI plus the tagged Windows build/release workflow finish successfully. Verify all
eight published assets and downloaded checksums; keep the release a pre-release and do not alter
historical tags/assets. Portable ZIP and installer EXE filenames must identify their purpose.
Archive old local residue recoverably and keep datasets, tools, environments and generated
artifacts out of Git. This supersedes the earlier local-only restriction below; no shutdown.

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
