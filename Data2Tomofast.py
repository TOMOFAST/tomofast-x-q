
# Processing gravity data for Tomofast-x inversion.
# Author: Vitaliy Ogarko
# Version 1.3.2

import numpy as np
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt

class Data2Tomofast:
    '''
    A class for converting the geophysical data to Tomofast-x inputs.
    '''

    def __init__(self, df):
        self.df = df

    #=================================================================================================
    def read_data(self, input_file, lat_column, long_column, data_column, epsg_from, epsg_to):
        '''
        Reads input geophysical data in CSV format.
        '''
        # Read input data file.
        df = pd.read_csv(input_file)

        print(df.head())

        # Convert data positions from lat/long to cartesian.
        transformer = Transformer.from_crs(
            epsg_from, # degrees
            epsg_to, # meters
            always_xy=True,
        )
        data_x, data_y = transformer.transform(df[long_column].values, df[lat_column].values)

        print("min/max X:", np.min(data_x), np.max(data_x), np.max(data_x) - np.min(data_x))
        print("min/max Y:", np.min(data_y), np.max(data_y), np.max(data_y) - np.min(data_y))

        # Update data frame with converted data positions.
        df['POINT_X'] = data_x
        df['POINT_Y'] = data_y

        data = df[data_column].values
        print("min/max data values:", np.min(data), np.max(data))

        Ndata = data.size
        print("Number of data:", Ndata)

        self.df = df

    #=================================================================================
    def add_elevation(self, elevation):
        '''
        Adds constant elevation to data.
        '''
        self.df['POINT_Z'] = np.zeros(self.df['POINT_X'].values.shape) - elevation

    #=================================================================================
    def write_data_tomofast(self, data_column, out_file):
        '''
        Writes data to file in Tomofast-x format.
        '''
        Ndata = self.df[data_column].values.size
        filename=out_file+'/data.csv'
        # Write a header.
        with open(filename, "w") as f:
            f.write(str(Ndata) + "\n")

        column_list = ["POINT_X", "POINT_Y", "POINT_Z", data_column]

        self.df.to_csv(filename, sep=' ', columns=column_list, index=False, header=False, mode="a")

        print("Wrote data to file:", out_file)

    #=================================================================================
    def plot_data(self, data_column):
        '''
        Plots data values.
        '''
        # Data values.
        colors = self.df[data_column].values
        plt.scatter(self.df['POINT_X'].values, self.df['POINT_Y'].values, c=colors, s=10)
        plt.colorbar(label="Data", orientation="vertical")
        plt.show()

    #=================================================================================
    def write_model_grid(self, padding_size, dx, dy, dz,directory):
        '''
        Writes the Tomofast-x model grid.
        dx, dy: scalars
        dz: vector of size nz
        '''
        data_x = self.df['POINT_X'].values
        data_y = self.df['POINT_Y'].values

        # Define the model horizontal dimensions, based on the observed data extent.
        # The model core area size (adding 1m on each side not to coinside with data position).
        xcore_min = data_x.min() - 1.
        xcore_max = data_x.max() + 1.
        ycore_min = data_y.min() - 1.
        ycore_max = data_y.max() + 1.

        Zmin = 0.
        Zmax = Zmin + np.sum(dz)

        print("Zmax =", Zmax)

        # Grid with paddings.
        Xmin = xcore_min - padding_size
        Xmax = xcore_max + padding_size
        Ymin = ycore_min - padding_size
        Ymax = ycore_max + padding_size

        # Grid dimensions.
        nx = int((Xmax - Xmin) / dx)
        ny = int((Ymax - Ymin) / dy)
        nz = dz.size

        self.nx=nx
        self.ny=ny
        print("nx, ny, nz =", nx, ny, nz)

        nelements = nx * ny * nz

        grid = np.zeros((nelements, 10))
        ind = 0

        for k in range(nz):
            Z1 = Zmin + sum(dz[0:k])
            Z2 = Z1 + dz[k]

            for j in range(ny):
                Y1 = Ymin + j * dy
                Y2 = Y1 + dy

                for i in range(nx):
                    X1 = Xmin + i * dx
                    X2 = X1 + dx

                    grid[ind, 0] = X1
                    grid[ind, 1] = X2
                    grid[ind, 2] = Y1
                    grid[ind, 3] = Y2
                    grid[ind, 4] = Z1
                    grid[ind, 5] = Z2
                    grid[ind, 6] = 0.

                    grid[ind, 7] = i + 1
                    grid[ind, 8] = j + 1
                    grid[ind, 9] = k + 1

                    ind = ind + 1

        model_grid_file_name = directory+"/model_grid.txt"

        # Save model grid to file.
        np.savetxt(model_grid_file_name, grid, delimiter=' ', fmt="%f %f %f %f %f %f %f %d %d %d", header=str(nelements), comments='')

        print("Wrote model grid to file:", model_grid_file_name)

#=================================================================================
def main():
    # Define the input CSV file with geophjysical data.
    input_file = 'FortNorth_ausgrav_grav_data_points_Subset.csv'
    long_column = 'LONGITUDE'
    lat_column = 'LATITUDE'
    data_column = 'SPHERICAL_'

    # Define input/output data reference system.
    epsg_from = "epsg:4283" # (GDA 94 reference system)
    epsg_to = "epsg:28351"  # (GDA 94 MGA zone 51)

    # Data elevation (m).
    elevation = 0.1

    # Horizontal model padding.
    padding_size = 10000.

    # Cell sizes (m).
    dx = 600.
    dy = 600.

    nz = 45

    # Define increasing cell size with depth.
    dz = np.zeros(nz)
    dz[0:20]  = 200.
    dz[20:34] = 200.
    dz[34:42] = 1000.
    dz[42:45] = 2000.

    #------------------------------------------------------------------
    data2tomofast = Data2Tomofast(None)

    # Read geophysical data.
    data2tomofast.read_data(input_file, lat_column, long_column, data_column, epsg_from, epsg_to)

    # Define data elevation (use constant for now).
    data2tomofast.add_elevation(elevation)

    # Write Tomofast-x data file.
    out_file = "TRANS_" + input_file
    data2tomofast.write_data_tomofast(data_column, out_file)

    # Plot data values (for verification).
    data2tomofast.plot_data(data_column)

    # Write Tomofast-x model grid.
    data2tomofast.write_model_grid(padding_size, dx, dy, dz)

#============================================================================
if __name__ == "__main__":
    main()