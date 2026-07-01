"""Run this script inside PowerFactory as a ComPython script.

It watches a folder for JSON requests from the MCP server, executes them inside
PowerFactory, and writes JSON responses back.
"""

from __future__ import print_function

import glob
import csv
import json
import os
import sys
import time
import traceback

import powerfactory


BRIDGE_DIR = os.environ.get(
    "POWERFACTORY_BRIDGE_DIR",
    r"C:\Users\daish\Documents\Auto Power Factory\pf_bridge",
)


def _name(obj):
    return str(getattr(obj, "loc_name", obj))


def _safe_get_attr(obj, attr):
    try:
        return obj.GetAttribute(attr)
    except Exception:
        return None


def _find_by_name(objects, name):
    for obj in objects:
        if _name(obj) == name:
            return obj
    lowered = name.lower()
    for obj in objects:
        if _name(obj).lower() == lowered:
            return obj
    return None


def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _ensure_output_path(path):
    output_path = os.path.abspath(os.path.expanduser(path))
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_path


def _get_app(show=False):
    app = powerfactory.GetApplication()
    if app is None:
        raise RuntimeError("PowerFactory application is not available")
    if show:
        app.Show()
    return app


def connect(params):
    app = _get_app(show=bool(params.get("show", False)))
    project = app.GetActiveProject()
    return {"connected": True, "active_project": _name(project) if project else None}


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
    return {"active_project": _name(project) if project else None, "has_active_project": project is not None}


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


def list_lines(params):
    app = _get_app()
    lines = app.GetCalcRelevantObjects("*.ElmLne") or []
    rows = []
    for line in lines:
        rows.append(
            {
                "name": _name(line),
                "out_of_service": bool(_safe_get_attr(line, "outserv")),
                "loading_percent": _safe_get_attr(line, "c:loading"),
            }
        )
    return rows


def list_buses(params):
    app = _get_app()
    terminals = app.GetCalcRelevantObjects("*.ElmTerm") or []
    rows = []
    for terminal in terminals:
        rows.append(
            {
                "name": _name(terminal),
                "voltage": _safe_get_attr(terminal, "m:u"),
                "voltage_pu": _safe_get_attr(terminal, "m:U"),
            }
        )
    return rows


def set_line_out_of_service(params):
    app = _get_app()
    line_name = params["line_name"]
    out_of_service = bool(params.get("out_of_service", True))
    lines = app.GetCalcRelevantObjects("*.ElmLne") or []
    line = _find_by_name(lines, line_name)
    if line is None:
        return {"changed": False, "line": line_name, "message": "Line not found"}

    try:
        line.outserv = 1 if out_of_service else 0
    except Exception:
        line.SetAttribute("outserv", 1 if out_of_service else 0)

    return {
        "changed": True,
        "line": _name(line),
        "out_of_service": bool(_safe_get_attr(line, "outserv")),
    }


def run_three_phase_short_circuit(params):
    app = _get_app()
    bus_name = params["bus_name"]
    terminals = app.GetCalcRelevantObjects("*.ElmTerm") or []
    terminal = _find_by_name(terminals, bus_name)
    if terminal is None:
        return {"executed": False, "bus": bus_name, "message": "Bus not found"}

    command = app.GetFromStudyCase("ComShc")
    if not command:
        return {"executed": False, "bus": bus_name, "message": "ComShc not found in active study case"}

    # IEC three-phase short circuit. PowerFactory accepts these attributes in
    # recent versions; unsupported attributes are ignored for compatibility.
    for attr, value in (
        ("iopt_mde", 0),
        ("iopt_shc", "3psc"),
        ("shcobj", terminal),
    ):
        try:
            setattr(command, attr, value)
        except Exception:
            try:
                command.SetAttribute(attr, value)
            except Exception:
                pass

    result = command.Execute()
    return {
        "executed": result == 0,
        "return_code": result,
        "bus": _name(terminal),
        "short_circuit_current_ka": _safe_get_attr(terminal, "m:Ikss"),
        "short_circuit_power_mva": _safe_get_attr(terminal, "m:Skss"),
    }


