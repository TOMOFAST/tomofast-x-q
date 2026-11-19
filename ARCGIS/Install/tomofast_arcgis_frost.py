# -*- coding: utf-8 -*-
"""Frost (fast FFT inversion) for the ArcGIS Pro panel.

Same behaviour as the QGIS plugin: with Frost ticked in the Experiment Type
section the mesh is the data grid (cell size = grid cell size, no padding),
the DTM is disabled, Save Files adds global.useFFT = 1 to the parameter file,
and Run Inversion runs frost_runner.py (in a background thread) instead of
Tomofast-x. Outputs go to OUTPUT/Paraview (Tomofast-x VTK files) and
OUTPUT/Frost.
"""
import os
import threading


class FrostMixin:

    # ------------------------------------------------------------------
    def _frost_on(self):
        """True when the Frost (FFT) inversion is selected."""
        return self.ui is not None and self.ui.checkBox_frost.isChecked()

    # ------------------------------------------------------------------
    def _on_frost_toggled(self):
        """Frost: one gridded data set, no DTM, no padding, mesh = data grid."""
        checked = self._frost_on()
        self.global_useFFT = 1 if checked else 0

        # Frost inverts one data set at a time
        if checked and self.ui.radioButton_joint_inv.isChecked():
            self.ui.radioButton_grav_inv.setChecked(True)
        self.ui.radioButton_joint_inv.setEnabled(not checked)

        if checked:
            # The FFT method assumes a level surface: drop any DTM
            if self.global_elevType == 2 or self.dtm_filename:
                self.global_elevType = 1
                self.global_elevFilename = ""
                self.dtm_filename = ""
                self.forward_depthWeighting_type = 1
                self.ui.lineEdit_dtm_path.setText("")
            self.ui.groupBox_dtm.setEnabled(False)
        else:
            # the DTM step is available again once data are loaded
            data_loaded = bool(
                self.ui.lineEdit_grav_data_path.text() or self.ui.lineEdit_magn_data_path.text()
            )
            self.ui.groupBox_dtm.setEnabled(data_loaded)

        self.ui.mQgsSpinBox_mesh_padding.setEnabled(not checked)
        if checked:
            self._apply_frost_mesh()
        else:
            self._sync_padding_to_depth()

    # ------------------------------------------------------------------
    def _apply_frost_mesh(self):
        """Frost: one model column per grid node, so the cell size is the grid
        cell size and there is no padding."""
        if not self._frost_on():
            return
        self.ui.mQgsSpinBox_mesh_padding.setValue(0)
        cell = getattr(self, "_frost_grid_cell", None)
        if not cell:
            return
        px, py = cell
        self.ui.mQgsSpinBox_mesh_size_x.setValue(px)
        self.ui.mQgsSpinBox_mesh_size_y.setValue(py)
        self.ui.mQgsSpinBox_mesh_size_z.setValue(px)

    # ------------------------------------------------------------------
    def _frost_check_setup(self):
        """Before saving the files: is this a problem Frost can solve?"""
        problems = []
        if self.global_experimentType == 3:
            problems.append("joint inversion (choose Gravity or Magnetic)")
        if self.is_2d:
            problems.append("2D profile data")
        if getattr(self, "global_dataType", "") != "raster":
            problems.append("point (csv) data: Frost needs a grid (GeoTIFF/ERS)")
        if self.global_experimentType == 1:
            if self.ui.comboBox_grav_type.currentData() == 2:
                problems.append("gravity gradiometry")
            if (self.ui.comboBox_grav_ncomp.currentData() or 1) != 1:
                problems.append("multi-component gravity data")
        if self.global_experimentType == 2:
            if (self.ui.comboBox_magn_ncomp.currentData() or 1) != 1:
                problems.append("multi-component magnetic data")
            if (self.ui.comboBox_magn_nmodel.currentData() or 1) != 1:
                problems.append("MVI (Frost inverts for susceptibility)")
        if problems:
            self.show_message(
                "Frost does not support: " + "; ".join(problems), "Frost", level="warning"
            )
            return False
        # no padding and a level surface
        self.ui.mQgsSpinBox_mesh_padding.setValue(0)
        self.global_elevType = 1
        return True

    # ------------------------------------------------------------------
    def _run_frost(self):
        """Run the FFT inversion of the active parameter file in a background thread."""
        import frost_runner

        param_path = os.path.abspath(self.paramfile_Path)
        _out_dir, _paraview_dir, frost_dir = frost_runner.output_dirs(param_path)
        try:
            os.makedirs(frost_dir, exist_ok=True)
        except OSError as e:
            self.show_message(f"Could not create the Frost output folder: {e}", level="warning")
            return
        log_path = os.path.join(frost_dir, "frost_log.txt")
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except OSError:
            pass

        self._process = None
        self._debug_polling_active = False
        self._debug_log_path = log_path
        self._debug_log_pos = 0
        self.ui.textEdit_inversion_log.clear()
        self._log_colored("Frost (FFT) inversion  [global.useFFT = 1]", "blue", bold=True)

        self._frost_cancel = threading.Event()
        self._frost_outcome = {}

        def work():
            try:
                self._frost_outcome["result"] = frost_runner.run_frost(
                    param_path, log_path=log_path, is_cancelled=self._frost_cancel.is_set
                )
            except Exception as e:  # reported in the GUI thread
                self._frost_outcome["error"] = e

        self._frost_thread = threading.Thread(target=work, name="Frost inversion", daemon=True)
        self._frost_thread.start()
        self.ui.pushButton_cancel_inversion.setEnabled(True)
        self.ui.root.after(500, self._poll_frost)

    # ------------------------------------------------------------------
    def _frost_running(self):
        thread = getattr(self, "_frost_thread", None)
        return thread is not None and thread.is_alive()

    # ------------------------------------------------------------------
    def _cancel_frost(self):
        self._frost_cancel.set()
        self.ui.textEdit_inversion_log.insertPlainText(
            "\n*** Cancelling: Frost stops at the end of its current step ***\n"
        )
        self.ui.textEdit_inversion_log.moveCursor(None)
        self.ui.pushButton_cancel_inversion.setEnabled(False)

    # ------------------------------------------------------------------
    def _tail_frost_log(self):
        if not (self._debug_log_path and os.path.exists(self._debug_log_path)):
            return
        try:
            with open(self._debug_log_path, "r", errors="replace") as fh:
                fh.seek(self._debug_log_pos)
                new_text = fh.read()
                if new_text:
                    self._debug_log_pos = fh.tell()
                    self.ui.textEdit_inversion_log.insertPlainText(new_text)
                    self.ui.textEdit_inversion_log.moveCursor(None)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def _poll_frost(self):
        self._tail_frost_log()
        if self._frost_running():
            self.ui.root.after(500, self._poll_frost)
            return

        # finished: report the outcome
        from frost_runner import FrostCancelled

        self._frost_thread = None
        self.ui.pushButton_cancel_inversion.setEnabled(False)
        result = self._frost_outcome.get("result")
        error = self._frost_outcome.get("error")
        if error is None and result:
            units = "mGal" if result["kind"] == "gravity" else "nT"
            self._log_colored("-" * 60, "gray")
            self._log_colored(
                f"PASS  Frost inversion finished in {result['total_time_s']:.1f} s "
                f"({result['nx']} x {result['ny']} x {result['nz']} cells)", "green", bold=True)
            self._log_colored(
                f"PASS  Data RMS residual {result['rms']:.4g} {units}; "
                f"model min/max {result['model_min']:.4g} / {result['model_max']:.4g}",
                "green", bold=True)
            self._log_colored(f"PASS  Paraview files: {result['paraview_dir']}", "green", bold=True)
            self._log_colored(f"PASS  Other outputs: {result['frost_dir']}", "green", bold=True)
        elif isinstance(error, FrostCancelled):
            self._log_colored("*** Frost inversion cancelled by user ***", "gray", bold=True)
        else:
            self._log_colored(f"ERROR  {error}", "red", bold=True)
            self.show_message(f"Frost inversion failed: {error}", "Frost", level="error")
