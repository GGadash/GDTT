from data_transform_tool.domain.errors import AppError, Severity


def test_app_error_exposes_safe_user_information() -> None:
    error = AppError("The output file is locked.", detail="PermissionError")

    assert str(error) == "The output file is locked."
    assert error.user_message == "The output file is locked."
    assert error.severity is Severity.BLOCKING_ERROR
    assert error.detail == "PermissionError"
