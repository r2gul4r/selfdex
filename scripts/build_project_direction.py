#!/usr/bin/env python3
"""Infer project direction and strategic opportunities from repository evidence."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import project_direction_evidence as direction_evidence
    from argparse_utils import add_format_argument, add_root_argument
    from cli_output_utils import write_json_or_markdown
    from project_direction_opportunities import build_opportunities
except ModuleNotFoundError:
    from scripts import project_direction_evidence as direction_evidence
    from scripts.argparse_utils import add_format_argument, add_root_argument
    from scripts.cli_output_utils import write_json_or_markdown
    from scripts.project_direction_opportunities import build_opportunities


SCHEMA_VERSION = 1
ProductSignalRule = tuple[str, str, tuple[str, ...], tuple[str, ...]]
PRODUCT_SIGNAL_RULES: tuple[ProductSignalRule, ...] = (
    (
        "interactive_experience",
        "The project exposes or describes a user-facing surface.",
        ("frontend", "renderer", "components", "pages", ".html", ".tsx", ".jsx"),
        ("ui", "screen", "page", "dashboard", "frontend", "web app"),
    ),
    (
        "service_layer",
        "The project appears to have a service or integration layer.",
        ("controller", "route", "api", "server", "backend", "service"),
        ("api", "backend", "endpoint", "server", "service"),
    ),
    (
        "data_pipeline",
        "The project has data collection, persistence, or normalization concerns.",
        ("migration", "schema", "collector", "crawler", "ingest", "database", ".sql"),
        ("data", "database", "crawl", "ingest", "schema", "collector"),
    ),
    (
        "automation_loop",
        "The project contains automation or agent workflow signals.",
        ("scripts", "agents.md", "state.md", "runs", "workflow", "task"),
        ("agent", "automation", "workflow", "orchestrate", "codex"),
    ),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer a project direction snapshot from local repository evidence.")
    add_root_argument(parser, help_text="Repository root to scan.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum opportunities to emit. Defaults to 5.")
    add_format_argument(parser)
    return parser.parse_args(argv)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def product_signal_from_rule(
    root: Path,
    files: list[Path],
    doc_text: str,
    rule: ProductSignalRule,
) -> dict[str, Any] | None:
    label, summary, path_patterns, doc_keywords = rule
    evidence_paths = direction_evidence.paths_matching(files, root, *path_patterns)
    if evidence_paths or direction_evidence.contains_any(doc_text, doc_keywords):
        return direction_evidence.signal(label, summary, evidence_paths)
    return None


def infer_product_signals(root: Path, files: list[Path], doc_text: str) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for rule in PRODUCT_SIGNAL_RULES:
        inferred = product_signal_from_rule(root, files, doc_text, rule)
        if inferred:
            signals.append(inferred)
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
            direction_evidence.rel_path(root, path)
            for path in files
            if path.suffix.lower() in suffix_or_path_tokens
            or any(str(token) in direction_evidence.rel_path(root, path).lower() for token in suffix_or_path_tokens)
        ][:5]
        if matching_names or matching_paths:
            signals.append(
                direction_evidence.signal(
                    label,
                    f"Detected {label} stack evidence.",
                    sorted(set(matching_names + matching_paths))[:5],
                )
            )
    return signals


def infer_constraints(root: Path, files: list[Path], doc_text: str) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    test_paths = direction_evidence.paths_matching(files, root, "test", "tests", "spec")
    if test_paths:
        constraints.append(
            direction_evidence.signal(
                "local_verification_available",
                "There is at least one local test or spec surface.",
                test_paths,
                "high",
            )
        )
    else:
        constraints.append(
            direction_evidence.signal(
                "verification_surface_unclear",
                "No obvious test or spec surface was found in the first scan.",
                [],
                "medium",
            )
        )

    env_paths = direction_evidence.paths_matching(files, root, ".env", "secret", "credential")
    if env_paths or direction_evidence.contains_any(doc_text, ("secret", "token", "credential", "api key")):
        constraints.append(
            direction_evidence.signal(
                "secret_boundary",
                "Some behavior may depend on environment secrets and should stay approval-gated.",
                env_paths,
            )
        )

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
        if direction_evidence.contains_any(doc_text, keywords):
            audience.append(label)
    if not audience and product_signals:
        audience.append("project users")
    return audience or ["unknown audience"]


def infer_purpose(root: Path, docs: list[tuple[Path, str]], product_signals: list[dict[str, Any]]) -> dict[str, Any]:
    heading = ""
    fallback = ""
    evidence_paths = []
    evidence: list[dict[str, str]] = []
    for path, text in docs:
        relative = direction_evidence.rel_path(root, path)
        quote = direction_evidence.first_meaningful_line(text) or direction_evidence.first_heading(text)
        evidence_paths.append(relative)
        if quote:
            evidence.append(
                {
                    "path": relative,
                    "signal": "project purpose documentation",
                    "quote": quote,
                    "confidence": "medium",
                }
            )
        heading = heading or direction_evidence.first_heading(text)
        fallback = fallback or direction_evidence.first_meaningful_line(text)
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
        "evidence": evidence[:5],
    }


def build_payload(root: Path, *, limit: int = 5) -> dict[str, Any]:
    root = root.resolve()
    files = direction_evidence.repo_files(root)
    doc_files = direction_evidence.pick_doc_files(root, files)
    docs = [(path, direction_evidence.safe_read_text(path)) for path in doc_files]
    doc_text = "\n".join(text for _, text in docs)
    quote_map = direction_evidence.quote_map_from_docs(root, docs)
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
        quote_map=quote_map,
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
        lines.append("- evidence:")
        for evidence in item.get("evidence", []) or []:
            quote = f" quote={evidence['quote']}" if evidence.get("quote") else ""
            lines.append(
                f"  - `{evidence['path']}` confidence=`{evidence['confidence']}` "
                f"signal={evidence['signal']}{quote}"
            )
        if not item.get("evidence"):
            lines.append("  - none")
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
