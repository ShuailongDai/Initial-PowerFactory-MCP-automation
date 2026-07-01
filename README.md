# PowerFactory MCP Automation

Natural-language automation for DIgSILENT PowerFactory using the Model Context
Protocol (MCP).

This project lets an MCP client ask PowerFactory to run repeatable engineering
tasks such as load-flow studies, bus-voltage extraction, line switching,
three-phase short-circuit studies, and line N-1 short-circuit capacity sweeps.

## Why this project exists

PowerFactory studies often require repetitive manual steps:

1. Change network state.
2. Run a calculation.
3. Export results.
4. Restore the original state.
5. Repeat for the next contingency.

This repository wraps those steps behind controlled MCP tools so engineers can
request study workflows in natural language while PowerFactory remains the
calculation engine.

## Features

- MCP server for PowerFactory automation
- In-app PowerFactory Python agent for robust GUI-session control
- Load-flow execution
- Bus-voltage and line-loading extraction
- Line open/close control
- Three-phase short-circuit calculation at a selected bus
- Line N-1 short-circuit capacity study with CSV export
- Example innovation proposal PDF/PPT generation scripts

## Repository layout

```text
.
├── src/powerfactory_mcp/
│   ├── agent.py                 # Run inside PowerFactory as MCP_Agent
│   ├── server_bridge.py         # Recommended MCP server
│   ├── server_direct.py         # Optional direct external API server
│   └── legacy_py33_bridge.py    # Legacy helper for old PowerFactory versions
├── scripts/
│   ├── find_powerfactory_python.ps1
│   └── test_bridge_connection.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── TROUBLESHOOTING.md
│   └── WORKFLOWS.md
├── examples/
│   └── n_minus_1_short_circuit_bus_5.csv
├── tools/
│   ├── generate_innovation_pdf.py
│   └── build_innovation_ppt.mjs
├── mcp_config.example.json
├── pyproject.toml
└── requirements.txt
```

## Quick start

Install dependencies:

```powershell
python -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
```

Create a Python script in PowerFactory named `MCP_Agent`, paste the contents of:

```text
src/powerfactory_mcp/agent.py
```

Run `MCP_Agent` inside PowerFactory. Then test the bridge:

```powershell
.\.venv312\Scripts\python.exe .\scripts\test_bridge_connection.py
```

Configure your MCP client using:

```text
mcp_config.example.json
```

## Example result

The included example ran a line N-1 three-phase short-circuit study at Bus 5.
The limiting case was:

```text
Outaged line: Line 4-5
Ikss: 1.0144 kA
Skss: 404.09 MVA
```

See:

```text
examples/n_minus_1_short_circuit_bus_5.csv
```

## Documentation

- [Setup](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Workflows](docs/WORKFLOWS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Notes

This project assumes you are using a properly licensed PowerFactory
installation. It does not bypass, modify, or automate licensing.
