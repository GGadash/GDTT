"""Command-line and packaged entry point for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import faulthandler
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO


def _open_smoke_trace() -> TextIO | None:
    """Open an opt-in diagnostic trace used by packaged release verification."""
    destination = os.environ.get("DTT_SMOKE_TRACE")
    if not destination:
        return None
    trace = Path(destination)
    trace.parent.mkdir(parents=True, exist_ok=True)
    return trace.open("a", encoding="utf-8")


def _trace(stream: TextIO | None, message: str) -> None:
    if stream is None:
        return
    stream.write(f"{message}\n")
    stream.flush()


def main(arguments: Sequence[str] | None = None) -> int:
    """Launch normally or execute the non-interactive packaged smoke contract."""
    resolved = list(sys.argv if arguments is None else arguments)
    if "--smoke-test" not in resolved:
        from data_transform_tool.app.bootstrap import run

        return run(resolved)

    trace_stream = _open_smoke_trace()
    _trace(trace_stream, "smoke-entry")
    if trace_stream is not None:
        faulthandler.enable(trace_stream)
        faulthandler.dump_traceback_later(30, repeat=True, file=trace_stream)

    from data_transform_tool import __version__
    from data_transform_tool.app.bootstrap import build_application
    from data_transform_tool.app.metadata import PRODUCT_NAME
    from data_transform_tool.app.split_join_smoke import run_split_join_smoke

    _trace(trace_stream, "imports-complete")
    qt_arguments = [argument for argument in resolved if argument != "--smoke-test"]
    _trace(trace_stream, "build-start")
    app, window = build_application(qt_arguments)
    _trace(trace_stream, "build-complete")
    passed = all(
        (
            app.applicationName() == PRODUCT_NAME,
            app.applicationVersion() == __version__,
            not app.windowIcon().isNull(),
            window.windowTitle() == PRODUCT_NAME,
            window.home_view is not None,
            window.export_view is not None,
            window.split_join_view is not None,
        )
    )
    try:
        run_split_join_smoke()
        _trace(trace_stream, "split-join-smoke=passed")
    except Exception as error:
        _trace(trace_stream, f"split-join-smoke=failed: {type(error).__name__}: {error}")
        passed = False
    window.close()
    app.processEvents()
    _trace(trace_stream, f"smoke-result={0 if passed else 2}")
    faulthandler.cancel_dump_traceback_later()
    if trace_stream is not None:
        faulthandler.disable()
        trace_stream.close()
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
