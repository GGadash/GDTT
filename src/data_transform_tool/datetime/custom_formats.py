"""Explicit, bounded custom field formats; no executable formatting expressions.

Copyright (c) 2026 Gadash +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext
from functools import lru_cache

from data_transform_tool.datetime.models import DateTimeFormatProfile, TemporalKind
from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    Diagnostic,
    InvalidValuePolicy,
    OperationResult,
    TransformationError,
    write_column,
)
from data_transform_tool.transformation.numeric import to_decimal

PREFIX = "gdtt-format:"


@dataclass(frozen=True)
class FieldFormat:
    kind: str
    pattern: str
    decimal: str = "."
    preserve: bool = False

    def __post_init__(self) -> None:
        if self.decimal not in {".", ","}:
            raise ValueError("Choose dot or comma as the decimal separator.")
        if not self.pattern or len(self.pattern) > 120:
            raise ValueError("A custom pattern must contain 1-120 characters.")
        if self.kind == "number":
            if not re.fullmatch(r"(?:#,##)?0+(?:\.0*#*)?", self.pattern):
                raise ValueError("Use 0, 0.00, 0.###, #,##0.00, or a similar 0/# mask.")
            if len(self.pattern.partition(".")[2]) > 12:
                raise ValueError("Use at most 12 decimal places.")
        elif self.kind in {"date", "time", "datetime"}:
            temporal_profile(self)
        elif self.kind == "text":
            if self.pattern != "@" and self.pattern.count("{value}") != 1:
                raise ValueError("Text formats must contain one {value} placeholder, or @.")
        elif self.kind == "boolean":
            values = self.pattern.split("|")
            if len(values) != 2 or not all(values) or values[0].casefold() == values[1].casefold():
                raise ValueError("Boolean format must be two distinct labels: True|False.")
        else:
            raise ValueError("Unsupported custom field type.")

    def encode(self) -> str:
        return PREFIX + json.dumps(asdict(self), separators=(",", ":"), ensure_ascii=False)

    @property
    def places(self) -> int:
        return len(self.pattern.partition(".")[2])

    def number(self, value: CellValue, *, parsing: bool = False) -> Decimal:
        if parsing and isinstance(value, str):
            text = value.strip().replace("\u202f", " ").replace("\u00a0", " ")
            group = "," if self.decimal == "." else "."
            integer, separator, fraction = text.partition(self.decimal)
            if group in integer or " " in integer:
                if "," not in self.pattern:
                    raise ValueError("Select a grouped input profile for thousands separators.")
                used = " " if " " in integer else group
                if not re.fullmatch(r"[+-]?\d{1,3}(?:" + re.escape(used) + r"\d{3})+", integer):
                    raise ValueError("Invalid thousands grouping.")
                integer = integer.replace(used, "")
            if not re.fullmatch(r"[+-]?\d+", integer) or (separator and not fraction.isdigit()):
                raise ValueError("Value does not match the selected decimal separator.")
            value = integer + ("." + fraction if separator else "")
        result = to_decimal(value)
        if parsing or self.preserve:
            return result
        with localcontext() as context:
            context.prec = max(
                28, len(result.as_tuple().digits) + abs(result.adjusted()) + self.places + 4
            )
            return result.quantize(Decimal(1).scaleb(-self.places), rounding=ROUND_HALF_UP)

    def display(self, value: CellValue, *, csv: bool = False) -> str:
        number = self.number(value)
        if self.preserve and csv:
            return format(number, "f").replace(".", self.decimal)
        # Always round presentation, including display-only mode; never mutate the stored value.
        number = FieldFormat("number", self.pattern, self.decimal).number(number)
        result = format(number, f",.{self.places}f" if "," in self.pattern else f".{self.places}f")
        optional = len(self.pattern.partition(".")[2]) - len(
            self.pattern.partition(".")[2].rstrip("#")
        )
        for _ in range(optional):
            if result.endswith("0"):
                result = result[:-1]
        result = result.rstrip(".")
        min_digits = self.pattern.partition(".")[0].count("0")
        if "," not in self.pattern and min_digits > 1:
            sign = "-" if result.startswith("-") else ""
            integer, dot, fraction = result.lstrip("-").partition(".")
            result = sign + integer.zfill(min_digits) + (dot + fraction if dot else "")
        return result.translate(str.maketrans(".,", ",.")) if self.decimal == "," else result


@lru_cache(maxsize=256)
def decode(profile: str | None) -> FieldFormat | None:
    if profile is None or not profile.startswith(PREFIX):
        return None
    data = json.loads(profile[len(PREFIX) :])
    if not isinstance(data, dict) or set(data) != {"kind", "pattern", "decimal", "preserve"}:
        raise ValueError("Invalid custom format configuration.")
    if not all(
        isinstance(data[key], str) for key in ("kind", "pattern", "decimal")
    ) or not isinstance(data["preserve"], bool):
        raise ValueError("Invalid custom format value types.")
    return FieldFormat(**data)


def temporal_profile(spec: FieldFormat) -> DateTimeFormatProfile:
    from data_transform_tool.datetime.profiles import DEFAULT_PROFILES

    pattern = spec.pattern
    # Exact new ISO masks keep the same strict shape and UTC semantics when typed.
    for profile in DEFAULT_PROFILES:
        if (
            profile.input_regex is not None
            and profile.temporal_kind.value == spec.kind
            and profile.display_pattern == pattern
        ):
            return profile
    tokens = re.compile(
        r"yyyy|MMMM|MMM|yy|MM|dd|HH|hh|mm|ss|AM/PM|XXX|M|d|H|h|m|s|\"[^\"]*\"|'[^']*'",
        re.IGNORECASE,
    )
    mapping = {
        "yyyy": "%Y",
        "yy": "%y",
        "mmmm": "%B",
        "mmm": "%b",
        "dd": "%d",
        "d": "%d",
        "hh": "%H",
        "h": "%H",
        "ss": "%S",
        "s": "%S",
        "sss": "%f",
        "am/pm": "%p",
        "xxx": "%z",
    }
    parts: list[str] = []
    end = 0
    for match in tokens.finditer(pattern):
        gap = pattern[end : match.start()]
        if re.search(r"[A-Za-z%]", gap):
            raise ValueError("Unsupported date/time token; quote literal text.")
        parts.append(gap)
        token = match[0]
        if token[0] in {"'", '"'}:
            parts.append(token[1:-1].replace("%", "%%"))
        elif token.lower() in {"mm", "m"}:
            minute = token.islower() and (
                spec.kind == "time"
                or bool(re.search(r"[Hh].*[: ]$", pattern[: match.start()]))
                or bool(re.match(r":s", pattern[match.end() :], re.IGNORECASE))
            )
            parts.append("%M" if minute else "%m")
        else:
            code = mapping[token.lower()]
            if token.lower() in {"h", "hh"} and "AM/PM" in pattern.upper():
                code = "%I"
            parts.append(code)
        end = match.end()
    if re.search(r"[A-Za-z%]", pattern[end:]) or not any("%" in p for p in parts):
        raise ValueError("Use a date/time mask such as yyyy-MM-dd HH:mm:ss.")
    parts.append(pattern[end:])
    compiled = "".join(parts)
    directives = re.findall(r"(?<!%)%[A-Za-z]", compiled)
    if len(set(directives)) != len(directives):
        raise ValueError("Repeated or unsupported date/time tokens; use the documented masks.")
    return DateTimeFormatProfile(
        "custom",
        "Custom",
        pattern,
        pattern,
        (compiled,),
        TemporalKind(spec.kind),
        compiled,
        colonize_offset="XXX" in pattern.upper(),
    )


def apply_profile(
    table: DataTable, source: str, profile: str, policy: InvalidValuePolicy, *, parsing: bool
) -> OperationResult:
    from data_transform_tool.datetime.operations import FormatDateTimeColumn, ParseDateTimeColumn

    spec = decode(profile)
    if spec is None or spec.kind in {"date", "time", "datetime"}:
        operation = ParseDateTimeColumn if parsing else FormatDateTimeColumn
        return operation(source, profile, invalid_policy=policy).apply(table)
    values: list[CellValue] = []
    invalid = 0
    for value in table.column_values(source):
        if value is None:
            values.append(None)
            continue
        try:
            if spec.kind == "number":
                converted: CellValue = spec.number(value, parsing=parsing)
            elif spec.kind == "text":
                if spec.pattern == "@":
                    converted = str(value)
                elif parsing:
                    prefix, suffix = spec.pattern.split("{value}")
                    text = str(value)
                    if not text.startswith(prefix) or not text.endswith(suffix):
                        raise ValueError("Source text does not match the input template.")
                    converted = text[len(prefix) : len(text) - len(suffix) if suffix else None]
                else:
                    converted = spec.pattern.replace("{value}", str(value))
            else:
                yes, no = spec.pattern.split("|")
                if isinstance(value, bool):
                    boolean = value
                elif str(value).casefold() in {yes.casefold(), "true", "1", "yes"}:
                    boolean = True
                elif str(value).casefold() in {no.casefold(), "false", "0", "no"}:
                    boolean = False
                else:
                    raise ValueError("Invalid Boolean value.")
                converted = boolean if parsing else (yes if boolean else no)
            values.append(converted)
        except (ArithmeticError, ValueError) as error:
            if policy is InvalidValuePolicy.STOP:
                raise TransformationError(
                    f"Invalid value in '{source}' for {spec.pattern}.", detail=str(error)
                ) from error
            invalid += 1
            values.append(value if policy is InvalidValuePolicy.PRESERVE else None)
    diagnostics = (
        (
            Diagnostic(
                "custom_format_invalid",
                "Values do not match the chosen custom format.",
                invalid,
                (source,),
            ),
        )
        if invalid
        else ()
    )
    return OperationResult(
        write_column(table, source_name=source, output_name=None, values=tuple(values)), diagnostics
    )


def profile_label(profile: str | None, default: str) -> str:
    spec = decode(profile)
    return spec.pattern if spec else profile or default
