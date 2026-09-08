# Next Steps

## Current owner request: 0.9.0 Split & Join

Local 0.9.0 tests, layout checks, portable/installer verification, automatic output names, and
C-lite acceptance are complete. Source is pushed and Windows/Linux CI passed. The owner now
authorizes binary publication: push the annotated `v0.9.0-rc.1` tag, await automated verification
and publication, then independently download and verify all eight Release assets. Keep this a
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
