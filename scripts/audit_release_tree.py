"""Audit prospective release-source files for hygiene and accidental disclosure.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    detail: str


EXCLUDED_COMPONENTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "exports",
    "htmlcov",
    "logs",
    "preview-output",
}
EXCLUDED_PREFIXES = {
    "packaging/output",
    "packaging/temp",
    "packaging/tools",
    "data/input",
    "data/output",
    "data/private",
}
BANNED_NAMES = {
    ".env",
    ".env.local",
    ".npmrc",
    ".pypirc",
    ".netrc",
    ".ds_store",
    "credentials.json",
    "desktop.ini",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "thumbs.db",
}
BANNED_SUFFIXES = {
    ".bak",
    ".crash",
    ".db",
    ".dmp",
    ".key",
    ".log",
    ".orig",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".swp",
    ".tmp",
}
GENERATED_BINARY_SUFFIXES = {".7z", ".dll", ".exe", ".msi", ".rar"}
DATASET_SUFFIXES = {".arrow", ".csv", ".feather", ".parquet", ".tsv", ".xls", ".xlsx"}
MAX_SOURCE_FILE_BYTES = 10 * 1024 * 1024
MAX_TEST_FIXTURE_BYTES = 1 * 1024 * 1024

SECRET_PATTERNS = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "assigned-secret",
        re.compile(
            r"""(?ix)
            \b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b
            \s*[:=]\s*
            ["'][^"'{}\s<>]{8,}["']
            """
        ),
    ),
    (
        "credential-url",
        re.compile(r"https?://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
    ),
)
LOCAL_PATH_PATTERN = re.compile(
    r"(?:[A-Za-z]:\\Users\\[^\\\r\n]+|E:\\AI\\OpenAI\\Codex\\DTT)",
    re.IGNORECASE,
)


def repository_files(repository: Path) -> tuple[Path, ...]:
    if repository.joinpath(".git").exists():
        command = (
            "git",
            "-c",
            f"safe.directory={repository.as_posix()}",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        )
        completed = subprocess.run(
            command,
            cwd=repository,
            check=True,
            capture_output=True,
        )
        names = completed.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        return tuple(repository / name for name in names if name)
    return tuple(
        path
        for path in sorted(repository.rglob("*"))
        if path.is_file() and not _excluded_without_git(path, repository)
    )


def _excluded_without_git(path: Path, repository: Path) -> bool:
    relative = path.relative_to(repository).as_posix().lower()
    parts = {part.lower() for part in path.relative_to(repository).parts}
    return (
        any(relative == prefix or relative.startswith(prefix + "/") for prefix in EXCLUDED_PREFIXES)
        or bool(parts.intersection(EXCLUDED_COMPONENTS))
        or path.name.lower() in {".coverage"}
        or path.suffix.lower() in {".pyc", ".pyo"}
        or relative.startswith("data/input/")
        or relative.startswith("data/output/")
        or relative.startswith("data/private/")
    )


def _relative(path: Path, repository: Path) -> str:
    return path.relative_to(repository).as_posix()


def _is_test_fixture(relative: str) -> bool:
    return relative.startswith("tests/fixtures/")


def _read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _office_metadata(path: Path, relative: str) -> list[Finding]:
    findings: list[Finding] = []
    if path.suffix.lower() not in {".docx", ".xlsx"}:
        return findings
    try:
        with ZipFile(path) as archive:
            try:
                properties = archive.read("docProps/core.xml").decode("utf-8")
            except KeyError:
                return findings
    except (BadZipFile, OSError, UnicodeDecodeError) as error:
        return [Finding("error", "invalid-office-package", relative, str(error))]
    for tag in ("creator", "lastModifiedBy"):
        match = re.search(
            rf"<(?:dc|cp):{tag}[^>]*>(.*?)</(?:dc|cp):{tag}>",
            properties,
            re.DOTALL,
        )
        if match and match.group(1).strip():
            findings.append(
                Finding(
                    "info",
                    "office-metadata",
                    relative,
                    f"{tag}={match.group(1).strip()}",
                )
            )
    return findings


def audit(repository: Path) -> tuple[tuple[Path, ...], tuple[Finding, ...]]:
    files = repository_files(repository)
    findings: list[Finding] = []
    for path in files:
        relative = _relative(path, repository)
        normalized = relative.lower()
        parts = {part.lower() for part in Path(relative).parts}
        suffix = path.suffix.lower()
        name = path.name.lower()

        if any(
            normalized == prefix or normalized.startswith(prefix + "/")
            for prefix in EXCLUDED_PREFIXES
        ) or parts.intersection(EXCLUDED_COMPONENTS):
            findings.append(
                Finding(
                    "error",
                    "excluded-output",
                    relative,
                    "Ignored runtime/build content entered the prospective source set.",
                )
            )
        if name in BANNED_NAMES or suffix in BANNED_SUFFIXES or name.endswith("~"):
            findings.append(
                Finding(
                    "error",
                    "sensitive-or-temporary-file",
                    relative,
                    (
                        "Credential, crash, database, log, backup, or temporary "
                        "file is not releasable."
                    ),
                )
            )
        if suffix in GENERATED_BINARY_SUFFIXES:
            findings.append(
                Finding(
                    "error",
                    "generated-binary",
                    relative,
                    (
                        "Generated executable/library/archive content must not "
                        "enter the source archive."
                    ),
                )
            )
        try:
            size = path.stat().st_size
        except OSError as error:
            findings.append(Finding("error", "unreadable-file", relative, str(error)))
            continue
        if size > MAX_SOURCE_FILE_BYTES:
            findings.append(
                Finding(
                    "error",
                    "oversized-source-file",
                    relative,
                    f"{size:,} bytes exceeds the 10 MiB source limit.",
                )
            )
        if suffix in DATASET_SUFFIXES:
            if not _is_test_fixture(relative):
                findings.append(
                    Finding(
                        "error",
                        "operational-dataset",
                        relative,
                        "Dataset-like files are allowed only as small synthetic test fixtures.",
                    )
                )
            elif size > MAX_TEST_FIXTURE_BYTES:
                findings.append(
                    Finding(
                        "error",
                        "oversized-test-fixture",
                        relative,
                        f"{size:,} bytes exceeds the 1 MiB fixture limit.",
                    )
                )

        text = _read_text(path)
        if text is not None:
            for code, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    findings.append(
                        Finding(
                            "error",
                            code,
                            relative,
                            "Text matches a credential/secret disclosure pattern.",
                        )
                    )
            if LOCAL_PATH_PATTERN.search(text):
                findings.append(
                    Finding(
                        "error",
                        "local-absolute-path",
                        relative,
                        "Text contains a developer-specific absolute workspace/user path.",
                    )
                )
        findings.extend(_office_metadata(path, relative))
    return files, tuple(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--list-output", type=Path)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve()
    files, findings = audit(repository)
    errors = tuple(item for item in findings if item.severity == "error")
    report = {
        "status": "passed" if not errors else "failed",
        "repository": str(repository),
        "filesAudited": len(files),
        "errorCount": len(errors),
        "informationalCount": len(findings) - len(errors),
        "findings": [asdict(item) for item in findings],
    }
    if arguments.json_output is not None:
        destination = arguments.json_output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if arguments.list_output is not None:
        destination = arguments.list_output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "\n".join(_relative(path, repository) for path in files) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
