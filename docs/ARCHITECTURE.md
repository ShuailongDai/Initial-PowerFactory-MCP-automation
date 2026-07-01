# Architecture

This project supports two PowerFactory control modes.

## Recommended mode: in-app bridge

The in-app bridge is the most robust option when PowerFactory's external
engine API is unavailable, blocked by licensing, or waits for a GUI session.

```text
Natural language client
        |
        v
MCP server: server_bridge.py
        |
        v
File bridge: pf_bridge/request_*.json and response_*.json
        |
        v
PowerFactory in-app Python script: agent.py
        |
        v
Active PowerFactory project and study case
```

The MCP server writes a JSON request file. The PowerFactory agent, running
inside PowerFactory, reads it, executes the command through the PowerFactory
Python API, and writes a JSON response.

## Optional mode: direct external API

`server_direct.py` calls `powerfactory.GetApplicationExt()` from outside
PowerFactory. This mode can be cleaner, but it depends on the local
PowerFactory licence/session configuration and may not work in every
installation.

## Core tool set

- Connect to the active PowerFactory session
- List projects, study cases, buses, and lines
- Run load flow
- Read bus voltages and line loadings
- Open or close a line
- Run three-phase short-circuit at a selected bus
- Run line N-1 short-circuit batch studies and export CSV
