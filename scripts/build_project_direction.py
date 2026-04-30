#!/usr/bin/env python3
"""Infer project direction and strategic opportunities from repository evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from argparse_utils import add_format_argument, add_root_argument
    from candidate_scoring_utils import grade_priority
    from cli_output_utils import write_json_or_markdown
    from repo_scan_excludes import path_has_excluded_dir
except ModuleNotFoundError:
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.candidate_scoring_utils import grade_priority
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.repo_scan_excludes import path_has_excluded_dir


SCHEMA_VERSION = 1
MAX_TEXT_BYTES = 80_000
MAX_DOC_FILES = 12
MAX_REPO_FILES = 1_500
TEXT_SUFFIXES = {
    ".css",
    ".gradle",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".py",
    ".rs",
    ".sql",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}
LOCAL_ARTIFACT_DIRS = {"runs"}
KEY_DOC_NAMES = {
    "agents.md",
    "autopilot.md",
    "project_harness.md",
    "readme.md",
    "state.md",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer a project direction snapshot from local repository evidence.")
    add_root_argument(parser, help_text="Repository root to scan.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum opportunities to emit. Defaults to 5.")
    add_format_argument(parser)
    return parser.parse_args(argv)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_read_text(path: Path, max_bytes: int = MAX_TEXT_BYTES) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= MAX_REPO_FILES:
            break
        if path_has_excluded_dir(path, root=root):
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in LOCAL_ARTIFACT_DIRS for part in relative_parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def pick_doc_files(root: Path, files: list[Path]) -> list[Path]:
    docs = [
        path
        for path in files
        if path.suffix.lower() in {".md", ".txt"} and (path.name.lower() in KEY_DOC_NAMES or "docs" in path.parts)
    ]
    return sorted(docs, key=lambda path: (0 if path.name.lower() == "readme.md" else 1, len(path.parts), rel_path(root, path)))[
        :MAX_DOC_FILES
    ]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().strip("-*`")
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if len(stripped) >= 24:
            return normalize_space(stripped)[:180]
    return ""


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def paths_matching(files: list[Path], root: Path, *patterns: str) -> list[str]:
    lowered_patterns = tuple(pattern.lower() for pattern in patterns)
    matches = []
    for path in files:
        relative = rel_path(root, path)
        lowered = relative.lower()
        if any(pattern in lowered for pattern in lowered_patterns):
            matches.append(relative)
    return matches[:5]


def signal(label: str, summary: str, paths: list[str], confidence: str = "medium") -> dict[str, Any]:
    return {
        "label": label,
        "summary": summary,
        "confidence": confidence,
        "evidence_paths": paths[:5],
    }


def infer_product_signals(root: Path, files: list[Path], doc_text: str) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    ui_paths = paths_matching(files, root, "frontend", "renderer", "components", "pages", ".html", ".tsx", ".jsx")
    if ui_paths or contains_any(doc_text, ("ui", "screen", "page", "dashboard", "frontend", "web app")):
        signals.append(signal("interactive_experience", "The project exposes or describes a user-facing surface.", ui_paths))

    api_paths = paths_matching(files, root, "controller", "route", "api", "server", "backend", "service")
    if api_paths or contains_any(doc_text, ("api", "backend", "endpoint", "server", "service")):
        signals.append(signal("service_layer", "The project appears to have a service or integration layer.", api_paths))

    data_paths = paths_matching(files, root, "migration", "schema", "collector", "crawler", "ingest", "database", ".sql")
    if data_paths or contains_any(doc_text, ("data", "database", "crawl", "ingest", "schema", "collector")):
        signals.append(signal("data_pipeline", "The project has data collection, persistence, or normalization concerns.", data_paths))

    automation_paths = paths_matching(files, root, "scripts", "agents.md", "state.md", "runs", "workflow", "task")
    if automation_paths or contains_any(doc_text, ("agent", "automation", "workflow", "orchestrate", "codex")):
        signals.append(signal("automation_loop", "The project contains automation or agent workflow signals.", automation_paths))

    return signals


def infer_technical_signals(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    names = {path.name.lower() for path in files}
    signals: list[dict[str, Any]] = []
    checks = [
        ("python", ("pyproject.toml", "requirements.txt", "setup.py"), (".py",)),
        ("node", ("package.json", "vite.config.ts", "next.config.js"), (".js", ".ts", ".tsx")),
        ("java", ("build.gradle", "pom.xml", "settings.gradle"), (".java", ".kt")),
        ("database", ("schema.sql",), (".sql",)),
        ("desktop_or_packaged_app", ("package.json", "tauri.conf.json"), ("electron", "native")),
    ]
    for label, filenames, suffix_or_path_tokens in checks:
        matching_names = [name for name in filenames if name in names]
        matching_paths = [
            rel_path(root, path)
            for path in files
            if path.suffix.lower() in suffix_or_path_tokens or any(str(token) in rel_path(root, path).lower() for token in suffix_or_path_tokens)
        ][:5]
        if matching_names or matching_paths:
            signals.append(
                signal(
                    label,
                    f"Detected {label} stack evidence.",
                    sorted(set(matching_names + matching_paths))[:5],
                )
            )
    return signals


def infer_constraints(root: Path, files: list[Path], doc_text: str) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    test_paths = paths_matching(files, root, "test", "tests", "spec")
    if test_paths:
        constraints.append(signal("local_verification_available", "There is at least one local test or spec surface.", test_paths, "high"))
    else:
        constraints.append(signal("verification_surface_unclear", "No obvious test or spec surface was found in the first scan.", [], "medium"))

    env_paths = paths_matching(files, root, ".env", "secret", "credential")
    if env_paths or contains_any(doc_text, ("secret", "token", "credential", "api key")):
        constraints.append(signal("secret_boundary", "Some behavior may depend on environment secrets and should stay approval-gated.", env_paths))

    return constraints


def infer_audience(doc_text: str, product_signals: list[dict[str, Any]]) -> list[str]:
    audience = []
    rules = [
        ("end users", ("user", "customer", "visitor", "member")),
        ("developers", ("developer", "api", "sdk", "cli", "library")),
        ("operators", ("admin", "operator", "dashboard", "monitor")),
        ("agents", ("agent", "codex", "automation", "workflow")),
    ]
    for label, keywords in rules:
        if contains_any(doc_text, keywords):
            audience.append(label)
    if not audience and product_signals:
        audience.append("project users")
    return audience or ["unknown audience"]


def infer_purpose(root: Path, docs: list[tuple[Path, str]], product_signals: list[dict[str, Any]]) -> dict[str, Any]:
    heading = ""
    fallback = ""
    evidence_paths = []
    for path, text in docs:
        evidence_paths.append(rel_path(root, path))
        heading = heading or first_heading(text)
        fallback = fallback or first_meaningful_line(text)
    if heading:
        summary = f"{heading} is the clearest documented project anchor."
    elif fallback:
        summary = fallback
    elif product_signals:
        labels = ", ".join(item["label"] for item in product_signals[:3])
        summary = f"{root.name} appears to center on {labels}."
    else:
        summary = f"{root.name} has no clear product thesis in the scanned evidence."
    return {
        "summary": summary,
        "evidence_paths": evidence_paths[:5],
    }


def score_dimensions(
    *,
    strategic_fit: int,
    user_value: int,
    novelty: int,
    feasibility: int,
    local_verifiability: int,
    reversibility: int,
    evidence_strength: int,
) -> dict[str, int]:
    return {
        "strategic_fit": strategic_fit,
        "user_value": user_value,
        "novelty": novelty,
        "feasibility": feasibility,
        "local_verifiability": local_verifiability,
        "reversibility": reversibility,
        "evidence_strength": evidence_strength,
    }


def opportunity(
    *,
    opportunity_id: str,
    title: str,
    rationale: list[str],
    evidence_paths: list[str],
    suggested_first_step: str,
    suggested_checks: list[str],
    dimensions: dict[str, int],
    risk: str = "guarded",
) -> dict[str, Any]:
    raw_score = sum(dimensions.values())
    priority_score = round(raw_score * 1.35, 2)
    decision = "pick" if priority_score >= 38 and risk in {"low", "guarded", "medium"} else "monitor"
    return {
        "opportunity_id": opportunity_id,
        "title": title,
        "source": "project_direction",
        "work_type": "direction",
        "decision": decision,
        "priority_score": priority_score,
        "priority_grade": grade_priority(int(priority_score)),
        "risk": risk,
        "strategic_dimensions": dimensions,
        "rationale": rationale,
        "evidence_paths": list(dict.fromkeys(evidence_paths))[:5],
        "suggested_first_step": suggested_first_step,
        "suggested_checks": suggested_checks,
    }


def build_opportunities(
    *,
    root: Path,
    files: list[Path],
    purpose: dict[str, Any],
    product_signals: list[dict[str, Any]],
    technical_signals: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    signal_labels = {item["label"] for item in product_signals}
    test_available = any(item["label"] == "local_verification_available" for item in constraints)
    check = "python -m unittest discover -s tests" if test_available else "manual local smoke check"
    purpose_paths = list(purpose.get("evidence_paths", []))
    opportunities: list[dict[str, Any]] = []

    if {"interactive_experience", "service_layer"} & signal_labels:
        evidence = paths_matching(files, root, "frontend", "pages", "components", "api", "controller", "route", "backend")
        opportunities.append(
            opportunity(
                opportunity_id="direction:core-user-journey",
                title="Prove and improve the primary user journey",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "A user-facing or service-facing surface exists, so a small vertical-slice improvement can raise product value beyond code hygiene.",
                    "The first step should connect or verify one visible path instead of broadly refactoring.",
                ],
                evidence_paths=evidence or purpose_paths,
                suggested_first_step="Pick one core user journey, document its expected result, and make the smallest code or test change that improves that path.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=5,
                    novelty=4,
                    feasibility=4,
                    local_verifiability=4 if test_available else 3,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    if "data_pipeline" in signal_labels:
        evidence = paths_matching(files, root, "collector", "crawler", "ingest", "schema", "migration", ".sql")
        opportunities.append(
            opportunity(
                opportunity_id="direction:data-quality-loop",
                title="Turn data freshness and quality into a product feedback loop",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "Data collection or persistence is visible, so product quality may depend on freshness, coverage, and explainable failures.",
                    "A small observability or validation step can unlock better future features than another local cleanup task.",
                ],
                evidence_paths=evidence or purpose_paths,
                suggested_first_step="Add or tighten one local data-quality check that reports stale, missing, or malformed product data before feature work relies on it.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=5,
                    novelty=4,
                    feasibility=3,
                    local_verifiability=4 if test_available else 3,
                    reversibility=3,
                    evidence_strength=4,
                ),
            )
        )

    if "automation_loop" in signal_labels:
        evidence = paths_matching(files, root, "scripts", "agents.md", "state.md", "runs", "workflow")
        opportunities.append(
            opportunity(
                opportunity_id="direction:autonomous-feedback-loop",
                title="Close one autonomous feedback loop with evidence",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "Automation or agent workflow signals are present, so the next improvement should make the system learn from a completed run.",
                    "This is a project evolution candidate because it improves decision quality, not just local code shape.",
                ],
                evidence_paths=evidence or purpose_paths,
                suggested_first_step="Record one missing decision or result field that would make the next automated run choose better work.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=5,
                    user_value=4,
                    novelty=5,
                    feasibility=4,
                    local_verifiability=4 if test_available else 3,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    if len(purpose_paths) <= 1 or "unknown" in " ".join(purpose.get("summary", "").lower().split()):
        evidence = purpose_paths or [rel_path(root, path) for path in files[:3]]
        opportunities.append(
            opportunity(
                opportunity_id="direction:project-thesis",
                title="Make the project thesis explicit for future work",
                rationale=[
                    "The scanned evidence does not expose a strong project thesis.",
                    "Selfdex needs a clear goal, audience, and current product bet before it can choose ambitious work safely.",
                ],
                evidence_paths=evidence,
                suggested_first_step="Add or update a short project thesis section that states the target user, current value proposition, and next product bet.",
                suggested_checks=["manual documentation review"],
                dimensions=score_dimensions(
                    strategic_fit=4,
                    user_value=4,
                    novelty=3,
                    feasibility=5,
                    local_verifiability=3,
                    reversibility=5,
                    evidence_strength=3,
                ),
                risk="low",
            )
        )

    if test_available and technical_signals:
        evidence = paths_matching(files, root, "test", "tests", "spec") + purpose_paths
        opportunities.append(
            opportunity(
                opportunity_id="direction:core-flow-check",
                title="Protect the most important project direction with one scenario check",
                rationale=[
                    f"Project direction: {purpose['summary']}",
                    "There is local verification evidence, so the project can protect a strategic behavior instead of only checking implementation details.",
                ],
                evidence_paths=evidence,
                suggested_first_step="Add or strengthen one scenario-level check around the behavior that best represents the project value.",
                suggested_checks=[check],
                dimensions=score_dimensions(
                    strategic_fit=4,
                    user_value=4,
                    novelty=3,
                    feasibility=4,
                    local_verifiability=5,
                    reversibility=4,
                    evidence_strength=4,
                ),
            )
        )

    return sorted(opportunities, key=lambda item: (-item["priority_score"], item["title"]))[: max(limit, 1)]


def build_payload(root: Path, *, limit: int = 5) -> dict[str, Any]:
    root = root.resolve()
    files = repo_files(root)
    doc_files = pick_doc_files(root, files)
    docs = [(path, safe_read_text(path)) for path in doc_files]
    doc_text = "\n".join(text for _, text in docs)
    product_signals = infer_product_signals(root, files, doc_text)
    technical_signals = infer_technical_signals(root, files)
    constraints = infer_constraints(root, files, doc_text)
    purpose = infer_purpose(root, docs, product_signals)
    audience = infer_audience(doc_text, product_signals)
    opportunities = build_opportunities(
        root=root,
        files=files,
        purpose=purpose,
        product_signals=product_signals,
        technical_signals=technical_signals,
        constraints=constraints,
        limit=limit,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": "selfdex_project_direction",
        "generated_at": utc_timestamp(),
        "root": str(root),
        "project_name": root.name,
        "purpose": purpose,
        "audience": audience,
        "product_signals": product_signals,
        "technical_signals": technical_signals,
        "constraints": constraints,
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    purpose = payload["purpose"]
    lines = [
        "# Project Direction Snapshot",
        "",
        f"- project_name: `{payload['project_name']}`",
        f"- purpose: {purpose['summary']}",
        f"- audience: `{', '.join(payload['audience'])}`",
        f"- opportunity_count: `{payload['opportunity_count']}`",
        "",
        "## Product Signals",
        "",
    ]
    for item in payload["product_signals"] or []:
        lines.append(f"- `{item['label']}`: {item['summary']}")
    if not payload["product_signals"]:
        lines.append("- none")

    lines.extend(["", "## Strategic Opportunities", ""])
    for item in payload["opportunities"] or []:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- decision: `{item['decision']}`",
                f"- priority_score: `{item['priority_score']}`",
                f"- risk: `{item['risk']}`",
                f"- suggested_first_step: {item['suggested_first_step']}",
                "- evidence_paths:",
            ]
        )
        lines.extend([f"  - `{path}`" for path in item["evidence_paths"]] or ["  - none"])
        lines.append("- rationale:")
        lines.extend([f"  - {text}" for text in item["rationale"]])
        lines.append("")
    if not payload["opportunities"]:
        lines.append("- none")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(Path(args.root), limit=args.limit)
    write_json_or_markdown(payload, args.format, render_markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
