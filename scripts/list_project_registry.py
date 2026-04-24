#!/usr/bin/env python3
"""Read the Selfdex project registry without scanning registered projects."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REGISTRY_NAME = "PROJECT_REGISTRY.md"
REQUIRED_COLUMNS = ("project_id", "path", "role", "write_policy", "verification")


@dataclass(frozen=True)
class ProjectEntry:
    project_id: str
    path: str
    role: str
    write_policy: str
    verification: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List registered Selfdex projects.")
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args()


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(" ", "")) <= {":", "-"} for cell in cells)


def split_verification(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def parse_registry(text: str) -> list[ProjectEntry]:
    lines = text.splitlines()
    entries: list[ProjectEntry] = []
    header: list[str] | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header and entries:
                break
            continue

        cells = split_table_row(stripped)
        if is_separator_row(cells):
            continue
        if header is None:
            normalized = [cell.lower() for cell in cells]
            if tuple(normalized) == REQUIRED_COLUMNS:
                header = normalized
            continue
        if len(cells) != len(header):
            continue

        row = dict(zip(header, cells))
        entries.append(
            ProjectEntry(
                project_id=row["project_id"],
                path=row["path"],
                role=row["role"],
                write_policy=row["write_policy"],
                verification=split_verification(row["verification"]),
            )
        )

    return entries


def resolve_project_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def load_registry(root: Path) -> tuple[Path, list[ProjectEntry]]:
    registry_path = root / REGISTRY_NAME
    text = registry_path.read_text(encoding="utf-8")
    return registry_path, parse_registry(text)


def project_to_dict(root: Path, entry: ProjectEntry) -> dict[str, Any]:
    resolved = resolve_project_path(root, entry.path)
    return {
        "project_id": entry.project_id,
        "path": entry.path,
        "resolved_path": str(resolved),
        "path_exists": resolved.exists(),
        "role": entry.role,
        "write_policy": entry.write_policy,
        "verification": entry.verification,
    }


def build_payload(root: Path) -> dict[str, Any]:
    registry_path, entries = load_registry(root)
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_project_registry",
        "registry_path": str(registry_path),
        "registered_project_count": len(entries),
        "projects": [project_to_dict(root, entry) for entry in entries],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Project Registry",
        "",
        f"- registered_project_count: `{payload['registered_project_count']}`",
        f"- registry_path: `{payload['registry_path']}`",
        "",
        "## Projects",
        "",
    ]
    for project in payload.get("projects", []):
        lines.extend(
            [
                f"### {project['project_id']}",
                "",
                f"- path: `{project['path']}`",
                f"- resolved_path: `{project['resolved_path']}`",
                f"- path_exists: `{project['path_exists']}`",
                f"- role: {project['role']}",
                f"- write_policy: {project['write_policy']}",
                "- verification:",
            ]
        )
        for item in project["verification"]:
            lines.append(f"  - `{item}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    try:
        payload = build_payload(root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
