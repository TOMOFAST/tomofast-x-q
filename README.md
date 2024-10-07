# Tomofast-x QGIS Plugin
 QGIS Plugin to help Tomofast-x usage
 
## Install
Save repository to disk as a zip file. Use QGIS Plugin Manager to load directly from zip file.

## Simple instructions
0. **Select tomofast-x-q plugin and Select Import existing field databases tab**
![tomofast dialog tab 1](plugin.png) 
1. Optionally pre-load an existing paramfile from disk
2. Select Grav, mag or both Inversion stype [Step 1]
3. Select a data layer (csv or tif format), define input and output projections, and Load data [Step 2a or Step 3a]
4. If csv data, select fields for lat_x, long_y & data [Step 2b or Step 3a, data loaded to QGIS once Assign fields button selected]
5. Select DTM tif file or use constant value [Step 4 reprojected dtm loaded to QGIS]
6. Specify mesh parameters (optionally defined from max/min extents of a polygon shapefile) and output directory for mesh and parameter files [Step 5 mesh and data files written out and loaded to QGIS]
7. **Select Global Parameters tab**
![tomofast dialog tab 2](plugin2.png) 
8. Define compression file directory and project description and other Inversion parameters
9. Specify Survey parameters
10. **Select Grav/Mag Parameters tab**
![tomofast dialog tab 3](plugin3.png) 
11. For mag survey autofill or define Magnetic Field parameters
12. Modify parameters and then save out Parameter File by clicking on Save Parameter File button [Parameter file written out]
13. **Run tomofast-x from command line using the just-generated files**

## Credits    
Plugin construction - Mark Jessell using QGIS Plugin Builder Plugin and code from Vitaliy Ogarko   
Tomofast-x - Vitaliy Ogarko   
IGRF calculation - https://github.com/klaundal/ppigrf  