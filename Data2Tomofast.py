# Processing gravity data for Tomofast-x inversion.
# Author: Vitaliy Ogarko
# Version 1.5

import numpy as np
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt
import os
from PyQt5.QtCore import QVariant


class Data2Tomofast:
    """
    A class for converting the geophysical data to Tomofast-x inputs.
    """

    def __init__(self, df):
        self.df = df

    # =================================================================================================
    def read_data(
        self, input_file, lat_column, long_column, data_column, epsg_from, epsg_to
    ):
        """
        Reads input geophysical data in CSV format.
        """
        # Read input data file.
        df = pd.read_csv(input_file)

        # Convert data positions from lat/long to cartesian.
        transformer = Transformer.from_crs(
            epsg_from,  # degrees
            epsg_to,  # meters
            always_xy=True,
        )
        data_x, data_y = transformer.transform(
            df[long_column].values, df[lat_column].values
        )

        # Update data frame with converted data positions.
        df["POINT_X"] = data_x
        df["POINT_Y"] = data_y

        data = df[data_column].values

        Ndata = data.size
        self.nData = Ndata

        self.df = df

    # =================================================================================
    def add_elevation(self, elevation, elevType, df_elev):
        """
        Adds constant elevation to data.
        """
        if elevType == 1:
            self.df["POINT_Z"] = np.zeros(self.df["POINT_X"].values.shape) - elevation
        else:
            # self.df["POINT_Z"] = -df_elev["POINT_Z"]
            # Function to safely extract numeric value from QVariant or a normal type
            def get_numeric_value(val):
                if isinstance(val, QVariant):
                    if val.isValid() and not val.isNull():
                        # Extracting the value as a double (returns a tuple, so we grab the first element)
                        return (
                            val.toDouble()[0]
                            if isinstance(val.toDouble()[0], (int, float))
                            else np.nan
                        )
                elif isinstance(val, (int, float)):
                    return val
                return np.nan

            # Apply the function to the column to convert all values to their negative
            self.df["POINT_Z"] = (
                -df_elev["POINT_Z"].apply(get_numeric_value) - elevation
            )

    # =================================================================================
    def write_data_tomofast(self, data_column, out_file, eType):
        """
        Writes data to file in Tomofast-x format.
        """
        Ndata = self.df[data_column].values.size
        if eType == 1:
            filename = out_file + "/data_grav.csv"
        else:
            filename = out_file + "/data_magn.csv"
        # Write a header.
        with open(filename, "w") as f:
            f.write(str(Ndata) + "\n")

        column_list = ["POINT_X", "POINT_Y", "POINT_Z", data_column]

        self.df.to_csv(
            filename, sep=" ", columns=column_list, index=False, header=False, mode="a"
        )

    # =================================================================================
    def plot_data(self, data_column):
        """
        Plots data values.
        """
        # Data values.
        colors = self.df[data_column].values
        plt.scatter(
            self.df["POINT_X"].values, self.df["POINT_Y"].values, c=colors, s=10
        )
        plt.colorbar(label="Data", orientation="vertical")
        plt.show()

    # =================================================================================
    def generate_cell_sizes(
        self, core_min, core_max, core_cell_size, padding_size, both_sides
    ):
        """
        Generates cell sizes with expanding paddings along one dimension.
        Returns an array with generated cell sizes and the actual padding size.
        """
        # Multiplier to increase cell size in the paddings.
        cell_size_multiplier = 1.15

        # Number of cells in the core.
        n_core = int((core_max - core_min) / core_cell_size)

        # Adding the core.
        cell_sizes = list()
        for i in range(n_core):
            cell_sizes.append(core_cell_size)

        # Adding expanding paddings.
        curr_padding = 0.0
        curr_cell_size = core_cell_size
        while curr_padding < padding_size:
            curr_cell_size = cell_size_multiplier * curr_cell_size
            curr_padding += curr_cell_size
            # Adding right padding.
            cell_sizes.append(curr_cell_size)
            if both_sides:
                # Adding left padding.
                cell_sizes.insert(0, curr_cell_size)

        # Convert list to numpy array.
        cell_sizes = np.array(cell_sizes)

        return cell_sizes, curr_padding

    # ========================================================================================
    def write_model_grid(self, padding_size, dx0, dy0, dz0, meshBox, directory):
        """
        Writes the Tomofast-x model grid.

        dx0, dy0, dz0: cell size in the model core area.
        padding_size: horizontal padding size.
        meshBox: defines the model core and depth.
        directory: output folder.
        """
        print("meshBox", meshBox)
        xcore_min = meshBox["west"] - 1.0
        xcore_max = meshBox["east"] + 1.0
        ycore_min = meshBox["south"] - 1.0
        ycore_max = meshBox["north"] + 1.0

        zcore_min = 0.0
        zcore_max = meshBox["core_depth"]

        z_padding_size = meshBox["full_depth"] - meshBox["core_depth"]

        # Define cell sizes for the mesh with expanding paddings.
        dx, x_padding = self.generate_cell_sizes(
            xcore_min, xcore_max, dx0, padding_size, True
        )
        dy, y_padding = self.generate_cell_sizes(
            ycore_min, ycore_max, dy0, padding_size, True
        )
        dz, z_padding = self.generate_cell_sizes(
            zcore_min, zcore_max, dz0, z_padding_size, False
        )

        # Grid with paddings.
        Xmin = xcore_min - x_padding
        Ymin = ycore_min - y_padding
        Zmin = zcore_min

        # Grid dimensions.
        nx = dx.size
        ny = dy.size
        nz = dz.size

        self.nx = nx
        self.ny = ny
        self.nz = nz

        nelements = nx * ny * nz

        grid = np.zeros((nelements, 10))
        ind = 0

        for k in range(nz):
            Z1 = Zmin + sum(dz[0:k])
            Z2 = Z1 + dz[k]

            for j in range(ny):
                Y1 = Ymin + sum(dy[0:j])
                Y2 = Y1 + dy[j]

                for i in range(nx):
                    X1 = Xmin + sum(dx[0:i])
                    X2 = X1 + dx[i]

                    grid[ind, 0] = X1
                    grid[ind, 1] = X2
                    grid[ind, 2] = Y1
                    grid[ind, 3] = Y2
                    grid[ind, 4] = Z1
                    grid[ind, 5] = Z2
                    grid[ind, 6] = 0.0

                    grid[ind, 7] = i + 1
                    grid[ind, 8] = j + 1
                    grid[ind, 9] = k + 1

                    ind = ind + 1

        model_grid_file_name = directory + "/model_grid.txt"

        # Save model grid to file.
        np.savetxt(
            model_grid_file_name,
            grid,
            delimiter=" ",
            fmt="%f %f %f %f %f %f %f %d %d %d",
            header=str(nelements),
            comments="",
        )

    # =================================================================================
    def add_topography(self, model_grid_file, elevation_grid_file):
        """
        Reads existing model grid file (in Tomofast-x format) and adds topography to it.
        model_grid_file - Tomofast-x model grid file.
        elevation_grid_file - a file with topography elevations for each Nx * Ny model grid cells.
        data_*.csv observations
        """
        # Read input files.
        model_grid = np.loadtxt(model_grid_file, dtype=float, skiprows=1)
        elevation_grid = np.loadtxt(
            elevation_grid_file, dtype=float, usecols=(2), skiprows=1, delimiter=","
        )
        # Extract nx, ny from the model grid file.
        nx = int(model_grid[-1, 7])
        ny = int(model_grid[-1, 8])
        nz = int(model_grid[-1, 9])

        # Convert to 2D array.
        elevation_grid = elevation_grid.reshape((ny, nx))

        # Loop through the model grid cells and adjust their elevation.
        ind = 0
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Extract elevation for this cell.
                    elevation = elevation_grid[j, i]

                    # Shift Z1 and Z2 by the elevation.
                    model_grid[ind, 4] = (
                        model_grid[ind, 4] + elevation
                    )  # elevation is already negative
                    model_grid[ind, 5] = (
                        model_grid[ind, 5] + elevation
                    )  # elevation is already negative

                    ind = ind + 1
        # -------------------------------------------------------------------
        nelements = nx * ny * nz
        ndata = ind
        # Build the output file name.
        # model_grid_file_no_ext = os.path.splitext(model_grid_file)[0]
        # model_grid_file_new = model_grid_file_no_ext + "_topo.txt"

        # Save the new model grid to file.
        np.savetxt(
            model_grid_file,
            model_grid,
            delimiter=" ",
            fmt="%f %f %f %f %f %f %f %d %d %d",
            header=str(nelements),
            comments="",
        )
        return elevation_grid.mean()


