# -*- coding: utf-8 -*-
"""
Entry point for the Tomofast-x ArcGIS GUI subprocess.
Adds the plugin root and Install/ to sys.path so all modules are importable.
"""
import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
_plugin_root = os.path.dirname(_here)          # tomofast_x_q/
_install = os.path.join(_here, "Install")

for p in (_install, _plugin_root):
    if p not in sys.path:
        sys.path.insert(0, p)

from tomofast_arcgis import TomofastArcGIS

if __name__ == "__main__":
    app = TomofastArcGIS()
    app.run()
