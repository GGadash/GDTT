"""Streaming CSV, TSV, and delimited-text inspection.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from charset_normalizer import from_bytes

from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.models import FileInspection, FileKind
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.io.reader import ProgressCallback
from data_transform_tool.io.readers.common import Row, inspect_row_stream, row_is_empty


@dataclass(frozen=True)
class _TextDetection:
    encoding: str
    encoding_confidence: float
    delimiter: str
    quote_character: str
    has_header: bool
    header_confidence: float
    warnings: tuple[str, ...]


class DelimitedTextReader:
    """Inspect delimited text with two streaming passes and bounded samples."""

    extensions = frozenset({".csv", ".tsv", ".txt"})

    def available_worksheets(self, path: Path) -> tuple[str, ...]:
        return ()

    def inspect(
        self,
        path: Path,
        options: InspectionOptions,
        cancellation: CancellationToken,
        progress: ProgressCallback | None = None,
    ) -> FileInspection:
        detection = self._detect(path, options)
        first_row = next(self._raw_rows(path, detection), None)
        if first_row is None:
            raise AppError("The selected text file does not contain any tabular rows.")

        initial_headers = (
            list(first_row)
            if detection.has_header
            else [f"Column {index}" for index in range(1, len(first_row) + 1)]
        )

        def data_rows() -> Iterator[Row]:
            rows = self._raw_rows(path, detection)
            if detection.has_header:
                next(rows, None)
            yield from rows

        suffix = path.suffix.casefold()
        file_kind = {".csv": FileKind.CSV, ".tsv": FileKind.TSV}.get(suffix, FileKind.TXT)
        return inspect_row_stream(
            path=path,
            file_kind=file_kind,
            initial_headers=initial_headers,
            rows_factory=data_rows,
            sample_limit=options.sample_limit,
            processing_strategy="Streaming delimited reader (two-pass, constant-memory previews)",
            estimated_memory_multiplier=3.0,
            worksheet=None,
            available_worksheets=(),
            encoding=detection.encoding,
            encoding_confidence=detection.encoding_confidence,
            delimiter=detection.delimiter,
            quote_character=detection.quote_character,
            header_detected=detection.has_header,
            header_confidence=detection.header_confidence,
            cancellation=cancellation,
            progress=progress,
            warnings=list(detection.warnings),
        )

    def _detect(self, path: Path, options: InspectionOptions) -> _TextDetection:
        with path.open("rb") as source:
            raw_sample = source.read(256_000)
        if not raw_sample:
            raise AppError("The selected text file is empty.")

        warnings: list[str] = []
        encoding, confidence = _detect_encoding(raw_sample, options.encoding)
        try:
            text_sample = raw_sample.decode(encoding)
        except (LookupError, UnicodeDecodeError) as error:
            raise AppError(
                f"The file could not be decoded using {encoding}.",
                detail=str(error),
            ) from error

        delimiter = options.delimiter
        quote_character = '"'
        if delimiter is None:
            try:
                dialect = csv.Sniffer().sniff(text_sample, delimiters=",\t;|")
                delimiter = dialect.delimiter
                quote_character = dialect.quotechar or '"'
            except csv.Error:
                delimiter = {".tsv": "\t", ".csv": ","}.get(path.suffix.casefold(), ",")
                warnings.append(
                    f"Delimiter detection was uncertain; {delimiter!r} was selected from "
                    "the file extension and can be overridden."
                )

        if options.has_header is None:
            try:
                has_header = csv.Sniffer().has_header(text_sample)
                header_confidence = 0.8
            except csv.Error:
                has_header = True
                header_confidence = 0.5
                warnings.append(
                    "Header detection was uncertain; the first row is treated as headers."
                )
        else:
            has_header = options.has_header
            header_confidence = 1.0

        if confidence < 0.6:
            warnings.append(
                f"Encoding confidence is low ({confidence:.0%}); review {encoding} "
                "before processing."
            )
        return _TextDetection(
            encoding=encoding,
            encoding_confidence=confidence,
            delimiter=delimiter,
            quote_character=quote_character,
            has_header=has_header,
            header_confidence=header_confidence,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _raw_rows(path: Path, detection: _TextDetection) -> Iterator[Row]:
        with path.open("r", encoding=detection.encoding, newline="") as source:
            reader = csv.reader(
                source,
                delimiter=detection.delimiter,
                quotechar=detection.quote_character,
            )
            for row in reader:
                normalized = tuple(row)
                if not row_is_empty(normalized):
                    yield normalized


def _detect_encoding(raw_sample: bytes, override: str | None) -> tuple[str, float]:
    if override:
        return override, 1.0
    if raw_sample.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", 1.0
    if raw_sample.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16", 1.0
    try:
        raw_sample.decode("utf-8")
    except UnicodeDecodeError:
        match = from_bytes(raw_sample).best()
        if match is None or match.encoding is None:
            return "utf-8", 0.0
        confidence = max(0.0, min(1.0, 1.0 - float(match.percent_chaos) / 100.0))
        return match.encoding, confidence
    return "utf-8", 1.0
