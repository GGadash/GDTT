# GitHub Release Guide

Do not release until the repository passes Phase 10 readiness.

1. Confirm no private/operational datasets or secrets are tracked.
2. Run all lint, type, test, performance, and clean-Windows package checks.
3. Update the central version, lockfile, notices, and changelog.
4. Build the Windows installer and compute checksums.
5. Commit only with owner approval.
6. Create an annotated `vMAJOR.MINOR.PATCH` tag, or a hyphenated pre-release tag such as
   `v0.8.0-rc.1`.
7. Push commit/tag only with owner approval. Pushing the tag is the explicit publication trigger.
8. The Windows workflow builds and verifies the candidate, checks that the tag base version
   matches `BUILD_MANIFEST.json`, creates the GitHub Release, and attaches the portable ZIP,
   installer, source archive, manifest, acceptance evidence, and checksums.
9. Hyphenated tags are automatically marked as pre-releases; stable tags create normal releases.
10. Download all published assets and run `VERIFY_CHECKSUMS.ps1` beside `SHA256SUMS.txt`.

Branch pushes, pull requests, and manually dispatched builds never publish a Release. If a
Release for the tag already exists, workflow reruns leave its assets unchanged.

Build outputs belong in CI artifacts or Releases, not Git history.
