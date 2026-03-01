# Tomofast-x QGIS Plugin
 QGIS Plugin to help Tomofast-x usage

 **<a href="https://tectonique.net/tomofast-x-q/Tomofast-x-q%20cheat%20sheet.pdf">Cheat Sheet</a>&nbsp;&nbsp;&nbsp; |&nbsp;&nbsp;&nbsp;<a href="https://tectonique.net/tomofast-x-q/Tomofast-x-q%20User%20Manual.pdf">Download Basic Help Document</a>**&nbsp;&nbsp;&nbsp; |&nbsp;&nbsp;&nbsp;<a href="https://tectonique.net/tomofast-x-q/tomofast_demo.mp4">Ctrl-click on link to watch demo video</a>**

## Recent changes
changelog=0.2.13   
    * Update calls for newer pandas compatibility   
    * Increase max depths for mesh generation
    * Update requirements
    0.2.12   
    * Allow simpler Windows runtime install   
    0.2.11   
    * Add support for Native Windows tomofast-x    
    * remove data field from mesh file   
    * minor GUI reorganisation   
    0.2.10   
    * Remove pre command widget for WSL (no longer needed)    
    * Allow Linux definition of mpirun path   
    * Allow outputs to be stored on linux drive   
    * Compatibility with both QGIS4/QT6 and QGIS3/QT5  
    0.2.9   
    * Add export to csv option
 
    
## Plugin Install
Use QGIS Plugin Manager in QGIS 3.xx to load directly the Plugin Repository (experimental) or download the zip file of this repository (QT6 branch) and use Install in QGIS 3.xx or QGIS 4.xx from Zip file in the QGIS Plugin Manager.   

## Tomofast-x Install
To use this plugin to its full potential you may want to install Tomofast-x itself on the same computer on which you are running QGIS.

See the [Installation instructions](https://github.com/TOMOFAST/Tomofast-manual/blob/main/install.md) for detailed installation instructions.

## Simple instructions

**Tooltips in plugin provide parameter name used in paramfile in squre brackets to help with subsequent manual editing**   
   
**Select tomofast-x-q plugin and Select Data/Mesh tab**   
![tomofast dialog tab 1](plugin.png)    
A. Optionally pre-load an existing paramfile from disk [Step 0]      
B. Select Grav, mag or both Inversion stype [Step 1]   
C. Select a data layer (csv or tif format), define input and output projections, and Load data [Step 2a or Step 3a]   
D. If csv data, select fields for lat_x, long_y & data [Step 2b or Step 3b, data loaded to QGIS once Assign fields button selected]   
E. Select DTM tif file or use constant value [Step 4 reprojected dtm loaded to QGIS]   
F. Specify mesh parameters (optionally defined from max/min extents of a polygon shapefile) and output directory for mesh and parameter files. Check Model Grid Size to make sure the mesh is not stupidly large.    
G. Define compression amount. Check the Estimated Memory Requirements to make sure you run the inversion on a computer with enough memory.    
[Step 5 mesh and data files written out and loaded to QGIS]   
    

**Select Grav/Mag Parameters tab**   
![tomofast dialog tab 2](plugin2.png)    
H. For mag survey autofill (using centroid of mesh) or define Magnetic Field parameters   
   
**Select Global Parameters tab**   
![tomofast dialog tab 3](plugin3.png)     
I. Specify Global Inversion parameters   
J. Modify parameters and then save out  File by clicking on Save Files button [Data and Parameter file written out]   
   
**Run tomofast-x from plugin using the just-generated files**   
![tomofast dialog tab 4](plugin4.png)    
K. If you have tomofast-x installed on your machine, you can run it directly from this tab, after defining the path to the tomofastx executable and the paramfile, and the number of processors to use.    
   
Under Windows this can be run as a native tomofastx.exe file or via WSL2 (Windows Subsystem For Linux v2), so you will need to specify which type of Windows you will run and:
- For **Native Windows** use you will need to specify the path to a bat file (tooltip give likely location)
- For **WSL** which Linux Distribution is installed 
- For **MacOs** use you will have to specify the path to the OpenMPI mpirun binary
   
Otherwise copy these files to another machine and run tomofast-x there (but you will have to fix the paths in the **paramfile.txt** file first)    
- **data_magn.csv and/or data_grav.csv**: observed geophysical response   
- **model_grid.txt**: Model mesh   
- **paramfile.txt**: parameter definition file   

## Credits    
Plugin construction - Mark Jessell using QGIS Plugin Builder Plugin and code from Vitaliy Ogarko   
Tomofast-x - Vitaliy Ogarko   
IGRF calculation - https://github.com/klaundal/ppigrf  
