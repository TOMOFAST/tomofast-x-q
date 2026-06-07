# -*- coding: utf-8 -*-
import os
import math
import re
import string as _string
import numpy as np


class ParamsMixin:

    # ------------------------------------------------------------------
    def spacer(self, title):
        self.f_params.write("\n")
        self.f_params.write(
            "===================================================================================\n"
        )
        self.f_params.write(title + "\n")
        self.f_params.write(
            "===================================================================================\n"
        )

    # ------------------------------------------------------------------
    def save_parameter_file(self):
        self.parse_parameters()

        self.ui.lineEdit_2_parfilePath.setText(
            self.global_outputFolderPath + "/paramfile.txt"
        )
        self.paramfile_Path = self.global_outputFolderPath + "/paramfile.txt"
        self.f_params = open(self.global_outputFolderPath + "/paramfile.txt", "w")

        self.spacer("GLOBAL")
        self.f_params.write(
            "global.outputFolderPath             = {}\n".format(
                self.global_outputFolderPath + "/OUTPUT"
            )
        )
        if not self.global_description:
            self.global_description = "Inversion Experiment"
        self.f_params.write(
            "global.description                  = {}\n".format(self.global_description)
        )
        self.f_params.write(
            "#global.experimentType               = {}\n".format(self.global_experimentType)
        )
        self.f_params.write(
            "#global.is_2d                        = {}\n".format(1 if self.is_2d else 0)
        )

        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "global.grav.dataUnitsMultiplier     = {}\n".format(
                    str(self.global_grav_dataUnitsMultiplier)
                )
            )
            self.f_params.write(
                "global.grav.modelUnitsMultiplier    = {}\n".format(
                    self.global_grav_modelUnitsMultiplier
                )
            )

        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "global.magn.dataUnitsMultiplier     = {}\n".format(
                    str(self.global_magn_dataUnitsMultiplier)
                )
            )
            self.f_params.write(
                "global.magn.modelUnitsMultiplier    = {}\n".format(
                    self.global_magn_modelUnitsMultiplier
                )
            )

        self.spacer("ELEVATION parameters")
        self.f_params.write(
            "#global.elevType                     = {}\n".format(self.global_elevType)
        )

        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "#global.grav.sensor_height                 = {}\n".format(
                    self.global_grav_sensor_height
                )
            )
        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "#global.magn.sensor_height                 = {}\n".format(
                    self.global_magn_sensor_height
                )
            )

        self.spacer("MODEL GRID parameters")
        self.f_params.write(
            "modelGrid.size                      = {} {} {}\n".format(
                self.modelGrid_size[0], self.modelGrid_size[1], self.modelGrid_size[2]
            )
        )
        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "modelGrid.grav.file                 = {}\n".format(
                    self.global_outputFolderPath + "/model_grid.txt"
                )
            )
        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "modelGrid.magn.file                 = {}\n".format(
                    self.global_outputFolderPath + "/model_grid.txt"
                )
            )

        if self.global_experimentType in (2, 3):
            self.spacer("MAGNETIC FIELD constants")
            self.f_params.write(
                "forward.magneticField.inclination                 = {}\n".format(
                    self.forward_magneticField_inclination
                )
            )
            self.f_params.write(
                "forward.magneticField.declination                 = {}\n".format(
                    self.forward_magneticField_declination
                )
            )
            self.f_params.write(
                "forward.magneticField.intensity_nT                = {}\n".format(
                    self.forward_magneticField_intensity
                )
            )
            if self.is_2d and self.profile_line_pts:
                profile_declination = (
                    np.arctan2(
                        self.profile_line_pts[1][0] - self.profile_line_pts[0][0],
                        self.profile_line_pts[1][1] - self.profile_line_pts[0][1],
                    )
                    * 180
                    / np.pi
                )
                self.f_params.write(
                    "forward.magneticField.XaxisDeclination                 = {}\n".format(
                        -(90 - profile_declination)
                    )
                )

        self.spacer("DATA parameters")

        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "forward.data.grav.nData             = {}\n".format(
                    self.forward_data_grav_nData
                )
            )
            self.f_params.write(
                "forward.data.grav.dataGridFile      = {}\n".format(
                    self.global_outputFolderPath + "/data_grav.csv"
                )
            )

        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "forward.data.magn.nData             = {}\n".format(
                    self.forward_data_magn_nData
                )
            )
            self.f_params.write(
                "forward.data.magn.dataGridFile      = {}\n".format(
                    self.global_outputFolderPath + "/data_magn.csv"
                )
            )
        else:
            self.f_params.write(
                "forward.data.magn.dataGridFile      = {}\n".format(
                    self.global_outputFolderPath + "/data_magn_topo.csv"
                )
            )

        self.spacer("DEPTH WEIGHTING")
        self.f_params.write(
            "forward.depthWeighting.type         = {}\n".format(
                self.forward_depthWeighting_type
            )
        )
        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "forward.depthWeighting.grav.power   = {}\n".format(
                    self.forward_depthWeighting_grav_power
                )
            )
        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "forward.depthWeighting.magn.power   = {}\n".format(
                    self.forward_depthWeighting_magn_power
                )
            )

        self.spacer("SENSITIVITY KERNEL")
        self.f_params.write(
            "sensit.readFromFiles                = {}\n".format(self.sensit_readFromFiles)
        )
        if self.sensit_readFromFiles == 0:
            self.f_params.write(
                "sensit.folderPath                   = {}\n".format(
                    self.global_outputFolderPath + "/OUTPUT/SENSIT/"
                )
            )
        else:
            self.f_params.write(
                "sensit.folderPath                   = {}\n".format(
                    self.kernelfiledirectory + "/"
                )
            )

        self.spacer("MATRIX COMPRESSION")
        self.f_params.write(
            "forward.matrixCompression.type      = {}\n".format(
                self.forward_matrixCompression_type
            )
        )
        self.f_params.write(
            "forward.matrixCompression.rate      = {}\n".format(
                self.forward_matrixCompression_rate
            )
        )

        self.spacer("INVERSION parameters")
        if (
            self.inversion_admm_grav_nLithologies > 0
            or self.inversion_admm_magn_nLithologies > 0
        ):
            self.f_params.write("inversion.nMajorIterations          = {}\n".format("50"))
        elif self.global_experimentType == 3:
            self.f_params.write("inversion.nMajorIterations          = {}\n".format("15"))
        else:
            self.f_params.write(
                "inversion.nMajorIterations          = {}\n".format(
                    self.inversion_nMajorIterations
                )
            )
        self.f_params.write(
            "inversion.nMinorIterations          = {}\n".format(
                self.inversion_nMinorIterations
            )
        )
        self.f_params.write(
            "inversion.writeModelEveryNiter      = {}\n".format(
                self.inversion_writeModelEveryNiter
            )
        )
        self.f_params.write(
            "#inversion.minResidual               = {}\n".format(self.inversion_minResidual)
        )
        if self.inversion_targetMisfit:
            self.f_params.write(
                "inversion.targetMisfit               = {}\n".format(
                    self.inversion_targetMisfit
                )
            )

        self.spacer("MODEL DAMPING (m - m_prior)")
        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "inversion.modelDamping.grav.weight  = {}\n".format(
                    self.inversion_modelDamping_grav_weight
                )
            )
        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "inversion.modelDamping.magn.weight  = {}\n".format(
                    self.inversion_modelDamping_magn_weight
                )
            )
        _norm_power = (
            self.inversion_modelDamping_magn_normPower
            if self.global_experimentType == 2
            else self.inversion_modelDamping_grav_normPower
        )
        self.f_params.write(
            "inversion.modelDamping.normPower    = {}\n".format(_norm_power)
        )

        self.spacer("JOINT INVERSION parameters")
        self.f_params.write(
            "inversion.joint.grav.problemWeight  = {}\n".format(
                self.inversion_joint_grav_problemWeight
            )
        )
        self.f_params.write(
            "inversion.joint.magn.problemWeight  = {}\n".format(
                self.inversion_joint_magn_problemWeight
            )
        )

        if self.global_experimentType == 3:
            self.spacer("CROSS-GRADIENT constraints")
            self.f_params.write("inversion.crossGradient.weight  = {}\n".format(0.8e2))
            self.f_params.write(
                "inversion.crossGradient.derivativeType  = {}\n".format(1)
            )

        self.spacer("ADMM constraints")
        if self.global_experimentType == 1:
            _admm_enable = self.inversion_admm_grav_enableADMM
            _admm_n_litho = self.inversion_admm_grav_nLithologies
        elif self.global_experimentType == 2:
            _admm_enable = self.inversion_admm_magn_enableADMM
            _admm_n_litho = self.inversion_admm_magn_nLithologies
        else:
            _admm_enable = max(
                self.inversion_admm_grav_enableADMM,
                self.inversion_admm_magn_enableADMM,
            )
            _admm_n_litho = max(
                self.inversion_admm_grav_nLithologies,
                self.inversion_admm_magn_nLithologies,
            )
        self.f_params.write(
            "inversion.admm.enableADMM           = {}\n".format(_admm_enable)
        )
        self.f_params.write(
            "inversion.admm.nLithologies         = {}\n".format(_admm_n_litho)
        )

        if self.global_experimentType in (1, 3):
            if self.inversion_admm_grav_nLithologies > 0:
                self.f_params.write(
                    "inversion.admm.dataCostThreshold      = {}\n".format("0.1e-3")
                )
                self.f_params.write(
                    "inversion.admm.weightMultiplier      = {}\n".format("2.0")
                )
            if self.inversion_admm_grav_bounds == "":
                self.f_params.write(
                    "inversion.admm.grav.bounds          = {}\n".format("-1d-10 1d10")
                )
            else:
                self.f_params.write(
                    "inversion.admm.grav.bounds          = {}\n".format(
                        self.inversion_admm_grav_bounds
                    )
                )
        if self.inversion_admm_grav_nLithologies > 0:
            self.f_params.write(
                "inversion.admm.grav.weight      = {}\n".format("1000.0")
            )
            self.f_params.write("inversion.admm.maxWeight      =   0.1000000E+11\n")
        else:
            self.f_params.write(
                "inversion.admm.grav.weight          = {}\n".format(
                    self.inversion_admm_grav_weight
                )
            )

        if self.global_experimentType in (2, 3):
            if self.inversion_admm_magn_nLithologies > 0:
                self.f_params.write(
                    "inversion.admm.dataCostThreshold      = {}\n".format("0.1e-3")
                )
                self.f_params.write(
                    "inversion.admm.weightMultiplier      = {}\n".format("2.0")
                )
            if self.inversion_admm_magn_bounds == "":
                self.f_params.write(
                    "inversion.admm.magn.bounds          = {}\n".format("-1d-10 1d10")
                )
            else:
                self.f_params.write(
                    "inversion.admm.magn.bounds          = {}\n".format(
                        self.inversion_admm_magn_bounds
                    )
                )
            if self.inversion_admm_magn_nLithologies > 0:
                self.f_params.write(
                    "inversion.admm.magn.weight      = {}\n".format("1000.0")
                )
                self.f_params.write("inversion.admm.maxWeight      =   0.1000000E+11\n")
            else:
                self.f_params.write(
                    "inversion.admm.magn.weight          = {}\n".format(
                        self.inversion_admm_magn_weight
                    )
                )

        self.spacer("MESH")
        self.f_params.write(
            "#mesh.cellx                          = {}\n".format(self.cell_x)
        )
        self.f_params.write(
            "#mesh.celly                          = {}\n".format(self.cell_y)
        )
        self.f_params.write(
            "#mesh.cellz                          = {}\n".format(self.dz)
        )
        self.f_params.write(
            "#mesh.padding                        = {}\n".format(self.padding)
        )
        self.f_params.write(
            "#mesh.z.coreDepth                       = {}\n".format(self.z_coreDepth)
        )
        self.f_params.write(
            "#mesh.z.fullDepth                  = {}\n".format(self.z_fullDepth)
        )
        self.f_params.write(
            "#mesh.south                          = {}\n".format(self.meshBox["south"])
        )
        self.f_params.write(
            "#mesh.west                           = {}\n".format(self.meshBox["west"])
        )
        self.f_params.write(
            "#mesh.north                          = {}\n".format(self.meshBox["north"])
        )
        self.f_params.write(
            "#mesh.east                           = {}\n".format(self.meshBox["east"])
        )

        self.spacer("ANOMALIES")
        self.f_params.write(
            "#global.elevFilename                 = {}\n".format(self.global_elevFilename)
        )
        self.f_params.write(
            "#roi.filename                        = {}\n".format(self.ROIFileName)
        )

        if self.global_experimentType in (1, 3):
            self.f_params.write(
                "#anomalies.grav.data.file            = {}\n".format(self.filename_grav)
            )
            self.f_params.write(
                "#anomalies.grav.proj.in              = {}\n".format(self.grav_proj_in)
            )
            self.f_params.write(
                "#anomalies.grav.proj.out             = {}\n".format(self.grav_proj_out)
            )

        if self.global_experimentType in (2, 3):
            self.f_params.write(
                "#anomalies.magn.data.file            = {}\n".format(self.filename_magn)
            )
            self.f_params.write(
                "#anomalies.magn.proj.in              = {}\n".format(self.magn_proj_in)
            )
            self.f_params.write(
                "#anomalies.magn.proj.out             = {}\n".format(self.magn_proj_out)
            )

        self.f_params.close()

        if self.is_2d and self.profile_line_pts:
            self._write_paraview_transform_script()

        self.show_message(
            "parfile.txt saved to {}".format(self.global_outputFolderPath)
        )

    # ------------------------------------------------------------------
    def _write_paraview_transform_script(self):
        (x1, y1) = self.profile_line_pts[0]
        (x2, y2) = self.profile_line_pts[1]
        dx, dy = x2 - x1, y2 - y1
        L = math.sqrt(dx ** 2 + dy ** 2)
        declination = math.degrees(math.atan2(dx, dy))
        crs = (
            self.magn_proj_out
            if self.global_experimentType in (2, 3)
            else self.grav_proj_out
        )
        script_path = self.global_outputFolderPath + "/paraview_transform.py"
        _tmpl = _string.Template("""\
import math
from paraview import simple as pv  # type: ignore

# Tomofast-x 2D profile -> real-world coordinate transform
# Generated by Tomofast-x-q plugin.
# Profile CRS : $crs

PROFILE_X1 = $x1
PROFILE_Y1 = $y1
PROFILE_X2 = $x2
PROFILE_Y2 = $y2

# Profile length    : $L m
# XaxisDeclination  : $decl degrees from North

source = pv.GetActiveSource()
if source is None:
    raise RuntimeError("No active source -- select a VTK dataset in the Pipeline Browser first.")

alpha = math.degrees(math.atan2(PROFILE_Y2 - PROFILE_Y1, PROFILE_X2 - PROFILE_X1))

tf = pv.Transform(Input=source)
tf.Transform.Rotate = [0.0, 0.0, alpha]
tf.Transform.Translate = [PROFILE_X1, PROFILE_Y1, 0.0]

pv.Show(tf)
pv.Render()
""")
        with open(script_path, "w") as fh:
            fh.write(
                _tmpl.substitute(
                    crs=str(crs),
                    x1=float(x1),
                    y1=float(y1),
                    x2=float(x2),
                    y2=float(y2),
                    L="{:.2f}".format(float(L)),
                    decl="{:.4f}".format(float(declination)),
                )
            )

    # ------------------------------------------------------------------
    def parse_parameters(self):
        self.global_outputFolderPath = self.ui.lineEdit_output_directory_path.text()
        self.global_description = self.ui.textEdit_experiment_description.toPlainText()

        self.modelGrid_size = [
            int(self.ui.nx_label.text()),
            int(self.ui.ny_label.text()),
            int(self.ui.nz_label.text()),
        ]
        self.modelGrid_grav_file = self.global_outputFolderPath + "/model_grav_grid.txt"
        self.modelGrid_magn_file = self.global_outputFolderPath + "/model_magn_grid.txt"

        self.forward_data_grav_dataGridFile = (
            self.global_outputFolderPath + "/data_grav.csv"
        )
        self.forward_data_magn_dataGridFile = (
            self.global_outputFolderPath + "/data_magn.csv"
        )

        self.sensit_readFromFiles = (
            1 if self.ui.checkBox_read_sens_matrix.isChecked() else 0
        )
        self.forward_matrixCompression_type = (
            1 if self.ui.checkBox_use_compression.isChecked() else 2
        )
        self.forward_matrixCompression_rate = (
            self.ui.mQgsDoubleSpinBox_compression_ratio.value()
        )

        self.inversion_nMajorIterations = self.ui.mQgsSpinBox_major_iters.value()
        self.inversion_nMinorIterations = self.ui.mQgsSpinBox_minor_iters.value()
        self.inversion_writeModelEveryNiter = (
            self.ui.mQgsSpinBox_model_save_iters.value()
        )
        self.inversion_minResidual = self.ui.textEdit_min_residual.toPlainText()
        self.inversion_targetMisfit = self.ui.lineEdit_targetMisfit.text().strip()

        self.inversion_modelDamping_grav_weight = (
            self.ui.mQgsDoubleSpinBox_grav_mmodel_damping_weight.value()
        )
        self.inversion_modelDamping_grav_normPower = (
            self.ui.mQgsDoubleSpinBox_grav_mmodel_norm_power.value()
        )
        self.inversion_modelDamping_magn_weight = (
            self.ui.mQgsDoubleSpinBox_magn_model_weight.value()
        )
        self.inversion_modelDamping_magn_normPower = (
            self.ui.mQgsDoubleSpinBox_magn_model_norm_power.value()
        )

        self.inversion_joint_grav_problemWeight = (
            self.ui.mQgsDoubleSpinBox_grav_weight.value()
        )
        self.inversion_joint_magn_problemWeight = (
            self.ui.mQgsDoubleSpinBox_magn_weight.value()
        )

        self.inversion_admm_grav_nLithologies = int(
            self.ui.spinBox_grav_number_ADMM_litho.value()
        )
        self.inversion_admm_grav_enableADMM = (
            1 if self.inversion_admm_grav_nLithologies > 0 else 0
        )

        self.inversion_admm_magn_nLithologies = int(
            self.ui.spinBox_magn_ADMM_number_litho.value()
        )
        self.inversion_admm_magn_enableADMM = (
            1 if self.inversion_admm_magn_nLithologies > 0 else 0
        )

        if self.ui.textEdit_grav_ADMM_bounds.toPlainText():
            self.inversion_admm_grav_bounds = (
                self.ui.textEdit_grav_ADMM_bounds.toPlainText()
            )
        if self.ui.lineEdit_grav_ADMM_weight.text():
            self.inversion_admm_grav_weight = self.ui.lineEdit_grav_ADMM_weight.text()
        if self.ui.textEdit_5_magn_ADMM_bounds.toPlainText():
            self.inversion_admm_magn_bounds = (
                self.ui.textEdit_5_magn_ADMM_bounds.toPlainText()
            )
        if self.ui.lineEdit_magn_ADMM_weight.text():
            self.inversion_admm_magn_weight = self.ui.lineEdit_magn_ADMM_weight.text()

        self.global_grav_dataUnitsMultiplier = float(
            self.ui.lineEdit_grav_data_multiplier.text()
        )
        self.global_grav_modelUnitsMultiplier = (
            self.ui.mQgsDoubleSpinBox_grav_model_multiplier.value()
        )
        self.global_magn_dataUnitsMultiplier = float(
            self.ui.lineEdit_magn_data_multiplier.text()
        )
        self.global_magn_modelUnitsMultiplier = (
            self.ui.mQgsDoubleSpinBox_magn_model_multiplier.value()
        )

        if self.ui.radioButton_grav_inv.isChecked():
            self.inversion_type = 1
        elif self.ui.radioButton_magn_inv.isChecked():
            self.inversion_type = 2
        else:
            self.inversion_type = 3

        self.filename_grav = self.ui.lineEdit_grav_data_path.text()
        self.filename_magn = self.ui.lineEdit_magn_data_path.text()

        self.global_elevFilename = self.ui.lineEdit_dtm_path.text()
        self.ROIFileName = self.ui.lineEdit_ROI_path.text()

        self.meshBox = {
            "south": self.ui.mQgsSpinBox_mesh_south.value(),
            "west":  self.ui.mQgsSpinBox_mesh_west.value(),
            "north": self.ui.mQgsSpinBox_mesh_north.value(),
            "east":  self.ui.mQgsSpinBox_mesh_east.value(),
        }

        self.forward_magneticField_declination = self.ui.doubleSpinBox_mag_dec.value()
        self.forward_magneticField_inclination = self.ui.doubleSpinBox_mag_inc.value()
        self.forward_magneticField_intensity   = self.ui.doubleSpinBox_mag_int.value()

        self.global_grav_sensor_height = self.ui.doubleSpinBox_grav_sensor_height.value()
        self.global_magn_sensor_height = self.ui.doubleSpinBox_magn_sensor_height.value()
        self.z_coreDepth = self.ui.doubleSpinBox_coreDepth.value()
        self.z_fullDepth = self.ui.doubleSpinBox_fullDepth.value()

    # ------------------------------------------------------------------
    def load_parfile(self):
        if not (os.path.exists(self.parfilename) and self.parfilename):
            return
        parfile = open(self.parfilename, "r")
        for pl in parfile.readlines():
            pls = pl.split("=")
            pkey = pls[0].strip().replace("#", "")

            if pkey == "global.is_2d" and len(pls) == 2:
                self.is_2d = bool(int(pls[1].strip()))
                continue

            if pkey in self.d_params:
                if len(pls) == 2:
                    pval = pls[1].strip()
                    if self.d_params[pkey][-2] == float and "d" in pval:
                        pval = pval.replace("d", "e")

                    if self.d_params[pkey][-1] == "size":
                        self.d_params[pkey][0][0] = self.d_params[pkey][-2](
                            pval.split(" ")[0]
                        )
                        self.d_params[pkey][0][1] = self.d_params[pkey][-2](
                            pval.split(" ")[1]
                        )
                        self.d_params[pkey][0][2] = self.d_params[pkey][-2](
                            pval.split(" ")[2]
                        )
                    else:
                        self.d_params[pkey][0] = self.d_params[pkey][-2](pval)

                    p = self.d_params[pkey]
                    if p[0] != "":
                        if p[-1] == "value":
                            p[1].setValue(p[-2](p[0]))
                        elif p[-1] == "plainText":
                            p[1].setText(p[-2](p[0]))
                        elif p[-1] == "text":
                            p[1].setText(p[-2](p[0]))
                        elif p[-1] == "epsg":
                            p[1].setCrs(p[-2](p[0]))
                        elif p[-1] == "check":
                            p[1].setChecked(bool(p[0]))
                        elif p[-1] == "check_both":
                            checked = (p[0] == 2)
                            p[1].setChecked(checked)
                            p[2].setChecked(checked)
                        elif p[-1] == "value_both":
                            p[1].setValue(p[-2](p[0]))
                            p[2].setValue(p[-2](p[0]))
                        elif p[-1] == "radio":
                            for button in range(1, len(p) - 2):
                                p[button].setChecked(False)
                                if int(p[0]) == button:
                                    p[button].setChecked(True)
                        elif p[-1] == "path":
                            p[1] = p[0]
                        elif p[-1] == "size":
                            p[1].setText(p[-2](p[0][0]))
                            p[2].setText(p[-2](p[0][1]))
                            p[3].setText(p[-2](p[0][2]))
                    else:
                        print("blank", pkey)
        parfile.close()

    # ------------------------------------------------------------------
    def reset_params(self):
        self.initialise_variables()
        for pkey in self.d_params:
            p = self.d_params[pkey]
            if p[-1] == "value":
                p[1].setValue(p[-2](p[0]))
            elif p[-1] == "plainText":
                p[1].setText(p[-2](p[0]))
            elif p[-1] == "text":
                p[1].setText(p[-2](p[0]))
            elif p[-1] == "epsg":
                p[1].setCrs(p[-2](p[0]))
            elif p[-1] == "check":
                p[1].setChecked(bool(p[0]))
            elif p[-1] == "radio":
                for button in range(1, len(p) - 2):
                    p[button].setChecked(False)
                    if int(p[0]) == button:
                        p[button].setChecked(True)
            elif p[-1] == "path":
                p[1] = p[0]
            elif p[-1] == "size":
                p[1].setText(p[-2](p[0][0]))
                p[2].setText(p[-2](p[0][1]))
                p[3].setText(p[-2](p[0][2]))
        self.inversion_type_reset_gui()
        self.ui.lineEdit_param_load_path.setText("")
        self.ui.groupBox_dtm.setEnabled(False)
        self.ui.groupBox_mesh_params.setEnabled(False)
        self.ui.groupBox_grav_fields.setEnabled(False)
        for w in (
            self.ui.mQgsSpinBox_mesh_south,
            self.ui.mQgsSpinBox_mesh_west,
            self.ui.mQgsSpinBox_mesh_north,
            self.ui.mQgsSpinBox_mesh_east,
        ):
            w.setEnabled(True)

    # ------------------------------------------------------------------
    def enable_boxes(self):
        self.inversion_type_reset_gui()

    # ------------------------------------------------------------------
    def inversion_type_reset_gui(self):
        if self.ui.radioButton_grav_inv.isChecked():
            self.ui.groupBox_grav_data_file.setEnabled(True)
            self.ui.mQgsProjectionSelectionWidget_grav_in.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_grav_out.setEnabled(False)
            self.ui.groupBox_grav_admm.setEnabled(True)
            self.ui.groupBox_grav_fields.setEnabled(True)
            self.ui.groupBox_grav_unit_multipliers.setEnabled(True)
            self.ui.groupBox_grav_model_damping.setEnabled(True)
            self.ui.label_grav_params_header.setEnabled(True)
            self.ui.pushButton_load_grav_data.setEnabled(True)

            self.ui.label_magn_params_header.setEnabled(False)
            self.ui.groupBox_magn_data_file.setEnabled(False)
            self.ui.groupBox_magn_fields.setEnabled(False)
            self.ui.groupBox_magnetic_field.setEnabled(False)
            self.ui.groupBox_magn_unit_multipliers.setEnabled(False)
            self.ui.groupBox_magn_model_damping.setEnabled(False)
            self.ui.groupBox_magn_admm.setEnabled(False)
            self.global_experimentType = 1
            if not self.ui.lineEdit_targetMisfit.text().strip():
                self.ui.lineEdit_targetMisfit.setText("1e-7")

        elif self.ui.radioButton_magn_inv.isChecked():
            self.ui.groupBox_grav_data_file.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_magn_in.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_magn_out.setEnabled(False)
            self.ui.groupBox_grav_admm.setEnabled(False)
            self.ui.groupBox_grav_fields.setEnabled(False)
            self.ui.groupBox_grav_unit_multipliers.setEnabled(False)
            self.ui.groupBox_grav_model_damping.setEnabled(False)
            self.ui.label_grav_params_header.setEnabled(False)

            self.ui.label_magn_params_header.setEnabled(True)
            self.ui.groupBox_magn_data_file.setEnabled(True)
            self.ui.groupBox_magn_fields.setEnabled(True)
            self.ui.groupBox_magnetic_field.setEnabled(True)
            self.ui.groupBox_magn_unit_multipliers.setEnabled(True)
            self.ui.groupBox_magn_model_damping.setEnabled(True)
            self.ui.groupBox_magn_admm.setEnabled(True)
            self.ui.pushButton_load_magn_data.setEnabled(True)
            self.global_experimentType = 2
            if not self.ui.lineEdit_targetMisfit.text().strip():
                self.ui.lineEdit_targetMisfit.setText("5")

        elif self.ui.radioButton_joint_inv.isChecked():
            self.ui.pushButton_load_magn_data.setEnabled(True)
            self.ui.groupBox_grav_data_file.setEnabled(True)
            self.ui.mQgsProjectionSelectionWidget_grav_in.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_grav_out.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_magn_in.setEnabled(False)
            self.ui.mQgsProjectionSelectionWidget_magn_out.setEnabled(False)
            self.ui.groupBox_grav_admm.setEnabled(True)
            self.ui.groupBox_grav_fields.setEnabled(True)
            self.ui.groupBox_grav_unit_multipliers.setEnabled(True)
            self.ui.groupBox_grav_model_damping.setEnabled(True)
            self.ui.label_grav_params_header.setEnabled(True)
            self.ui.pushButton_load_grav_data.setEnabled(True)

            self.ui.label_magn_params_header.setEnabled(True)
            self.ui.groupBox_magn_data_file.setEnabled(True)
            self.ui.groupBox_magn_fields.setEnabled(True)
            self.ui.groupBox_magnetic_field.setEnabled(True)
            self.ui.groupBox_magn_unit_multipliers.setEnabled(True)
            self.ui.groupBox_magn_model_damping.setEnabled(True)
            self.ui.groupBox_magn_admm.setEnabled(True)
            self.global_experimentType = 3
            if not self.ui.lineEdit_targetMisfit.text().strip():
                self.ui.lineEdit_targetMisfit.setText("1e-7")

    # ------------------------------------------------------------------
    def process_parameter_file(self):
        self.select_parfile()
        if self.parfilename and os.path.exists(self.parfilename):
            self.load_parfile()
            self.enable_boxes()
            self.parse_parameters()
            self._load_layers_from_parfile()
            self.show_message("Parfile loaded OK")

    def _load_layers_from_parfile(self):
        grav_crs = self.ui.mQgsProjectionSelectionWidget_grav_in.crs().authid()
        if grav_crs:
            self.grav_proj_in = grav_crs
        grav_crs_out = self.ui.mQgsProjectionSelectionWidget_grav_out.crs().authid()
        if grav_crs_out:
            self.grav_proj_out = grav_crs_out
        magn_crs = self.ui.mQgsProjectionSelectionWidget_magn_in.crs().authid()
        if magn_crs:
            self.magn_proj_in = magn_crs
        magn_crs_out = self.ui.mQgsProjectionSelectionWidget_magn_out.crs().authid()
        if magn_crs_out:
            self.magn_proj_out = magn_crs_out

        grav_loaded = False
        magn_loaded = False

        try:
            if (
                self.global_experimentType in (1, 3)
                and self.filename_grav
                and os.path.exists(self.filename_grav)
            ):
                dataType = "grav" if self.global_experimentType == 3 else None
                suffix = self.filename_grav.split(".")[-1].lower()
                self.process_data_file(dataType)
                if suffix == "csv":
                    self.xcol_grav = self.ui.comboBox_grav_field_x.currentText()
                    self.ycol_grav = self.ui.comboBox_grav_field_y.currentText()
                    self.datacol_grav = self.ui.comboBox_grav_field_data.currentText()
                    self.load_csv_vector_grav(
                        self.filename_grav, self.xcol_grav, self.ycol_grav,
                        self.datacol_grav,
                    )
                    self.ui.comboBox_grav_field_x.setEnabled(True)
                    self.ui.comboBox_grav_field_y.setEnabled(True)
                    self.ui.comboBox_grav_field_data.setEnabled(True)
                    self.ui.pushButton_assign_grav_fields.setEnabled(True)
                self.ui.pushButton_load_grav_data.setEnabled(True)
                grav_loaded = True
        except Exception as e:
            print(f"Warning: could not load grav data layer: {e}")

        try:
            if (
                self.global_experimentType in (2, 3)
                and self.filename_magn
                and os.path.exists(self.filename_magn)
            ):
                dataType = "magn" if self.global_experimentType == 3 else None
                suffix = self.filename_magn.split(".")[-1].lower()
                self.process_data_file(dataType)
                if suffix == "csv":
                    self.xcol_magn = self.ui.comboBox_magn_field_x.currentText()
                    self.ycol_magn = self.ui.comboBox_magn_field_y.currentText()
                    self.datacol_magn = self.ui.comboBox_magn_field_data.currentText()
                    self.load_csv_vector_magn(
                        self.filename_magn, self.xcol_magn, self.ycol_magn,
                        self.datacol_magn,
                    )
                    self.ui.comboBox_magn_field_x.setEnabled(True)
                    self.ui.comboBox_magn_field_y.setEnabled(True)
                    self.ui.comboBox_magn_field_data.setEnabled(True)
                    self.ui.pushButton_assign_magn_fields.setEnabled(True)
                self.ui.pushButton_load_magn_data.setEnabled(True)
                magn_loaded = True
        except Exception as e:
            print(f"Warning: could not load magn data layer: {e}")

        try:
            if self.global_elevFilename and os.path.exists(self.global_elevFilename):
                self.dtm_filename = self.global_elevFilename
                self.load_dtm()
                self.global_elevType = 2
                self.forward_depthWeighting_type = 2
        except Exception as e:
            print(f"Warning: could not load DTM layer: {e}")

        try:
            if self.ROIFileName and os.path.exists(self.ROIFileName):
                self._load_ROI_file(self.ROIFileName)
        except Exception as e:
            print(f"Warning: could not load ROI layer: {e}")

        if grav_loaded or magn_loaded:
            self.update_widgets()
            self.ui.groupBox_dtm.setEnabled(True)
            self.ui.groupBox_mesh_params.setEnabled(True)

    # ------------------------------------------------------------------
    def select_parfile(self):
        from tkinter import filedialog
        self.parfilename = filedialog.askopenfilename(
            title="Select Parameter File", filetypes=[("TXT", "*.txt")]
        )
        self.ui.lineEdit_param_load_path.setText(self.parfilename)

    # ------------------------------------------------------------------
    def export_model(self):
        paramfile_Dir = os.path.dirname(self.paramfile_Path)
        filename_model_grid = os.path.join(paramfile_Dir, "model_grid.txt")
        print("Reading model from: ", filename_model_grid)

        if self.global_experimentType == 1:
            codes = ["grav"]
        elif self.global_experimentType == 2:
            codes = ["mag"]
        else:
            codes = ["grav", "mag"]

        for code in codes:
            filename_model_final = os.path.join(
                paramfile_Dir, "OUTPUT/model/" + code + "_final_model_full.txt"
            )
            if not os.path.exists(filename_model_final):
                self.show_message(
                    f"Model file not found for {code}: {filename_model_final}",
                    level="warning",
                )
                continue

            filename_model_csv = os.path.join(
                paramfile_Dir, "OUTPUT/" + code + "_final_model3D_full.csv"
            )
            model_grid = np.loadtxt(
                filename_model_grid, dtype=float,
                usecols=(0, 1, 2, 3, 4, 5), skiprows=1,
            )
            model_values = np.loadtxt(filename_model_final, dtype=float, skiprows=1)

            if model_grid.shape[0] != model_values.shape[0]:
                self.show_message(
                    f"Inconsistent model dimensions for {code}!", level="warning"
                )
                continue

            Ncells = model_grid.shape[0]
            positions = np.ndarray((Ncells, 3), dtype=float)
            positions[:, 0] = (model_grid[:, 0] + model_grid[:, 1]) / 2.0
            positions[:, 1] = (model_grid[:, 2] + model_grid[:, 3]) / 2.0
            positions[:, 2] = (model_grid[:, 4] + model_grid[:, 5]) / 2.0
            positions[:, 2] = -positions[:, 2]

            combined = np.column_stack((positions, model_values))
            np.savetxt(
                filename_model_csv, combined, delimiter=",",
                header="x,y,z,data", comments="", fmt="%.6f",
            )
            self.show_message(
                f"Model saved as {code}_final_model3D_full.csv in the OUTPUT directory"
            )

    # ------------------------------------------------------------------
    def replace_text_in_file(self, file_path, old_text, new_text):
        try:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            updated_content = content.replace(old_text, new_text)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def add_quotes_to_path(self, path):
        return '"' + path + '"'

    def convert_windows_wsl_path_to_linux(self, windows_path, distro):
        normalized = windows_path.replace("\\", "/")
        prefixes = [
            "//wsl.localhost/" + distro,
            "/wsl.localhost/" + distro,
            "//wsl$/" + distro,
            "/wsl$/" + distro,
            "wsl.localhost/" + distro,
            "wsl$/" + distro,
        ]
        norm_lower = normalized.lower()
        for prefix in prefixes:
            if norm_lower.startswith(prefix.lower()):
                linux_path = normalized[len(prefix):]
                if not linux_path.startswith("/"):
                    linux_path = "/" + linux_path
                return linux_path
        return normalized

    def _validate_path(self, path: str) -> str:
        if re.search(r'[;&|`$<>!]', path):
            raise ValueError(f"Unsafe characters in path: {path}")
        return path