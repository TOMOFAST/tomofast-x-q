# -*- coding: utf-8 -*-
import os
import tempfile
import numpy as np
import pandas as pd
from osgeo import gdal, ogr, osr
from datetime import datetime
from ppigrf import igrf, get_inclination_declination


class DataMixin:

    # ------------------------------------------------------------------
    def data_extents(self, xmin, ymin, xmax, ymax):
        self.ui.mQgsSpinBox_mesh_south.setValue(int(ymin))
        self.ui.mQgsSpinBox_mesh_north.setValue(int(ymax))
        self.ui.mQgsSpinBox_mesh_west.setValue(int(xmin))
        self.ui.mQgsSpinBox_mesh_east.setValue(int(xmax))
        self.meshBox = {
            "south": int(ymin),
            "west":  int(xmin),
            "north": int(ymax),
            "east":  int(xmax),
        }

    # ------------------------------------------------------------------
    def process_data_file(self, dataType=None):
        if self.global_experimentType == 1:
            filename = self.ui.lineEdit_grav_data_path.text()
            paths = os.path.split(filename)
            self.global_dataNameGrav = "".join(paths[1].split(".")[:-1])
        elif self.global_experimentType == 2:
            filename = self.ui.lineEdit_magn_data_path.text()
            paths = os.path.split(filename)
            self.global_dataNameMagn = "".join(paths[1].split(".")[:-1])
        else:  # joint
            if dataType == "grav":
                filename = self.ui.lineEdit_grav_data_path.text()
                paths = os.path.split(filename)
                self.global_dataNameGrav = "".join(paths[1].split(".")[:-1])
            elif dataType == "magn":
                filename = self.ui.lineEdit_magn_data_path.text()
                paths = os.path.split(filename)
                self.global_dataNameMagn = "".join(paths[1].split(".")[:-1])
            else:
                self.show_message("Unknown data type", level="warning")
                return

        suffix = paths[1].split(".")[-1]

        if suffix.lower() == "csv":
            self.data = pd.read_csv(filename)

            if self.global_experimentType in (1, 3):
                self.ui.comboBox_grav_field_x.addItems(self.data.columns)
                self.ui.comboBox_grav_field_y.addItems(self.data.columns)
                self.ui.comboBox_grav_field_y.setCurrentIndex(1)
                self.ui.comboBox_grav_field_data.addItems(self.data.columns)
                self.ui.comboBox_grav_field_data.setCurrentIndex(2)
                self.input_data_grav = filename

            if self.global_experimentType in (2, 3):
                self.ui.comboBox_magn_field_x.addItems(self.data.columns)
                self.ui.comboBox_magn_field_y.addItems(self.data.columns)
                self.ui.comboBox_magn_field_y.setCurrentIndex(1)
                self.ui.comboBox_magn_field_data.addItems(self.data.columns)
                self.ui.comboBox_magn_field_data.setCurrentIndex(2)
                self.input_data_magn = filename

            self.global_dataType = "points"
            self._record_pending(filename)

        elif suffix.lower() in ("tif", "tiff", "ers"):
            src_ds = gdal.Open(filename)
            if src_ds is None:
                self.show_message(f"Cannot open raster: {filename}", level="warning")
                return
            gt = src_ds.GetGeoTransform()
            nx = src_ds.RasterXSize
            ny = src_ds.RasterYSize
            xmin = gt[0]
            ymax = gt[3]
            xmax = gt[0] + nx * gt[1]
            ymin = gt[3] + ny * gt[5]

            srs = osr.SpatialReference()
            srs.ImportFromWkt(src_ds.GetProjection())
            auth = srs.GetAttrValue("AUTHORITY", 0)
            code = srs.GetAttrValue("AUTHORITY", 1)
            proj = f"{auth}:{code}" if auth and code else "EPSG:4326"
            src_ds = None

            if self.global_experimentType == 1:
                self.grav_proj_in = proj
                self.grav_proj_out = proj
            elif self.global_experimentType == 2:
                self.magn_proj_in = proj
                self.magn_proj_out = proj
            else:
                if dataType == "grav":
                    self.grav_proj_in = proj
                    self.grav_proj_out = proj
                else:
                    self.magn_proj_in = proj
                    self.magn_proj_out = proj

            self.ui.mQgsSpinBox_mesh_south.setValue(int(ymin))
            self.ui.mQgsSpinBox_mesh_north.setValue(int(ymax))
            self.ui.mQgsSpinBox_mesh_west.setValue(int(xmin))
            self.ui.mQgsSpinBox_mesh_east.setValue(int(xmax))
            self.meshBox = {
                "south": int(ymin),
                "west":  int(xmin),
                "north": int(ymax),
                "east":  int(xmax),
            }
            self.update_model_grid_size()
            self.global_dataType = "raster"
            self._record_pending(filename)

    # ------------------------------------------------------------------
    def select_data_file(self, dataType):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("Point/grid", "*.csv *.CSV *.TIF *.tif *.TIFF *.tiff *.ERS *.ers")],
        )
        if filename and os.path.exists(filename):
            if dataType == "grav":
                self.ui.lineEdit_grav_data_path.setText(filename)
                self.ui.pushButton_load_grav_data.setEnabled(True)
                self.filename_grav = filename
                if filename.split(".")[-1].lower() == "csv":
                    self.ui.mQgsProjectionSelectionWidget_grav_in.setEnabled(True)
                    self.ui.mQgsProjectionSelectionWidget_grav_out.setEnabled(True)
            else:
                self.ui.lineEdit_magn_data_path.setText(filename)
                self.ui.pushButton_load_magn_data.setEnabled(True)
                self.filename_magn = filename
                if filename.split(".")[-1].lower() == "csv":
                    self.ui.mQgsProjectionSelectionWidget_magn_in.setEnabled(True)
                    self.ui.mQgsProjectionSelectionWidget_magn_out.setEnabled(True)

    # ------------------------------------------------------------------
    def select_dtm(self):
        from tkinter import filedialog
        self.dtm_filename = filedialog.askopenfilename(
            title="Select DTM File",
            filetypes=[("TIFF", "*.tif *.tiff *.TIF *.TIFF")],
        )
        self.ui.lineEdit_dtm_path.setText(self.dtm_filename)
        if self.dtm_filename and os.path.exists(self.dtm_filename):
            self.load_dtm()
            self.global_elevFilename = self.dtm_filename
            self.global_elevType = 2
            self.forward_depthWeighting_type = 2

    # ------------------------------------------------------------------
    def confirm_data_file(self, dataType):
        self.is_2d = False
        self.process_data_file(dataType)
        if dataType == "grav":
            suffix = self.ui.lineEdit_grav_data_path.text().split(".")[-1]
        else:
            suffix = self.ui.lineEdit_magn_data_path.text().split(".")[-1]

        if suffix.lower() == "csv":
            self.global_dataType = "points"
            if dataType == "grav":
                self.grav_proj_in = (
                    self.ui.mQgsProjectionSelectionWidget_grav_in.crs().authid()
                )
                self.grav_proj_out = (
                    self.ui.mQgsProjectionSelectionWidget_grav_out.crs().authid()
                )
            else:
                self.magn_proj_in = (
                    self.ui.mQgsProjectionSelectionWidget_magn_in.crs().authid()
                )
                self.magn_proj_out = (
                    self.ui.mQgsProjectionSelectionWidget_magn_out.crs().authid()
                )
        else:
            self.global_dataType = "raster"

        if self.global_dataType == "points":
            self.ui.groupBox_grav_fields.setEnabled(True)
            self.ui.label_grav_field_long_x.setEnabled(True)
            self.ui.label_grav_field_lat_y.setEnabled(True)
            self.ui.label_grav_field_data_col.setEnabled(True)
            if dataType == "grav":
                self.ui.comboBox_grav_field_x.setEnabled(True)
                self.ui.comboBox_grav_field_y.setEnabled(True)
                self.ui.comboBox_grav_field_data.setEnabled(True)
                self.ui.pushButton_assign_grav_fields.setEnabled(True)
            else:
                self.ui.comboBox_magn_field_x.setEnabled(True)
                self.ui.comboBox_magn_field_y.setEnabled(True)
                self.ui.comboBox_magn_field_data.setEnabled(True)
                self.ui.pushButton_assign_magn_fields.setEnabled(True)
            self.ui.pushButton_select_dtm_path.setEnabled(False)
        else:
            self.ui.groupBox_dtm.setEnabled(True)
            self.ui.groupBox_grav_fields.setEnabled(True)
            self.ui.lineEdit_dtm_path.setEnabled(False)
            self.ui.pushButton_select_dtm_path.setEnabled(False)
            self.update_widgets()

    # ------------------------------------------------------------------
    def process_data_fields_grav(self):
        self.update_widgets()
        self.load_csv_vector_grav(
            self.filename_grav, self.xcol_grav, self.ycol_grav, self.datacol_grav
        )

    def process_data_fields_magn(self):
        self.update_widgets()
        self.load_csv_vector_magn(
            self.filename_magn, self.xcol_magn, self.ycol_magn, self.datacol_magn
        )

    # ------------------------------------------------------------------
    def update_widgets(self):
        if self.global_experimentType in (1, 3):
            self.xcol_grav = self.ui.comboBox_grav_field_x.currentText()
            self.ycol_grav = self.ui.comboBox_grav_field_y.currentText()
            self.datacol_grav = self.ui.comboBox_grav_field_data.currentText()

            self.ui.groupBox_dtm.setEnabled(True)
            self.ui.groupBox_grav_fields.setEnabled(True)
            self.ui.lineEdit_dtm_path.setEnabled(False)
            self.ui.pushButton_select_dtm_path.setEnabled(True)
            self.ui.groupBox_mesh_params.setEnabled(True)
            self.ui.lineEdit_output_directory_path.setEnabled(True)
            self.ui.lineEdit_output_directory_path_select.setEnabled(True)
            self.ui.lineEdit_ROI_path_select.setEnabled(True)

        if self.global_experimentType in (2, 3):
            self.xcol_magn = self.ui.comboBox_magn_field_x.currentText()
            self.ycol_magn = self.ui.comboBox_magn_field_y.currentText()
            self.datacol_magn = self.ui.comboBox_magn_field_data.currentText()

            self.ui.groupBox_dtm.setEnabled(True)
            self.ui.groupBox_magn_fields.setEnabled(True)
            self.ui.lineEdit_dtm_path.setEnabled(True)
            self.ui.pushButton_select_dtm_path.setEnabled(True)
            self.ui.groupBox_mesh_params.setEnabled(True)
            self.ui.lineEdit_output_directory_path.setEnabled(True)
            self.ui.lineEdit_output_directory_path_select.setEnabled(True)
            self.ui.lineEdit_ROI_path_select.setEnabled(True)

        self.ui.doubleSpinBox_coreDepth.setEnabled(True)
        self.ui.doubleSpinBox_fullDepth.setEnabled(True)
        self.ui.mQgsDoubleSpinBox_compression_ratio.setEnabled(True)

    # ------------------------------------------------------------------
    def update_mag_field(self):
        from pyproj import Transformer
        self.magn_SurveyHeight = self.ui.doubleSpinBox_magn_sensor_height.value()
        date_text = str(self.ui.dateEdit.date().toPyDate())
        date_split = date_text.split("-")
        self.magn_SurveyDay = date_split[2]
        self.magn_SurveyMonth = date_split[1]
        self.magn_SurveyYear = date_split[0]
        date = datetime(
            int(self.magn_SurveyYear),
            int(self.magn_SurveyMonth),
            int(self.magn_SurveyDay),
        )

        midx = self.meshBox["west"] + (
            (self.meshBox["east"] - self.meshBox["west"]) / 2.0
        )
        midy = self.meshBox["south"] + (
            (self.meshBox["north"] - self.meshBox["south"]) / 2.0
        )

        transformer = Transformer.from_crs(
            self.magn_proj_out, "EPSG:4326", always_xy=True
        )
        long, lat = transformer.transform(midx, midy)

        Be, Bn, Bu = igrf(long, lat, self.magn_SurveyHeight, date)
        (
            self.forward_magneticField_inclination,
            self.forward_magneticField_declination,
        ) = get_inclination_declination(Be, Bn, Bu, degrees=True)
        self.forward_magneticField_intensity = np.sqrt(Be**2 + Bn**2 + Bu**2)

        self.ui.doubleSpinBox_mag_dec.setValue(
            self.forward_magneticField_declination.item()
        )
        self.ui.doubleSpinBox_mag_inc.setValue(
            self.forward_magneticField_inclination.item()
        )
        self.ui.doubleSpinBox_mag_int.setValue(
            self.forward_magneticField_intensity.item()
        )

    # ------------------------------------------------------------------
    def load_csv_vector_grav(self, data_file_path, xcol_grav, ycol_grav, datacol_grav):
        from pyproj import Transformer
        try:
            df = pd.read_csv(data_file_path)
            transformer = Transformer.from_crs(
                self.grav_proj_in, self.grav_proj_out, always_xy=True
            )
            xs, ys = transformer.transform(
                df[xcol_grav].values, df[ycol_grav].values
            )
            self.nData = len(df)
            self.data_extents(
                float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))
            )
        except Exception as e:
            self.show_message(f"Could not load grav data: {e}", level="warning")

    def load_csv_vector_magn(self, data_file_path, xcol, ycol, datacol_magn):
        from pyproj import Transformer
        try:
            df = pd.read_csv(data_file_path)
            transformer = Transformer.from_crs(
                self.magn_proj_in, self.magn_proj_out, always_xy=True
            )
            xs, ys = transformer.transform(df[xcol].values, df[ycol].values)
            self.nData = len(df)
            self.data_extents(
                float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))
            )
        except Exception as e:
            self.show_message(f"Could not load magn data: {e}", level="warning")

    # ------------------------------------------------------------------
    def load_dtm(self):
        if self.global_experimentType in (1, 3):
            proj_in = self.grav_proj_in
            proj_out = self.grav_proj_out
        else:
            proj_in = self.magn_proj_in
            proj_out = self.magn_proj_out

        reproj_path = os.path.join(tempfile.gettempdir(), "tomofast_dtm_reproj.tif")
        src_ds = gdal.Open(self.dtm_filename)
        if src_ds is None:
            self.show_message(
                f"Cannot open DTM: {self.dtm_filename}", level="warning"
            )
            return
        warp_options = gdal.WarpOptions(
            srcSRS=proj_in,
            dstSRS=proj_out,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )
        out_ds = gdal.Warp(reproj_path, src_ds, options=warp_options)
        if out_ds is None:
            self.show_message("gdal.Warp failed for DTM", level="warning")
            src_ds = None
            return
        self.dtm_array = out_ds.ReadAsArray()
        out_ds = None
        src_ds = None
        self.dtm_raster_path = reproj_path
        self._record_pending(reproj_path)

    # ------------------------------------------------------------------
    def add_dtm(self, dataType):
        if dataType == 1:
            data_column = self.datacol_grav
            reprojFileName = "/reproj_data_grav.csv"
        else:
            data_column = self.datacol_magn
            reprojFileName = "/reproj_data_magn.csv"

        if self.global_dataType == "points":
            df = pd.DataFrame(self.data2tomofast.df)
            xs = df["POINT_X"].values
            ys = df["POINT_Y"].values
            elevations = self._sample_raster_at_points(self.dtm_raster_path, xs, ys)
            if data_column in df.columns:
                data_vals = df[data_column].values
            else:
                data_vals = df.iloc[:, 2].values
            data_df = pd.DataFrame({
                "POINT_X": xs,
                "POINT_Y": ys,
                "POINT_Z": elevations,
                "data1": data_vals,
            })
        else:
            csv_path = self.global_outputFolderPath + reprojFileName
            df = pd.read_csv(csv_path)
            if self.is_2d and self.profile_line_pts:
                xs = df["x_world"].values
                ys = df["y_world"].values
            else:
                xs = df["POINT_X"].values
                ys = df["POINT_Y"].values
            elevations = self._sample_raster_at_points(self.dtm_raster_path, xs, ys)
            data_df = pd.DataFrame({
                "POINT_X": df["POINT_X"].values,
                "POINT_Y": df["POINT_Y"].values,
                "POINT_Z": elevations,
                "data1": df["data1"].values,
            })

        self.data_df = data_df.copy(deep=True)

    # ------------------------------------------------------------------
    def add_elevation(self, elevation, elevType, df_elev):
        if elevType == 1:
            self.data2tomofast.df["POINT_Z"] = (
                np.zeros(self.data2tomofast.df["POINT_X"].values.shape) - elevation
            )
        else:
            self.data2tomofast.df["POINT_Z"] = (
                -df_elev["POINT_Z"] - elevation
            )

    # ------------------------------------------------------------------
    def load_ROI(self):
        from tkinter import filedialog
        self.ROIFileName, _ = filedialog.askopenfilename(
            title="Select ROI File",
            filetypes=[("SHP", "*.shp")],
        ), None
        # askopenfilename returns a string, not a tuple
        if isinstance(self.ROIFileName, tuple):
            self.ROIFileName = self.ROIFileName[0]
        self.ui.lineEdit_ROI_path.setText(self.ROIFileName)
        if self.ROIFileName and os.path.exists(self.ROIFileName):
            self._load_ROI_file(self.ROIFileName)

    def _load_ROI_file(self, roi_filename):
        from pyproj import Transformer
        proj = (
            self.grav_proj_out
            if self.global_experimentType in (1, 3)
            else self.magn_proj_out
        )
        ds = ogr.Open(roi_filename)
        if ds is None:
            return
        lyr = ds.GetLayer()
        src_srs = lyr.GetSpatialRef()
        src_proj = src_srs.ExportToProj4() if src_srs else proj
        try:
            transformer = Transformer.from_crs(src_proj, proj, always_xy=True)
        except Exception:
            transformer = None

        features = list(lyr)
        ds = None
        if not features:
            return

        feat = features[0]
        geom = feat.GetGeometryRef()
        geom_type = geom.GetGeometryType()

        if geom_type in (ogr.wkbLineString, ogr.wkbLineString25D):
            pts_raw = [
                (geom.GetX(i), geom.GetY(i)) for i in range(geom.GetPointCount())
            ]
            if len(pts_raw) != 2:
                self.show_message(
                    "2D profile must be a straight line with exactly 2 nodes",
                    level="warning",
                )
                return
            if transformer:
                xs_out, ys_out = transformer.transform(
                    [p[0] for p in pts_raw], [p[1] for p in pts_raw]
                )
            else:
                xs_out = [p[0] for p in pts_raw]
                ys_out = [p[1] for p in pts_raw]
            self.is_2d = True
            self.profile_line_pts = [
                (xs_out[0], ys_out[0]),
                (xs_out[1], ys_out[1]),
            ]
            for w in (
                self.ui.mQgsSpinBox_mesh_south,
                self.ui.mQgsSpinBox_mesh_west,
                self.ui.mQgsSpinBox_mesh_north,
                self.ui.mQgsSpinBox_mesh_east,
            ):
                w.setEnabled(False)
            self.show_message(
                "2D profile mode: mesh will be oriented along the profile line"
            )
        else:
            self.is_2d = False
            self.profile_line_pts = None
            env = geom.GetEnvelope()  # (xmin, xmax, ymin, ymax)
            if transformer:
                xs_out, ys_out = transformer.transform(
                    [env[0], env[1]], [env[2], env[3]]
                )
            else:
                xs_out = [env[0], env[1]]
                ys_out = [env[2], env[3]]
            self.data_extents(
                min(xs_out), min(ys_out), max(xs_out), max(ys_out)
            )
            for w in (
                self.ui.mQgsSpinBox_mesh_south,
                self.ui.mQgsSpinBox_mesh_west,
                self.ui.mQgsSpinBox_mesh_north,
                self.ui.mQgsSpinBox_mesh_east,
            ):
                w.setEnabled(True)

        self._record_pending(roi_filename)