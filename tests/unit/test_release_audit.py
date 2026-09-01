"""Release-source audit regression checks."""

from __future__ import annotations

import runpy
from pathlib import Path


def test_prospective_release_source_has_no_blocking_hygiene_findings() -> None:
    script = runpy.run_path("scripts/audit_release_tree.py")
    files, findings = script["audit"](Path.cwd())

    assert files
    assert not [finding for finding in findings if finding.severity == "error"]


def test_release_audit_supports_source_archive_without_git(tmp_path: Path) -> None:
    script = runpy.run_path("scripts/audit_release_tree.py")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/example.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "packaging/output").mkdir(parents=True)
    (tmp_path / "packaging/output/generated.exe").write_bytes(b"not-released")

    files = script["repository_files"](tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in files] == ["src/example.py"]
