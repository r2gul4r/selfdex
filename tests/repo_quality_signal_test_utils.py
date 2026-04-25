from __future__ import annotations

from typing import Any


def hotspot_repo_metric_file() -> dict[str, Any]:
    return {
        "path": "scripts/hotspot.py",
        "language": "python",
        "module_size": {
            "bytes": 20000,
            "code_lines": 500,
            "max_line_length": 140,
        },
        "complexity": {
            "max_indent_level": 6,
            "cyclomatic_estimate": 50,
            "decision_points": 60,
            "function_like_blocks": 25,
        },
        "duplication": {
            "group_count": 4,
            "duplicated_line_instances": 60,
            "max_duplicate_block_lines": 12,
        },
        "change_frequency": {
            "commit_count": 4,
            "commits_per_30_days": 3.5,
            "author_count": 2,
        },
    }


def low_signal_markdown_metric_file() -> dict[str, Any]:
    return {
        "path": "README.md",
        "language": "markdown",
        "module_size": {"bytes": 100, "code_lines": 10, "max_line_length": 60},
        "complexity": {
            "max_indent_level": 1,
            "cyclomatic_estimate": 1,
            "decision_points": 0,
            "function_like_blocks": 0,
        },
        "duplication": {
            "group_count": 0,
            "duplicated_line_instances": 0,
            "max_duplicate_block_lines": 0,
        },
        "change_frequency": {
            "commit_count": 0,
            "commits_per_30_days": 0,
            "author_count": 0,
        },
    }


def repo_metrics_payload() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "summary": {"file_count": 2},
        "files": [
            hotspot_repo_metric_file(),
            low_signal_markdown_metric_file(),
        ],
    }