# =================================================================================
def main():
    # Test adding topography.
    # data2tomofast = Data2Tomofast(None)
    # model_grid_file = 'o22/model_grid.txt'
    # elevation_grid_file = 'o22/elevation_grid.csv'
    # data2tomofast.add_topography(model_grid_file, elevation_grid_file)

    # Define the input CSV file with geophjysical data.
    input_file = "FortNorth_ausgrav_grav_data_points_Subset.csv"
    long_column = "LONGITUDE"
    lat_column = "LATITUDE"
    data_column = "SPHERICAL_"

    # Define input/output data reference system.
    epsg_from = "epsg:4283"  # (GDA 94 reference system)
    epsg_to = "epsg:28351"  # (GDA 94 MGA zone 51)

    # Data elevation (m).
    elevation = 0.1

    # Horizontal model padding.
    padding_size = 10000.0

    # Cell sizes (m).
    dx = 600.0
    dy = 600.0
    dz = 600.0

    # ------------------------------------------------------------------
    data2tomofast = Data2Tomofast(None)

    # Read geophysical data.
    data2tomofast.read_data(
        input_file, lat_column, long_column, data_column, epsg_from, epsg_to
    )

    # Define data elevation (use constant for now).
    data2tomofast.add_elevation(elevation)

    # Write Tomofast-x data file.
    out_file = "o33"
    data2tomofast.write_data_tomofast(data_column, out_file, eType=1)

    # Plot data values (for verification).
    data2tomofast.plot_data(data_column)

    # Data positions.
    data_x = data2tomofast.df["POINT_X"].values
    data_y = data2tomofast.df["POINT_Y"].values

    meshBox = dict()

    # Define the model core horizontal dimensions, based on the observed data extent.
    meshBox["west"] = data_x.min()
    meshBox["east"] = data_x.max()
    meshBox["south"] = data_y.min()
    meshBox["north"] = data_y.max()

    meshBox["core_depth"] = 10000.0
    meshBox["full_depth"] = 20000.0

    # Write Tomofast-x model grid.
    data2tomofast.write_model_grid(padding_size, dx, dy, dz, meshBox, directory="o33")


# ============================================================================
if __name__ == "__main__":
    main()
