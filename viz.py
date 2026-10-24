import os
import numpy as np
import sys


# Open viewer windows, kept referenced so they are not garbage collected
_open_viewers = []


def core_bounds_from_model_grid(model_grid_file):
    """
    Return (xmin, xmax, ymin, ymax) of the core (unbuffered) part of a
    Tomofast-x model grid, or None if it cannot be determined.

    The core cells all share one X and one Y width (the most common width),
    while the padding cells grow by a factor per cell, so the core is the set
    of cells with the modal width in each horizontal direction.
    """
    try:
        grid = np.loadtxt(model_grid_file, dtype=float, usecols=(0, 1, 2, 3), skiprows=1)
    except Exception as e:
        print(f"Could not read model grid {model_grid_file}: {e}")
        return None

    def core_range(lo, hi):
        width = np.round(hi - lo, 3)
        values, counts = np.unique(width, return_counts=True)
        modal = values[np.argmax(counts)]
        core = width == modal
        return lo[core].min(), hi[core].max()

    xmin, xmax = core_range(grid[:, 0], grid[:, 1])
    ymin, ymax = core_range(grid[:, 2], grid[:, 3])
    return xmin, xmax, ymin, ymax


def crop_to_core(grid, core_bounds):
    """
    Keep only the cells whose centre lies inside the core extent in X and Y
    (Z is left alone). Returns the original grid if nothing would remain.
    """
    xmin, xmax, ymin, ymax = core_bounds
    centers = grid.cell_centers().points
    mask = (
        (centers[:, 0] >= xmin) & (centers[:, 0] <= xmax)
        & (centers[:, 1] >= ymin) & (centers[:, 1] <= ymax)
    )
    if not mask.any() or mask.all():
        return grid
    return grid.extract_cells(np.where(mask)[0])


def display_voxet_files_clipped_qgis(files, clip_percentile=95, cmap='viridis', opacity=1.0,
                                     show_edges=False, core_bounds=None):
    """
    Display multiple VTK voxet files with colors clipped to a specific percentile in QGIS.

    core_bounds: optional (xmin, xmax, ymin, ymax). When given, the buffer
    (padding) cells outside it are dropped, so they are neither displayed nor
    counted in the colour range.
    """
    # Check if PyVista is installed
    try:
        import pyvista as pv
    except ImportError:
        print("PyVista is not installed. Please install PyVista...")
        return
    
    # Show the scene in a Qt window (see show_plotter_in_qt_window). VTK's
    # Qt widget needs a native X11/Cocoa/Win32 window, so under a Wayland
    # session fall back to PyVista's own window.
    from qgis.PyQt.QtGui import QGuiApplication
    use_qt_window = QGuiApplication.platformName() != "wayland"

    # Off-screen when the scene is moved into a Qt window below
    plotter = pv.Plotter(off_screen=use_qt_window)
    
    print(f"Attempting to process {len(files)} voxet files...")
    
    # Track if we've successfully added any meshes
    meshes_added = 0
    
    # First pass: load every file so all share one pooled colour range
    loaded = []
    for file_path in files:
        try:
            print(f"Loading voxet file: {file_path}")
            
            # Read the VTK file
            grid = pv.read(file_path)

            # Ignore the buffer (padding) cells in X and Y
            if core_bounds is not None:
                grid = crop_to_core(grid, core_bounds)

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
                
            # Vector models (e.g. MVI Mx,My,Mz) are displayed by magnitude
            if data.ndim == 2 and data.shape[1] > 1:
                magnitude = np.linalg.norm(data, axis=1)
                scalar_name = f"{scalar_name}_magnitude"
                if scalar_name.removesuffix("_magnitude") in grid.cell_data:
                    grid.cell_data[scalar_name] = magnitude
                else:
                    grid.point_data[scalar_name] = magnitude
                grid.set_active_scalars(scalar_name)
                data = magnitude

            print(f"Using scalar field: {scalar_name}")
            print(f"Data range: [{np.min(data)}, {np.max(data)}]")
            loaded.append((file_path, grid, scalar_name, np.asarray(data)))

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    # Shared clipping values (percentile of the pooled data) for all files
    if loaded:
        pooled = np.concatenate([d.ravel() for _, _, _, d in loaded])
        vmin = np.min(pooled)
        vmax = np.percentile(pooled, clip_percentile)
        print(f"Shared clipped range ({clip_percentile}%): [{vmin}, {vmax}]")

    # Second pass: add each mesh with the shared colour range
    for file_path, grid, scalar_name, _ in loaded:
        try:
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
    
    # Only add a single scalar bar if meshes were successfully added
    if meshes_added > 0:
        try:
            # Add a single scalar bar for all meshes
            plotter.add_scalar_bar(title=f"Value (clipped at {clip_percentile}%)")
            print("Added scalar bar")
        except Exception as e:
            print(f"Could not add scalar bar: {str(e)}")
    else:
        print("No meshes were added, cannot display scalar bar")
    
    # Only display if at least one mesh was added
    if meshes_added > 0:
        print("Displaying visualization...")
        if use_qt_window:
            show_plotter_in_qt_window(plotter, title=os.path.basename(files[0]))
        else:
            plotter.add_axes()
            plotter.show(interactive=True)
    else:
        print("No data to visualize, skipping display")
    
    return plotter


def show_plotter_in_qt_window(plotter, title="3D model"):
    """
    Show a plotter's scene in a non-modal Qt window inside the running
    QGIS application.

    plotter.show() opens VTK's own native window, and on macOS closing
    that window crashes QGIS. Rendering through VTK's Qt widget instead
    lets QGIS's event loop own the window, so it opens and closes cleanly.
    """
    import vtkmodules.qt
    from qgis.PyQt.QtCore import QT_VERSION_STR, Qt
    from qgis.PyQt.QtWidgets import QApplication, QDialog, QVBoxLayout

    # On Qt6 a plain QWidget base repaints endlessly (seen on macOS),
    # freezing QGIS; VTK supports a QOpenGLWidget base there instead.
    # This must be set before QVTKRenderWindowInteractor is first imported.
    if QT_VERSION_STR.startswith("6"):
        vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
    from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
    from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

    class ViewerDialog(QDialog):
        def closeEvent(self, event):
            # Release the OpenGL context while the widget still exists
            self.axes_widget.SetEnabled(False)
            self.vtk_widget.Finalize()
            self.plotter.close()
            if self in _open_viewers:
                _open_viewers.remove(self)
            super().closeEvent(event)

    dialog = ViewerDialog(QApplication.activeWindow())
    dialog.setWindowTitle(title)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
    dialog.resize(1024, 768)

    vtk_widget = QVTKRenderWindowInteractor(dialog)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(vtk_widget)

    # Move the plotter's renderer into the widget's render window
    renderer = plotter.renderer
    plotter.ren_win.RemoveRenderer(renderer)
    render_window = vtk_widget.GetRenderWindow()
    render_window.AddRenderer(renderer)
    interactor = render_window.GetInteractor()
    interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())

    # Orientation axes in the lower-left corner
    axes_widget = vtkOrientationMarkerWidget()
    axes_widget.SetOrientationMarker(vtkAxesActor())
    axes_widget.SetInteractor(interactor)
    axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
    axes_widget.SetEnabled(True)
    axes_widget.InteractiveOff()

    dialog.plotter = plotter
    dialog.vtk_widget = vtk_widget
    dialog.axes_widget = axes_widget
    _open_viewers.append(dialog)

    # Same starting view that plotter.show() would give
    plotter.view_isometric()
    dialog.show()
    vtk_widget.Initialize()
    render_window.Render()
    return dialog
