# License, credits and support

## Summary

GDTT is **Data Transform Tool by Gadash (Akila DJ)**. OpenAI Codex assisted with architecture, implementation, documentation and verification. Original GDTT work and third-party dependencies do not share one blanket license.

## Copyright and project license

The app's About panel displays **Copyright (c) 2026 Gadash +**. The authoritative root [LICENSE](https://github.com/GGadash/GDTT/blob/main/LICENSE) currently retains the owner's supplied **Copyright (c) 2026 Akila DJ +** notice. This documentation preserves those notices; it does not silently rewrite the license or label it MIT/Apache.

The project license text is:

> GDTT — Data Transform Tool by Gadash (Akila DJ) License
>
> Copyright (c) 2026 Akila DJ +
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software to use, copy, modify, merge, publish, distribute, sublicense,
> and/or sell copies, without restriction.
>
> The software is provided "as is", without warranty of any kind, express or
> implied. In no event shall the authors or copyright holders be liable for any
> claim or damages arising from its use.
>
> Attribution is not legally required, but citing GDTT / Data Transform Tool by Gadash (Akila DJ)
> is greatly appreciated if this project is useful to you.

The versioned LICENSE governs if a summary elsewhere differs. Its optional-attribution wording does not cancel obligations imposed by dependencies' own licenses.

## Development and third-party credits

[OpenAI Codex](https://openai.com/codex/) supported the AI-assisted development process. This is a development credit, not an endorsement, security certification, warranty or commitment by OpenAI to provide GDTT support.

| Product | Role |
| --- | --- |
| Python | Language and standard library, including datetime/Decimal/SQLite facilities |
| PySide6 / Qt for Python | Desktop UI |
| Pydantic | Validated configuration models |
| platformdirs | Per-user application paths |
| tzdata | IANA timezone data, including on Windows |
| charset-normalizer | Text encoding detection |
| openpyxl | XLSX reading and reopening verification |
| XlsxWriter | Plain and formatted XLSX output |
| uv and Hatchling | Dependency management and Python builds |
| pytest, pytest-qt, pytest-cov | Automated test tooling |
| Ruff and mypy | Formatting/lint and static type checks |
| Git and GitHub Actions | Source history and automated checks/release builds |
| PyInstaller | Portable Windows application packaging |
| NSIS | Current-user Windows installer |
| Polars, PyArrow and DuckDB | Optional benchmark/optimization candidates, not the current mandatory production engine |

The [complete third-party notices](https://github.com/GGadash/GDTT/blob/main/THIRD_PARTY_NOTICES.md) link products and license sources. The app's About / Components tab shows installed component versions; `uv.lock` and the release manifest identify the corresponding build environment. Review actual bundled licenses when redistributing.

## Limitations and disclaimers

The current release is unsigned and has not completed separate hands-on clean-Windows acceptance. Automated test success does not guarantee correctness for every input or regulatory suitability. Preserve backups and independently review consequential outputs. See [Release status and safety](https://github.com/GGadash/GDTT/wiki/Release-Status-and-Safety).

## Attribution

Suggested citation: **GDTT — Data Transform Tool by Gadash (Akila DJ), version 0.10.1**, with the [project URL](https://github.com/GGadash/GDTT) and the exact release used.

## Sponsor and help GDTT

If GDTT is useful to you, you can support its creator through Ko-fi:

- [Support Gadash on Ko-fi](https://ko-fi.com/gadash)
- [GDTT project support on Ko-fi](https://ko-fi.com/s/00a96c800b)

You can also help without donating: [report a reproducible issue, suggest a feature or propose a documentation improvement](https://github.com/GGadash/GDTT/issues). Remove private data and credentials from examples before sharing.

Donations are optional. They do not change the license, grant a warranty or guarantee feature delivery. Do not send account credentials or payment details through issues or documentation.
