# Third-Party Notices and Development Credits

GDTT — Data Transform Tool by Gadash (Akila DJ) is authored by Gadash (Akila DJ) through an AI-assisted development process
with OpenAI Codex. OpenAI Codex helped analyze the specification, design the architecture,
create code and documentation, and execute verification; the repository remains the
source of truth for the resulting work.

The project license in `LICENSE` applies to original GDTT code and does
not replace dependency licenses. The current application and development workflow use:

| Product | Purpose | Project and license information |
|---|---|---|
| Python | Application language and standard library | https://www.python.org/ and https://docs.python.org/3/license.html |
| PySide6 / Qt for Python | Windows desktop user interface | https://doc.qt.io/qtforpython-6/ and https://doc.qt.io/qtforpython-6/licenses.html |
| Pydantic | Validated configuration models | https://docs.pydantic.dev/ and https://github.com/pydantic/pydantic/blob/main/LICENSE |
| platformdirs | Per-user settings and log paths | https://platformdirs.readthedocs.io/ and https://github.com/tox-dev/platformdirs/blob/main/LICENSE |
| tzdata | IANA timezone database for Windows | https://pypi.org/project/tzdata/ and https://github.com/python/tzdata/blob/master/LICENSE |
| charset-normalizer | Text encoding detection | https://charset-normalizer.readthedocs.io/ and https://github.com/jawah/charset_normalizer/blob/master/LICENSE |
| openpyxl | Read-only XLSX inspection and verification | https://openpyxl.readthedocs.io/ and https://foss.heptapod.net/openpyxl/openpyxl/-/blob/branch/3.1/LICENCE.rst |
| XlsxWriter | Plain and formatted XLSX creation | https://xlsxwriter.readthedocs.io/ and https://github.com/jmcnamara/XlsxWriter/blob/main/LICENSE.txt |
| Polars | Phase 9 lazy/streaming processing benchmark and selected primary production-engine candidate | https://pola.rs/ and https://github.com/pola-rs/polars/blob/main/LICENSE |
| PyArrow / Apache Arrow | Phase 9 record-batch and streaming-interchange benchmark | https://arrow.apache.org/docs/python/ and https://www.apache.org/licenses/LICENSE-2.0 |
| DuckDB | Optional Phase 9 out-of-core/local-query benchmark candidate | https://duckdb.org/docs/stable/ and https://github.com/duckdb/duckdb/blob/main/LICENSE |
| uv | Python and dependency management | https://docs.astral.sh/uv/ and https://github.com/astral-sh/uv/blob/main/LICENSE-MIT |
| Hatchling | Python build backend | https://hatch.pypa.io/ and https://github.com/pypa/hatch/blob/master/LICENSE.txt |
| pytest / pytest-qt / pytest-cov | Automated testing | https://pytest.org/, https://pytest-qt.readthedocs.io/, and https://pytest-cov.readthedocs.io/ |
| Ruff | Linting and formatting | https://docs.astral.sh/ruff/ and https://github.com/astral-sh/ruff/blob/main/LICENSE |
| mypy | Static type checking | https://mypy-lang.org/ and https://github.com/python/mypy/blob/master/LICENSE |
| Git | Local source history and recovery | https://git-scm.com/ and https://github.com/git/git/blob/master/COPYING |
| PyInstaller | Build-time Windows one-directory application packaging | https://pyinstaller.org/ and https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt |
| NSIS | Build-time current-user Windows installer creation | https://nsis.sourceforge.io/ and https://nsis.sourceforge.io/Docs/AppendixI.html |

Before any public release, regenerate and review a complete dependency/license inventory
from the actual lockfile and packaged artifact.
