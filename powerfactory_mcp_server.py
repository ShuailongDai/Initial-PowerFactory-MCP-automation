"""MCP server for automating DIgSILENT PowerFactory 2024.

Run this server with a Python version that matches PowerFactory's Python API.
For this workspace, `.venv312` matches:

    D:/Program Files/DIgSILENT/PowerFactory 2024/Python/3.12
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("powerfactory")

_APP: Any | None = None
_DEFAULT_PF_PYTHONPATH = r"D:\Program Files\DIgSILENT\PowerFactory 2024\Python\3.12"


def _prepare_powerfactory_import() -> None:
    pf_python_path = os.environ.get("POWERFACTORY_PYTHONPATH", _DEFAULT_PF_PYTHONPATH)
    pf_path = Path(pf_python_path)
    pf_root = pf_path.parents[1]

    if str(pf_path) not in sys.path:
        sys.path.insert(0, str(pf_path))

    os.environ["PATH"] = os.pathsep.join([str(pf_path), str(pf_root), os.environ.get("PATH", "")])

    if hasattr(os, "add_dll_directory"):
        candidate_dirs = [pf_path, pf_root]
        for dll_dir in candidate_dirs:
            if dll_dir.exists():
                os.add_dll_directory(str(dll_dir))


def _get_app(show: bool = False) -> Any:
    global _APP

    if _APP is not None:
        return _APP

    _prepare_powerfactory_import()

    try:
        import powerfactory  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Cannot import PowerFactory Python module. Check POWERFACTORY_PYTHONPATH "
            "and make sure this MCP server runs with the matching Python version."
        ) from exc

    username = os.environ.get("POWERFACTORY_USER", "")
    password = os.environ.get("POWERFACTORY_PASSWORD", "")
    command_line = os.environ.get("POWERFACTORY_COMMAND_LINE", "")
    use_ext = os.environ.get("POWERFACTORY_USE_EXT", "1") != "0"

    getter = powerfactory.GetApplicationExt if use_ext and hasattr(powerfactory, "GetApplicationExt") else powerfactory.GetApplication
    args = [arg for arg in (username, password, command_line) if arg]
    app = getter(*args)
    if app is None:
        raise RuntimeError(
            "PowerFactory application is not available. Start PowerFactory 2024 first, "
            "then try again."
        )

    if show:
        app.Show()

    _APP = app
    return app


def _name(obj: Any) -> str:
    return str(getattr(obj, "loc_name", obj))


def _safe_get_attr(obj: Any, attr: str) -> Any:
    try:
        return obj.GetAttribute(attr)
    except Exception:
        try:
            return getattr(obj, attr)
        except Exception:
            return None


def _ensure_output_path(path: str) -> Path:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


@mcp.tool()
def connect(show: bool = False) -> dict[str, Any]:
    """Connect to PowerFactory and optionally show the application window."""
    app = _get_app(show=show)
    active_project = app.GetActiveProject()

    return {
        "connected": True,
        "active_project": _name(active_project) if active_project else None,
    }


@mcp.tool()
def list_projects() -> list[str]:
    """List projects available under the current PowerFactory user."""
    app = _get_app()
    user = app.GetCurrentUser()
    if not user:
        return []

    projects = user.GetContents("*.IntPrj") or []
    return [_name(project) for project in projects]


@mcp.tool()
def activate_project(project_name: str) -> dict[str, Any]:
    """Activate a PowerFactory project by name."""
    app = _get_app()
    result = app.ActivateProject(project_name)
    active_project = app.GetActiveProject()
    active_name = _name(active_project) if active_project else None

    return {
        "activated": active_name == project_name or bool(result),
        "project": project_name,
        "active_project": active_name,
        "raw_result": str(result),
    }


@mcp.tool()
def get_active_project() -> dict[str, Any]:
    """Return the currently active project."""
    app = _get_app()
    project = app.GetActiveProject()

    return {
        "active_project": _name(project) if project else None,
        "has_active_project": project is not None,
    }


@mcp.tool()
def list_study_cases() -> list[str]:
    """List study cases in the active project."""
    app = _get_app()
    study_folder = app.GetProjectFolder("study")
    if not study_folder:
        return []

    cases = study_folder.GetContents("*.IntCase") or []
    return [_name(case) for case in cases]


@mcp.tool()
def activate_study_case(study_case_name: str) -> dict[str, Any]:
    """Activate a study case by name in the active project."""
    app = _get_app()
    study_folder = app.GetProjectFolder("study")
    if not study_folder:
        return {"activated": False, "study_case": study_case_name, "message": "No study folder"}

    matches = study_folder.GetContents(f"{study_case_name}.IntCase") or []
    if not matches:
        return {
            "activated": False,
            "study_case": study_case_name,
            "message": "Study case not found",
        }

    result = matches[0].Activate()
    return {"activated": result == 0 or result is None, "study_case": study_case_name, "raw_result": str(result)}


@mcp.tool()
def run_load_flow() -> dict[str, Any]:
    """Run load flow in the active study case."""
    app = _get_app()
    command = app.GetFromStudyCase("ComLdf")
    if not command:
        return {"executed": False, "message": "ComLdf not found in active study case"}

    result = command.Execute()
    return {"executed": result == 0, "return_code": result}


@mcp.tool()
def get_bus_voltages() -> list[dict[str, Any]]:
    """Read voltage results for all calculation-relevant terminals."""
    app = _get_app()
    terminals = app.GetCalcRelevantObjects("*.ElmTerm") or []

    rows: list[dict[str, Any]] = []
    for terminal in terminals:
        rows.append(
            {
                "name": _name(terminal),
                "voltage_kv": _safe_get_attr(terminal, "m:u"),
                "voltage_pu": _safe_get_attr(terminal, "m:U"),
                "angle_deg": _safe_get_attr(terminal, "m:phiu"),
            }
        )

    return rows


@mcp.tool()
def get_line_loadings() -> list[dict[str, Any]]:
    """Read loading results for all calculation-relevant lines."""
    app = _get_app()
    lines = app.GetCalcRelevantObjects("*.ElmLne") or []

    rows: list[dict[str, Any]] = []
    for line in lines:
        rows.append(
            {
                "name": _name(line),
                "loading_percent": _safe_get_attr(line, "c:loading"),
                "current_ka": _safe_get_attr(line, "m:I:bus1"),
                "active_power_mw": _safe_get_attr(line, "m:P:bus1"),
                "reactive_power_mvar": _safe_get_attr(line, "m:Q:bus1"),
            }
        )

    return rows


@mcp.tool()
def export_bus_voltages_csv(path: str = "outputs/bus_voltages.csv") -> dict[str, Any]:
    """Export bus voltage results to CSV."""
    rows = get_bus_voltages()
    output_path = _ensure_output_path(path)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["name", "voltage_kv", "voltage_pu", "angle_deg"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {"path": str(output_path), "rows": len(rows)}


@mcp.tool()
def export_line_loadings_csv(path: str = "outputs/line_loadings.csv") -> dict[str, Any]:
    """Export line loading results to CSV."""
    rows = get_line_loadings()
    output_path = _ensure_output_path(path)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "name",
                "loading_percent",
                "current_ka",
                "active_power_mw",
                "reactive_power_mvar",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {"path": str(output_path), "rows": len(rows)}


if __name__ == "__main__":
    mcp.run()
