import os
import numpy as np
import sys

# Check if PyVista is installed
try:
    import pyvista as pv
except ImportError:
    print("PyVista is not installed. Installing PyVista...")


def display_voxet_files_clipped_qgis(files, clip_percentile=95, cmap='viridis', opacity=1.0, show_edges=False):
    """
    Display multiple VTK voxet files with colors clipped to a specific percentile in QGIS.
    """
    # Create a plotter
    plotter = pv.Plotter()
    
    print(f"Attempting to process {len(files)} voxet files...")
    
    # Track if we've successfully added any meshes
    meshes_added = 0
    
    # Process each voxet file
    for i, file_path in enumerate(files):
        try:
            print(f"Loading voxet file: {file_path}")
            
            # Read the VTK file
            grid = pv.read(file_path)
            
            # Get active scalar data
            scalar_name = grid.active_scalars_name
            if not scalar_name:
                # If no active scalars, try to find the first available array
                scalar_names = grid.array_names
                if scalar_names:
                    scalar_name = scalar_names[0]
                    grid.set_active_scalars(scalar_name)
                else:
                    print(f"No scalar data found in {file_path}, skipping...")
                    continue
            
            # Get the scalar data range
            data = grid.active_scalars
            if data is None:
                print(f"No active scalar data in {file_path}, skipping...")
                continue
                
            print(f"Using scalar field: {scalar_name}")
            
            # Calculate clipping values at specified percentile
            vmin = np.min(data)
            vmax = np.percentile(data, clip_percentile)
            
            print(f"Data range: [{np.min(data)}, {np.max(data)}]")
            print(f"Clipped range (95%): [{vmin}, {vmax}]")
            
            # Add to plotter with clipped color range
            # Set show_scalar_bar=False to prevent automatic scalar bars for each mesh
            plotter.add_mesh(
                grid,
                scalars=scalar_name,
                cmap=cmap,
                clim=[vmin, vmax],  # Set color limits
                opacity=opacity,
                show_edges=show_edges,
                reset_camera=False,
                name=os.path.basename(file_path),
                show_scalar_bar=False  # Important: Don't show scalar bar for each mesh
            )
            
            meshes_added += 1
            print(f"Successfully added {file_path} to the visualization")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Add axes
    plotter.add_axes()
    
    # Only add a single scalar bar if meshes were successfully added
    if meshes_added > 0:
        try:
            # Add a single scalar bar for all meshes
            plotter.add_scalar_bar(title="Value (clipped at 95%)")
            print("Added scalar bar")
        except Exception as e:
            print(f"Could not add scalar bar: {str(e)}")
    else:
        print("No meshes were added, cannot display scalar bar")
    
    # Only display if at least one mesh was added
    if meshes_added > 0:
        print("Displaying visualization...")
        # Show the plotter
        plotter.show(interactive=True)
        print("Visualization closed")
    else:
        print("No data to visualize, skipping display")
    
    return plotter

# Example usage for QGIS console (use absolute paths)
voxet_files = [
    "C:/path/to/voxet1.vtk",
    "C:/path/to/voxet2.vtk",
    "C:/path/to/voxet3.vtk"
]

print("Starting voxet visualization...")
display_voxet_files_clipped_qgis(
    files=voxet_files,
    clip_percentile=95,
    cmap='rainbow',
    opacity=0.7,
    show_edges=False
)
print("Function execution completed")