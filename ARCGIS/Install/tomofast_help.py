# -*- coding: utf-8 -*-
"""Tooltips and the Run tab help text for the ArcGIS Pro panel.

Copied from the QGIS plugin (Tomofast_x.py define_tips and the Run Inversion
help block in ui_dockwidget_generated.py) so both versions describe parameters
the same way; the parfile name of each parameter is in square brackets.
Keys are the widget attribute names on TomofastUI.
"""

TOOLTIPS = {
    'checkBox_read_sens_matrix': (
        'Load previously calculated sensistivity matrix\n'
        '\n'
        '[forward.sensit.readFromFiles]'
    ),
    'checkBox_use_compression': (
        'Use wavelet compression to speed calculations and reduce memory demands of inversion\n'
        '\n'
        '[forward.matrixCompression.type]'
    ),
    'comboBox_grav_field_x': (
        'Define column in csv file that contains Longitude/Easting information'
    ),
    'comboBox_grav_field_y': (
        'Define column in csv file that contains Latitude/Northing information'
    ),
    'comboBox_grav_field_data': (
        'Column in the csv file that contains the gravity data.\n'
        '\n'
        "With several components this is the FIRST component's column, and the\n"
        'following columns of the file are the other components, in file order:\n'
        '  1 component (gravity, or gradiometry Gz/Gzz): this column only.\n'
        '  6 components (gradiometry tensor): this column is xx, and the next five\n'
        '  columns must be yy, zz, xy, yz, xz in that order.\n'
        '\n'
        'Not used for GeoTIFF input (see the Load Grav button).'
    ),
    'label_grav_field_data_col': (
        'Column in the csv file that contains the gravity data.\n'
        '\n'
        "With several components this is the FIRST component's column, and the\n"
        'following columns of the file are the other components, in file order:\n'
        '  1 component (gravity, or gradiometry Gz/Gzz): this column only.\n'
        '  6 components (gradiometry tensor): this column is xx, and the next five\n'
        '  columns must be yy, zz, xy, yz, xz in that order.\n'
        '\n'
        'Not used for GeoTIFF input (see the Load Grav button).'
    ),
    'comboBox_magn_field_data': (
        'Column in the csv file that contains the magnetic data.\n'
        '\n'
        "With several components this is the FIRST component's column, and the\n"
        'following columns of the file are the other components, in file order:\n'
        '  TMI (1 component): this column only.\n'
        '  Bx,By,Bz (3 components): this column is Bx, and the next two columns\n'
        '  must be By and Bz in that order.\n'
        '\n'
        'Not used for GeoTIFF input (see the Load Mag button).'
    ),
    'label_magn_field_data_col': (
        'Column in the csv file that contains the magnetic data.\n'
        '\n'
        "With several components this is the FIRST component's column, and the\n"
        'following columns of the file are the other components, in file order:\n'
        '  TMI (1 component): this column only.\n'
        '  Bx,By,Bz (3 components): this column is Bx, and the next two columns\n'
        '  must be By and Bz in that order.\n'
        '\n'
        'Not used for GeoTIFF input (see the Load Mag button).'
    ),
    'comboBox_grav_type': (
        'Type of gravity data.\n'
        'Gravity: gravity data.\n'
        'Gradiometry: gravity gradient data (Eotvos). The depth weighting power is\n'
        'set to 3 and the default target misfit changes to suit Eotvos units.\n'
        '\n'
        '[forward.data.grav.type]'
    ),
    'comboBox_grav_ncomp': (
        'Number of gradiometry data components.\n'
        '1 component: Gz/Gzz only.\n'
        '6 components: full tensor in the order xx, yy, zz, xy, yz, xz.\n'
        'Fixed at 1 for plain gravity data.\n'
        '\n'
        '[forward.data.grav.nDataComponents]'
    ),
    'comboBox_magn_ncomp': (
        'Type of magnetic data.\n'
        'TMI data: total magnetic intensity (1 component).\n'
        'Bx,By,Bz data: three-component magnetic field data.\n'
        '\n'
        '[forward.data.magn.nDataComponents]'
    ),
    'comboBox_magn_nmodel': (
        'Type of magnetic model.\n'
        'Scalar model: one susceptibility per cell.\n'
        'Vector (MVI): magnetisation vector inversion, solving for (Mx, My, Mz) in\n'
        'every cell. The sensitivity matrix and run time grow about three times.\n'
        '\n'
        '[modelGrid.magn.nModelComponents]'
    ),
    'comboBox_magn_field_x': (
        'Define column in csv file that contains Longitude/Easting information'
    ),
    'comboBox_magn_field_y': (
        'Define column in csv file that contains Latitude/Northing information'
    ),
    'groupBox_magn_fields': (
        'Define column in csv file that contains Magnetic information'
    ),
    'lineEdit_grav_ADMM_weight': (
        'Define weighting of ADMM constraint\n'
        '\n'
        '[inversion.admm.grav.weight]'
    ),
    'lineEdit_magn_ADMM_weight': (
        'Define weighting of ADMM constraint\n'
        '\n'
        '[inversion.admm.magn.weight]'
    ),
    'mQgsDoubleSpinBox_grav_mmodel_damping_weight': (
        'Define weight of gravity model damping term (m - m_prior)\n'
        '\n'
        '[inversion.modelDamping.grav.weight]'
    ),
    'mQgsDoubleSpinBox_compression_ratio': (
        'Amount of wavelet compression [smaller value means more compression]\n'
        'Automatically set to provide 1% error but value can be manually overidden\n'
        '\n'
        '[forward.matrixCompression.rate]'
    ),
    'mQgsDoubleSpinBox_grav_model_multiplier': (
        'Multiplier for scaling of output models\n'
        '\n'
        '[global.grav_modelUnitsMultiplier]'
    ),
    'lineEdit_grav_data_multiplier': (
        'Multiplier for input gravity data to convert it to SI units\n'
        '\n'
        '[global.grav_dataUnitsMultiplier]'
    ),
    'mQgsDoubleSpinBox_grav_mmodel_norm_power': (
        'Define power exponent of gravity model damping term\n'
        '\n'
        '[inversion.modelDamping.normPower]'
    ),
    'mQgsDoubleSpinBox_magn_model_multiplier': (
        'Multiplier for scaling of output models\n'
        '\n'
        '[global.magn_modelUnitsMultiplier]'
    ),
    'lineEdit_magn_data_multiplier': (
        'Multiplier for input magnetic data to convert it to SI units\n'
        '\n'
        '[global.magn_dataUnitsMultiplier]'
    ),
    'mQgsDoubleSpinBox_grav_weight': (
        'Relative weighting of gravity data for joint inversion\n'
        '\n'
        '[inversion.joint.grav.problemWeight]'
    ),
    'mQgsDoubleSpinBox_magn_weight': (
        'Relative weighting of magnetic data for joint inversion\n'
        '\n'
        '[inversion.joint.magn.problemWeight]'
    ),
    'mQgsDoubleSpinBox_magn_model_norm_power': (
        'Define power exponent of magnetic model damping term\n'
        '\n'
        '[inversion.modelDamping.normPower]'
    ),
    'mQgsDoubleSpinBox_magn_model_weight': (
        'Define weight of magnetic model damping term (m - m_prior)\n'
        '\n'
        '[inversion.modelDamping.magn.weight]'
    ),
    'label_grav_input_crs': (
        'Define input gravity data projection system [EPSG:4326]\n'
        '\n'
        '[anomalies.grav.proj.in]'
    ),
    'label_grav_output_crs': (
        'Define processed gravity data projection system [EPSG:4326]\n'
        '\n'
        '[anomalies.grav.proj.out]'
    ),
    'label_magn_input_crs': (
        'Define input magnetic data projection system [EPSG:4326]\n'
        '\n'
        '[anomalies.magn.proj.in]'
    ),
    'label_magn_output_crs': (
        'Define processed magnetic data projection system [EPSG:4326]\n'
        '\n'
        '[anomalies.magn.proj.out]'
    ),
    'mQgsSpinBox_mesh_south': (
        'Define minimum Northing value for model grid (not taking into account the padding)\n'
        '\n'
        '[#mesh.south]'
    ),
    'mQgsSpinBox_mesh_east': (
        'Define minimum Easting value for model grid (not taking into account the padding)\n'
        '\n'
        '[#mesh.east]'
    ),
    'mQgsSpinBox_mesh_west': (
        'Define maximum Easting value for model grid (not taking into account the padding)\n'
        '\n'
        '[#mesh.west]'
    ),
    'mQgsSpinBox_mesh_north': (
        'Define maximum Northing value for model grid (not taking into account the padding)\n'
        '\n'
        '[#mesh.north]'
    ),
    'mQgsSpinBox_mesh_size_x': (
        'Define model grid x cell dimension\n'
        '\n'
        '[#mesh.cellx]'
    ),
    'mQgsSpinBox_mesh_size_y': (
        'Define model grid x cell dimension\n'
        '\n'
        '[#mesh.celly]'
    ),
    'textEdit_z_cell_size_list': (
        'Define model grid z cell size as comma separated list of cell z values for each layer thicknesses in the adjacent list\n'
        '\n'
        'e.g. 50,100,200\n'
        '\n'
        'Leave blank to use core/full depth system[#mesh.cellz_z_list]'
    ),
    'textEdit_z_layer_thickness_list': (
        'Define model grid layer thicknesses as comma separated list of thickness of layers for each z cell size in the adjacent list\n'
        '\n'
        'e.g. 200,400,800 \n'
        '\n'
        'Leave blank to use core/full depth system[#mesh.cellz_z_thickness_list]'
    ),
    'mQgsSpinBox_mesh_padding': (
        'Define uniform padding distance around model\n'
        '\n'
        'Set automatically to the model depth (sum of the z layer thicknesses, or the full depth) when those change, but can be edited afterwards\n'
        '\n'
        '[#mesh.padding]'
    ),
    'nx_label': (
        'Number of model grid cells in the x direction (this will be calculated from the cell dimensions and model extents)\n'
        '\n'
        '[modelGrid.size]'
    ),
    'ny_label': (
        'Number of model grid cells in the y direction (this will be calculated from the cell dimensions and model extents)\n'
        '\n'
        '[modelGrid.size]'
    ),
    'nz_label': (
        'Number of model grid cells in the z direction (this will be calculated from the cell dimensions and model extents)\n'
        '\n'
        '[modelGrid.size]'
    ),
    'memory_label': (
        'Estimate of the memory required in GB to run the inversion, based on: 8 * nx * ny * nz * ndata * compression'
    ),
    'mQgsSpinBox_major_iters': (
        'Number of major iterations of inversion to run, unless minimum residual value if data error is reached\n'
        '\n'
        '[inversion.nMajorIterations]'
    ),
    'mQgsSpinBox_minor_iters': (
        'Number of minor iterations of inversion to run per major iteration\n'
        '\n'
        '[inversion.nMinorIterations]'
    ),
    'mQgsSpinBox_model_save_iters': (
        'spacing between major iterations to save model outputs (0 means only save final model)\n'
        '\n'
        '[inversion.writeModelEveryNiter]'
    ),
    'lineEdit_output_directory_path_select': (
        'Select or create directory that will store all data, model grid and parfiles, then process data, dtm and model grid files\n'
        '\n'
        '[global.outputFolderPath]'
    ),
    'pushButton_select_dtm_path': (
        'Load TIF format Digital Terrane Model\n'
        '\n'
        '[global.elevFilename]'
    ),
    'pushButton_param_load_path': (
        'Optional: Load existing parfile as the basis for updating an experiment'
    ),
    'pushButton_assign_magn_fields': (
        'Assign x,y,data fields defined above'
    ),
    'pushButton_load_grav_data': (
        'Load gravity data as a map layer\n'
        '\n'
        '[anomalies.grav.data.file]\n'
        '\n'
        'GeoTIFF naming for the number of components chosen alongside\n'
        '(for csv files see the Data tooltip):\n'
        '1 component: one file, any name.\n'
        '6 components (xx, yy, zz, xy, yz, xz): six files in the same folder, on\n'
        'the same grid, with names identical except for the tag xx, yy, zz, xy,\n'
        'yz or xz (any case, set off by _ - or .), e.g. gg_xx.tif ... gg_xz.tif.\n'
        'Select any one of them; the others are found automatically.'
    ),
    'pushButton_load_magn_data': (
        'Load magnetic data as a map layer\n'
        '\n'
        '[anomalies.magn.data_file]\n'
        '\n'
        'GeoTIFF naming for the type of data chosen alongside\n'
        '(for csv files see the Data tooltip):\n'
        'TMI data: one file, any name.\n'
        'Bx,By,Bz data: three files in the same folder, on the same grid, with\n'
        'names identical except for the tag Bx, By or Bz (any case, set off by\n'
        '_ - or .), e.g. mag_Bx.tif, mag_By.tif, mag_Bz.tif.\n'
        'Select any one of them; the others are found automatically.'
    ),
    'pushButton_grav_data_path': (
        'Select a gravity dataset in csv, tif or ers format\n'
        '\n'
        '[anomalies.grav.data.file]'
    ),
    'pushButton_magn_data_path': (
        'Select a magnetic dataset in csv, tif or ers format\n'
        '\n'
        '[anomalies.magn.data_file]'
    ),
    'pushButton_assign_grav_fields': (
        'Assign x,y,data fields defined above'
    ),
    'radioButton_grav_inv': (
        'Define parameters for gravity inversion experiment'
    ),
    'radioButton_magn_inv': (
        'Define parameters for magnetic inversion experiment'
    ),
    'radioButton_joint_inv': (
        'Define parameters for joint gravity-magnetic inversion experiment'
    ),
    'spinBox_grav_number_ADMM_litho': (
        'Number of distinct pairs of ADMM density upper and lower bounds\n'
        '\n'
        '[inversion.admm.grav.nLithologies]'
    ),
    'spinBox_magn_ADMM_number_litho': (
        'Number of distinct pairs of ADMM magnetic susceptibility upper and lower bounds\n'
        '\n'
        '[inversion.admm.magn.nLithologies]'
    ),
    'textEdit_experiment_description': (
        'Provide free-form metadata for experiment\n'
        '\n'
        '[global.description]'
    ),
    'textEdit_grav_ADMM_bounds': (
        'Space separated pairs of upper and lower ADMM density bounds\n'
        '\n'
        '[inversion.admm.grav.bounds]'
    ),
    'textEdit_min_residual': (
        'Residual data error threshold before inversion stops\n'
        '\n'
        '[inversion.minResidual]'
    ),
    'textEdit_5_magn_ADMM_bounds': (
        'Space separated pairs of upper and lower ADMM magnetic susceptibility bounds\n'
        '\n'
        '[inversion.admm.magn.bounds]'
    ),
    'doubleSpinBox_magn_sensor_height': (
        'Height of mag sensor above DTM, assumes draped survey at const height\n'
        '\n'
        '[global.magn_sensor_height]'
    ),
    'doubleSpinBox_grav_sensor_height': (
        'Height of grav sensor above DTM, assumes draped survey at const height\n'
        '\n'
        '[global.grav_sensor_height]'
    ),
    'dateEdit': (
        'Date of Mag Survey, used for auto IGRF calculation'
    ),
    'lineEdit_ROI_path_select': (
        'Load a shapefile to define x,y limts of Mesh (converts max/min extents of shape into a rectangle)'
    ),
    'pushButton_calc_IGRF': (
        'Generates estimated Magnetic Field parameters based on height of sensor, date of survey and centroid of Mesh\n'
        '\n'
        '[]'
    ),
    'doubleSpinBox_mag_dec': (
        'Manual overide of Magnetic Declination\n'
        '\n'
        '[forward.magneticField.declination]'
    ),
    'doubleSpinBox_mag_inc': (
        'Manual overide of Magnetic Inclination\n'
        '\n'
        '[forward.magneticField.inclination]'
    ),
    'doubleSpinBox_mag_int': (
        'Manual overide of Magnetic Intensity\n'
        '\n'
        '[forward.magneticField.intensity]'
    ),
    'pushButton_select_tomoPath': (
        "Select path to tomofast executable, e.g. '/opt/homebrew/bin/tomofastx'"
    ),
    'pushButton_2_select_parfilePath': (
        'Select a parfile to run the inversion (prefilled with the parfile created by this plugin)'
    ),
    'pushButton_select_mpirun_mipexec': (
        'Path to mpirun executable, if not in PATH, \n'
        " e.g. for MacOS '/opt/homebrew/bin/mpirun' (not needed on Windows)"
    ),
    'lineEdit_pre_command_2_WSL_Distro': (
        "Name of WSL Distro to run the inversion in, e.g. 'Ubuntu-20.04' (Windows WSL only)\n"
        'It will be the element after \\wsl.localhost\\ in a windows path to the WSL disk'
    ),
    'mQgsSpinBox_noProc': (
        'Number of processors to use for inversion (If more than 1 requires openmpi to be installed)'
    ),
    'pushButton_3_runInversion': (
        'Run the inversion using the parameters defined in the parfile'
    ),
    'pushButton_3_visualise': (
        'Visualise X-Y-Z slices of output model\n'
        'Requires pyvista to be installed in the ArcGIS Pro Python environment'
    ),
    'pushButton_kernel_path_select': (
        'Select path to directory containing prior sensitivity kernel to reuse\n'
        '\n'
        '[sensit.folderPath]'
    ),
    'pushButton_3_Export': (
        'Export 3D model as csv file'
    ),
}

