"""
Run the FFT inversion of fast_inversion.py ("Frost") from a Tomofast-x parameter file.

The parameter file is the one the plugin writes, with ``global.useFFT = 1``.  The inputs are read back from the files
it names (data file, model grid) and from its parameters:

    data             forward.data.grav.dataGridFile / forward.data.magn.dataGridFile  (N, then x y z value)
    mesh             modelGrid.grav.file / modelGrid.magn.file  (no horizontal padding: one column per data point)
    beta             forward.depthWeighting.grav.power / .magn.power
    station height   from the z column of the data (z positive down, model top at z = 0)
    units            global.*.dataUnitsMultiplier / modelUnitsMultiplier, as in Tomofast-x
    magnetic field   forward.magneticField.inclination / declination / intensity_nT
                     (x = easting, y = northing, so the declination given to fast_inversion is 90 - D)
    noise level      fast_inversion default (2 % of the largest datum); plane detrend, taper padding

Outputs, in the output folder of the parameter file (<folder>/OUTPUT for files written by the plugin):

    Paraview/<grav|mag>_final_model3D_full.vtk, _half_x.vtk, _half_y.vtk, _half_z.vtk
        same format and names as Tomofast-x, so the plugin's viewer and ParaView scripts work unchanged
    Frost/<grav|mag>_final_model_full.txt              model in Tomofast-x format (N, then one value per cell)
    Frost/<grav|mag>_observed_data.txt, _calc_final_data.txt, _residual_data.txt   (N, then x y z value)
    Frost/frost_summary.txt, Frost/frost_log.txt
"""
import os
import shutil
import sys
import time
from contextlib import redirect_stdout

import numpy as np

END_MARKER = "FROST FINISHED."


class FrostError(Exception):
    """The parameter file or its inputs cannot be run with Frost."""


class FrostCancelled(Exception):
    """The run was cancelled by the user."""


# ------------------------------------------------------------------------------------------------- parameter file
def read_parfile(path):
    """Parameters of a Tomofast-x parameter file as {name: value string}.

    Active lines win over lines commented out with '#' (the plugin stores its own values, such as
    '#global.experimentType', as comments)."""
    active, commented = {}, {}
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            target = commented if key.startswith("#") else active
            key = key.lstrip("#").strip()
            if key:
                target.setdefault(key, value.strip())
    commented.update(active)
    return commented


def uses_fft(param_path):
    """True when the parameter file asks for the FFT inversion (global.useFFT not 0)."""
    try:
        value = read_parfile(param_path).get("global.useFFT", "0")
        return int(float(value.replace("d", "e"))) != 0
    except (OSError, ValueError):
        return False


def _float(params, key, default=None):
    value = params.get(key)
    if value is None or value == "":
        if default is None:
            raise FrostError(f"Parameter {key} is missing from the parameter file")
        return float(default)
    try:
        return float(value.replace("d", "e").replace("D", "e"))
    except ValueError:
        raise FrostError(f"Parameter {key} is not a number: {value}")


def _resolve(path, param_dir):
    if not path or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(param_dir, path))


def output_dirs(param_path):
    """(output folder, Paraview folder, Frost folder) of a parameter file."""
    param_dir = os.path.dirname(os.path.abspath(param_path))
    try:
        out = read_parfile(param_path).get("global.outputFolderPath", "")
    except OSError:
        out = ""
    out = _resolve(out, param_dir) if out else os.path.join(param_dir, "OUTPUT")
    return out, os.path.join(out, "Paraview"), os.path.join(out, "Frost")


