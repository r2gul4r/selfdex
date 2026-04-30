"""Text parsing and classification helpers for Selfdex planner candidates."""

from __future__ import annotations

import re

try:
    from markdown_utils import clean_markdown_value, extract_markdown_section
except ModuleNotFoundError:
    from scripts.markdown_utils import clean_markdown_value, extract_markdown_section


STOP_WORDS = {
    "and",
    "can",
    "for",
    "from",
    "into",
    "that",
    "the",
    "this",
    "with",
}

WORK_TYPE_KEYWORDS = {
    "repair": {
        "bug",
        "broken",
        "failing",
        "failure",
        "fix",
        "regression",
        "repair",
        "restore",
    },
    "hardening": {
        "budget",
        "check",
        "checker",
        "coverage",
        "drift",
        "fixture",
        "guard",
        "reject",
        "test",
        "tests",
        "validation",
        "verify",
    },
    "automation": {
        "automate",
        "automation",
        "generated",
        "record",
        "recorder",
        "refresh",
        "run",
        "runs",
        "write",
        "writes",
    },
    "capability": {
        "analysis",
        "classification",
        "classify",
        "evaluator",
        "multi",
        "orchestration",
        "planner",
        "project",
        "registry",
        "socratic",
        "work_type",
    },
    "direction": {
        "audience",
        "direction",
        "opportunity",
        "product",
        "strategy",
        "thesis",
        "trajectory",
        "user",
        "vision",
        "workflow",
    },
    "improvement": {
        "cleanup",
        "docs",
        "improve",
        "improvement",
        "refactor",
        "reduce",
        "simplify",
    },
}

WORK_TYPE_PRIORITY = (
    "repair",
    "hardening",
    "automation",
    "capability",
    "direction",
    "improvement",
)

WORK_TYPE_DESCRIPTIONS = {
    "repair": "restore broken behavior",
    "hardening": "make existing behavior harder to break",
    "improvement": "improve quality without adding a new capability",
    "capability": "add a new system ability",
    "direction": "move the project toward a better product or technical trajectory",
    "automation": "automate repeated coordination work",
}


def parse_campaign_goal(text: str) -> str:
    for line in extract_markdown_section(text, "Campaign"):
        match = re.match(r"^\s*-\s*goal:\s*(.+?)\s*$", line)
        if match:
            return clean_markdown_value(match.group(1))
    return ""


def parse_campaign_queue(text: str) -> list[str]:
    candidates: list[str] = []
    for line in extract_markdown_section(text, "Candidate Queue"):
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if not match:
            continue
        title = clean_markdown_value(match.group(1))
        if title:
            candidates.append(title)
    return candidates


def normalize_goal_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("er"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def meaningful_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in re.split(r"[^a-z0-9]+", value.lower()):
        if len(raw_token) < 3 or raw_token in STOP_WORDS:
            continue
        tokens.add(normalize_goal_token(raw_token))
    return tokens


def campaign_goal_matches(goal: str, title: str) -> list[str]:
    if not goal:
        return []
    return sorted(meaningful_tokens(goal) & meaningful_tokens(title))


def classify_work_type(title: str, default: str = "improvement") -> str:
    tokens = meaningful_tokens(title)
    for work_type in WORK_TYPE_PRIORITY:
        keywords = {normalize_goal_token(keyword) for keyword in WORK_TYPE_KEYWORDS[work_type]}
        if tokens & keywords:
            return work_type
    return default
