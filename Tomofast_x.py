# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Tomofast_x
                                 A QGIS plugin
 Supprts Tomofast-x geophysical inversion code
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-04-03
        git sha              : $Format:%H$
        copyright            : (C) 2024 by uwa.edu.au
        email                : mark.jessell@uwa.edu.au
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,QFileInfo,QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,QFileDialog
from qgis.core import QgsMapLayerProxyModel,QgsCoordinateReferenceSystem,QgsVectorLayer,QgsProject,QgsRasterLayer,QgsFeature,QgsField,QgsVectorFileWriter,QgsPoint
#from PyQt4.QtCore import QFileInfo
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Tomofast_x_dialog import Tomofast_xDialog
import os.path
# import functions from scripts
from .Data2Tomofast import Data2Tomofast   
import numpy as np
import pandas as pd
from osgeo import gdal
import processing

class Tomofast_x:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Tomofast_x_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Tomofast-x')




        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Tomofast_x', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Tomofast_x/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Tomofast-x'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Tomofast-x'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_data_file(self):
        self.filename, _filter = QFileDialog.getOpenFileName(None, "Select Data File",".", "CSV (*.csv)")
        
        self.dlg.lineEdit_12.setText(self.filename)

    def select_dtm(self):
        self.dtm_filename, _filter = QFileDialog.getOpenFileName(None, "Select DTM File", ".", "TIFF (*.tif)")
        
        self.dlg.lineEdit_13.setText(self.dtm_filename)

    def confirm_data_file(self):
        self.process_data_file()
        self.proj_in=self.dlg.mQgsProjectionSelectionWidget_3.crs().authid()
        self.proj_out=self.dlg.mQgsProjectionSelectionWidget_5.crs().authid()




        #enable GroupBox 4
        self.dlg.groupBox_9.setEnabled(True)
        self.dlg.label_44.setEnabled(True)
        self.dlg.label_45.setEnabled(True)
        self.dlg.label_47.setEnabled(True)
        self.dlg.comboBox_2.setEnabled(True)
        self.dlg.comboBox_3.setEnabled(True)
        self.dlg.comboBox_4.setEnabled(True)
        self.dlg.pushButton_9.setEnabled(True)


    
    def confirm_data_fields(self):
        self.process_data_file()
        self.xcol=self.dlg.comboBox_2.currentText()
        self.ycol=self.dlg.comboBox_3.currentText()
        self.datacol=self.dlg.comboBox_4.currentText()
        
        #enable GroupBox 2
        self.dlg.groupBox_2.setEnabled(True)
        self.dlg.label_20.setEnabled(True)
        self.dlg.lineEdit_13.setEnabled(True)
        self.dlg.pushButton_3.setEnabled(True)
        self.dlg.pushButton_12.setEnabled(True)

        #enable GroupBox 3
        self.dlg.groupBox_3.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_2.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_3.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_4.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_5.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_6.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_7.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_8.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_9.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_10.setEnabled(True)
        self.dlg.mQgsDoubleSpinBox_11.setEnabled(True)
        self.dlg.spinBox.setEnabled(True)
        self.dlg.lineEdit_17.setEnabled(True)
        #self.dlg.pushButton_14.setEnabled(True)
        self.dlg.pushButton_10.setEnabled(True)

        self.load_csv_vector()

    def load_csv_vector(self):
        fileInfo = QFileInfo(self.filename)    
        baseName = fileInfo.baseName()
        layer = QgsVectorLayer('file:///'+self.filename+'?crs={}&xField={}&yField={}'.format(self.proj_in,self.xcol,self.ycol),baseName, 'delimitedtext') 
        
        if layer.isValid():
            parameter = {
                'INPUT': layer,
                'TARGET_CRS': self.proj_out,
                'OUTPUT': 'memory:{}_Reprojected'.format(baseName)
            }
            result = processing.run('native:reprojectlayer', parameter)['OUTPUT']
            crs = layer.crs()
            crs.createFromId(int(self.proj_out.split(':')[1]))
            result.setCrs(crs)
            result.renderer().symbol().setSize(1)
            QgsProject.instance().addMapLayer(result)
            # Refresh the layer to reflect the changes
            result.triggerRepaint()

        else:
            print("invalid layer",'file:///'+self.filename+'?&yField={}&xField={}'.format(self.xcol,self.ycol))
    
    def rearrange( self ):
        from collections import OrderedDict
        root = QgsProject.instance().layerTreeRoot()
        LayerNamesEnumDict=lambda listCh:{listCh[q[0]].name()+str(q[0]):q[1]
                                        for q in enumerate(listCh)}

        mLNED = LayerNamesEnumDict(root.children())
        mLNEDkeys = OrderedDict(sorted(LayerNamesEnumDict(root.children()).items())).keys()

        mLNEDsorted = [mLNED[k].clone() for k in mLNEDkeys]
        root.insertChildNodes(0,mLNEDsorted)
        for n in mLNED.values():
            root.removeChildNode(n)

    def load_mesh_vector(self):
        df=pd.read_csv(self.directoryname+"/model_grid.txt",sep=' ',skiprows=1,header=None,nrows=self.data2tomofast.nx*self.data2tomofast.ny)    
        print(df)
        df=df.drop(axis=1,columns=[1,3,4,5,6,7,8,9])
        temp = QgsVectorLayer("Point","model_grid","memory")
        temp_data = temp.dataProvider()
        # Start of the edition 
        temp.startEditing()

        # Creation of my fields 
        for head in df : 
            myField = QgsField( str(head), QVariant.Double )
            temp.addAttribute(myField)
        # Update     
        temp.updateFields()

        # Addition of features
        # [1] because i don't want the indexes 
        for row in df.itertuples():
            f = QgsFeature()
            f.setAttributes([row[1],row[2]])
            f.setGeometry(QgsPoint(row[1],row[2]))
            temp.addFeature(f)
            #print(row)
        # saving changes and adding the layer
        temp.commitChanges()
        crs = QgsCoordinateReferenceSystem(self.proj_out)
        temp.setCrs(crs)
        temp.renderer().symbol().setSize(0.25)

        temp.commitChanges()

        QgsProject.instance().addMapLayer(temp)
        self.sample_elevation()

        '''layer = QgsProject.instance().mapLayersByName("model_grid")[0]
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.layerName = 'model_grid'
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        QgsVectorFileWriter.writeAsVectorFormatV3(layer,self.directoryname+'/mesh_grid.shp',QgsProject.instance().transformContext(), options)
        '''

    def sample_elevation(self):
        mesh = QgsProject.instance().mapLayersByName("model_grid")[0]
        dtm  = QgsProject.instance().mapLayersByName("Reprojected DTM")[0]
        parameter={'INPUT':mesh,
                    'RASTERCOPY':dtm,
                    'COLUMN_PREFIX':'elevation',
                    'OUTPUT':'TEMPORARY_OUTPUT'
        }
        processing.runAndLoadResults("native:rastersampling", parameter)

        elev = QgsProject.instance().mapLayersByName("Sampled")[0]
        elev.setName('elevation_grid')
        elev.renderer().symbol().setSize(.25)

        self.rename_dp_field(elev,'0','x')
        self.rename_dp_field(elev,'2','y')
        self.rename_dp_field(elev,'elevation1','elevation')

        QgsVectorFileWriter.writeAsVectorFormat(elev,
        self.directoryname+'/elevation_grid.csv',
        "utf-8",driverName = "CSV" )

    def rename_dp_field(self,rlayer, oldname, newname):
        findex = rlayer.dataProvider().fieldNameIndex(oldname)
        if findex != -1:
            rlayer.dataProvider().renameAttributes({findex: newname})
            rlayer.updateFields()

    def load_dtm(self):
        fileInfo = QFileInfo(self.dtm_filename)    
        baseName = fileInfo.baseName()
        layer = QgsRasterLayer(self.dtm_filename, baseName)
       
        if layer.isValid():

            import processing

            parameter={'INPUT':self.dtm_filename,
            'SOURCE_CRS':QgsCoordinateReferenceSystem(self.proj_in),
            'TARGET_CRS':QgsCoordinateReferenceSystem(self.proj_out),
            'RESAMPLING':0,
            'NODATA':None,
            'TARGET_RESOLUTION':None,
            'OPTIONS':'',
            'DATA_TYPE':0,
            'TARGET_EXTENT':None,
            'TARGET_EXTENT_CRS':None,
            'MULTITHREADING':False,
            'EXTRA':'',
            'OUTPUT':'TEMPORARY_OUTPUT'}

            result=processing.runAndLoadResults("gdal:warpreproject", parameter)

            temppath=result['OUTPUT']
            gd = gdal.Open(temppath)
            self.dtm_array = gd.ReadAsArray()
            print('array shape',self.dtm_array.shape)
            layers = QgsProject.instance().mapLayersByName('Reprojected')
            layers[0].setName('Reprojected DTM')
            self.rearrange()
        else:
            print("invalid layer",'file:///'+self.dtm_filename,baseName)
        


    def process_data_file(self):
        import os
        import pandas as pd
        self.filename=self.dlg.lineEdit_12.text()
        paths=os.path.split(self.filename)
        suffix=paths[1].split('.')[-1]

        if(suffix=='csv'):
            self.data=pd.read_csv(self.filename)

            self.dlg.comboBox_2.addItems(self.data.columns)
            self.dlg.comboBox_3.addItems(self.data.columns)
            self.dlg.comboBox_4.addItems(self.data.columns)
            self.input_data=self.filename

    def select_ouput_directory(self):      
        self.directoryname = QFileDialog.getExistingDirectory(None, "Select output path for your Tomofgast-x input files")
        
        self.dlg.lineEdit_17.setText(self.directoryname)
        if(self.directoryname):
            self.dlg.pushButton_14.setEnabled(True)

    
    def select_sensitivity_directory(self):      
        self.sensitivitydirectoryname = QFileDialog.getExistingDirectory(None, "Select output path for your Tomofgast-x sensitvity matrices")
        
        self.dlg.lineEdit_20.setText(self.sensitivitydirectoryname)


    def save_outputs(self):   
        self.cell_x=self.dlg.mQgsDoubleSpinBox.value()
        self.cell_y=self.dlg.mQgsDoubleSpinBox_2.value()
        self.padding=self.dlg.mQgsDoubleSpinBox_3.value()
        self.z_layers=self.dlg.spinBox.value()
        self.z_layer1_base=int(self.dlg.mQgsDoubleSpinBox_4.value())
        self.z_layer1_size=int(self.dlg.mQgsDoubleSpinBox_5.value())
        self.z_layer2_base=self.dlg.mQgsDoubleSpinBox_7.value()
        self.z_layer2_size=self.dlg.mQgsDoubleSpinBox_6.value()
        self.z_layer3_base=self.dlg.mQgsDoubleSpinBox_8.value()
        self.z_layer3_size=self.dlg.mQgsDoubleSpinBox_9.value()
        self.z_layer4_base=self.dlg.mQgsDoubleSpinBox_10.value()
        self.z_layer4_size=self.dlg.mQgsDoubleSpinBox_11.value()
        self.elevation=0
        self.dz = np.zeros(self.z_layer1_base)
        self.dz[0:self.z_layer1_base]  = self.z_layer1_size
        self.data2tomofast = Data2Tomofast(None)
        self.data2tomofast.read_data(self.filename, self.ycol, self.xcol, self.datacol, self.proj_in, self.proj_out)
        self.data2tomofast.add_elevation(self.elevation)
        self.data2tomofast.write_data_tomofast(self.datacol, self.directoryname)
        self.data2tomofast.write_model_grid(self.padding, self.cell_x, self.cell_y, self.dz, self.directoryname)

        self.load_mesh_vector()

    
    def spacer(self,title):
        self.params.write("\n")
        self.params.write("===================================================================================\n")
        self.params.write(title+'\n')
        self.params.write("===================================================================================\n")

    def save_parameter_file(self):
        self.parse_parameters()

        self.params=open(self.directoryname+'/paramfile.txt','w')

        self.spacer("GLOBAL")
        self.params.write("global.outputFolderPath     = {}\n".format(self.directoryname))
        self.params.write("global.description          = {}\n".format(self.global_description))

        self.spacer("MODEL GRID parameters")

        # nx ny nz
        self.params.write("modelGrid.size                      = {} {} {}\n".format(self.modelGrid_size[0],self.modelGrid_size[1] ,self.modelGrid_size[2] ))
        self.params.write("modelGrid.grav.file                 = {}\n".format(self.modelGrid_grav_file))

        self.spacer("DATA parameters")

        self.params.write("forward.data.grav.nData             = {}\n".format(self.forward_data_grav_nData))
        self.params.write("forward.data.grav.dataGridFile      = {}\n".format(self.forward_data_grav_dataGridFile))
        self.params.write("forward.data.grav.dataValuesFile    = {}\n".format(self.forward_data_grav_dataValuesFile))

        self.spacer("DEPTH WEIGHTING")

        self.params.write("forward.depthWeighting.type         = {}\n".format(self.forward_depthWeighting_type))
        self.params.write("forward.depthWeighting.grav.power   = {}\n".format(self.forward_depthWeighting_grav_power))

        self.spacer("SENSITIVITY KERNEL")

        self.params.write("sensit.readFromFiles                = {}\n".format(self.sensit_readFromFiles))
        self.params.write("sensit.folderPath                   = {}\n".format(self.sensit_folderPath))

        self.spacer("MATRIX COMPRESSION")

        # 0-none, 1-wavelet compression.
        self.params.write("forward.matrixCompression.type      = {}\n".format(self.forward_matrixCompression_type))
        self.params.write("forward.matrixCompression.rate      = {}\n".format(self.forward_matrixCompression_rate))

        self.spacer("PRIOR MODEL")

        self.params.write("inversion.priorModel.type           = {}\n".format(self.inversion_priorModel_type))
        self.params.write("inversion.priorModel.grav.value     = {}\n".format(self.inversion_priorModel_grav_value))

        self.spacer("STARTING MODEL")

        self.params.write("inversion.startingModel.type        = {}\n".format(self.inversion_startingModel_type))
        self.params.write("inversion.startingModel.grav.value  = {}\n".format(self.inversion_startingModel_grav_value))

        self.spacer("INVERSION parameters")

        self.params.write("inversion.nMajorIterations          = {}\n".format(self.inversion_nMajorIterations))
        self.params.write("inversion.nMinorIterations          = {}\n".format(self.inversion_nMinorIterations))
        self.params.write("inversion.writeModelEveryNiter      = {}\n".format(self.inversion_writeModelEveryNiter))
        self.params.write("inversion.minResidual               = {}\n".format(self.inversion_minResidual))

        self.spacer("MODEL DAMPING (m - m_prior)")

        self.params.write("inversion.modelDamping.grav.weight  = {}\n".format(self.inversion_modelDamping_grav_weight))
        self.params.write("inversion.modelDamping.normPower    = {}\n".format(self.inversion_modelDamping_normPower))
       
        self.spacer("JOINT INVERSION parameters")

        self.params.write("inversion.joint.grav.problemWeight  = {}\n".format(self.inversion_joint_grav_problemWeight))
        self.params.write("inversion.joint.magn.problemWeight  = {}\n".format(self.inversion_joint_magn_problemWeight))

        self.spacer("ADMM constraints")

        self.params.write("inversion.admm.enableADMM           = {}\n".format(self.inversion_admm_enableADMM))
        self.params.write("inversion.admm.nLithologies         = {}\n".format(self.inversion_admm_nLithologies))
        self.params.write("inversion.admm.grav.bounds          = {}\n".format(self.inversion_admm_grav_bounds))
        self.params.write("inversion.admm.grav.weight          = {}\n".format(self.inversion_admm_grav_weight))
        self.params.write("inversion.admm.magn.bounds          = {}\n".format(self.inversion_admm_magn_bounds))
        self.params.write("inversion.admm.magn.weight          = {}\n".format(self.inversion_admm_magn_weight))

        self.spacer("MULTIPLIERS")


        self.params.write("inversion.admm.enableADMM           = {}\n".format(self.inversion_admm_enableADMM))  
        self.params.write("inversion.admm.enableADMM           = {}\n".format(self.inversion_admm_enableADMM))  
        self.params.write("inversion.admm.enableADMM           = {}\n".format(self.inversion_admm_enableADMM)) 
        self.params.write("inversion.admm.enableADMM           = {}\n".format(self.inversion_admm_enableADMM)) 

        self.params.close()


    def parse_parameters(self):

        self.global_outputFolderPath             = self.directoryname
        self.global_description                  = self.dlg.textEdit.toPlainText()

        self.modelGrid_size                      = [int(self.dlg.mQgsDoubleSpinBox_12.value()), int(self.dlg.mQgsDoubleSpinBox_13.value()), int(self.dlg.mQgsDoubleSpinBox_14.value())]
        self.modelGrid_grav_file                 = self.directoryname+'/data.csv'
        self.forward_data_grav_nData             = len(self.data2tomofast.df)
        self.forward_data_grav_dataGridFile      = self.directoryname+'/model_grid.txt'
        self.forward_data_grav_dataValuesFile    = self.directoryname+'/grav_calc_read_data.txt'


        if(self.dlg.checkBox_3.isChecked()):
            self.forward_depthWeighting_type      = 1
        else:
            self.forward_depthWeighting_type      = 0

        self.forward_depthWeighting_grav_power   = self.dlg.mQgsDoubleSpinBox_20.value()
        self.sensit_readFromFiles                = self.dlg.checkBox.isChecked()
        self.sensit_folderPath                   = self.sensitivitydirectoryname

        if(self.dlg.checkBox_2.isChecked()):
            self.forward_matrixCompression_type      = 1
        else:
            self.forward_matrixCompression_type      = 0
        
        self.forward_matrixCompression_rate      = self.dlg.mQgsDoubleSpinBox_22.value()

        if(self.dlg.checkBox_5.isChecked()):
            self.inversion_priorModel_type      = 1
        else:
            self.inversion_priorModel_type      = 0
        
        if(self.dlg.checkBox_8.isChecked()):
            self.inversion_priorModel_type      = 1
        else:
            self.inversion_priorModel_type      = 0

        self.inversion_priorModel_grav_value     = self.dlg.mQgsDoubleSpinBox_23.value()
        
        if(self.dlg.checkBox_4.isChecked()):
            self.inversion_startingModel_type      = 1
        else:
            self.inversion_startingModel_type      = 0

        if(self.dlg.checkBox_7.isChecked()):
            self.inversion_startingModel_type      = 1
        else:
            self.inversion_startingModel_type      = 0

        self.inversion_startingModel_grav_value  = self.dlg.mQgsDoubleSpinBox_27.value()

        self.inversion_nMajorIterations          = self.dlg.mQgsDoubleSpinBox_28.value()
        self.inversion_nMinorIterations          = self.dlg.mQgsDoubleSpinBox_29.value()
        self.inversion_writeModelEveryNiter      = self.dlg.mQgsDoubleSpinBox_31.value()
        self.inversion_minResidual               = self.dlg.mQgsDoubleSpinBox_30.value()

        self.inversion_modelDamping_grav_weight  = self.dlg.mQgsDoubleSpinBox_33.value()
        self.inversion_modelDamping_normPower    = self.dlg.mQgsDoubleSpinBox_32.value()

        self.inversion_joint_grav_problemWeight  = self.dlg.mQgsDoubleSpinBox_36.value()
        self.inversion_joint_magn_problemWeight  = self.dlg.mQgsDoubleSpinBox_37.value()

        if(self.dlg.checkBox_9.isChecked()):
            self.inversion_admm_enableADMM      = 1
        else:
            self.inversion_admm_enableADMM      = 0
        if(self.dlg.checkBox_10.isChecked()):
            self.inversion_admm_enableADMM      = 1
        else:
            self.inversion_admm_enableADMM      = 0

        self.inversion_admm_nLithologies         = self.dlg.spinBox_11.value() #??
        self.inversion_admm_nLithologies         = self.dlg.spinBox_17.value() #??
        self.inversion_admm_grav_bounds          = self.dlg.textEdit_2.toPlainText()
        self.inversion_admm_grav_weight          = self.dlg.mQgsDoubleSpinBox_38.value()
        self.inversion_admm_magn_bounds          = self.dlg.textEdit_5.toPlainText()
        self.inversion_admm_magn_weight          = self.dlg.mQgsDoubleSpinBox_44.value()

        self.grav_dataUnitsMultiplier            = self.dlg.mQgsDoubleSpinBox_26.value()
        self.magn_dataUnitsMultiplier            = self.dlg.mQgsDoubleSpinBox_25.value()
        self.grav_modelUnitsMultiplier           = self.dlg.mQgsDoubleSpinBox_35.value()
        self.magn_modelUnitsMultiplier           = self.dlg.mQgsDoubleSpinBox_34.value()

    def inversion_type(self):

        #enable GroupBoxes

        if(self.dlg.radioButton.isChecked()): #grav
            self.dlg.groupBox.setEnabled(True)
            self.dlg.groupBox_9.setEnabled(True)
            self.dlg.groupBox_7.setEnabled(False)
            self.dlg.groupBox_10.setEnabled(False)

            self.dlg.groupBox_16.setEnabled(True)
            self.dlg.groupBox_26.setEnabled(True)
            self.dlg.groupBox_22.setEnabled(True)
            self.dlg.groupBox_24.setEnabled(True)
            self.dlg.groupBox_21.setEnabled(True)
            self.dlg.groupBox_6.setEnabled(True)
            
            self.dlg.groupBox_29.setEnabled(False)
            self.dlg.groupBox_30.setEnabled(False)
            self.dlg.groupBox_23.setEnabled(False)
            self.dlg.groupBox_31.setEnabled(False)
            self.dlg.groupBox_32.setEnabled(False)
            self.dlg.groupBox_35.setEnabled(False)

        elif(self.dlg.radioButton_2.isChecked()): #mag
            self.dlg.groupBox.setEnabled(False)
            self.dlg.groupBox_9.setEnabled(False)
            self.dlg.groupBox_7.setEnabled(True)
            self.dlg.groupBox_10.setEnabled(True)

            self.dlg.groupBox_16.setEnabled(False)
            self.dlg.groupBox_26.setEnabled(False)
            self.dlg.groupBox_22.setEnabled(False)
            self.dlg.groupBox_24.setEnabled(False)
            self.dlg.groupBox_21.setEnabled(False)
            self.dlg.groupBox_6.setEnabled(False)
            
            self.dlg.groupBox_29.setEnabled(True)
            self.dlg.groupBox_30.setEnabled(True)
            self.dlg.groupBox_23.setEnabled(True)
            self.dlg.groupBox_31.setEnabled(True)
            self.dlg.groupBox_32.setEnabled(True)
            self.dlg.groupBox_35.setEnabled(True)

        elif(self.dlg.radioButton_3.isChecked()): #grav/mag
            self.dlg.groupBox.setEnabled(True)
            self.dlg.groupBox_9.setEnabled(True)
            self.dlg.groupBox_7.setEnabled(True)
            self.dlg.groupBox_10.setEnabled(True)

            self.dlg.groupBox_16.setEnabled(True)
            self.dlg.groupBox_26.setEnabled(True)
            self.dlg.groupBox_22.setEnabled(True)
            self.dlg.groupBox_24.setEnabled(True)
            self.dlg.groupBox_21.setEnabled(True)
            self.dlg.groupBox_6.setEnabled(True)
            
            self.dlg.groupBox_29.setEnabled(True)
            self.dlg.groupBox_30.setEnabled(True)
            self.dlg.groupBox_23.setEnabled(True)
            self.dlg.groupBox_31.setEnabled(True)
            self.dlg.groupBox_32.setEnabled(True)
            self.dlg.groupBox_35.setEnabled(True)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = Tomofast_xDialog()
            self.dlg.setFixedSize(1131, 750)
            self.dlg.mQgsProjectionSelectionWidget_3.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
            self.dlg.mQgsProjectionSelectionWidget_5.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
            self.dlg.pushButton_14.setEnabled(False)


        self.dlg.pushButton_7.clicked.connect(self.select_data_file)
        self.dlg.pushButton_2.clicked.connect(self.confirm_data_file)
        self.dlg.pushButton_3.clicked.connect(self.load_dtm)
        self.dlg.pushButton_9.clicked.connect(self.confirm_data_fields)
        self.dlg.pushButton_10.clicked.connect(self.select_ouput_directory)
        self.dlg.pushButton_11.clicked.connect(self.select_sensitivity_directory)
        self.dlg.pushButton_12.clicked.connect(self.select_dtm)
        self.dlg.pushButton_14.clicked.connect(self.save_outputs)
        self.dlg.pushButton_5.clicked.connect(self.save_parameter_file)
        self.dlg.radioButton.toggled.connect(self.inversion_type)
        self.dlg.radioButton_2.toggled.connect(self.inversion_type)
        self.dlg.radioButton_3.toggled.connect(self.inversion_type)
        #self.dlg.pushButton_5.clicked.connect(self.parse_parameters)
        result = self.dlg.exec_()