# ------------------------------------------------------------------------------------------------- input files
def _read_model_grid_axes(path, size, is_cancelled=None):
    """Cell edges along x, y and z of a Tomofast-x model grid (rows ordered with i fastest, then j, then k)."""
    import pandas as pd

    nx, ny, nz = size
    names = ["x1", "x2", "y1", "y2", "z1", "z2", "i", "j", "k"]
    top = pd.read_csv(path, sep=r"\s+", skiprows=1, header=None, names=names, nrows=nx * ny)
    if len(top) != nx * ny:
        raise FrostError(f"Model grid {path} has fewer cells than modelGrid.size")
    x1 = top["x1"].values[:nx]
    x2 = top["x2"].values[:nx]
    y1 = top["y1"].values[::nx][:ny]
    y2 = top["y2"].values[::nx][:ny]

    # z edges: the cells of the first column (i = j = 1), one per layer
    z = _layer_z_edges_fast(path, nx * ny, nz)
    if z is None:
        # rows not in the standard order: parse the whole file (slow for large grids)
        z1 = np.full(nz, np.nan)
        z2 = np.full(nz, np.nan)
        for chunk in pd.read_csv(path, sep=r"\s+", skiprows=1, header=None, names=names,
                                 usecols=["z1", "z2", "i", "j", "k"], chunksize=2_000_000):
            _check(is_cancelled)
            sel = chunk[(chunk["i"] == 1) & (chunk["j"] == 1)]
            z1[sel["k"].values - 1] = sel["z1"].values
            z2[sel["k"].values - 1] = sel["z2"].values
        if np.isnan(z1).any():
            raise FrostError(f"Model grid {path}: could not read all {nz} layers")
        z = (z1, z2)
    return (x1, x2, y1, y2) + tuple(z)


def _layer_z_edges_fast(path, cells_per_layer, nz, block_size=1 << 26):
    """z1, z2 of each layer from the first cell of each layer block, or None.

    The plugin writes the grid with i fastest, then j, then k, so the first cell of layer k is line
    1 + k * nx * ny of the file.  Only those lines are parsed: the file is read in large blocks and the
    line breaks are located with numpy, instead of parsing every line.  Returns None if a line found
    there is not cell (1, 1, k+1), so the caller can fall back to reading the whole file."""
    z1 = np.empty(nz)
    z2 = np.empty(nz)
    k = 0
    target = 1  # absolute line number (0 = header) of the first cell of layer k
    first_line = 0  # absolute line number of the first line in buf
    carry = b""
    with open(path, "rb") as f:
        while k < nz:
            chunk = f.read(block_size)
            buf = carry + chunk
            if not buf:
                break
            ends = np.flatnonzero(np.frombuffer(buf, dtype=np.uint8) == 10)
            if not chunk and (ends.size == 0 or ends[-1] != len(buf) - 1):
                ends = np.append(ends, len(buf))  # last line without a line break
            while k < nz and target < first_line + ends.size:
                m = target - first_line
                start = 0 if m == 0 else ends[m - 1] + 1
                fields = buf[start:ends[m]].split()
                try:
                    if (len(fields) < 9 or int(fields[6]) != 1 or int(fields[7]) != 1
                            or int(fields[8]) != k + 1):
                        return None
                    z1[k], z2[k] = float(fields[4]), float(fields[5])
                except ValueError:
                    return None
                k += 1
                target += cells_per_layer
            if not chunk:
                break
            done = ends[-1] + 1 if ends.size else 0
            carry = buf[done:]
            first_line += ends.size
    return (z1, z2) if k == nz else None


def _read_data(path):
    """x, y, z and value columns of a Tomofast-x data file (missing values -> NaN)."""
    with open(path, "r", errors="replace") as fh:
        lines = fh.read().splitlines()[1:]
    rows = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        value = parts[3] if len(parts) > 3 else "nan"
        try:
            rows.append((float(parts[0]), float(parts[1]), float(parts[2]), float(value)))
        except ValueError:
            rows.append((float(parts[0]), float(parts[1]), float(parts[2]), np.nan))
    if not rows:
        raise FrostError(f"No data found in {path}")
    return np.array(rows, dtype=float).T


def _uniform(edges_lo, edges_hi, axis, log):
    widths = edges_hi - edges_lo
    w = float(np.median(widths))
    if np.max(np.abs(widths - w)) > 1e-3 * w:
        raise FrostError(
            f"The model grid has cells of different sizes along {axis}. Frost needs a mesh without horizontal "
            f"padding: set Padding to 0 and save the files again."
        )
    return w


# ------------------------------------------------------------------------------------------------- VTK output
_LF = b"\n"


def _i8(n):
    """Fortran (i8) formatting, as Tomofast-x writes the VTK headers."""
    return ("%8d" % n).encode()


