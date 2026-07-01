"""MCP server that talks to a Python agent running inside PowerFactory.

Use this when external `powerfactory.GetApplicationExt()` is unavailable or
blocked by licence/session mode, but PowerFactory's internal Python works.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("powerfactory")

_ROOT = Path(__file__).resolve().parent
_DEFAULT_BRIDGE_DIR = _ROOT / "pf_bridge"


def _call_agent(command: str, params: dict[str, Any] | None = None) -> Any:
    bridge_dir = Path(os.environ.get("POWERFACTORY_BRIDGE_DIR", str(_DEFAULT_BRIDGE_DIR))).resolve()
    bridge_dir.mkdir(parents=True, exist_ok=True)

    request_id = uuid.uuid4().hex
    request_path = bridge_dir / f"request_{request_id}.json"
    response_path = bridge_dir / f"response_{request_id}.json"
    tmp_path = bridge_dir / f"request_{request_id}.json.tmp"

    tmp_path.write_text(
        json.dumps({"id": request_id, "command": command, "params": params or {}}),
        encoding="utf-8",
    )
    tmp_path.replace(request_path)

    timeout = float(os.environ.get("POWERFACTORY_BRIDGE_TIMEOUT", "120"))
    deadline = time.time() + timeout
    while time.time() < deadline:
        if response_path.exists():
            response = json.loads(response_path.read_text(encoding="utf-8"))
            try:
                response_path.unlink()
            except OSError:
                pass
            if not response.get("ok"):
                raise RuntimeError(response.get("error", "PowerFactory agent failed"))
            return response.get("result")
        time.sleep(0.25)

    raise RuntimeError(
        "Timed out waiting for PowerFactory in-app agent. "
        "Run powerfactory_inapp_agent.py inside PowerFactory first."
    )


@mcp.tool()
def connect(show: bool = False) -> dict[str, Any]:
    """Connect to PowerFactory through the in-app agent."""
    return _call_agent("connect", {"show": show})


@mcp.tool()
def list_projects() -> list[str]:
    """List projects available under the current PowerFactory user."""
    return _call_agent("list_projects")


@mcp.tool()
def activate_project(project_name: str) -> dict[str, Any]:
    """Activate a PowerFactory project by name."""
    return _call_agent("activate_project", {"project_name": project_name})


@mcp.tool()
def get_active_project() -> dict[str, Any]:
    """Return the currently active project."""
    return _call_agent("get_active_project")


@mcp.tool()
def list_study_cases() -> list[str]:
    """List study cases in the active project."""
    return _call_agent("list_study_cases")


@mcp.tool()
def activate_study_case(study_case_name: str) -> dict[str, Any]:
    """Activate a study case by name in the active project."""
    return _call_agent("activate_study_case", {"study_case_name": study_case_name})


@mcp.tool()
def run_load_flow() -> dict[str, Any]:
    """Run load flow in the active study case."""
    return _call_agent("run_load_flow")


@mcp.tool()
def get_bus_voltages() -> list[dict[str, Any]]:
    """Read voltage results for all calculation-relevant terminals."""
    return _call_agent("get_bus_voltages")


@mcp.tool()
def get_line_loadings() -> list[dict[str, Any]]:
    """Read loading results for all calculation-relevant lines."""
    return _call_agent("get_line_loadings")


@mcp.tool()
def list_lines() -> list[dict[str, Any]]:
    """List calculation-relevant transmission lines."""
    return _call_agent("list_lines")


@mcp.tool()
def list_buses() -> list[dict[str, Any]]:
    """List calculation-relevant buses/terminals."""
    return _call_agent("list_buses")


@mcp.tool()
def set_line_out_of_service(line_name: str, out_of_service: bool = True) -> dict[str, Any]:
    """Open or close a line by setting its out-of-service flag."""
    return _call_agent(
        "set_line_out_of_service",
        {"line_name": line_name, "out_of_service": out_of_service},
    )


@mcp.tool()
def run_three_phase_short_circuit(bus_name: str) -> dict[str, Any]:
    """Run a three-phase short-circuit calculation at a bus and return Ikss/Skss."""
    return _call_agent("run_three_phase_short_circuit", {"bus_name": bus_name})


@mcp.tool()
def run_n_minus_1_line_short_circuit(
    target_bus_name: str,
    export_path: str = "outputs/n_minus_1_short_circuit.csv",
) -> dict[str, Any]:
    """Open each line one at a time and measure 3-phase short-circuit level at a target bus."""
    return _call_agent(
        "run_n_minus_1_line_short_circuit",
        {"target_bus_name": target_bus_name, "export_path": export_path},
    )


@mcp.tool()
def export_bus_voltages_csv(path: str = "outputs/bus_voltages.csv") -> dict[str, Any]:
    """Export bus voltage results to CSV."""
    return _call_agent("export_bus_voltages_csv", {"path": path})


@mcp.tool()
def export_line_loadings_csv(path: str = "outputs/line_loadings.csv") -> dict[str, Any]:
    """Export line loading results to CSV."""
    return _call_agent("export_line_loadings_csv", {"path": path})


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
