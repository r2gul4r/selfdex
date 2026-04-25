"""Shared CLI output helpers for JSON/markdown report scripts."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any


def write_json_or_markdown(
    payload: dict[str, Any],
    output_format: str,
    render_markdown: Callable[[dict[str, Any]], str],
) -> None:
    if output_format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    sys.stdout.write(render_markdown(payload))
