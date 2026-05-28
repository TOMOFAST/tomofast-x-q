# -*- coding: utf-8 -*-

import os

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal, Qt, QTimer

from .ui_dockwidget_generated import Ui_mQgsSpinBox_mesh_south_2


class Tomofast_xDockWidget(QtWidgets.QDockWidget, Ui_mQgsSpinBox_mesh_south_2):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(Tomofast_xDockWidget, self).__init__(parent)
        self.setupUi(self)
        # The generated UI uses absolute geometry on tabWidget inside dockWidgetContents
        # (no layout), so the tabWidget never resizes when the dock widget shrinks.
        # Installing a VBoxLayout makes it fill and track the dock widget's size.
        layout = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(self.tabWidget)
        self.tabWidget.setMinimumSize(0, 0)
        self._wrap_tabs_in_scroll_areas()
        self._layout_finalized = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._layout_finalized:
            self._layout_finalized = True
            # Defer one tick so Qt completes the first layout pass before we
            # read sizeHint() and pin the page size.
            QTimer.singleShot(0, self._pin_layout_tab_sizes)

    def _pin_layout_tab_sizes(self):
        """Pin layout-managed tabs to their natural size so scroll bars work.

        groupBox_14 has setMinimumSize(600, 730), which propagates through
        gridLayout_2 so that page.sizeHint() returns a valid content size.
        """
        for i in range(self.tabWidget.count()):
            scroll = self.tabWidget.widget(i)
            if not isinstance(scroll, QtWidgets.QScrollArea) or not scroll.widgetResizable():
                continue
            page = scroll.widget()
            if page is None:
                continue
            hint = page.sizeHint()
            w = max(hint.width() if hint.width() > 0 else 0, 500)
            h = max(hint.height() if hint.height() > 0 else 0, 400)
            scroll.takeWidget()
            page.setFixedSize(w, h)
            scroll.setWidgetResizable(False)
            scroll.setWidget(page)

    def _wrap_tabs_in_scroll_areas(self):
        """Wrap each tab page in a QScrollArea so small screens can scroll the content."""
        pages_and_texts = [
            (self.tabWidget.widget(i), self.tabWidget.tabText(i))
            for i in range(self.tabWidget.count())
        ]
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(0)

        for page, tab_text in pages_and_texts:
            scroll = QtWidgets.QScrollArea()
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setMinimumSize(200, 200)

            if page.layout() is not None:
                # Layout-managed tab (Run Inversion): gridLayout_2 positions
                # groupBox_14 only after the first show, so defer size-pinning
                # to _pin_layout_tab_sizes() via showEvent.
                scroll.setWidgetResizable(True)
            else:
                # Absolute-positioned tab: direct children have valid geometries
                # from setupUi, so we can fix the size immediately.
                max_right = 0
                max_bottom = 0
                for child in page.children():
                    if isinstance(child, QtWidgets.QWidget):
                        geom = child.geometry()
                        max_right = max(max_right, geom.right())
                        max_bottom = max(max_bottom, geom.bottom())
                page.setFixedSize(max(max_right + 10, 500), max(max_bottom + 10, 400))
                scroll.setWidgetResizable(False)

            scroll.setWidget(page)
            self.tabWidget.addTab(scroll, tab_text)

        self.tabWidget.setCurrentIndex(0)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
