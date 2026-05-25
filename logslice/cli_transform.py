"""CLI helpers for building a Transformer from parsed arguments."""
from __future__ import annotations

import argparse
from typing import List

from logslice.transformer import (
    TransformRule,
    Transformer,
    TransformerConfig,
    lowercase,
    regex_replace,
    strip_whitespace,
    uppercase,
)

_BUILTIN_TRANSFORMS = {
    "uppercase": uppercase,
    "lowercase": lowercase,
    "strip": strip_whitespace,
}


def add_transform_args(parser: argparse.ArgumentParser) -> None:
    """Register --transform flags on *parser*."""
    parser.add_argument(
        "--transform",
        metavar="FIELD:OP",
        action="append",
        default=[],
        dest="transforms",
        help=(
            "Apply a transformation to a named field. "
            "OP is one of: uppercase, lowercase, strip, "
            "or regex_replace=PATTERN:REPLACEMENT."
        ),
    )
    parser.add_argument(
        "--transform-stop-on-error",
        action="store_true",
        default=False,
        help="Abort processing when a transform raises an error.",
    )


def _parse_single(spec: str) -> TransformRule:
    """Parse a single FIELD:OP spec into a TransformRule."""
    if ":" not in spec:
        raise argparse.ArgumentTypeError(
            f"Invalid --transform spec (expected FIELD:OP): {spec!r}"
        )
    field, op = spec.split(":", 1)
    field = field.strip()
    op = op.strip()

    if op in _BUILTIN_TRANSFORMS:
        return TransformRule(field=field, transform=_BUILTIN_TRANSFORMS[op], label=spec)

    if op.startswith("regex_replace="):
        rest = op[len("regex_replace="):]
        if ":" not in rest:
            raise argparse.ArgumentTypeError(
                f"regex_replace requires PATTERN:REPLACEMENT, got: {rest!r}"
            )
        pattern, replacement = rest.split(":", 1)
        return TransformRule(
            field=field,
            transform=regex_replace(pattern, replacement),
            label=spec,
        )

    raise argparse.ArgumentTypeError(
        f"Unknown transform operation {op!r}. "
        f"Valid ops: {', '.join(_BUILTIN_TRANSFORMS)} or regex_replace=PATTERN:REPLACEMENT"
    )


def build_transformer(args: argparse.Namespace) -> Transformer:
    """Construct a Transformer from parsed CLI *args*."""
    rules: List[TransformRule] = []
    for spec in getattr(args, "transforms", []):
        rules.append(_parse_single(spec))
    cfg = TransformerConfig(
        rules=rules,
        stop_on_error=getattr(args, "transform_stop_on_error", False),
    )
    return Transformer(cfg)