HELP_TEXT = (
    'The native windows version of tomofast-x can be downloaded from\n'
    '\n'
    'https://tectonique.net/tomofast-x-q/OpenMP_version/tomofastx_win.zip\n'
    '\n'
    'simply unzip and store in a permanent location on your drive.\n'
    '\n'
    'If you have direct access to tomofast-x on your own machine, you can run the inversion in the background by defining the path to the tomofast executable and parfile above (the Command text, which can be left as is, and the WSL Distro, which should be the one you use, are required for running tomofast-x on WSL under Windows, but can be ignore for other OS including Windows Native).\n'
    '\n'
    'Otherwise:\n'
    '\n'
    '1) Before you attempt to run the inversion, check the estimated memory requirements in the Global Parameters tab (in the Matrix Compression area). \n'
    '\n'
    '2) Tomofast source code and installation instructions available here:\n'
    '\n'
    'https://github.com/TOMOFAST/Tomofast-x/\n'
    '\n'
    '3) Once you have saved the parameter file in the previous tab, you can copy the entire directory that contains the parfile to your machine but then you will need to update the paths in the paramfile to match the new machine,  with tomofast-x installed and from the tomofast-x directory you can run the inversion by entering either of the following lines on the command line:\n'
    '\n'
    'a) For single node calculations type:\n'
    '\n'
    './tomofastx -p <Parfile path>\n'
    '\n'
    'b) For multiprocessor calculations type:\n'
    '\n'
    'mpirun -np <Number-of-cores> ./tomofastx -j <Parfile path>\n'
    '\n'
    '4) If the code runs successfully you will see in the end of the screen log the messages "Writing the full model...", and "THE END". \n'
    '\n'
    'To visualize the final model, open in Paraview the file Paraview/grav_final_model3D_full.vtk or Paraview/mag_final_model3D_full.vtk, located in the output folder. '
)
