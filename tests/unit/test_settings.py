from pathlib import Path

from data_transform_tool.settings.models import AppSettings
from data_transform_tool.settings.paths import application_data_directory, logs_directory
from data_transform_tool.settings.repository import SettingsRepository


def test_settings_round_trip(tmp_path: Path) -> None:
    repository = SettingsRepository(tmp_path / "settings.json")
    expected = AppSettings(theme="dark", window_width=1300, window_height=800)

    repository.save(expected)

    assert repository.load() == expected


def test_invalid_settings_fall_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not-json", encoding="utf-8")

    assert SettingsRepository(path).load() == AppSettings()


def test_release_storage_overrides_are_explicit_and_separate(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    data = tmp_path / "isolated-data"
    logs = tmp_path / "isolated-logs"
    monkeypatch.setenv("DTT_DATA_DIRECTORY", str(data))
    monkeypatch.setenv("DTT_LOG_DIRECTORY", str(logs))

    assert application_data_directory() == data.resolve()
    assert logs_directory() == logs.resolve()
