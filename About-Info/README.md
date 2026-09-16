# Documentation Map

This directory holds detailed project knowledge so a human or a new Codex session can
continue without relying on chat history.

For readers, start with the [public Wiki](https://github.com/GGadash/GDTT/wiki) or its
[versioned Home page](Wiki/Home.md). Current release limitations, licensing and workflow guides
are grouped there; historical phase notes should not be read as current feature availability.

| Need | Read |
|---|---|
| Summary-first user documentation | `Wiki/Home.md` and its linked pages |
| Publish or maintain the wiki | `Human-Docs/WIKI_MAINTENANCE.md` |
| Complete local GitHub wiki checkout and refresh steps | `exports/wiki-publish/` from the project root; see `Human-Docs/WIKI_MAINTENANCE.md` |
| Current status and next task | `AI-Handoff/CURRENT_STATE.md`, `NEXT_STEPS.md` |
| Architectural choices | `AI-Handoff/DECISIONS.md`, `Architecture/ARCHITECTURE.md` |
| Product overview and usage | `Human-Docs/PROJECT_OVERVIEW.md`, `USER_GUIDE.md` |
| Release candidate and clean-computer checks | `Human-Docs/RELEASE_ACCEPTANCE.md` |
| Data behavior | `Data-Processing/` |
| Find or change code | `Architecture/MODULE_MAP.md`, `Modification-Guides/` |
| Git, GitHub, recovery, releases | `Git-GitHub/` |
| Work effectively with Codex | `Vibe-Coding/` |
| Stable requirements/config schemas | `Machine-Readable/` |
| Editable architecture and workflow diagrams | `Diagrams/` |

Application code is in `src/data_transform_tool/`; tests are in `tests/`; versioned
profiles and templates live in `config/`; packaging scripts live in `scripts/` and
`packaging/`. UI code is under `ui/`, while calculations must live in UI-independent
domain modules introduced by their implementation phases.