def _write_vtk_struct_grid(path, xc, yc, zc, values, label):
    """Structured grid of the cell centres (Tomofast-x visualisation_paraview_struct_grid)."""
    nx, ny, nz = values.shape
    n = nx * ny * nz
    # Points ordered with i fastest, then j, then k; z axis inverted (elevation)
    Z, Y, X = np.meshgrid(-zc, yc, xc, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(">f4")
    data = values.transpose(2, 1, 0).ravel().astype(">f4")
    with open(path, "wb") as f:
        f.write(b"# vtk DataFile Version 3.0" + _LF + b"Tomofast-x" + _LF + b"BINARY" + _LF)
        f.write(b"DATASET STRUCTURED_GRID" + _LF)
        f.write(b"DIMENSIONS " + _i8(nx) + b" " + _i8(ny) + b" " + _i8(nz) + _LF)
        f.write(_LF + _LF + b"POINTS " + _i8(n) + b" FLOAT" + _LF)
        f.write(pts.tobytes())
        f.write(_LF + _LF + b"POINT_DATA " + _i8(n) + _LF)
        f.write(b"SCALARS " + label.encode() + b" FLOAT" + _LF + b"LOOKUP_TABLE default" + _LF)
        f.write(data.tobytes())


def _write_vtk_legogrid(path, x1, x2, y1, y2, z1, z2, values, irange, jrange, krange, label):
    """Unstructured grid of voxels for a block of cells (Tomofast-x visualisation_paraview_legogrid)."""
    ii = np.arange(*irange)
    jj = np.arange(*jrange)
    kk = np.arange(*krange)
    K, J, I = np.meshgrid(kk, jj, ii, indexing="ij")
    I, J, K = I.ravel(), J.ravel(), K.ravel()
    n = I.size
    xa, xb = x1[I], x2[I]
    ya, yb = y1[J], y2[J]
    za, zb = -z1[K], -z2[K]
    # corner order of Tomofast-x: (x1,y1),(x2,y1),(x1,y2),(x2,y2) at the top, then the same at the bottom
    corners = np.empty((n, 8, 3), dtype=">f4")
    for c, (xs, ys, zs) in enumerate(
        [(xa, ya, za), (xb, ya, za), (xa, yb, za), (xb, yb, za),
         (xa, ya, zb), (xb, ya, zb), (xa, yb, zb), (xb, yb, zb)]
    ):
        corners[:, c, 0] = xs
        corners[:, c, 1] = ys
        corners[:, c, 2] = zs
    cells = np.empty((n, 9), dtype=">i4")
    cells[:, 0] = 8
    cells[:, 1:] = 8 * np.arange(n)[:, None] + np.arange(8)[None, :]
    with open(path, "wb") as f:
        f.write(b"# vtk DataFile Version 3.0" + _LF + b"Tomofast-x" + _LF + b"BINARY" + _LF)
        f.write(b"DATASET UNSTRUCTURED_GRID" + _LF + _LF)
        f.write(b"POINTS " + _i8(8 * n) + b" FLOAT" + _LF)
        f.write(corners.tobytes())
        f.write(_LF + _LF + b"CELLS " + _i8(n) + b" " + _i8(9 * n) + _LF)
        f.write(cells.tobytes())
        f.write(_LF + _LF + b"CELL_TYPES " + _i8(n) + _LF)
        f.write(np.full(n, 11, dtype=">i4").tobytes())
        f.write(_LF + _LF + b"CELL_DATA " + _i8(n) + _LF)
        f.write(b"SCALARS " + label.encode() + b" FLOAT" + _LF + b"LOOKUP_TABLE default" + _LF)
        f.write(values[I, J, K].astype(">f4").tobytes())


def _write_data_file(path, x, y, z, v):
    """Data in Tomofast-x format: N, then x y z value."""
    with open(path, "w") as f:
        f.write(f"{x.size}\n")
        np.savetxt(f, np.column_stack([x, y, z, v]), fmt="%.6f %.6f %.6f %.9g")


# ------------------------------------------------------------------------------------------------- run
class _LogWriter:
    """File-like object that sends whole lines to the log."""

    def __init__(self, log):
        self.log = log
        self.buf = ""

    def write(self, text):
        self.buf += text
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self.log(line)
        return len(text)

    def flush(self):
        if self.buf:
            self.log(self.buf)
            self.buf = ""


def run_frost(param_path, log_path=None, is_cancelled=None, log=None):
    """Run the FFT inversion described by a parameter file and write its outputs.

    log_path      file the progress is written to (default <output>/Frost/frost_log.txt)
    is_cancelled  optional callable; when it returns True the run stops with FrostCancelled at the next step
    log           optional extra callable that receives each log line
    Returns a dict that summarises the run."""
    out_dir, paraview_dir, frost_dir = output_dirs(param_path)
    os.makedirs(paraview_dir, exist_ok=True)
    os.makedirs(frost_dir, exist_ok=True)
    if log_path is None:
        log_path = os.path.join(frost_dir, "frost_log.txt")

    with open(log_path, "w") as log_fh:
        def write(line=""):
            log_fh.write(line + "\n")
            log_fh.flush()
            if log is not None:
                log(line)

        try:
            summary = _run(param_path, out_dir, paraview_dir, frost_dir, write, is_cancelled)
        except FrostCancelled as e:
            write(f"\n*** {e} ***")
            raise
        except Exception as e:
            write(f"\nERROR: {e}")
            raise
        write("")
        write(END_MARKER)
        return summary


def _import_fast_inversion():
    try:
        if __package__:
            from . import fast_inversion as fi
        else:
            import fast_inversion as fi
    except ImportError as e:
        if "scipy" in str(e):
            raise FrostError(
                "Frost needs the Python package scipy, which is not installed in this QGIS. "
                "Install it (for example: pip install scipy in the QGIS Python environment) and restart QGIS."
            )
        raise
    return fi


def _run(param_path, out_dir, paraview_dir, frost_dir, write, is_cancelled):
    t_start = time.perf_counter()
    fi = _import_fast_inversion()
    param_path = os.path.abspath(param_path)
    param_dir = os.path.dirname(param_path)
    params = read_parfile(param_path)

    write("Frost: fast FFT inversion (fast_inversion.py v%s)" % getattr(fi, "__version__", "?"))
    write("Parameter file: " + param_path)

    # --- problem type
    exp_type = params.get("global.experimentType")
    if exp_type is None:
        has_g = "modelGrid.grav.file" in params
        has_m = "modelGrid.magn.file" in params
        exp_type = "3" if (has_g and has_m) else ("2" if has_m else "1")
    exp_type = int(float(exp_type))
    if exp_type == 3:
        raise FrostError("Frost inverts one data set at a time: joint inversion is not supported")
    if params.get("global.is_2d", "0").strip() not in ("0", ""):
        raise FrostError("Frost needs gridded data: 2D profile inversions are not supported")

    if exp_type == 1:
        prefix, label, code = "grav", "rho", "grav"
        if int(_float(params, "forward.data.grav.type", 1)) != 1:
            raise FrostError("Frost supports gravity data, not gravity gradiometry")
        if int(_float(params, "forward.data.grav.nDataComponents", 1)) != 1:
            raise FrostError("Frost supports single-component gravity data only")
        kind = "gravity"
    else:
        prefix, label, code = "mag", "k", "magn"
        if int(_float(params, "forward.data.magn.nDataComponents", 1)) != 1:
            raise FrostError("Frost supports total-field magnetic data (one component) only")
        if int(_float(params, "modelGrid.magn.nModelComponents", 1)) != 1:
            raise FrostError("Frost supports susceptibility inversion, not MVI")
        kind = "magnetic"

    data_mult = _float(params, f"global.{code}.dataUnitsMultiplier", 1.0)
    model_mult = _float(params, f"global.{code}.modelUnitsMultiplier", 1.0)
    beta = _float(params, f"forward.depthWeighting.{code}.power",
                  params.get("forward.depthWeighting.power") or (2.0 if exp_type == 1 else 3.0))

    # --- mesh
    grid_file = _resolve(params.get(f"modelGrid.{code}.file", ""), param_dir)
    if not grid_file or not os.path.exists(grid_file):
        raise FrostError(f"Model grid file not found: {grid_file}")
    try:
        size = [int(v) for v in params["modelGrid.size"].split()[:3]]
    except (KeyError, ValueError):
        raise FrostError("modelGrid.size is missing from the parameter file")
    write(f"Reading model grid {grid_file} ({size[0]} x {size[1]} x {size[2]} cells)")
    x1, x2, y1, y2, z1, z2 = _read_model_grid_axes(grid_file, size, is_cancelled)
    nx, ny, nz = size
    dx = _uniform(x1, x2, "x", write)
    dy = _uniform(y1, y2, "y", write)
    xc = 0.5 * (x1 + x2)
    yc = 0.5 * (y1 + y2)
    zc = 0.5 * (z1 + z2)
    z_edges = np.concatenate([z1, z2[-1:]])
    if np.any(np.abs(z1[1:] - z2[:-1]) > 1e-6 * max(1.0, abs(z2[-1]))):
        raise FrostError("The layers of the model grid are not contiguous in depth")
    _check(is_cancelled)

    # --- data
    data_file = _resolve(params.get(f"forward.data.{code}.dataGridFile", ""), param_dir)
    if not data_file or not os.path.exists(data_file):
        raise FrostError(f"Data file not found: {data_file}")
    write(f"Reading data {data_file}")
    dxs, dys, dzs, dvs = _read_data(data_file)
    ii = np.rint((dxs - xc[0]) / dx).astype(int)
    jj = np.rint((dys - yc[0]) / dy).astype(int)
    inside = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
    inside[inside] &= (np.abs(dxs[inside] - xc[ii[inside]]) < 0.25 * dx) & (
        np.abs(dys[inside] - yc[jj[inside]]) < 0.25 * dy)
    if not inside.any():
        raise FrostError("No data point lies on the centre of a model column: the data must be the grid of the mesh "
                         "(raster data, padding 0)")
    if (~inside).sum():
        write(f"WARNING: {int((~inside).sum())} data points are not on the mesh columns and are ignored")

    # data in the units of fast_inversion: mGal (gravity) or nT (magnetic)
    to_fi = data_mult / 1e-5 if kind == "gravity" else data_mult
    grid = np.full((nx, ny), np.nan)
    grid[ii[inside], jj[inside]] = dvs[inside] * to_fi
    n_missing = int(np.isnan(grid).sum())
    if n_missing:
        write(f"{n_missing} of {nx * ny} grid nodes have no data (filled with the trend, left out of the misfit)")

    # station height above the top of the model (z positive down)
    z_station = float(np.median(dzs[inside]))
    if np.std(dzs[inside]) > 0.01 * min(dx, dy):
        write("WARNING: the stations are not on a level surface; Frost uses their median height")
    top = float(z_edges[0])
    height = top - z_station
    if abs(height) < 1e-6:
        # stations on the model top (sensor height 0, e.g. ground data): the FFT method needs them above it
        height = 1.0
        write("Sensor height is 0: Frost places the stations 1 m above the model top (ground data)")
    elif height < 0:
        raise FrostError("The stations must be above the top of the model: set a sensor height >= 0")
    z_rel = z_edges - top

    field_kw = {}
    if kind == "magnetic":
        if "forward.magneticField.XaxisDeclination" in params:
            raise FrostError("Frost does not support a rotated X axis (forward.magneticField.XaxisDeclination)")
        inc = _float(params, "forward.magneticField.inclination")
        dec = _float(params, "forward.magneticField.declination")
        intensity = _float(params, "forward.magneticField.intensity_nT",
                           params.get("forward.magneticField.intensity", None))
        # x = easting, y = northing: declination measured from +x towards +y is 90 - D
        field_kw = dict(field=intensity, inclination=inc, declination=90.0 - dec)
        write(f"Magnetic field: {intensity:g} nT, inclination {inc:g}, declination {dec:g} (from +x: {90 - dec:g})")

    write(f"Grid {nx} x {ny} stations, dx = {dx:g} m, dy = {dy:g} m; {nz} layers to {z_edges[-1]:g} m")
    write(f"Station height above the model top {height:g} m; depth-weighting power beta = {beta:g}")
    write(f"Data units multiplier {data_mult:g}, model units multiplier {model_mult:g}")
    _check(is_cancelled)

    # --- inversion
    write("")
    write("Running the FFT inversion ...")
    t0 = time.perf_counter()
    writer = _LogWriter(write)
    with redirect_stdout(writer):
        res = fi.invert(grid, dx, dy, z_rel, beta, kind=kind, height=height, detrend="plane", verbose=True,
                        **field_kw)
    writer.flush()
    t_inv = time.perf_counter() - t0
    write(f"Inversion time {t_inv:.2f} s")
    _check(is_cancelled)

    # --- outputs (model in the units Tomofast-x writes: value / modelUnitsMultiplier)
    model = res.model / model_mult
    write("")
    write(f"Model min/max values = {np.nanmin(model):.6g} {np.nanmax(model):.6g}")
    write(f"Data RMS residual = {res.rms:.6g} ({'mGal' if kind == 'gravity' else 'nT'})")

    write("Writing Paraview files to " + paraview_dir)
    _write_vtk_struct_grid(os.path.join(paraview_dir, f"{prefix}_final_model3D_full.vtk"), xc, yc, zc, model, label)
    for axis, rng in (
        ("x", ((nx // 2, nx // 2 + 1), (0, ny), (0, nz))),
        ("y", ((0, nx), (ny // 2, ny // 2 + 1), (0, nz))),
        ("z", ((0, nx), (0, ny), (nz // 2, nz // 2 + 1))),
    ):
        _write_vtk_legogrid(os.path.join(paraview_dir, f"{prefix}_final_model3D_half_{axis}.vtk"),
                            x1, x2, y1, y2, z1, z2, model, *rng, label)
    _check(is_cancelled)

    write("Writing model and data files to " + frost_dir)
    with open(os.path.join(frost_dir, f"{prefix}_final_model_full.txt"), "w") as f:
        f.write(f"{model.size}\n")
        np.savetxt(f, model.transpose(2, 1, 0).ravel(), fmt="%.9g")

    # data back in the units of the input file, at the stations that had data
    from_fi = 1.0 / to_fi
    I, J = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    valid = np.isfinite(grid)
    gx, gy = xc[I[valid]], yc[J[valid]]
    gz = np.full(gx.size, z_station)
    _write_data_file(os.path.join(frost_dir, f"{prefix}_observed_data.txt"), gx, gy, gz, grid[valid] * from_fi)
    _write_data_file(os.path.join(frost_dir, f"{prefix}_calc_final_data.txt"), gx, gy, gz,
                     res.predicted[valid] * from_fi)
    _write_data_file(os.path.join(frost_dir, f"{prefix}_residual_data.txt"), gx, gy, gz,
                     res.residual[valid] * from_fi)

    elapsed = time.perf_counter() - t_start
    summary = {
        "kind": kind, "prefix": prefix, "nx": nx, "ny": ny, "nz": nz, "dx": dx, "dy": dy,
        "beta": beta, "height": height, "mu": float(res.mu), "rms": float(res.rms),
        "rms_filter": float(res.rms_filter), "model_min": float(np.nanmin(model)),
        "model_max": float(np.nanmax(model)), "n_missing": n_missing, "inversion_time_s": t_inv,
        "total_time_s": elapsed, "paraview_dir": paraview_dir, "frost_dir": frost_dir,
    }
    with open(os.path.join(frost_dir, "frost_summary.txt"), "w") as f:
        f.write("Frost (FFT) inversion summary\n")
        f.write(f"parameter file          = {param_path}\n")
        for key, value in summary.items():
            f.write(f"{key:<23} = {value}\n")

    # keep a copy of the parameter file with the results, as Tomofast-x does
    try:
        shutil.copyfile(param_path, os.path.join(out_dir, os.path.basename(param_path)))
    except OSError:
        pass

    write(f"Total time {elapsed:.2f} s")
    return summary


def _check(is_cancelled):
    if is_cancelled is not None and is_cancelled():
        raise FrostCancelled("Frost inversion cancelled by the user")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python frost_runner.py <paramfile>")
    run_frost(sys.argv[1], log=lambda line: sys.__stdout__.write(line + "\n"))
