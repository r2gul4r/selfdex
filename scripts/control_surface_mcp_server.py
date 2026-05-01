#!/usr/bin/env python3
"""Expose the Selfdex control surface as a read-only MCP-style JSON-RPC tool."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
from typing import Any

try:
    import build_control_surface_snapshot
except ModuleNotFoundError:
    from scripts import build_control_surface_snapshot


SERVER_NAME = "selfdex-control-surface"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-03-26"
MCP_PATH = "/mcp"
HEALTH_PATH = "/health"
TOOL_NAME = "selfdex_control_surface_snapshot"
DEFAULT_RUN_LIMIT = 5
MAX_RUN_LIMIT = 20


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or inspect the read-only Selfdex control-surface MCP scaffold."
    )
    parser.add_argument("--root", default=".", help="Selfdex repository root.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host for --serve.")
    parser.add_argument("--port", type=int, default=8765, help="HTTP bind port for --serve.")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a local HTTP JSON-RPC endpoint at /mcp.",
    )
    parser.add_argument(
        "--describe-tools",
        action="store_true",
        help="Print the MCP tool descriptors and exit.",
    )
    return parser.parse_args(argv)


def control_surface_tool_descriptor() -> dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "title": "Get Selfdex control surface snapshot",
        "description": (
            "Use this read-only tool to inspect the current Selfdex command-center "
            "state: registered projects, the next recommended task, and recent run "
            "summaries, plus approval status. It never starts Codex, creates "
            "branches, or writes to target projects."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_limit": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": MAX_RUN_LIMIT,
                    "default": DEFAULT_RUN_LIMIT,
                    "description": "Maximum number of timestamped run summaries to return.",
                }
            },
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
    }


def describe_tools_payload() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "analysis_kind": "selfdex_mcp_tool_descriptor",
        "server": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "transport": "local_http_json_rpc_scaffold",
            "endpoint": MCP_PATH,
        },
        "surface_kind": "read_only",
        "mutating_tools_exposed": False,
        "tools": [control_surface_tool_descriptor()],
    }


def normalize_run_limit(arguments: dict[str, Any] | None) -> int:
    value = DEFAULT_RUN_LIMIT if not arguments else arguments.get("run_limit", DEFAULT_RUN_LIMIT)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("run_limit must be an integer")
    if value < 0 or value > MAX_RUN_LIMIT:
        raise ValueError(f"run_limit must be between 0 and {MAX_RUN_LIMIT}")
    return value


def call_tool(name: str, arguments: dict[str, Any] | None, root: Path) -> dict[str, Any]:
    if name != TOOL_NAME:
        raise ValueError(f"unknown tool: {name}")

    run_limit = normalize_run_limit(arguments)
    snapshot = build_control_surface_snapshot.build_payload(root, run_limit=run_limit)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    return {
        "content": [
            {
                "type": "text",
                "text": text,
            }
        ],
        "structuredContent": {
            "surface_kind": snapshot["surface_kind"],
            "mutating_tools_exposed": snapshot["mutating_tools_exposed"],
            "project_count": snapshot["project_count"],
            "next_task": snapshot.get("next_task"),
            "recent_run_count": len(snapshot["recent_runs"]),
            "approval_status": snapshot.get("approval_status", {}),
            "errors": snapshot.get("errors", []),
        },
        "isError": False,
    }


def json_rpc_error(
    request_id: Any,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def json_rpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def handle_rpc_request(message: dict[str, Any], root: Path) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if not isinstance(method, str):
        return json_rpc_error(request_id, -32600, "Invalid Request", "method must be a string")
    if not isinstance(params, dict):
        return json_rpc_error(request_id, -32602, "Invalid params", "params must be an object")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "capabilities": {"tools": {}},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [control_surface_tool_descriptor()]}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str):
                return json_rpc_error(request_id, -32602, "Invalid params", "tool name is required")
            if not isinstance(arguments, dict):
                return json_rpc_error(
                    request_id,
                    -32602,
                    "Invalid params",
                    "tool arguments must be an object",
                )
            result = call_tool(name, arguments, root)
        else:
            return json_rpc_error(request_id, -32601, "Method not found", method)
    except ValueError as exc:
        return json_rpc_error(request_id, -32602, "Invalid params", str(exc))
    except (FileNotFoundError, RuntimeError, json.JSONDecodeError) as exc:
        return json_rpc_error(request_id, -32000, "Tool execution failed", str(exc))

    if "id" not in message:
        return None
    return json_rpc_result(request_id, result)


def make_handler(root: Path) -> type[BaseHTTPRequestHandler]:
    class ControlSurfaceMcpHandler(BaseHTTPRequestHandler):
        server_version = f"{SERVER_NAME}/{SERVER_VERSION}"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != HEALTH_PATH:
                self.send_json({"error": "not found"}, status=404)
                return
            self.send_json({"status": "ok", "server": SERVER_NAME})

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path != MCP_PATH:
                self.send_json({"error": "not found"}, status=404)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            try:
                message = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                self.send_json(json_rpc_error(None, -32700, "Parse error", str(exc)), status=400)
                return

            if not isinstance(message, dict):
                self.send_json(json_rpc_error(None, -32600, "Invalid Request"), status=400)
                return

            response = handle_rpc_request(message, root)
            if response is None:
                self.send_response(204)
                self.end_headers()
                return
            self.send_json(response)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ControlSurfaceMcpHandler


def serve(root: Path, host: str, port: int) -> None:
    handler = make_handler(root)
    server = HTTPServer((host, port), handler)
    print(f"{SERVER_NAME} listening on http://{host}:{port}{MCP_PATH}", file=sys.stderr)
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()

    if args.describe_tools:
        json.dump(describe_tools_payload(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.serve:
        serve(root, args.host, args.port)
        return 0

    print("Nothing to do. Use --describe-tools for a static check or --serve to run /mcp.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
