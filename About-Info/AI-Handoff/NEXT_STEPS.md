# Next Steps

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
7. The `v0.8.0-rc.1` tag exposed and led to correction of an unresolvable mutable setup-uv
   reference before packaging began. After owner authorization, push `v0.8.0-rc.2` to exercise
   the corrected Windows build, verification, and GitHub Release publication.
8. The source is published at `GGadash/GDTT`; keep GitHub CI green and continue to require
   explicit owner authorization for future commits, pushes, tags, and releases.
