"""Python 3.3 bridge for DIgSILENT PowerFactory.

This script is launched by the MCP server because older PowerFactory versions
ship a powerfactory.pyd module that only loads in Python 3.3.
"""

from __future__ import print_function

import csv
import json
import os
import sys
import traceback


def _name(obj):
    return str(getattr(obj, "loc_name", obj))


def _safe_get_attr(obj, attr):
    try:
        return obj.GetAttribute(attr)
    except Exception:
        return None


def _prepare_import():
    pf_python_path = os.environ.get("POWERFACTORY_PYTHONPATH")
    if pf_python_path and pf_python_path not in sys.path:
        sys.path.insert(0, pf_python_path)

    if pf_python_path:
        pf_root = os.path.dirname(pf_python_path)
        paths = [pf_python_path, pf_root, os.environ.get("PATH", "")]
        os.environ["PATH"] = os.pathsep.join([p for p in paths if p])


def _get_app(show=False):
    _prepare_import()
    import powerfactory

    app = powerfactory.GetApplication()
    if app is None:
        raise RuntimeError("PowerFactory application is not available. Start PowerFactory first.")

    if show:
        app.Show()

    return app


def _ensure_output_path(path):
    output_path = os.path.abspath(os.path.expanduser(path))
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_path


def connect(params):
    app = _get_app(show=bool(params.get("show", False)))
    project = app.GetActiveProject()
    return {
        "connected": True,
        "active_project": _name(project) if project else None,
    }


def list_projects(params):
    app = _get_app()
    user = app.GetCurrentUser()
    projects = user.GetContents("*.IntPrj") if user else []
    return [_name(project) for project in projects]


def activate_project(params):
    app = _get_app()
    project_name = params["project_name"]
    project = app.ActivateProject(project_name)
    if not project:
        return {"activated": False, "project": project_name, "message": "Project not found"}
    return {"activated": True, "project": project_name}


def get_active_project(params):
    app = _get_app()
    project = app.GetActiveProject()
    return {
        "active_project": _name(project) if project else None,
        "has_active_project": project is not None,
    }


def list_study_cases(params):
    app = _get_app()
    study_folder = app.GetProjectFolder("study")
    if not study_folder:
        return []
    return [_name(case) for case in study_folder.GetContents("*.IntCase")]


def activate_study_case(params):
    app = _get_app()
    study_case_name = params["study_case_name"]
    study_folder = app.GetProjectFolder("study")
    if not study_folder:
        return {"activated": False, "study_case": study_case_name, "message": "No study folder"}

    matches = study_folder.GetContents(study_case_name + ".IntCase")
    if not matches:
        return {"activated": False, "study_case": study_case_name, "message": "Study case not found"}

    matches[0].Activate()
    return {"activated": True, "study_case": study_case_name}


def run_load_flow(params):
    app = _get_app()
    command = app.GetFromStudyCase("ComLdf")
    if not command:
        return {"executed": False, "message": "ComLdf not found in active study case"}

    result = command.Execute()
    return {"executed": result == 0, "return_code": result}


def get_bus_voltages(params):
    app = _get_app()
    terminals = app.GetCalcRelevantObjects("*.ElmTerm") or []
    rows = []
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


def get_line_loadings(params):
    app = _get_app()
    lines = app.GetCalcRelevantObjects("*.ElmLne") or []
    rows = []
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


def export_bus_voltages_csv(params):
    rows = get_bus_voltages(params)
    output_path = _ensure_output_path(params.get("path", "outputs/bus_voltages.csv"))
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["name", "voltage_kv", "voltage_pu", "angle_deg"])
        writer.writeheader()
        writer.writerows(rows)
    return {"path": output_path, "rows": len(rows)}


def export_line_loadings_csv(params):
    rows = get_line_loadings(params)
    output_path = _ensure_output_path(params.get("path", "outputs/line_loadings.csv"))
    with open(output_path, "w", newline="") as csvfile:
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
    return {"path": output_path, "rows": len(rows)}


COMMANDS = {
    "connect": connect,
    "list_projects": list_projects,
    "activate_project": activate_project,
    "get_active_project": get_active_project,
    "list_study_cases": list_study_cases,
    "activate_study_case": activate_study_case,
    "run_load_flow": run_load_flow,
    "get_bus_voltages": get_bus_voltages,
    "get_line_loadings": get_line_loadings,
    "export_bus_voltages_csv": export_bus_voltages_csv,
    "export_line_loadings_csv": export_line_loadings_csv,
}


def main():
    try:
        request = json.loads(sys.stdin.read())
        command = request["command"]
        params = request.get("params", {})
        if command not in COMMANDS:
            raise RuntimeError("Unknown command: " + command)
        result = COMMANDS[command](params)
        print(json.dumps({"ok": True, "result": result}))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
