# -*- coding: utf-8 -*-
"""Combo box listing project layers that are saved to disk.

The parfile needs a file path, so only layers backed by a real file are
offered (memory layers and processing temp outputs are skipped).
"""

import os

from qgis.PyQt import QtCore, QtWidgets
from qgis.core import (
    QgsProcessingUtils,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)

try:
    from qgis.core import Qgis

    _LINE = Qgis.GeometryType.Line
    _POLYGON = Qgis.GeometryType.Polygon
except AttributeError:
    _LINE = QgsWkbTypes.LineGeometry
    _POLYGON = QgsWkbTypes.PolygonGeometry

_PATH_ROLE = QtCore.Qt.ItemDataRole.UserRole
_LAYER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


def _norm(path):
    return os.path.normcase(os.path.normpath(path)) if path else ""


def _is_temp(path):
    temp = _norm(QgsProcessingUtils.tempFolder())
    return bool(temp) and _norm(path).startswith(temp)


def layer_disk_path(layer):
    """Path of the file backing `layer`, or "" if it isn't saved to disk."""
    if isinstance(layer, QgsRasterLayer):
        if layer.providerType() != "gdal":
            return ""
        path = layer.source().split("|")[0]
    elif isinstance(layer, QgsVectorLayer):
        provider = layer.providerType()
        if provider == "ogr":
            path = layer.source().split("|")[0]
        elif provider == "delimitedtext":
            path = QtCore.QUrl(layer.source()).toLocalFile()
        else:
            return ""
    else:
        return ""
    if not path or not os.path.isfile(path) or _is_temp(path):
        return ""
    return path


def delimited_text_xy(layer):
    """(xField, yField) of a delimited-text layer, or None."""
    if not isinstance(layer, QgsVectorLayer) or layer.providerType() != "delimitedtext":
        return None
    query = QtCore.QUrlQuery(QtCore.QUrl(layer.source()))
    x, y = query.queryItemValue("xField"), query.queryItemValue("yField")
    return (x, y) if x and y else None


def _accepts(kind, layer, path):
    suffix = path.rsplit(".", 1)[-1].lower()
    if kind == "grav_mag":
        if isinstance(layer, QgsRasterLayer):
            return suffix in ("tif", "tiff", "ers")
        return layer.providerType() == "delimitedtext" and suffix == "csv"
    if kind == "dtm":
        return isinstance(layer, QgsRasterLayer) and suffix in ("tif", "tiff")
    if kind == "roi":
        if not isinstance(layer, QgsVectorLayer) or layer.providerType() != "ogr":
            return False
        return QgsWkbTypes.geometryType(layer.wkbType()) in (_LINE, _POLYGON)
    return False


class LayerPathCombo(QtWidgets.QComboBox):
    """Lists eligible saved layers, plus the current on-disk file if any."""

    PLACEHOLDER = "(select a saved layer)"

    def __init__(self, parent, kind):
        super().__init__(parent)
        self._kind = kind
        self._disk_path = ""
        self.refresh()

    def showPopup(self):
        self.refresh()  # layers may have been added/saved since last open
        super().showPopup()

    def selected_path(self):
        return self.currentData(_PATH_ROLE) or ""

    def selected_layer(self):
        layer_id = self.currentData(_LAYER_ROLE)
        return QgsProject.instance().mapLayer(layer_id) if layer_id else None

    def set_path(self, path):
        """Show `path` (a layer's file if one matches, else a plain file entry)."""
        self._disk_path = path or ""
        self.refresh(select=self._disk_path)

    def refresh(self, select=None):
        target = _norm(self.selected_path() if select is None else select)
        self.blockSignals(True)
        self.clear()
        self.addItem(self.PLACEHOLDER, "")
        seen = set()
        for layer in QgsProject.instance().mapLayers().values():
            path = layer_disk_path(layer)
            if not path or not _accepts(self._kind, layer, path):
                continue
            self.addItem(layer.name(), path)
            idx = self.count() - 1
            self.setItemData(idx, layer.id(), _LAYER_ROLE)
            self.setItemData(idx, path, QtCore.Qt.ItemDataRole.ToolTipRole)
            seen.add(_norm(path))
        if self._disk_path and _norm(self._disk_path) not in seen:
            self.addItem("File: " + os.path.basename(self._disk_path), self._disk_path)
            self.setItemData(
                self.count() - 1, self._disk_path, QtCore.Qt.ItemDataRole.ToolTipRole
            )
        index = 0
        for i in range(1, self.count()):
            if _norm(self.itemData(i, _PATH_ROLE)) == target:
                index = i
                break
        self.setCurrentIndex(index)
        self.setToolTip(self.selected_path())
        self.blockSignals(False)


class FollowEnabled(QtCore.QObject):
    """Event filter: keeps `followers` enabled/disabled in step with `leader`."""

    def __init__(self, leader, followers):
        super().__init__(leader)
        self._followers = followers
        leader.installEventFilter(self)
        self._sync(leader)

    def _sync(self, leader):
        for w in self._followers:
            w.setEnabled(leader.isEnabled())

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.EnabledChange:
            self._sync(obj)
        return False
