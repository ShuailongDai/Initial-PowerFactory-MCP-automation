# Troubleshooting

## PowerFactory says the Python interpreter was not found

Install the exact Python version selected in the PowerFactory configuration
dialog. For example, if PowerFactory is configured for Python 3.12, install
official 64-bit Python 3.12 and restart PowerFactory.

## `GetApplicationExt()` hangs

Use the in-app bridge mode instead of direct external mode. Start `MCP_Agent`
inside PowerFactory, then use `server_bridge.py`.

## MCP requests time out

Check that:

- `MCP_Agent` is still running inside PowerFactory.
- The `POWERFACTORY_BRIDGE_DIR` in the MCP config matches the bridge directory
  printed by PowerFactory.
- PowerFactory is not blocked by a modal dialog.

## New MCP command is not recognized

The PowerFactory in-app agent is still running old code. Stop and re-run the
`MCP_Agent` Python script after updating `agent.py`.
