# Setup

## 1. Install PowerFactory and matching Python

PowerFactory's internal Python configuration must point to a Python version
available on the machine. For PowerFactory 2024, Python 3.12 is a practical
choice when the installation contains:

```text
D:\Program Files\DIgSILENT\PowerFactory 2024\Python\3.12
```

Install official 64-bit Python 3.12 and configure PowerFactory to use it.

## 2. Install MCP dependencies

From this repository:

```powershell
python -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
```

For editable development:

```powershell
.\.venv312\Scripts\python.exe -m pip install -e .
```

## 3. Create the PowerFactory in-app agent

In PowerFactory:

1. Open Data Manager.
2. Go to the active project's `Library` / `Scripts` area.
3. Create a Python script or ComPython object named `MCP_Agent`.
4. Copy the contents of `src/powerfactory_mcp/agent.py` into the script.
5. Execute the script.

The PowerFactory output window should show:

```text
PowerFactory MCP in-app agent started
```

## 4. Configure the MCP client

Use `mcp_config.example.json` as the MCP client configuration:

```json
{
  "mcpServers": {
    "powerfactory": {
      "command": "C:/path/to/repo/.venv312/Scripts/python.exe",
      "args": [
        "C:/path/to/repo/src/powerfactory_mcp/server_bridge.py"
      ],
      "env": {
        "POWERFACTORY_BRIDGE_DIR": "C:/path/to/repo/pf_bridge",
        "POWERFACTORY_BRIDGE_TIMEOUT": "120"
      }
    }
  }
}
```

Keep `MCP_Agent` running inside PowerFactory while using the MCP tools.
