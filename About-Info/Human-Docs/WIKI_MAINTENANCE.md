# Maintaining the public wiki

## Summary

The user guide lives at https://github.com/GGadash/GDTT/wiki. Its reviewed Markdown source is
versioned under `About-Info/Wiki/` in the application repository. GitHub stores the live wiki in
a separate `GGadash/GDTT.wiki.git` repository; pushing main alone does not update the wiki.

This is documentation for the Windows app, not a GitHub Pages deployment of the desktop app.
Public readers do not need a GitHub account. Keep wiki editing restricted to collaborators.

## Structure and source of truth

Home opens with a short overview and a reading order. Each content page begins with Summary;
the sidebar links every guide and the footer links licensing and release limitations.
The 14 content pages cover setup, three workflows, formats/timezones, gaps/nulls, exports,
files/folders, appearance, architecture, troubleshooting, release safety and credits.

Keep current UI/code, the root LICENSE, THIRD_PARTY_NOTICES, machine-readable schemas,
CHANGELOG and published release evidence authoritative. Do not turn old phase proposals into
claims of implemented features. Versioned wiki sources make changes reviewable and recoverable.

## Review and publication procedure

1. Fetch the application repository and the separate wiki before editing. Preserve unreviewed
   web edits; compare them with the versioned source and reconcile rather than overwriting.
2. Edit affected files in About-Info/Wiki and relevant underlying guides. Update the documented
   release/version, test evidence, unsigned/clean-Windows status and date only from evidence.
3. Run `uv run python scripts/verify_wiki_docs.py`, `git diff --check` and
   `uv run python scripts/audit_release_tree.py`. Verify any new external links separately.
4. Commit and push reviewed application documentation only with publication authority.
5. Clone `https://github.com/GGadash/GDTT.wiki.git` into an ignored working directory, such as
   `exports/wiki-publish/`. GitHub requires an initial Home page saved in the web UI first.
6. Synchronize the reviewed Markdown source into that clone, including _Sidebar.md and
   _Footer.md. Inspect its diff, commit and push the wiki's existing default branch.
   Do not force-push, delete unrelated pages or overwrite unreconciled collaborator changes.
7. Check the anonymous live Home page, sidebar, diagrams and important navigation/download links.
   Read back remote Git hashes/content to confirm publication. Record completion in AI-Handoff.

A browser-automation failure is not a reason to invent credentials or bypass login. Ask an
authorized maintainer to save the initial Home page; normal Git publication can then proceed.
If publication is pending, say so explicitly and link the source copy instead of claiming it live.

## Documentation-only boundary

Documentation/settings changes do not change app version 0.10.1, rebuild binaries, retag the
release, or replace verified assets. CI may still run its normal checks on the main documentation
commit. The historical source ZIP remains the snapshot tied to its release tag.
