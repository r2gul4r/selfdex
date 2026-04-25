"""File metric models and line-analysis helpers for repository scans."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


MIN_DUPLICATE_TOKEN_COUNT = 6

LANGUAGE_BY_NAME = {
    "makefile": "makefile",
}

LANGUAGE_BY_SUFFIX = {
    ".md": "markdown",
    ".py": "python",
    ".ps1": "powershell",
    ".rules": "rules",
    ".sh": "shell",
    ".toml": "toml",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}

COMMENT_PREFIXES = {
    "makefile": ("#",),
    "powershell": ("#",),
    "python": ("#",),
    "rules": ("#",),
    "shell": ("#",),
    "text": (),
    "toml": ("#",),
    "yaml": ("#",),
}

DECISION_TOKENS = {
    "powershell": ("if", "elseif", "switch", "for", "foreach", "while", "catch", "and", "or"),
    "python": ("if", "elif", "for", "while", "except", "case", "match", "and", "or"),
    "shell": ("if", "elif", "for", "while", "case", "&&", "||"),
}


@dataclass(frozen=True)
class GitHistoryMetrics:
    commit_count: int = 0
    author_count: int = 0
    first_commit_at: str | None = None
    last_commit_at: str | None = None
    active_days: int = 0
    commits_per_30_days: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "commit_count": self.commit_count,
            "author_count": self.author_count,
            "first_commit_at": self.first_commit_at,
            "last_commit_at": self.last_commit_at,
            "active_days": self.active_days,
            "commits_per_30_days": self.commits_per_30_days,
        }


@dataclass(frozen=True)
class FileMetrics:
    path: str
    language: str
    bytes_size: int
    total_lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    max_line_length: int
    function_like_blocks: int
    class_like_blocks: int
    decision_points: int
    cyclomatic_estimate: int
    max_indent_level: int
    duplication_group_count: int = 0
    duplicated_line_instances: int = 0
    max_duplicate_block_lines: int = 0
    git_history: GitHistoryMetrics = field(default_factory=GitHistoryMetrics)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "module_size": {
                "bytes": self.bytes_size,
                "total_lines": self.total_lines,
                "blank_lines": self.blank_lines,
                "comment_lines": self.comment_lines,
                "code_lines": self.code_lines,
                "max_line_length": self.max_line_length,
            },
            "complexity": {
                "function_like_blocks": self.function_like_blocks,
                "class_like_blocks": self.class_like_blocks,
                "decision_points": self.decision_points,
                "cyclomatic_estimate": self.cyclomatic_estimate,
                "max_indent_level": self.max_indent_level,
            },
            "duplication": {
                "group_count": self.duplication_group_count,
                "duplicated_line_instances": self.duplicated_line_instances,
                "max_duplicate_block_lines": self.max_duplicate_block_lines,
            },
            "change_frequency": self.git_history.to_dict(),
        }


@dataclass(frozen=True)
class NormalizedCodeLine:
    normalized: str
    original_line: int


@dataclass(frozen=True)
class DuplicateOccurrence:
    path: str
    start_index: int
    line_count: int
    start_line: int
    end_line: int


@dataclass(frozen=True)
class DuplicateGroup:
    fingerprint: str
    normalized_line_count: int
    token_count: int
    occurrences: tuple[DuplicateOccurrence, ...]
    excerpt_lines: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "fingerprint": self.fingerprint,
            "normalized_line_count": self.normalized_line_count,
            "token_count": self.token_count,
            "occurrence_count": len(self.occurrences),
            "modules": [
                {
                    "path": item.path,
                    "start_line": item.start_line,
                    "end_line": item.end_line,
                }
                for item in self.occurrences
            ],
            "excerpt": list(self.excerpt_lines),
        }


def infer_language(path: Path) -> str:
    lower_name = path.name.lower()
    if lower_name in LANGUAGE_BY_NAME:
        return LANGUAGE_BY_NAME[lower_name]
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "text")


def is_block_comment_start(language: str, line: str) -> bool:
    stripped = line.strip()
    if language == "markdown":
        return stripped.startswith("<!--")
    return False


def is_block_comment_end(language: str, line: str) -> bool:
    stripped = line.strip()
    if language == "markdown":
        return "-->" in stripped
    return False


def is_comment_line(language: str, line: str, in_block_comment: bool) -> tuple[bool, bool]:
    stripped = line.strip()
    if not stripped:
        return False, in_block_comment

    if in_block_comment:
        return True, not is_block_comment_end(language, line)

    if is_block_comment_start(language, line):
        return True, not is_block_comment_end(language, line)

    prefixes = COMMENT_PREFIXES.get(language, ())
    return stripped.startswith(prefixes), False


def count_decision_points(language: str, line: str) -> int:
    stripped = line.strip()
    if not stripped:
        return 0

    tokens = DECISION_TOKENS.get(language)
    if not tokens:
        return 0

    total = 0
    for token in tokens:
        if token in {"&&", "||"}:
            total += stripped.count(token)
            continue
        padded = f" {stripped} "
        total += padded.count(f" {token} ")
    return total


def count_function_like_blocks(language: str, line: str) -> int:
    stripped = line.strip()
    if not stripped:
        return 0

    if language == "python":
        return 1 if stripped.startswith("def ") else 0
    if language == "shell":
        if stripped.startswith("function "):
            return 1
        if stripped.endswith("() {"):
            return 1
        return 0
    if language == "powershell":
        return 1 if stripped.startswith("function ") else 0
    return 0


def count_class_like_blocks(language: str, line: str) -> int:
    stripped = line.strip()
    if language == "python":
        return 1 if stripped.startswith("class ") else 0
    return 0


def compute_indent_level(line: str) -> int:
    expanded = line.expandtabs(4)
    leading = len(expanded) - len(expanded.lstrip(" "))
    if leading == 0:
        return 0
    return leading // 4


def normalize_code_line(language: str, line: str) -> str:
    expanded = line.expandtabs(4).strip()
    if not expanded:
        return ""
    if language == "python":
        return re.sub(r"\s+", " ", expanded)
    if language in {"shell", "powershell", "makefile", "toml", "yaml", "rules", "markdown", "text"}:
        return re.sub(r"\s+", " ", expanded)
    return re.sub(r"\s+", " ", expanded)


def collect_normalized_code_lines(language: str, lines: list[str]) -> list[NormalizedCodeLine]:
    normalized_lines: list[NormalizedCodeLine] = []
    in_block_comment = False

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        is_comment, in_block_comment = is_comment_line(language, line, in_block_comment)
        if is_comment:
            continue
        normalized = normalize_code_line(language, line)
        if normalized:
            normalized_lines.append(NormalizedCodeLine(normalized=normalized, original_line=index))

    return normalized_lines


def analyze_file(root: Path, path: Path) -> FileMetrics:
    language = infer_language(path)
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    blank_lines = 0
    comment_lines = 0
    function_like_blocks = 0
    class_like_blocks = 0
    decision_points = 0
    max_line_length = 0
    max_indent_level = 0
    in_block_comment = False

    for line in lines:
        max_line_length = max(max_line_length, len(line))
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue

        is_comment, in_block_comment = is_comment_line(language, line, in_block_comment)
        if is_comment:
            comment_lines += 1
            continue

        function_like_blocks += count_function_like_blocks(language, line)
        class_like_blocks += count_class_like_blocks(language, line)
        decision_points += count_decision_points(language, line)
        max_indent_level = max(max_indent_level, compute_indent_level(line))

    total_lines = len(lines)
    code_lines = max(total_lines - blank_lines - comment_lines, 0)
    relative_path = path.resolve().relative_to(root.resolve()).as_posix()

    return FileMetrics(
        path=relative_path,
        language=language,
        bytes_size=path.stat().st_size,
        total_lines=total_lines,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        code_lines=code_lines,
        max_line_length=max_line_length,
        function_like_blocks=function_like_blocks,
        class_like_blocks=class_like_blocks,
        decision_points=decision_points,
        cyclomatic_estimate=max(1, decision_points + 1),
        max_indent_level=max_indent_level,
    )
