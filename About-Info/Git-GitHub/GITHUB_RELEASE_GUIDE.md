# GitHub Release Guide

Do not release until the repository passes Phase 10 readiness.

1. Confirm no private/operational datasets or secrets are tracked.
2. Run all lint, type, test, performance, and clean-Windows package checks.
3. Update the central version, lockfile, notices, and changelog.
4. Build the Windows installer and compute checksums.
5. Commit only with owner approval.
6. Create an annotated `vMAJOR.MINOR.PATCH` tag.
7. Push commit/tag only with owner approval.
8. Create a GitHub release with changes, limitations, requirements, artifacts, and checksums.
9. Mark alpha/beta builds as pre-releases.
10. Download and re-verify the published artifact.

Build outputs belong in CI artifacts or Releases, not Git history.
