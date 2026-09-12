"""Application identity and generated Windows metadata contracts."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

from data_transform_tool import __version__
from data_transform_tool.__main__ import main
from data_transform_tool.resources import application_icon, icon_path


def _version_generator() -> dict[str, Any]:
    return runpy.run_path(str(Path(__file__).parents[2] / "scripts/generate_windows_version.py"))


def test_application_icons_and_offscreen_smoke_contract_exist() -> None:
    assert all(icon_path(extension).is_file() for extension in ("svg", "png", "ico"))
    assert not application_icon().isNull()
    assert main(["data-transform-tool", "--smoke-test", "-platform", "offscreen"]) == 0


def test_windows_version_resource_uses_canonical_product_metadata() -> None:
    generator = _version_generator()
    assert generator["version_tuple"](__version__) == (0, 10, 0, 0)
    resource = generator["version_resource"](__version__)
    assert "GDTT" in resource
    assert "Gadash (Akila DJ)" in resource
    assert "OpenAI Codex" in resource
    assert f"ProductVersion', '{__version__}'" in resource
    specification = Path("packaging/data_transform_tool.spec").read_text(encoding="utf-8")
    assert "msvcp140_codecvt_ids.dll" in specification


def test_current_user_installer_contract_is_versioned() -> None:
    installer = Path("packaging/data_transform_tool.nsi").read_text(encoding="utf-8")
    assert "RequestExecutionLevel user" in installer
    assert "MUI_PAGE_LICENSE" in installer
    assert 'Section /o "Desktop shortcut"' in installer
    assert "WriteUninstaller" in installer
    assert "OpenAI Codex" in installer
    assert Path("scripts/bootstrap_nsis.ps1").is_file()
    assert Path("scripts/build_installer.ps1").is_file()
    assert Path("scripts/verify_installer.ps1").is_file()


def test_release_candidate_and_ci_contracts_are_versioned() -> None:
    expected_scripts = (
        "scripts/audit_release_tree.py",
        "scripts/run_representative_workflows.py",
        "scripts/build_source_archive.ps1",
        "scripts/verify_c_lite.ps1",
        "scripts/verify_artifact_checksums.ps1",
        "scripts/finalize_release_candidate.ps1",
        "scripts/build_release_candidate.ps1",
    )
    assert all(Path(path).is_file() for path in expected_scripts)

    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    windows = Path(".github/workflows/build-windows.yml").read_text(encoding="utf-8")
    assert "audit_release_tree.py" in ci
    assert "run_representative_workflows.py" in ci
    assert "build_source_archive.ps1" in windows
    assert "verify_c_lite.ps1" in windows
    assert "finalize_release_candidate.ps1" in windows
    assert "Publish tagged GitHub release" in windows
    assert "github.event_name == 'push'" in windows
    assert "actions/download-artifact@v7" in windows
    assert "astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9" in windows
    assert "contents: write" in windows
    assert '"release", "create", $tag' in windows
    assert '"--verify-tag"' in windows
    assert '"--prerelease", "--latest=false"' in windows
    assert "persist-credentials: false" in ci
    assert "persist-credentials: false" in windows

    build_script = Path("scripts/build_windows.ps1").read_text(encoding="utf-8")
    assert '"$executableHash *GDTT/GDTT.exe"' not in build_script
    assert "sha256 = $executableHash" in build_script
    assert '"GDTT-$version-windows-x64-Portable.zip"' in build_script
    installer_build = Path("scripts/build_installer.ps1").read_text(encoding="utf-8")
    assert '"GDTT-$version-windows-x64-installer.exe"' in installer_build
    assert "packaging/output/GDTT-*-windows-x64-Portable.zip" in windows
    assert "packaging/output/GDTT-*-windows-x64-installer.exe" in windows
    assert '"GDTT-$tagVersion-windows-x64-Portable.zip"' in windows
    assert '"GDTT-$tagVersion-windows-x64-installer.exe"' in windows

    finalizer = Path("scripts/finalize_release_candidate.ps1").read_text(encoding="utf-8")
    assert "RELEASE_CANDIDATE.md" in finalizer
    assert "VERIFY_CHECKSUMS.ps1" in finalizer
    assert ".*[/\\\\]" in finalizer
