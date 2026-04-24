"""Small markdown parsing helpers shared by Selfdex scripts."""

from __future__ import annotations

import re


def clean_markdown_value(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1]
    return value.replace("`", "").strip()


def extract_markdown_section(text: str, heading: str) -> list[str]:
    lines: list[str] = []
    in_section = False
    heading_level = 0
    heading_pattern = re.compile(r"^(#+)\s+(.+?)\s*$")

    for line in text.splitlines():
        match = heading_pattern.match(line)
        if match:
            level = len(match.group(1))
            name = match.group(2).strip().lower()
            if in_section and level <= heading_level:
                break
            if name == heading.lower():
                in_section = True
                heading_level = level
                continue
        if in_section:
            lines.append(line)
    return lines
