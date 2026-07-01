"""Test the PowerFactory in-app MCP bridge agent."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path


bridge_dir = Path(
    os.environ.get(
        "POWERFACTORY_BRIDGE_DIR",
        r"C:\Users\daish\Documents\Auto Power Factory\pf_bridge",
    )
).resolve()
bridge_dir.mkdir(parents=True, exist_ok=True)

request_id = uuid.uuid4().hex
request_path = bridge_dir / f"request_{request_id}.json"
response_path = bridge_dir / f"response_{request_id}.json"

print("POWERFACTORY_BRIDGE_DIR =", bridge_dir, flush=True)
print("Sending connect request =", request_id, flush=True)

request_path.write_text(
    json.dumps({"id": request_id, "command": "connect", "params": {"show": False}}),
    encoding="utf-8",
)

deadline = time.time() + 120
while time.time() < deadline:
    if response_path.exists():
        response = json.loads(response_path.read_text(encoding="utf-8"))
        response_path.unlink(missing_ok=True)
        break
    time.sleep(0.5)
else:
    print("FAILED: no response from PowerFactory MCP_Agent", flush=True)
    print("Make sure the MCP_Agent Python script is still running inside PowerFactory.", flush=True)
    raise SystemExit(1)

print("Response =", response, flush=True)
if not response.get("ok"):
    print("FAILED:", response.get("error"), flush=True)
    raise SystemExit(1)

result = response["result"]
print("OK: connected through PowerFactory MCP_Agent", flush=True)
print("Active project =", result.get("active_project") or "(none)", flush=True)
