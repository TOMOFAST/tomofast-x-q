# Tomofast-x QGIS Plugin
 QGIS Plugin to help Tomofast-x usage
 
## Install
Save repository to disk as a zip file. Use QGIS Plugin Manager to load directly from zip file.

## Simple instructions
**Select tomofast-x-q plugin and Select Import existing field databases tab**   
![tomofast dialog tab 1](plugin.png)    
A. Optionally pre-load an existing paramfile from disk [Step 0]      
B. Select Grav, mag or both Inversion stype [Step 1]   
C. Select a data layer (csv or tif format), define input and output projections, and Load data [Step 2a or Step 3a]   
D. If csv data, select fields for lat_x, long_y & data [Step 2b or Step 3b, data loaded to QGIS once Assign fields button selected]   
E. Select DTM tif file or use constant value [Step 4 reprojected dtm loaded to QGIS]   
F. Specify mesh parameters (optionally defined from max/min extents of a polygon shapefile) and output directory for mesh and parameter files. Check Model Grid Size to make sure the mesh is not stupidly large. [Step 5 mesh and data files written out and loaded to QGIS]  
    
**Select Global Parameters tab**   
![tomofast dialog tab 2](plugin2.png)    
G. Define compression file directory and project description and other Inversion parameters. Check the Estimated Memory Requirements to make sure you run the inversion on a computer with enough memory.   
H. Specify Survey parameters   
   
**Select Grav/Mag Parameters tab**   
![tomofast dialog tab 3](plugin3.png)    
I. For mag survey autofill (using centroid of mesh) or define Magnetic Field parameters   
J. Modify parameters and then save out Parameter File by clicking on Save Parameter File button [Parameter file written out]   
   
**Run tomofast-x from command line using the just-generated files**

## Credits    
Plugin construction - Mark Jessell using QGIS Plugin Builder Plugin and code from Vitaliy Ogarko   
Tomofast-x - Vitaliy Ogarko   
IGRF calculation - https://github.com/klaundal/ppigrf  