# -*- coding: utf-8 -*-
import os
import time
import tempfile
import numpy as np
import pandas as pd
from osgeo import gdal
from Data2Tomofast import Data2Tomofast


class MeshMixin:

    # ------------------------------------------------------------------
    def extract_depth_layers(self, z_cell_size_list, z_layer_thickness_list):
        z_cell_size_list = [
            float(x) for x in z_cell_size_list.split(",") if x.strip()
        ]
        z_layer_thickness_list = [
            float(x) for x in z_layer_thickness_list.split(",") if x.strip()
        ]
        depth_layers = []
        for cell_size, layer_thick in zip(z_cell_size_list, z_layer_thickness_list):
            depth_layers.append({"cell_size": cell_size, "layer_thick": layer_thick})
        return depth_layers

    # ------------------------------------------------------------------
    def setupMesh(self):
        self.cell_x = self.ui.mQgsSpinBox_mesh_size_x.value()
        self.cell_y = self.ui.mQgsSpinBox_mesh_size_y.value()
        self.padding = self.ui.mQgsSpinBox_mesh_padding.value()

        self.z_cell_size_list = self.ui.textEdit_z_cell_size_list.toPlainText()
        self.z_layer_thickness_list = (
            self.ui.textEdit_z_layer_thickness_list.toPlainText()
        )
        self.depth_layers = self.extract_depth_layers(
            self.z_cell_size_list, self.z_layer_thickness_list
        )
        total_layers = 0
        if self.depth_layers:
            for layer in self.depth_layers:
                total_layers += layer["layer_thick"] / layer["cell_size"]

        self.dz = self.ui.mQgsSpinBox_mesh_size_z.value()

        self.data2tomofast = Data2Tomofast(None)
        self.meshBox = {
            "south": self.ui.mQgsSpinBox_mesh_south.value(),
            "west":  self.ui.mQgsSpinBox_mesh_west.value(),
            "north": self.ui.mQgsSpinBox_mesh_north.value(),
            "east":  self.ui.mQgsSpinBox_mesh_east.value(),
            "core_depth": self.ui.doubleSpinBox_coreDepth.value(),
            "full_depth": self.ui.doubleSpinBox_fullDepth.value(),
            "total_layers": total_layers,
        }

        self.global_grav_sensor_height = (
            self.ui.doubleSpinBox_grav_sensor_height.value()
        )
        self.global_magn_sensor_height = (
            self.ui.doubleSpinBox_magn_sensor_height.value()
        )

    # ------------------------------------------------------------------
    def in_ROI(self, x, y, meshBox):
        return (
            meshBox["west"] <= x <= meshBox["east"]
            and meshBox["south"] <= y <= meshBox["north"]
        )

    # ------------------------------------------------------------------
    def _profile_unit_vectors(self):
        (x1, y1), (x2, y2) = self.profile_line_pts
        dx, dy = x2 - x1, y2 - y1
        L = np.sqrt(dx ** 2 + dy ** 2)
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        return (ux, uy), (px, py), L

    # ------------------------------------------------------------------
    def _rewrite_model_grid_2d_world(self):
        (x0w, y0w) = self.profile_line_pts[0]
        (ux, uy), (qx, qy), _ = self._profile_unit_vectors()
        mg = pd.read_csv(
            self.global_outputFolderPath + "/model_grid.txt",
            sep=" ", skiprows=1, header=None,
            names=["x1", "x2", "y1", "y2", "z1", "z2", "i", "j", "k"],
        )
        s1, s2 = mg["x1"].values, mg["x2"].values
        t1, t2 = mg["y1"].values, mg["y2"].values
        s_mid = (s1 + s2) / 2.0
        t_mid = (t1 + t2) / 2.0
        x1_world = x0w + s1 * ux + t_mid * qx
        x2_world = x0w + s2 * ux + t_mid * qx
        y1_world = y0w + s_mid * uy + t1 * qy
        y2_world = y0w + s_mid * uy + t2 * qy
        mg["x1"] = np.minimum(x1_world, x2_world)
        mg["x2"] = np.maximum(x1_world, x2_world)
        mg["y1"] = np.minimum(y1_world, y2_world)
        mg["y2"] = np.maximum(y1_world, y2_world)
        grid = mg[["x1", "x2", "y1", "y2", "z1", "z2", "i", "j", "k"]].values
        np.savetxt(
            self.global_outputFolderPath + "/model_grid.txt",
            grid,
            delimiter=" ",
            fmt="%f %f %f %f %f %f %d %d %d",
            header=str(len(mg)),
            comments="",
        )

    # ------------------------------------------------------------------
    def _project_data_to_profile(self):
        (x1, y1) = self.profile_line_pts[0]
        (ux, uy), _, _ = self._profile_unit_vectors()
        pts_x = self.data2tomofast.df["POINT_X"].values
        pts_y = self.data2tomofast.df["POINT_Y"].values
        self.data2tomofast.df["x_world"] = pts_x
        self.data2tomofast.df["y_world"] = pts_y
        self.data2tomofast.df["POINT_X"] = (pts_x - x1) * ux + (pts_y - y1) * uy
        self.data2tomofast.df["POINT_Y"] = 0.0

    # ------------------------------------------------------------------
    def convert_raster_data(self, filename, proj_out, dataType):
        if dataType == 1:
            self.datacol_grav = "data"
            self.filename_grav = self.global_outputFolderPath + "/data_grav.csv"
            reprojDataName = "/reproj_data_grav.tif"
            reprojPoints = "/reproj_data_grav.csv"
            source_proj = self.grav_proj_in
        else:
            self.datacol_magn = "data"
            self.filename_magn = self.global_outputFolderPath + "/data_magn.csv"
            reprojDataName = "/reproj_data_magn.tif"
            reprojPoints = "/reproj_data_magn.csv"
            source_proj = self.magn_proj_in

        self.setupMesh()

        meshBoxOffset = {
            "south": int(self.meshBox["south"]),
            "west":  int(self.meshBox["west"]),
            "north": int(self.meshBox["north"]),
            "east":  int(self.meshBox["east"]),
            "core_depth": self.ui.doubleSpinBox_coreDepth.value(),
            "full_depth": self.ui.doubleSpinBox_fullDepth.value(),
        }

        if self.is_2d and self.profile_line_pts:
            (ux, uy), (qx, qy), profile_len = self._profile_unit_vectors()
            self.data2tomofast.write_model_grid_2d(
                profile_len, self.padding, self.cell_x, self.cell_y,
                self.dz, meshBoxOffset, self.global_outputFolderPath, self.depth_layers,
            )
        else:
            self.data2tomofast.write_model_grid(
                self.padding, self.cell_x, self.cell_y,
                self.dz, meshBoxOffset, self.global_outputFolderPath, self.depth_layers,
            )

        n_surface_rows = (
            self.data2tomofast.nx
            if (self.is_2d and self.profile_line_pts)
            else self.data2tomofast.nx * self.data2tomofast.ny
        )
        df = pd.read_csv(
            self.global_outputFolderPath + "/model_grid.txt",
            sep=" ", skiprows=1, header=None, nrows=n_surface_rows,
            names=["x1", "x2", "y1", "y2", "z1", "z2", "i", "j", "k"],
        )

        if self.is_2d and self.profile_line_pts:
            x_cell_size = df["x2"] - df["x1"]
            df = df[
                np.abs(x_cell_size - self.cell_x) < 0.1 * self.cell_x
            ].reset_index(drop=True)
            (x1, y1) = self.profile_line_pts[0]
            (ux, uy), _, _ = self._profile_unit_vectors()
            d_along = (df["x1"] + df["x2"]) / 2.0
            df["x_world"] = x1 + d_along * ux
            df["y_world"] = y1 + d_along * uy
        else:
            df["x_world"] = (df["x1"] + df["x2"]) / 2.0
            df["y_world"] = (df["y1"] + df["y2"]) / 2.0
            # Clip to unbuffered ROI (same as QGIS in_ROI check at line 2967)
            df = df[
                (df["x_world"] >= self.meshBox["west"]) &
                (df["x_world"] <= self.meshBox["east"]) &
                (df["y_world"] >= self.meshBox["south"]) &
                (df["y_world"] <= self.meshBox["north"])
            ].reset_index(drop=True)

        # Reproject raster
        reproj_raster_path = self.global_outputFolderPath + reprojDataName
        src_ds = gdal.Open(filename)
        if src_ds is None:
            raise RuntimeError(f"Could not open input raster: {filename}")
        warp_options = gdal.WarpOptions(
            srcSRS=source_proj,
            dstSRS=proj_out,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )
        out_ds = gdal.Warp(reproj_raster_path, src_ds, options=warp_options)
        if out_ds is None:
            raise RuntimeError(f"gdal.Warp failed for input: {filename}")
        out_ds = None
        src_ds = None

        # Sample raster at mesh cell centres using _sample_raster_at_points
        xs = df["x_world"].values
        ys = df["y_world"].values
        sampled_vals = self._sample_raster_at_points(reproj_raster_path, xs, ys)

        data_df = pd.DataFrame({
            "POINT_X": df["x_world"].values,
            "POINT_Y": df["y_world"].values,
            "data1": sampled_vals,
        })

        if self.is_2d and self.profile_line_pts:
            data_df["x_world"] = data_df["POINT_X"]
            data_df["y_world"] = data_df["POINT_Y"]
            (x1, y1) = self.profile_line_pts[0]
            (ux, uy), _, _ = self._profile_unit_vectors()
            along = (
                (data_df["POINT_X"] - x1) * ux
                + (data_df["POINT_Y"] - y1) * uy
            )
            data_df["POINT_X"] = along
            data_df["POINT_Y"] = 0.0

        data_df.to_csv(self.global_outputFolderPath + reprojPoints, index=False)

    # ------------------------------------------------------------------
    def convert_point_data(self, dataFormat):
        if self.global_experimentType == 1:
            if dataFormat == "points":
                self.data2tomofast.read_data(
                    self.filename_grav, self.ycol_grav, self.xcol_grav,
                    self.datacol_grav, self.grav_proj_in, self.grav_proj_out,
                )
            else:
                y_col = "y_world" if (self.is_2d and self.profile_line_pts) else "POINT_Y"
                x_col = "x_world" if (self.is_2d and self.profile_line_pts) else "POINT_X"
                self.data2tomofast.read_data(
                    self.global_outputFolderPath + "/reproj_data_grav.csv",
                    y_col, x_col, "data1", self.grav_proj_out, self.grav_proj_out,
                )
                self.datacol_grav = "data1"
            if self.data2tomofast.df is not None and len(self.data2tomofast.df) == 0:
                raise ValueError(
                    f"Grav data file has 0 rows. "
                    f"File: {self.filename_grav if dataFormat == 'points' else 'reproj_data_grav.csv'}. "
                    f"Check that the file exists, has data rows, and the column names match."
                )
            if self.global_elevType == 1:
                self.add_elevation(self.global_grav_sensor_height, self.global_elevType, 0)
            else:
                self.add_dtm(1)
                self.add_elevation(self.global_grav_sensor_height, self.global_elevType, self.data_df)
            if self.is_2d and self.profile_line_pts:
                self._project_data_to_profile()
            self.data2tomofast.write_data_tomofast(
                self.datacol_grav, self.global_outputFolderPath, 1
            )

        elif self.global_experimentType == 2:
            if dataFormat == "points":
                self.data2tomofast.read_data(
                    self.filename_magn, self.ycol_magn, self.xcol_magn,
                    self.datacol_magn, self.magn_proj_in, self.magn_proj_out,
                )
            else:
                y_col = "y_world" if (self.is_2d and self.profile_line_pts) else "POINT_Y"
                x_col = "x_world" if (self.is_2d and self.profile_line_pts) else "POINT_X"
                self.data2tomofast.read_data(
                    self.global_outputFolderPath + "/reproj_data_magn.csv",
                    y_col, x_col, "data1", self.magn_proj_out, self.magn_proj_out,
                )
                self.datacol_magn = "data1"
            if self.data2tomofast.df is not None and len(self.data2tomofast.df) == 0:
                raise ValueError(
                    f"Magn data file has 0 rows. "
                    f"File: {self.filename_magn if dataFormat == 'points' else 'reproj_data_magn.csv'}. "
                    f"Check that the file exists, has data rows, and the column names match."
                )
            if self.global_elevType == 1:
                self.add_elevation(self.global_magn_sensor_height, self.global_elevType, 0)
            else:
                self.add_dtm(2)
                self.add_elevation(self.global_magn_sensor_height, self.global_elevType, self.data_df)
            if self.is_2d and self.profile_line_pts:
                self._project_data_to_profile()
            self.data2tomofast.write_data_tomofast(
                self.datacol_magn, self.global_outputFolderPath, 2
            )

        else:  # joint
            if dataFormat == "points":
                self.data2tomofast.read_data(
                    self.filename_grav, self.ycol_grav, self.xcol_grav,
                    self.datacol_grav, self.grav_proj_in, self.grav_proj_out,
                )
            else:
                y_col = "y_world" if (self.is_2d and self.profile_line_pts) else "POINT_Y"
                x_col = "x_world" if (self.is_2d and self.profile_line_pts) else "POINT_X"
                self.data2tomofast.read_data(
                    self.global_outputFolderPath + "/reproj_data_grav.csv",
                    y_col, x_col, "data1", self.grav_proj_out, self.grav_proj_out,
                )
                self.datacol_grav = "data1"
            if self.global_elevType == 1:
                self.add_elevation(self.global_grav_sensor_height, self.global_elevType, 0)
            else:
                self.add_dtm(1)
                self.add_elevation(self.global_grav_sensor_height, self.global_elevType, self.data_df)
            if self.is_2d and self.profile_line_pts:
                self._project_data_to_profile()
            self.data2tomofast.write_data_tomofast(
                self.datacol_grav, self.global_outputFolderPath, 1
            )

            if dataFormat == "points":
                self.data2tomofast.read_data(
                    self.filename_magn, self.ycol_magn, self.xcol_magn,
                    self.datacol_magn, self.magn_proj_in, self.magn_proj_out,
                )
            else:
                y_col = "y_world" if (self.is_2d and self.profile_line_pts) else "POINT_Y"
                x_col = "x_world" if (self.is_2d and self.profile_line_pts) else "POINT_X"
                self.data2tomofast.read_data(
                    self.global_outputFolderPath + "/reproj_data_magn.csv",
                    y_col, x_col, "data1", self.magn_proj_out, self.magn_proj_out,
                )
                self.datacol_magn = "data1"
            if self.global_elevType == 1:
                self.add_elevation(self.global_magn_sensor_height, self.global_elevType, 0)
            else:
                self.add_dtm(2)
                self.add_elevation(self.global_magn_sensor_height, self.global_elevType, self.data_df)
            if self.is_2d and self.profile_line_pts:
                self._project_data_to_profile()
            self.data2tomofast.write_data_tomofast(
                self.datacol_magn, self.global_outputFolderPath, 2
            )

        if dataFormat == "points":
            if self.is_2d and self.profile_line_pts:
                _, _, profile_len = self._profile_unit_vectors()
                depth_box = {
                    "core_depth": self.ui.doubleSpinBox_coreDepth.value(),
                    "full_depth": self.ui.doubleSpinBox_fullDepth.value(),
                }
                self.data2tomofast.write_model_grid_2d(
                    profile_len, self.padding, self.cell_x, self.cell_y,
                    self.dz, depth_box, self.global_outputFolderPath, self.depth_layers,
                )
            else:
                self.data2tomofast.write_model_grid(
                    self.padding, self.cell_x, self.cell_y,
                    self.dz, self.meshBox, self.global_outputFolderPath, self.depth_layers,
                )

        self.ui.nx_label.setText(str(self.data2tomofast.nx))
        self.ui.ny_label.setText(str(self.data2tomofast.ny))
        self.ui.nz_label.setText(str(self.data2tomofast.nz))

        if self.global_experimentType in (1, 3):
            self.forward_data_grav_nData = self.data2tomofast.nData
        if self.global_experimentType in (2, 3):
            self.forward_data_magn_nData = self.data2tomofast.nData

    # ------------------------------------------------------------------
    def load_mesh_vector(self):
        df = pd.read_csv(
            self.global_outputFolderPath + "/model_grid.txt",
            sep=" ", skiprows=1, header=None,
            nrows=self.data2tomofast.nx * self.data2tomofast.ny,
        )
        df[0] = (df[0] + df[1]) / 2.0
        df[2] = (df[2] + df[3]) / 2.0
        df = df.drop(columns=[1, 3, 4, 5, 6, 7, 8])

        if self.is_2d and self.profile_line_pts:
            (px1, py1) = self.profile_line_pts[0]
            (ux, uy), (qx, qy), _ = self._profile_unit_vectors()
            d_along = df[0].values
            d_cross = df[2].values
            df[0] = px1 + d_along * ux + d_cross * qx
            df[2] = py1 + d_along * uy + d_cross * qy

        # Save top-layer mesh points as a CSV and record for display
        mesh_csv = os.path.join(tempfile.gettempdir(), "tomofast_model_grid.csv")
        df.to_csv(mesh_csv, index=False)
        self._record_pending(mesh_csv)

        if self.global_elevType == 2:
            self.sample_elevation()

    # ------------------------------------------------------------------
    def sample_elevation(self):
        model_grid_df = pd.read_csv(
            self.global_outputFolderPath + "/model_grid.txt",
            sep=" ", skiprows=1, header=None,
            nrows=self.data2tomofast.nx * self.data2tomofast.ny,
            names=["x1", "x2", "y1", "y2", "z1", "z2", "i", "j", "k"],
        )
        model_grid_df["cx"] = (model_grid_df["x1"] + model_grid_df["x2"]) / 2.0
        model_grid_df["cy"] = (model_grid_df["y1"] + model_grid_df["y2"]) / 2.0

        if self.is_2d and self.profile_line_pts:
            (px1, py1) = self.profile_line_pts[0]
            (ux, uy), (qx, qy), _ = self._profile_unit_vectors()
            cx_out = (
                px1
                + model_grid_df["cx"].values * ux
                + model_grid_df["cy"].values * qx
            )
            cy_out = (
                py1
                + model_grid_df["cx"].values * uy
                + model_grid_df["cy"].values * qy
            )
        else:
            cx_out = model_grid_df["cx"].values
            cy_out = model_grid_df["cy"].values

        elevations_raw = self._sample_raster_at_points(self.dtm_raster_path, cx_out, cy_out)

        missing = sum(1 for v in elevations_raw if v == 0.0)
        elevations = [-v for v in elevations_raw]

        if missing > 0:
            self.show_message(
                f"{missing} mesh points had no DTM coverage — elevations set to zero.",
                level="warning",
            )

        output_df = pd.DataFrame({"x": cx_out, "y": cy_out, "elevation": elevations})
        output_df.to_csv(
            self.global_outputFolderPath + "/elevation_grid.csv", index=False
        )

    # ------------------------------------------------------------------
    def tidy_data(self, temp_file_path1, fileName1, dataName1):
        with open(fileName1, "r") as f:
            lines = f.readlines()[1:]

        with open(temp_file_path1, "w") as temp_file:
            temp_file.writelines(f"x y height {dataName1}\n")
            temp_file.writelines(lines)
            temp_file.flush()

        temp_data = pd.read_csv(
            temp_file_path1, na_values=["", " "], sep=r"\s+"
        )
        temp_data = temp_data.dropna()
        data_len = len(temp_data)
        if self.global_experimentType == 1:
            self.forward_data_grav_nData = data_len
        else:
            self.forward_data_magn_nData = data_len

        time.sleep(5)

        if self.is_2d and self.profile_line_pts:
            (x1w, y1w) = self.profile_line_pts[0]
            (ux, uy), _, _ = self._profile_unit_vectors()
            along = temp_data["x"].values
            temp_world = temp_data.copy()
            temp_world["x"] = x1w + along * ux
            temp_world["y"] = y1w + along * uy
            temp_world.to_csv(temp_file_path1, sep=" ", index=False)
        else:
            temp_data.to_csv(temp_file_path1, sep=" ", index=False)

        with open(fileName1, "w") as temp_file:
            temp_file.writelines(f"{data_len}\n")
            temp_file.flush()

        temp_data.to_csv(f"{fileName1}", sep=" ", header=False, index=False, mode="a")

    # ------------------------------------------------------------------
    def tidy_layers(self):
        if self.global_dataType != "points":
            if self.global_experimentType == 1:
                fileName1 = self.global_outputFolderPath + "/data_grav.csv"
                proj1 = self.grav_proj_out
                dataName1 = "grav_data"
            elif self.global_experimentType == 2:
                fileName1 = self.global_outputFolderPath + "/data_magn.csv"
                proj1 = self.magn_proj_out
                dataName1 = "magn_data"
            else:
                fileName1 = self.global_outputFolderPath + "/data_grav.csv"
                proj1 = self.grav_proj_out
                dataName1 = "grav_data"
                fileName2 = self.global_outputFolderPath + "/data_magn.csv"
                dataName2 = "magn_data"

            temp_file_path1 = self.global_outputFolderPath + "/data_temp.csv"
            self.tidy_data(temp_file_path1, fileName1, dataName1)
            self._record_pending(temp_file_path1)

            if self.global_experimentType == 3:
                self.tidy_data(temp_file_path1, fileName2, dataName2)
                self._record_pending(temp_file_path1)

    # ------------------------------------------------------------------
    def select_ouput_directory(self):
        from tkinter import filedialog
        self.global_outputFolderPath = filedialog.askdirectory(
            title="Select output path for your Tomofast-x input files"
        )
        self.ui.lineEdit_output_directory_path.setText(self.global_outputFolderPath)
        if self.global_outputFolderPath and os.path.exists(self.global_outputFolderPath):
            self.output_directory = os.path.split(
                self.ui.lineEdit_output_directory_path.text()
            )[-1]
            try:
                result = self.save_outputs()
                if result:
                    self.show_message(
                        "Files saved to " + self.ui.lineEdit_output_directory_path.text()
                    )
                    self.update_memory_size()
                    self.save_parameter_file()
            except Exception as _e:
                import traceback
                self.show_message(
                    "Error saving files: " + str(_e), level="critical"
                )
                print("Tomofast-x save error:\n" + traceback.format_exc())

    # ------------------------------------------------------------------
    def save_outputs(self):
        self.forward_magneticField_declination = (
            self.ui.doubleSpinBox_mag_dec.value()
        )
        self.forward_magneticField_inclination = (
            self.ui.doubleSpinBox_mag_inc.value()
        )
        self.forward_magneticField_intensity = (
            self.ui.doubleSpinBox_mag_int.value()
        )

        if (
            self.global_experimentType in (2, 3)
            and self.forward_magneticField_declination == 0.0
            and self.forward_magneticField_inclination == -45.0
            and self.forward_magneticField_intensity == 65000.0
        ):
            self.show_message(
                "Please define Magnetic Field Parameters", level="warning"
            )
            return False

        self.setupMesh()

        if self.global_experimentType == 1:
            self.ui.mQgsDoubleSpinBox_grav_weight.setValue(1.0)
            self.ui.mQgsDoubleSpinBox_magn_weight.setValue(0.0)
        elif self.global_experimentType == 2:
            self.ui.mQgsDoubleSpinBox_grav_weight.setValue(0.0)
            self.ui.mQgsDoubleSpinBox_magn_weight.setValue(1.0)

        if self.global_dataType == "points":
            self.convert_point_data(self.global_dataType)
        else:
            if self.global_experimentType == 1:
                self.convert_raster_data(
                    self.ui.lineEdit_grav_data_path.text(), self.grav_proj_out, 1
                )
                self.convert_point_data(self.global_dataType)
            elif self.global_experimentType == 2:
                self.convert_raster_data(
                    self.ui.lineEdit_magn_data_path.text(), self.magn_proj_out, 2
                )
                self.convert_point_data(self.global_dataType)
            else:
                self.convert_raster_data(
                    self.ui.lineEdit_grav_data_path.text(), self.grav_proj_out, 1
                )
                self.convert_raster_data(
                    self.ui.lineEdit_magn_data_path.text(), self.magn_proj_out, 2
                )
                self.convert_point_data(self.global_dataType)

        self.load_mesh_vector()
        if self.global_elevType == 2:
            mean_elevation = self.data2tomofast.add_topography(
                self.global_outputFolderPath + "/model_grid.txt",
                self.global_outputFolderPath + "/elevation_grid.csv",
            )
        else:
            mean_elevation = 0

        self.tidy_layers()

        if self.is_2d and self.profile_line_pts:
            for fname in ["reproj_data_grav.csv", "reproj_data_magn.csv"]:
                fpath = self.global_outputFolderPath + "/" + fname
                if os.path.exists(fpath):
                    os.remove(fpath)

        return True

    # ------------------------------------------------------------------
    def update_model_grid_size(self):
        self.setupMesh()
        if (
            self.cell_x == 0
            or self.cell_y == 0
            or int(self.ui.mQgsSpinBox_mesh_size_z.value()) == 0
        ):
            return
        nx = int(
            (self.meshBox["east"] - self.meshBox["west"] + (2 * self.padding))
            / self.cell_x
        )
        ny = int(
            (self.meshBox["north"] - self.meshBox["south"] + (2 * self.padding))
            / self.cell_y
        )
        ncore = int(
            float(self.ui.doubleSpinBox_coreDepth.value())
            / float(self.ui.mQgsSpinBox_mesh_size_z.value())
        )
        try:
            npad = int(
                np.log(
                    float(
                        self.ui.doubleSpinBox_fullDepth.value()
                        - float(self.ui.doubleSpinBox_coreDepth.value())
                    )
                    / (float(self.ui.mQgsSpinBox_mesh_size_z.value()))
                )
                / np.log(1.15)
            )
        except Exception:
            npad = 0
        nz = ncore + npad

        self.ui.nx_label.setText(str(nx))
        self.ui.ny_label.setText(str(ny))
        self.ui.nz_label.setText(str(nz))

        data_nx = int((self.meshBox["east"] - self.meshBox["west"]) / self.cell_x)
        data_ny = int((self.meshBox["north"] - self.meshBox["south"]) / self.cell_y)
        self.update_memory_size()
        self.update_ideal_compression_ratio(data_nx, data_ny, nz)

    # ------------------------------------------------------------------
    def update_ideal_compression_ratio(self, nx, ny, nz):
        if nx * ny * nz > 400000:
            ideal_cr = 35.07 * (0.01 ** -0.872) * ((nx * ny * nz) ** -0.884)
            val = ideal_cr * 2
            if self.is_2d:
                val *= 100.0
            val = min(val, 1.0)
            self.forward_matrixCompression_rate = val
            self.ui.mQgsDoubleSpinBox_compression_ratio.setValue(val)
        else:
            self.forward_matrixCompression_rate = 1.0
            self.ui.mQgsDoubleSpinBox_compression_ratio.setValue(1.0)

    # ------------------------------------------------------------------
    def update_memory_size(self):
        self.setupMesh()
        if self.ui.checkBox_use_compression.isChecked():
            compression = self.ui.mQgsDoubleSpinBox_compression_ratio.value()
        else:
            compression = 1.0

        if self.is_2d and self.profile_line_pts:
            (x1, y1) = self.profile_line_pts[0]
            (x2, y2) = self.profile_line_pts[1]
            profile_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            data_nx = int(profile_length / self.cell_x) if self.cell_x > 0 else 0
            data_ny = 1
            nx = data_nx + int(2 * self.padding / self.cell_x) if self.cell_x > 0 else 0
            ny = 1 + int(2 * self.padding / self.cell_y) if self.cell_y > 0 else 0
        elif self.is_2d:
            data_nx = (
                int((self.meshBox["east"] - self.meshBox["west"]) / self.cell_x)
                if self.cell_x > 0 else 0
            )
            data_ny = 1
            nx = data_nx + int(2 * self.padding / self.cell_x) if self.cell_x > 0 else 0
            ny = 1 + int(2 * self.padding / self.cell_y) if self.cell_y > 0 else 0
        else:
            nx = (
                int((self.meshBox["east"] - self.meshBox["west"] + (2 * self.padding)) / self.cell_x)
                if self.cell_x > 0 else 0
            )
            ny = (
                int((self.meshBox["north"] - self.meshBox["south"] + (2 * self.padding)) / self.cell_y)
                if self.cell_y > 0 else 0
            )
            data_nx = (
                int((self.meshBox["east"] - self.meshBox["west"]) / self.cell_x)
                if self.cell_x > 0 else 0
            )
            data_ny = (
                int((self.meshBox["north"] - self.meshBox["south"]) / self.cell_y)
                if self.cell_y > 0 else 0
            )

        if self.meshBox["total_layers"] > 0:
            nz = int(self.meshBox["total_layers"])
        else:
            ncore = int(
                float(self.ui.doubleSpinBox_coreDepth.value())
                / float(self.ui.mQgsSpinBox_mesh_size_z.value())
            )
            try:
                npad = int(
                    np.log(
                        float(
                            self.ui.doubleSpinBox_fullDepth.value()
                            - float(self.ui.doubleSpinBox_coreDepth.value())
                        )
                        / (float(self.ui.mQgsSpinBox_mesh_size_z.value()))
                    )
                    / np.log(1.15)
                )
            except Exception:
                npad = 0
            nz = ncore + npad

        if self.global_experimentType in (1, 3):
            data_path = self.ui.lineEdit_grav_data_path.text()
        else:
            data_path = self.ui.lineEdit_magn_data_path.text()

        suffix = data_path.split(".")[-1].lower()
        self.suffix_known = suffix

        if self.suffix_known != "csv":
            local_nData = data_nx * data_ny
        else:
            local_nData = self.nData
        if self.global_experimentType in (1, 2):
            memory = 8 * compression * nx * ny * nz * local_nData
        else:
            memory = 8 * compression * nx * ny * nz * local_nData * 2

        memory = round(memory / (1024 * 1024 * 1024), 3)
        self.ui.memory_label.setText(str(memory))
        if self.meshBox["total_layers"] > 0:
            self.ui.nz_label.setText(str(nz))

    # ------------------------------------------------------------------
    def mesh_layers(self):
        self.ui.doubleSpinBox_coreDepth.setEnabled(True)
        self.ui.doubleSpinBox_fullDepth.setEnabled(True)