"""Diagnose where the old PowerFactory Python 3.3 API fails."""

from __future__ import print_function

import os
import sys


def say(message):
    print(message)
    sys.stdout.flush()


pf_python_path = os.environ.get("POWERFACTORY_PYTHONPATH", r"D:\PowerFactory\PowerFactory\python")
pf_root = os.path.dirname(pf_python_path)

say("Python executable: " + sys.executable)
say("Python version: " + sys.version.replace("\n", " "))
say("POWERFACTORY_PYTHONPATH: " + pf_python_path)
say("PowerFactory root: " + pf_root)

if pf_python_path not in sys.path:
    sys.path.insert(0, pf_python_path)

os.environ["PATH"] = os.pathsep.join(
    [
        pf_python_path,
        pf_root,
        os.environ.get("PATH", ""),
    ]
)

say("Step 1: importing powerfactory...")
import powerfactory

say("Step 2: import OK")
say("Step 3: calling GetApplication()...")
app = powerfactory.GetApplication()

say("Step 4: GetApplication returned")
if app is None:
    say("Result: app is None")
else:
    say("Result: connected")
    project = app.GetActiveProject()
    say("Active project: " + (getattr(project, "loc_name", None) or "(none)"))
