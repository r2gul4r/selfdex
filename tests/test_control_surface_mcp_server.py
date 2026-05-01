from __future__ import annotations

from http.server import HTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_loader_utils import load_script


control_surface_mcp = load_script("control_surface_mcp_server.py")


def write_registry(root: Path) -> None:
    (root / "project_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "projects": [
                    {
                        "project_id": "selfdex",
                        "path": ".",
                        "role": "control harness",
                        "write_policy": "selfdex-local writes only",
                        "verification": ["python -m unittest discover -s tests"],
                    },
                    {
                        "project_id": "demo",
                        "path": "../demo",
                        "role": "read-only target",
                        "write_policy": "read-only",
                        "verification": ["read-only planning"],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_campaign(root: Path) -> None:
    (root / "CAMPAIGN_STATE.md").write_text(
        """# Campaign State

## Campaign

- name: `test`
- goal: `Make Selfdex a command center for selected projects.`

## Candidate Queue

- Wrap control surface as MCP tool.
""",
        encoding="utf-8",
    )
    (root / "CAMPAIGN_STATE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_kind": "selfdex_campaign_contract",
                "campaign": {
                    "direction_review_default": "recommend_and_wait_for_user_approval",
                },
                "model_usage_policy": {
                    "gpt_direction_review_auto_call": False,
                    "gpt_direction_review_approval": "user-approved-or-user-called-only",
                },
                "first_app_surface": {
                    "write_capable_target_execution_exposed": False,
                },
                "latest_run": {
                    "status": "completed",
                    "artifact_path": "runs/selfdex/20260501-000001-wrapper.md",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "STATE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_kind": "selfdex_state_contract",
                "current_task": {
                    "task": "Wrap control surface as MCP tool.",
                    "phase": "verified",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_runs(root: Path) -> None:
    runs = root / "runs" / "selfdex"
    runs.mkdir(parents=True)
    (runs / "20260501-000001-wrapper.md").write_text(
        """# MCP Wrapper Run

- status: `completed`
- project_key: `selfdex`
- summary: `wrapper`
""",
        encoding="utf-8",
    )
    (root / "runs" / "external-validation").mkdir()
    (root / "runs" / "external-validation" / "summary.md").write_text(
        "# External Summary\n\n- status: `pass`\n",
        encoding="utf-8",
    )


def write_fixture(root: Path) -> None:
    write_registry(root)
    write_campaign(root)
    write_runs(root)


class ControlSurfaceMcpServerTests(unittest.TestCase):
    def test_tool_descriptor_is_read_only(self) -> None:
        descriptor = control_surface_mcp.control_surface_tool_descriptor()

        self.assertEqual(descriptor["name"], "selfdex_control_surface_snapshot")
        self.assertTrue(descriptor["annotations"]["readOnlyHint"])
        self.assertFalse(descriptor["annotations"]["destructiveHint"])
        self.assertFalse(descriptor["annotations"]["openWorldHint"])
        self.assertFalse(descriptor["inputSchema"]["additionalProperties"])

    def test_tools_call_returns_read_only_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)

            result = control_surface_mcp.call_tool(
                "selfdex_control_surface_snapshot",
                {"run_limit": 1},
                root,
            )

        snapshot = json.loads(result["content"][0]["text"])
        self.assertFalse(snapshot["mutating_tools_exposed"])
        self.assertEqual(snapshot["surface_kind"], "read_only")
        self.assertEqual(snapshot["projects"][1]["write_policy"], "read-only")
        self.assertEqual(snapshot["next_task"]["title"], "Wrap control surface as MCP tool.")
        self.assertEqual(snapshot["recent_runs"][0]["path"], "runs/selfdex/20260501-000001-wrapper.md")
        self.assertFalse(snapshot["approval_status"]["gpt_direction_review_auto_call"])
        self.assertEqual(snapshot["approval_status"]["current_phase"], "verified")
        self.assertFalse(result["structuredContent"]["approval_status"]["write_capable_apps_mcp_tools_exposed"])
        self.assertEqual(result["structuredContent"]["recent_run_count"], 1)

    def test_json_rpc_lists_and_calls_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)

            list_response = control_surface_mcp.handle_rpc_request(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
                root,
            )
            call_response = control_surface_mcp.handle_rpc_request(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "selfdex_control_surface_snapshot",
                        "arguments": {"run_limit": 0},
                    },
                },
                root,
            )

        self.assertEqual(list_response["result"]["tools"][0]["name"], "selfdex_control_surface_snapshot")
        self.assertFalse(call_response["result"]["structuredContent"]["mutating_tools_exposed"])
        self.assertIn("approval_status", call_response["result"]["structuredContent"])
        self.assertEqual(call_response["result"]["structuredContent"]["recent_run_count"], 0)

    def test_http_mcp_endpoint_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root)
            handler = control_surface_mcp.make_handler(root)
            server = HTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                payload = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/list",
                        "params": {},
                    }
                ).encode("utf-8")
                req = request.Request(
                    f"http://127.0.0.1:{port}/mcp",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with request.urlopen(req, timeout=5) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(response_payload["result"]["tools"][0]["name"], "selfdex_control_surface_snapshot")

    def test_invalid_run_limit_returns_json_rpc_error(self) -> None:
        response = control_surface_mcp.handle_rpc_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "selfdex_control_surface_snapshot",
                    "arguments": {"run_limit": 99},
                },
            },
            Path("."),
        )

        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("run_limit", response["error"]["data"])


if __name__ == "__main__":
    unittest.main()
