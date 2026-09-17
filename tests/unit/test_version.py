from data_transform_tool import __version__


def test_version_is_current_semantic_version() -> None:
    assert __version__ == "0.10.2"
