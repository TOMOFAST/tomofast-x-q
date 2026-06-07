# -*- coding: utf-8 -*-
"""
ArcGIS Pro Python Toolbox for Tomofast-x.
Launches the tkinter GUI subprocess and polls for pending layer additions.
"""
import arcpy
import os
import sys
import json
import time
import tempfile
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))

# sys.executable inside ArcGIS Pro is ArcGISPro.exe, not python.exe.
# sys.exec_prefix is the conda env root, so python.exe lives there.
_PYTHON_EXE = os.path.join(sys.exec_prefix, "python.exe")
if not os.path.exists(_PYTHON_EXE):
    _PYTHON_EXE = os.path.join(sys.exec_prefix, "Scripts", "python.exe")
if not os.path.exists(_PYTHON_EXE):
    _PYTHON_EXE = sys.executable

_LAUNCHER = os.path.join(_HERE, "tomofast_launcher.py")
_PENDING_FILE = os.path.join(tempfile.gettempdir(), "tomofast_pending.json")


def _clear_pending():
    if os.path.exists(_PENDING_FILE):
        try:
            os.remove(_PENDING_FILE)
        except Exception:
            pass


def _add_pending_layers(seen):
    """Add any new files recorded in the pending JSON to the active ArcGIS map.

    Uses *seen* (a set) to avoid adding the same path twice across polling
    cycles. The pending file is NOT deleted — new paths written by the GUI
    while this function runs are preserved for the next poll.
    """
    if not os.path.exists(_PENDING_FILE):
        return
    try:
        with open(_PENDING_FILE) as fh:
            paths = json.load(fh)   # flat list: ["path1", "path2", ...]
    except Exception as e:
        arcpy.AddWarning(f"Could not read pending file: {e}")
        return

    if not isinstance(paths, list):
        return

    new_paths = [
        p for p in paths
        if isinstance(p, str) and p not in seen and os.path.exists(p)
    ]
    if not new_paths:
        return

    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        if m is None:
            arcpy.AddWarning("No active map — could not add pending layers.")
            return
        for path in new_paths:
            try:
                m.addDataFromPath(path)
                arcpy.AddMessage(f"Added layer: {path}")
            except Exception as e:
                arcpy.AddWarning(f"Could not add {path}: {e}")
            seen.add(path)  # mark regardless of success so we don't retry
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
    except Exception as e:
        arcpy.AddWarning(f"Error adding layers: {e}")


class Toolbox:
    def __init__(self):
        self.label = "Tomofast-x"
        self.alias = "tomofastx"
        self.tools = [OpenTomofastPanel]


class OpenTomofastPanel:
    def __init__(self):
        self.label = "Open Tomofast-x Panel"
        self.description = "Launch the Tomofast-x data preparation and inversion GUI."
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def isLicensed(self):
        return True

    def execute(self, parameters, messages):
        _clear_pending()

        if not os.path.exists(_LAUNCHER):
            arcpy.AddError(f"Launcher not found: {_LAUNCHER}")
            return

        arcpy.AddMessage(f"Python: {_PYTHON_EXE}")
        arcpy.AddMessage(f"Launcher: {_LAUNCHER}")
        arcpy.AddMessage("Starting Tomofast-x GUI...")

        proc = subprocess.Popen(
            [_PYTHON_EXE, _LAUNCHER],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        seen = set()
        while proc.poll() is None:
            _add_pending_layers(seen)
            time.sleep(2)

        # Final sweep for layers written just before the GUI closed.
        _add_pending_layers(seen)

        stdout, stderr = proc.communicate()
        if proc.returncode != 0 and stderr:
            arcpy.AddWarning(
                f"GUI exited with warnings:\n{stderr.decode(errors='replace')[:2000]}"
            )
        else:
            arcpy.AddMessage("Tomofast-x GUI closed.")