def run_n_minus_1_line_short_circuit(params):
    app = _get_app()
    target_bus_name = params["target_bus_name"]
    export_path = params.get("export_path", "")

    terminals = app.GetCalcRelevantObjects("*.ElmTerm") or []
    target_bus = _find_by_name(terminals, target_bus_name)
    if target_bus is None:
        return {
            "executed": False,
            "target_bus": target_bus_name,
            "message": "Target bus not found",
        }

    lines = app.GetCalcRelevantObjects("*.ElmLne") or []
    command = app.GetFromStudyCase("ComShc")
    if not command:
        return {
            "executed": False,
            "target_bus": target_bus_name,
            "message": "ComShc not found in active study case",
        }

    original_states = {}
    rows = []

    try:
        for line in lines:
            line_name = _name(line)
            original_states[line_name] = _safe_get_attr(line, "outserv")

            try:
                line.outserv = 1
            except Exception:
                line.SetAttribute("outserv", 1)

            for attr, value in (
                ("iopt_mde", 0),
                ("iopt_shc", "3psc"),
                ("shcobj", target_bus),
            ):
                try:
                    setattr(command, attr, value)
                except Exception:
                    try:
                        command.SetAttribute(attr, value)
                    except Exception:
                        pass

            result = command.Execute()
            rows.append(
                {
                    "outaged_line": line_name,
                    "target_bus": _name(target_bus),
                    "executed": result == 0,
                    "return_code": result,
                    "short_circuit_current_ka": _safe_get_attr(target_bus, "m:Ikss"),
                    "short_circuit_power_mva": _safe_get_attr(target_bus, "m:Skss"),
                }
            )

            try:
                line.outserv = original_states[line_name]
            except Exception:
                line.SetAttribute("outserv", original_states[line_name])
    finally:
        for line in lines:
            line_name = _name(line)
            if line_name in original_states:
                try:
                    line.outserv = original_states[line_name]
                except Exception:
                    try:
                        line.SetAttribute("outserv", original_states[line_name])
                    except Exception:
                        pass

    output_path = ""
    if export_path:
        output_path = _ensure_output_path(export_path)
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "outaged_line",
                    "target_bus",
                    "executed",
                    "return_code",
                    "short_circuit_current_ka",
                    "short_circuit_power_mva",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    return {
        "executed": True,
        "target_bus": _name(target_bus),
        "contingencies": len(rows),
        "export_path": output_path,
        "results": rows,
    }


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
    "list_lines": list_lines,
    "list_buses": list_buses,
    "set_line_out_of_service": set_line_out_of_service,
    "run_three_phase_short_circuit": run_three_phase_short_circuit,
    "run_n_minus_1_line_short_circuit": run_n_minus_1_line_short_circuit,
    "export_bus_voltages_csv": export_bus_voltages_csv,
    "export_line_loadings_csv": export_line_loadings_csv,
}


def _write_json(path, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as handle:
        json.dump(data, handle)
    if os.path.exists(path):
        os.remove(path)
    os.rename(tmp_path, path)


def _handle_request(path):
    with open(path, "r") as handle:
        request = json.load(handle)

    request_id = request["id"]
    command = request["command"]
    params = request.get("params", {})

    if command == "stop_agent":
        result = {"stopped": True}
        response = {"id": request_id, "ok": True, "result": result}
        _write_json(os.path.join(BRIDGE_DIR, "response_" + request_id + ".json"), response)
        return False

    if command not in COMMANDS:
        raise RuntimeError("Unknown command: " + command)

    result = COMMANDS[command](params)
    response = {"id": request_id, "ok": True, "result": result}
    _write_json(os.path.join(BRIDGE_DIR, "response_" + request_id + ".json"), response)
    return True


def main():
    _ensure_dir(BRIDGE_DIR)
    app = _get_app()
    app.PrintPlain("PowerFactory MCP in-app agent started: " + BRIDGE_DIR)

    running = True
    while running:
        request_paths = sorted(glob.glob(os.path.join(BRIDGE_DIR, "request_*.json")))
        for request_path in request_paths:
            try:
                running = _handle_request(request_path)
            except Exception as exc:
                request_id = os.path.basename(request_path)[8:-5]
                response = {
                    "id": request_id,
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                _write_json(os.path.join(BRIDGE_DIR, "response_" + request_id + ".json"), response)
            try:
                os.remove(request_path)
            except Exception:
                pass
        time.sleep(0.5)

    app.PrintPlain("PowerFactory MCP in-app agent stopped")


if __name__ == "__main__":
    main()
