# -*- coding: utf-8 -*-
import os
import sys
import json
import tempfile
import platform
import subprocess
import shutil
import re
import time
import webbrowser
import numpy as np
import pandas as pd
from osgeo import gdal, osr
from Data2Tomofast import Data2Tomofast
from ppigrf import igrf, get_inclination_declination
from datetime import datetime


class TomofastArcGISBase:

    def __init__(self):
        # ARCGIS/ directory (parent of Install/)
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ui = None
        self.tomo_Path = ""
        self.data2tomofast = None
        self.dtm_raster_path = ""
        self.data_df = None
        self.nData = 0
        self.global_dataNameGrav = ""
        self.global_dataNameMagn = ""
        self.xcol_grav = ""
        self.ycol_grav = ""
        self.datacol_grav = ""
        self.xcol_magn = ""
        self.ycol_magn = ""
        self.datacol_magn = ""
        self.input_data_grav = ""
        self.input_data_magn = ""
        self.parfilename = ""
        self.kernelfiledirectory = ""
        self._debug_polling_active = False
        self._debug_log_path = ""
        self._debug_log_pos = 0
        self.initialise_variables()

    # ------------------------------------------------------------------
    def run(self):
        import tkinter as tk
        from tomofast_ui import TomofastUI

        root = tk.Tk()
        self.ui = TomofastUI(root)

        # ---- Button commands ----------------------------------------
        self.ui.pushButton_calc_IGRF.configure(command=self.update_mag_field)
        self.ui.pushButton_load_grav_data.configure(
            command=lambda: self.confirm_data_file("grav")
        )
        self.ui.pushButton_load_magn_data.configure(
            command=lambda: self.confirm_data_file("magn")
        )
        self.ui.pushButton_grav_data_path.configure(
            command=lambda: self.select_data_file("grav")
        )
        self.ui.pushButton_magn_data_path.configure(
            command=lambda: self.select_data_file("magn")
        )
        self.ui.pushButton_assign_grav_fields.configure(
            command=self.process_data_fields_grav
        )
        self.ui.pushButton_assign_magn_fields.configure(
            command=self.process_data_fields_magn
        )
        self.ui.lineEdit_output_directory_path_select.configure(
            command=self.select_ouput_directory
        )
        self.ui.pushButton_select_dtm_path.configure(command=self.select_dtm)
        self.ui.pushButton_param_load_path.configure(command=self.process_parameter_file)
        self.ui.lineEdit_ROI_path_select.configure(command=self.load_ROI)
        self.ui.pushButton_reset.configure(command=self.reset_params)
        self.ui.pushButton_select_tomoPath.configure(command=self.select_tomo_Path)
        self.ui.pushButton_2_select_parfilePath.configure(
            command=self.select_paramfile_path
        )
        self.ui.pushButton_select_mpirun_mipexec.configure(
            command=self.select_mpirunexec_path
        )
        self.ui.pushButton_select_setvars.configure(command=self.select_setvars_path)
        self.ui.pushButton_3_visualise.configure(command=self.visualise_output)
        self.ui.pushButton_kernel_path_select.configure(command=self.select_kernel_path)
        self.ui.pushButton_3_runInversion.configure(command=self.run_inversion)
        self.ui.pushButton_3_Export.configure(command=self.export_model)
        self.ui.pushButton_plugin_manual.configure(
            command=lambda: webbrowser.open(
                "https://tectonique.net/tomofast-x-q/Tomofast-x-q%20User%20Manual.pdf"
            )
        )
        self.ui.pushButton_plugin_cheat_sheat.configure(
            command=lambda: webbrowser.open(
                "https://tectonique.net/tomofast-x-q/Tomofast-x-q%20cheat%20sheet.pdf"
            )
        )
        self.ui.pushButton_tomofast_manual.configure(
            command=lambda: webbrowser.open(
                "https://github.com/TOMOFAST/Tomofast-x/raw/refs/heads/master/docs/Tomofast-x%20User%20Manual.docx"
            )
        )

        # ---- IntVar traces (radio-button toggled / OS mode) ----------
        self.ui._inv_type_var.trace_add(
            "write", lambda *_: self.inversion_type_reset_gui()
        )
        self.ui._os_var.trace_add(
            "write", lambda *_: self._update_run_controls()
        )

        # ---- Spinbox var traces (valueChanged equivalent) ------------
        for _attr in (
            "mQgsSpinBox_mesh_south",
            "mQgsSpinBox_mesh_north",
            "mQgsSpinBox_mesh_east",
            "mQgsSpinBox_mesh_west",
            "mQgsSpinBox_mesh_size_x",
            "mQgsSpinBox_mesh_size_y",
            "mQgsSpinBox_mesh_size_z",
            "mQgsSpinBox_mesh_padding",
        ):
            getattr(self.ui, _attr)._var.trace_add(
                "write", lambda *_: self.update_model_grid_size()
            )

        def _on_depth_change(*_):
            self.mesh_layers()
            self.update_model_grid_size()

        self.ui.doubleSpinBox_coreDepth._var.trace_add("write", _on_depth_change)
        self.ui.doubleSpinBox_fullDepth._var.trace_add("write", _on_depth_change)

        self.ui.mQgsDoubleSpinBox_compression_ratio._var.trace_add(
            "write", lambda *_: self.update_memory_size()
        )
        self.ui.checkBox_use_compression._var.trace_add(
            "write", lambda *_: self.update_memory_size()
        )

        # ---- Text widget KeyRelease (textChanged equivalent) ---------
        self.ui.textEdit_z_cell_size_list._widget.bind(
            "<KeyRelease>", lambda e: self.update_model_grid_size()
        )
        self.ui.textEdit_z_layer_thickness_list._widget.bind(
            "<KeyRelease>", lambda e: self.update_model_grid_size()
        )

        # ---- Initial widget state ------------------------------------
        self.ui.doubleSpinBox_coreDepth.setEnabled(False)
        self.ui.doubleSpinBox_fullDepth.setEnabled(False)
        self.ui.radioButton_magn_inv.setChecked(False)
        self.ui.pushButton_reset.setEnabled(True)

        self.ui.mQgsProjectionSelectionWidget_grav_in.setCrs("EPSG:4326")
        self.ui.mQgsProjectionSelectionWidget_grav_out.setCrs("EPSG:4326")
        self.ui.mQgsProjectionSelectionWidget_magn_in.setCrs("EPSG:4326")
        self.ui.mQgsProjectionSelectionWidget_magn_out.setCrs("EPSG:4326")

        self._update_run_controls()
        self.define_parameters()
        self.reset_params()

        # ---- Load saved config --------------------------------------
        tomoconfig = os.path.join(self.plugin_dir, "tomoconfig.txt")
        if os.path.exists(tomoconfig):
            with open(tomoconfig, "r") as tpfile:
                line = tpfile.readline()
                self.tomo_Path = line.rstrip()
                self.ui.lineEdit_tomoPath.setText(self.tomo_Path)

                line = tpfile.readline()
                self.ui.lineEdit_pre_command_2_WSL_Distro.setText(line.rstrip())

                tpfile.readline()  # blank line

                line = tpfile.readline()
                self.ui.lineEdit_2_mpirunPath_2.setText(line.rstrip())

                line = tpfile.readline()
                self.ui.lineEdit_setvarsPath.setText(line.rstrip())
                self.setvars_Path = line.rstrip()

                line = tpfile.readline().rstrip()
                if line in ("0", "1"):
                    native = line == "1"
                    self.ui.radioButton_windowsNative.setChecked(native)
                    self.ui.radioButton_windowsWSL.setChecked(not native)

                line = tpfile.readline().rstrip()
                if line.isdigit():
                    self.ui.mQgsSpinBox_noProc.setValue(int(line))

        self.ui.version_label.setText("v " + self.show_version())
        self.define_tips()
        root.mainloop()

    # ------------------------------------------------------------------
    def initialise_variables(self):
        self.global_experimentType = 1
        self.global_description = ""
        self.modelGrid_grav_file = ""
        self.global_outputFolderPath = ""
        self.forward_data_grav_nData = 0
        self.forward_data_grav_dataGridFile = ""
        self.modelGrid_magn_file = ""
        self.forward_data_magn_nData = 0
        self.forward_data_magn_dataGridFile = ""
        self.forward_depthWeighting_type = 1
        self.forward_depthWeighting_grav_type = 1
        self.forward_depthWeighting_magn_type = 1
        self.forward_depthWeighting_grav_power = 2
        self.forward_depthWeighting_magn_power = 3
        self.sensit_readFromFiles = 0
        self.forward_matrixCompression_type = 1
        self.forward_matrixCompression_rate = 0.1
        self.inversion_priorModel_type = 0
        self.inversion_priorModel_grav_value = 0
        self.inversion_startingModel_type = 0
        self.inversion_startingModel_grav_value = 0
        self.inversion_nMajorIterations = 3
        self.inversion_nMinorIterations = 100
        self.inversion_writeModelEveryNiter = 0
        self.inversion_minResidual = 1e-13
        self.inversion_targetMisfit = 1e-7
        self.inversion_modelDamping_grav_weight = 0
        self.inversion_modelDamping_grav_normPower = 2
        self.inversion_modelDamping_magn_weight = 0
        self.inversion_modelDamping_magn_normPower = 2
        self.inversion_joint_grav_problemWeight = 1
        self.inversion_joint_magn_problemWeight = 2.5e-6
        self.inversion_admm_grav_enableADMM = 0
        self.inversion_admm_grav_nLithologies = 0
        self.inversion_admm_grav_bounds = ""
        self.inversion_admm_grav_weight = 0
        self.inversion_admm_magn_enableADMM = 0
        self.inversion_admm_magn_nLithologies = 0
        self.inversion_admm_magn_bounds = ""
        self.inversion_admm_magn_weight = 0
        self.cell_x = 2000
        self.cell_y = 2000
        self.dz = 100
        self.padding = 10000
        self.z_coreDepth = 10000
        self.z_fullDepth = 20000
        self.filename_grav = ""
        self.filename_magn = ""
        self.grav_proj_in = "EPSG:4326"
        self.grav_proj_out = "EPSG:4326"
        self.magn_proj_in = "EPSG:4326"
        self.magn_proj_out = "EPSG:4326"
        self.global_elevType = 1
        self.global_elevFilename = ""
        self.ROIFileName = ""
        self.is_2d = False
        self.profile_line_pts = None
        self.modelGrid_size = [0, 0, 0]
        self.global_grav_dataUnitsMultiplier = 0.00001
        self.global_magn_dataUnitsMultiplier = 1
        self.global_grav_modelUnitsMultiplier = 1
        self.global_magn_modelUnitsMultiplier = 1
        self.meshBox = {
            "south": 6730000,
            "west": 430000,
            "north": 6790000,
            "east": 482000,
        }
        self.magn_SurveyDay = 1
        self.magn_SurveyMonth = 1
        self.magn_SurveyYear = 2000
        self.forward_magneticField_declination = 0
        self.forward_magneticField_inclination = -45
        self.forward_magneticField_intensity = 65000
        self.dataType = "points"
        self.global_grav_sensor_height = 0
        self.global_magn_sensor_height = 0
        self.paramfile_Path = ""
        self.suffix_known = False
        self.setvars_Path = ""
        self.z_by_list = ""
        self.depth_layers = []
        self.nData = 0
        self.kernelfiledirectory = ""

    # ------------------------------------------------------------------
    def define_parameters(self):
        self.d_params = {
            "global.outputFolderPath": [
                self.global_outputFolderPath,
                self.ui.lineEdit_output_directory_path,
                str, "text",
            ],
            "global.description": [
                self.global_description,
                self.ui.textEdit_experiment_description,
                str, "plainText",
            ],
            "global.experimentType": [
                self.global_experimentType,
                self.ui.radioButton_grav_inv,
                self.ui.radioButton_magn_inv,
                self.ui.radioButton_joint_inv,
                int, "radio",
            ],
            "global.elevFilename": [
                self.global_elevFilename,
                self.ui.lineEdit_dtm_path,
                str, "text",
            ],
            "roi.filename": [
                self.ROIFileName,
                self.ui.lineEdit_ROI_path,
                str, "text",
            ],
            "anomalies.grav.data.file": [
                self.filename_grav,
                self.ui.lineEdit_grav_data_path,
                str, "text",
            ],
            "anomalies.magn.data.file": [
                self.filename_magn,
                self.ui.lineEdit_magn_data_path,
                str, "text",
            ],
            "anomalies.grav.proj.in": [
                self.grav_proj_in,
                self.ui.mQgsProjectionSelectionWidget_grav_in,
                str, "epsg",
            ],
            "anomalies.grav.proj.out": [
                self.grav_proj_out,
                self.ui.mQgsProjectionSelectionWidget_grav_out,
                str, "epsg",
            ],
            "anomalies.magn.proj.in": [
                self.magn_proj_in,
                self.ui.mQgsProjectionSelectionWidget_magn_in,
                str, "epsg",
            ],
            "anomalies.magn.proj.out": [
                self.magn_proj_out,
                self.ui.mQgsProjectionSelectionWidget_magn_out,
                str, "epsg",
            ],
            "forward.data.grav.dataGridFile": [
                self.forward_data_grav_dataGridFile, "", str, "path",
            ],
            "forward.data.magn.dataGridFile": [
                self.forward_data_magn_dataGridFile, "", str, "path",
            ],
            "modelGrid.size": [
                self.modelGrid_size,
                self.ui.nx_label,
                self.ui.ny_label,
                self.ui.nz_label,
                str, "size",
            ],
            "forward.data.grav.nData": [
                self.forward_data_grav_nData, "", int, "ndata",
            ],
            "forward.data.magn.nData": [
                self.forward_data_magn_nData, "", int, "ndata",
            ],
            "anomalies.grav.data_file": [
                self.modelGrid_grav_file,
                self.ui.lineEdit_grav_data_path,
                str, "text",
            ],
            "anomalies.magn.data_file": [
                self.modelGrid_magn_file,
                self.ui.lineEdit_magn_data_path,
                str, "text",
            ],
            "sensit.readFromFiles": [
                self.sensit_readFromFiles,
                self.ui.checkBox_read_sens_matrix,
                int, "check",
            ],
            "forward.matrixCompression.type": [
                self.forward_matrixCompression_type,
                self.ui.checkBox_use_compression,
                int, "check",
            ],
            "forward.matrixCompression.rate": [
                self.forward_matrixCompression_rate,
                self.ui.mQgsDoubleSpinBox_compression_ratio,
                float, "value",
            ],
            "inversion.nMajorIterations": [
                self.inversion_nMajorIterations,
                self.ui.mQgsSpinBox_major_iters,
                int, "value",
            ],
            "inversion.nMinorIterations": [
                self.inversion_nMinorIterations,
                self.ui.mQgsSpinBox_minor_iters,
                int, "value",
            ],
            "inversion.writeModelEveryNiter": [
                self.inversion_writeModelEveryNiter,
                self.ui.mQgsSpinBox_model_save_iters,
                int, "value",
            ],
            "inversion.minResidual": [
                self.inversion_minResidual,
                self.ui.textEdit_min_residual,
                str, "plainText",
            ],
            "inversion.targetMisfit": [
                self.inversion_targetMisfit,
                self.ui.lineEdit_targetMisfit,
                str, "text",
            ],
            "inversion.modelDamping.grav.weight": [
                self.inversion_modelDamping_grav_weight,
                self.ui.mQgsDoubleSpinBox_grav_mmodel_damping_weight,
                float, "value",
            ],
            "inversion.modelDamping.grav.normPower": [
                self.inversion_modelDamping_grav_normPower,
                self.ui.mQgsDoubleSpinBox_grav_mmodel_norm_power,
                float, "value",
            ],
            "inversion.modelDamping.magn.weight": [
                self.inversion_modelDamping_magn_weight,
                self.ui.mQgsDoubleSpinBox_grav_mmodel_damping_weight,
                float, "value",
            ],
            "inversion.modelDamping.magn.normPower": [
                self.inversion_modelDamping_magn_normPower,
                self.ui.mQgsDoubleSpinBox_grav_mmodel_norm_power,
                float, "value",
            ],
            "inversion.joint.grav.problemWeight": [
                self.inversion_joint_grav_problemWeight,
                self.ui.mQgsDoubleSpinBox_grav_weight,
                float, "value",
            ],
            "inversion.joint.magn.problemWeight": [
                self.inversion_joint_magn_problemWeight,
                self.ui.mQgsDoubleSpinBox_magn_weight,
                float, "value",
            ],
            "inversion.admm.grav.nLithologies": [
                self.inversion_admm_grav_nLithologies,
                self.ui.spinBox_grav_number_ADMM_litho,
                int, "value",
            ],
            "inversion.admm.grav.bounds": [
                self.inversion_admm_grav_bounds,
                self.ui.textEdit_grav_ADMM_bounds,
                str, "plainText",
            ],
            "inversion.admm.grav.weight": [
                self.inversion_admm_grav_weight,
                self.ui.lineEdit_grav_ADMM_weight,
                str, "text",
            ],
            "inversion.admm.magn.nLithologies": [
                self.inversion_admm_magn_nLithologies,
                self.ui.spinBox_magn_ADMM_number_litho,
                int, "value",
            ],
            "inversion.admm.magn.bounds": [
                self.inversion_admm_magn_bounds,
                self.ui.textEdit_5_magn_ADMM_bounds,
                str, "plainText",
            ],
            "inversion.admm.magn.weight": [
                self.inversion_admm_magn_weight,
                self.ui.lineEdit_magn_ADMM_weight,
                str, "text",
            ],
            "global.grav.dataUnitsMultiplier": [
                self.global_grav_dataUnitsMultiplier,
                self.ui.lineEdit_grav_data_multiplier,
                str, "text",
            ],
            "global.grav.modelUnitsMultiplier": [
                self.global_grav_modelUnitsMultiplier,
                self.ui.mQgsDoubleSpinBox_grav_model_multiplier,
                float, "value",
            ],
            "global.magn.dataUnitsMultiplier": [
                self.global_magn_dataUnitsMultiplier,
                self.ui.lineEdit_magn_data_multiplier,
                str, "text",
            ],
            "global.magn.modelUnitsMultiplier": [
                self.global_magn_modelUnitsMultiplier,
                self.ui.mQgsDoubleSpinBox_magn_model_multiplier,
                float, "value",
            ],
            "global.grav.sensor_height": [
                self.global_grav_sensor_height,
                self.ui.doubleSpinBox_grav_sensor_height,
                float, "value",
            ],
            "global.magn.sensor_height": [
                self.global_magn_sensor_height,
                self.ui.doubleSpinBox_magn_sensor_height,
                float, "value",
            ],
            "mesh.cellx": [self.cell_x, self.ui.mQgsSpinBox_mesh_size_x, int, "value"],
            "mesh.celly": [self.cell_y, self.ui.mQgsSpinBox_mesh_size_y, int, "value"],
            "mesh.cellz": [self.dz, self.ui.mQgsSpinBox_mesh_size_z, float, "value"],
            "mesh.z.coreDepth": [
                self.z_coreDepth, self.ui.doubleSpinBox_coreDepth, float, "value",
            ],
            "mesh.z.fullDepth": [
                self.z_fullDepth, self.ui.doubleSpinBox_fullDepth, float, "value",
            ],
            "mesh.padding": [self.padding, self.ui.mQgsSpinBox_mesh_padding, int, "value"],
            "mesh.south": [self.meshBox["south"], self.ui.mQgsSpinBox_mesh_south, int, "value"],
            "mesh.west":  [self.meshBox["west"],  self.ui.mQgsSpinBox_mesh_west,  int, "value"],
            "mesh.north": [self.meshBox["north"], self.ui.mQgsSpinBox_mesh_north, int, "value"],
            "mesh.east":  [self.meshBox["east"],  self.ui.mQgsSpinBox_mesh_east,  int, "value"],
            "forward.magneticField.declination": [
                self.forward_magneticField_declination,
                self.ui.doubleSpinBox_mag_dec,
                float, "value",
            ],
            "forward.magneticField.inclination": [
                self.forward_magneticField_inclination,
                self.ui.doubleSpinBox_mag_inc,
                float, "value",
            ],
            "forward.magneticField.intensity": [
                self.forward_magneticField_intensity,
                self.ui.doubleSpinBox_mag_int,
                float, "value",
            ],
            "forward.magneticField.intensity_nT": [
                self.forward_magneticField_intensity,
                self.ui.doubleSpinBox_mag_int,
                float, "value",
            ],
            "inversion.modelDamping.normPower": [
                self.inversion_modelDamping_grav_normPower,
                self.ui.mQgsDoubleSpinBox_grav_mmodel_norm_power,
                self.ui.mQgsDoubleSpinBox_magn_model_norm_power,
                float, "value_both",
            ],
            "inversion.admm.nLithologies": [
                self.inversion_admm_grav_nLithologies,
                self.ui.spinBox_grav_number_ADMM_litho,
                self.ui.spinBox_magn_ADMM_number_litho,
                int, "value_both",
            ],
        }

    # ------------------------------------------------------------------
    def show_message(self, msg, title="Info", level="info"):
        from tkinter import messagebox
        if level == "warning":
            messagebox.showwarning(title, msg)
        elif level == "error":
            messagebox.showerror(title, msg)
        else:
            messagebox.showinfo(title, msg)

    def _record_pending(self, path):
        """Append *path* to the pending-layers flat list read by Tomofast_X.pyt."""
        pending_file = os.path.join(tempfile.gettempdir(), "tomofast_pending.json")
        try:
            if os.path.exists(pending_file):
                with open(pending_file, "r") as f:
                    paths = json.load(f)
                if not isinstance(paths, list):
                    paths = []
            else:
                paths = []
            if path not in paths:
                paths.append(path)
            with open(pending_file, "w") as f:
                json.dump(paths, f)
        except Exception:
            pass

    def _sample_raster_at_points(self, raster_path, xs, ys):
        ds = gdal.Open(raster_path)
        if ds is None:
            return [0.0] * len(xs)
        gt = ds.GetGeoTransform()
        band = ds.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        data = band.ReadAsArray()
        values = []
        for x, y in zip(xs, ys):
            col = int((x - gt[0]) / gt[1])
            row = int((y - gt[3]) / gt[5])
            if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                val = float(data[row, col])
                if nodata is not None and val == nodata:
                    values.append(0.0)
                else:
                    values.append(val)
            else:
                values.append(0.0)
        ds = None
        return values

    def show_version(self):
        metadata_path = os.path.join(os.path.dirname(self.plugin_dir), "metadata.txt")
        with open(metadata_path) as plugin_version_file:
            metadata = plugin_version_file.readlines()
            for line in metadata:
                parts = line.split("=")
                if len(parts) == 2 and parts[0] == "version":
                    plugin_version = parts[1]
        return plugin_version

    # ---- No-op stubs (QGIS layer operations not applicable) ----------
    def colour_points(self, layer, value_field, ramp_name, invert):
        pass

    def _move_layer_to_top(self, layer):
        pass

    def rearrange(self):
        pass

    def rename_dp_field(self, rlayer, oldname, newname):
        pass

    def define_tips(self):
        pass

    def visualise_output(self):
        pass