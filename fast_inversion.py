"""
fast_inversion.py - depth-weighted inversion of gridded gravity or magnetic data with fast Fourier transforms.

The inversion considered is the usual depth-weighted, smallest-model inversion with a penalty (no bounds, no smoothness
terms), the minimiser of

        sum over stations (d - G m)^2  +  mu * sum over cells dz * w(z)^2 (m - m_ref)^2 ,     w(z) = (z + Z0)^(-beta/2),

where dz is the thickness of the layer of the cell: the model norm is weighted by the volume of the cells (all cells
have the same horizontal size).  For layers of equal thickness this is the usual sum over cells, with a rescaled mu; for
layers of unequal thickness it is the discretisation of the integral of w^2 (m - m_ref)^2 over the volume.

For data on a regular grid on a level surface this minimiser is, for every horizontal wavevector, a filter applied to the
data, so it can be computed with one two-dimensional FFT per layer of the mesh and without a sensitivity matrix.  The
penalty mu is chosen so that the residual of the filter equals the noise level that you give (discrepancy principle),
or you can set it yourself.

What is computed, exactly.  The filter is the exact minimiser for a grid that is padded and periodic.  The model returned
is the part of that solution below the data grid, so it is an approximation to the minimiser of the problem on the
finite grid: close to it (a few per cent) for anomalies inside the grid, less close for anomalies cut by the edge of
the grid (README.md of the package, section Accuracy).  For that reason two sets of misfit numbers are returned:
    predicted, residual, rms, chi2    of the MODEL RETURNED, computed by forward modelling it on a grid padded 4 times
                                      (these describe the model that you get; check_pad=None skips this step);
    rms_filter, chi2_filter           of the filter on the padded grid (the quantity that the choice of mu controls).
Missing data (NaN) are filled with the trend before the filter is applied and are left out of the misfit; this is not
the same as solving the inverse problem with those stations removed.

Conventions
    data[i, j]      value at x = i*dx, y = j*dy  (first array axis = x, second = y)
    model[i, j, l]  cell (i, j) below station (i, j), layer l between depths z_edges[l] and z_edges[l+1]
    z               positive downward, measured from the ground surface; the stations are 'height' above it
    gravity         data in mGal, model = density contrast in kg/m3
    gradient        vertical gravity gradient in Eotvos, model in kg/m3
    magnetic        total-field anomaly in nT, model = susceptibility in SI (induced magnetisation by default)
                    field direction: inclination (positive down) and declination measured from the +x axis towards +y;
                    if x is north and y is east, this is the usual declination.

Reference: V. Ogarko et al., "Which depth-weighting exponent? ..." (manuscript, 2026), Section 6.3 and Appendix A.
Requires numpy and scipy.   Command line:  python fast_inversion.py --help
"""
from dataclasses import dataclass
import numpy as np
from scipy import fft as sfft
from scipy.optimize import brentq

GAMMA = 6.674e-11          # gravitational constant, SI
__version__ = '1.2.1'
DIRECTION_TOL = 1e-12      # magnetic data: direction factors smaller than this are treated as exactly zero
__all__ = ['invert', 'forward', 'Result', 'save_vtk']


@dataclass
class Result:
    model: np.ndarray        # (nx, ny, nz) recovered property (including the reference model, if any)
    predicted: np.ndarray    # (nx, ny) data of the model returned, forward modelled (plus the trend that was removed)
    residual: np.ndarray     # (nx, ny) observed - predicted (NaN where the data were missing)
    mu: float                # penalty used (in the internal units of the filter)
    chi2: float              # mean squared residual of the model returned / noise_std^2 (nan if no noise level given)
    rms: float               # root-mean-square residual of the model returned, in data units
    trend: np.ndarray        # (nx, ny) mean or plane removed from the data before the inversion (zeros if none)
    z_centres: np.ndarray    # depth of the layer centres below the ground surface
    rms_filter: float = float('nan')     # rms residual of the filter on the padded, periodic grid (what mu was tuned on)
    chi2_filter: float = float('nan')    # the same, squared and divided by noise_std^2
    misfit_of: str = 'model'             # 'model': predicted, residual, rms, chi2 are those of the model returned;
                                         # 'filter': the forward calculation was skipped (check_pad=None) and they are those of the filter


# ----------------------------------------------------------------------------------------------------------------------
def _direction(inc, dec):
    i, d = np.radians(inc), np.radians(dec)
    v = np.array([np.cos(i) * np.cos(d), np.cos(i) * np.sin(d), np.sin(i)])          # (x, y, z down)
    v[np.abs(v) < 1e-12] = 0.0          # e.g. cos(90 deg) = 6e-17: keep unobservable wavenumbers exactly unobservable
    return v


def _padded_shape(shape, pad):
    return tuple(sfft.next_fast_len(int(np.ceil(pad * n)), real=True) for n in shape)


def _spectral_setup(shape, padded, dx, dy, kind, field=None, inclination=None, declination=0.0,
                    mag_inclination=None, mag_declination=None):
    """Wavenumbers (rfft2 layout) and the factor C(k) that relates the spectrum of the data to that of a thin sheet:
    data_hat = C(k) * sum over layers [ model_hat_l * integral over the layer of exp(-k z) dz ]."""
    kx = 2 * np.pi * sfft.fftfreq(padded[0], dx)[:, None]
    ky = 2 * np.pi * sfft.rfftfreq(padded[1], dy)[None, :]
    k = np.sqrt(kx ** 2 + ky ** 2)
    ks = np.where(k > 0, k, 1.0)
    cell = np.sinc(kx * dx / (2 * np.pi)) * np.sinc(ky * dy / (2 * np.pi))             # horizontal extent of a cell
    if kind == 'gravity':
        C = 2 * np.pi * GAMMA * 1e5 * cell + 0j
    elif kind == 'gradient':
        C = 2 * np.pi * GAMMA * 1e9 * k * cell + 0j
    elif kind == 'magnetic':
        if field is None or inclination is None:
            raise ValueError("magnetic data need 'field' (nT) and 'inclination' (degrees)")
        f = _direction(inclination, declination)
        m = f if mag_inclination is None else _direction(mag_inclination, declination if mag_declination is None else mag_declination)
        th_f = f[2] + 1j * (f[0] * kx + f[1] * ky) / ks
        th_m = m[2] + 1j * (m[0] * kx + m[1] * ky) / ks
        C = 0.5 * field * k * th_f * th_m * cell
        C[0, 0] = 0.0
    else:
        raise ValueError("kind must be 'gravity', 'gradient' or 'magnetic'")
    # A real grid has a spectrum with conjugate symmetry.  In the half-spectrum stored by rfft2 the columns ky = 0 and
    # ky = Nyquist contain both members of each conjugate pair, and irfft2 uses only the symmetric part of what it is given
    # there.  The forward operator that is actually applied (rfft2, multiply by C, irfft2) therefore has the symmetrised C
    # in those columns.  For an inclined magnetic field C is complex and the Nyquist terms are not symmetric, so C is
    # symmetrised here: the filter then uses exactly the operator that the forward calculation applies.  (For gravity and
    # gradient data, and for a vertical field, C is real and even and nothing changes.)
    partner = (-np.arange(padded[0])) % padded[0]
    for j in ([0] + ([padded[1] // 2] if padded[1] % 2 == 0 else [])):
        C[:, j] = 0.5 * (C[:, j] + np.conj(C[partner, j]))
    if kind == 'magnetic':
        # Wavenumbers that the field direction makes unobservable (direction factor exactly zero, for example the
        # wavevectors perpendicular to a horizontal field, or the Nyquist terms at an inclination of 45 degrees) come out
        # of the arithmetic as rounding noise of relative size 1e-16, and with mu = 0 the filter would divide by it.  A
        # direction factor below DIRECTION_TOL (1e-12) is therefore set to zero: such a wavenumber is treated as
        # unobservable and is left in the residual.
        C[np.abs(C) <= DIRECTION_TOL * np.abs(0.5 * field * k * cell)] = 0.0
    return k, ks, C


def _layer_kernel(k, ks, zt, zb):
    """integral of exp(-k z) over the layer zt < z < zb"""
    return np.where(k > 0, (np.exp(-ks * zt) - np.exp(-ks * zb)) / ks, zb - zt)


def _pad(a, padded, mode):
    n1, n2 = a.shape; N1, N2 = padded
    o1, o2 = (N1 - n1) // 2, (N2 - n2) // 2
    if mode == 'zero':
        big = np.zeros(padded); big[o1:o1 + n1, o2:o2 + n2] = a
    elif mode == 'taper':                       # extend the edge values and bring them smoothly to zero
        big = np.pad(a, ((o1, N1 - n1 - o1), (o2, N2 - n2 - o2)), mode='edge')

        def window(n, N, o):
            w = np.ones(N)
            if o > 0:
                w[:o] = 0.5 * (1 - np.cos(np.pi * (np.arange(o) + 0.5) / o))
            r = N - n - o
            if r > 0:
                w[o + n:] = 0.5 * (1 + np.cos(np.pi * (np.arange(r) + 0.5) / r))
            return w
        big *= window(n1, N1, o1)[:, None] * window(n2, N2, o2)[None, :]
    else:
        raise ValueError("pad_mode must be 'taper' or 'zero'")
    return big, (o1, o2)


def _layers(z_edges, height):
    z_edges = np.asarray(z_edges, float)
    if z_edges.ndim != 1 or z_edges.size < 2 or np.any(np.diff(z_edges) <= 0) or z_edges[0] < 0:
        raise ValueError('z_edges must be increasing depths (m) of the layer boundaries, starting at or below 0')
    if height < 0 or (height == 0 and z_edges[0] == 0):
        raise ValueError("the stations must be above the top of the model: give height > 0 (m)")
    return z_edges, 0.5 * (z_edges[1:] + z_edges[:-1]), np.diff(z_edges)


# ----------------------------------------------------------------------------------------------------------------------
def forward(model, dx, dy, z_edges, kind='gravity', height=1.0, pad=4.0, **field_kw):
    """Data on the station grid of a model given on the mesh (nx, ny, nz), computed with FFTs.
    The model is surrounded by zeros up to 'pad' times the grid, and the padded grid is periodic, so the data contain the
    effect of the periodic copies of the model.  For a model that fills the grid this error is about 1 per cent of the
    largest datum for pad = 2, 0.1 per cent for pad = 4 and 0.05 per cent for pad = 6; it is smaller for a compact body.
    field_kw: for kind='magnetic', field=..., inclination=..., declination=... (see the module docstring)."""
    model = np.asarray(model, float)
    z_edges, zc, dz = _layers(z_edges, height)
    shape = model.shape[:2]; padded = _padded_shape(shape, pad)
    k, ks, C = _spectral_setup(shape, padded, dx, dy, kind, **field_kw)
    acc = np.zeros(k.shape, complex)
    for l in range(zc.size):
        if model[:, :, l].any():
            big, (o1, o2) = _pad(model[:, :, l], padded, 'zero')
            acc += sfft.rfft2(big, workers=-1) * _layer_kernel(k, ks, z_edges[l] + height, z_edges[l + 1] + height)
    o1, o2 = (padded[0] - shape[0]) // 2, (padded[1] - shape[1]) // 2
    return sfft.irfft2(acc * C, s=padded, workers=-1)[o1:o1 + shape[0], o2:o2 + shape[1]]


def invert(data, dx, dy, z_edges, beta, kind='gravity', height=1.0, noise_std=None, mu=None, Z0=0.0,
           reference=None, detrend=None, pad=2.0, pad_mode='taper', check_pad=4.0, dtype=np.float64, verbose=False,
           **field_kw):
    """Depth-weighted inversion of a data grid with FFTs.

    data       2-D array (nx, ny); NaN marks missing values (they are filled with the trend and left out of the misfit)
    dx, dy     station spacing along the first and second array axes (m)
    z_edges    depths (m, positive down, from the ground surface) of the layer boundaries, e.g. np.arange(33) * 50.0
    beta       exponent of the depth weighting w = (z + Z0)^(-beta/2), z = depth below the stations
    kind       'gravity' (mGal -> kg/m3), 'gradient' (Eotvos -> kg/m3) or 'magnetic' (nT -> SI)
    height     height of the stations above the ground surface (m), > 0
    noise_std  standard deviation of the noise, in data units: the penalty is chosen so that the root-mean-square
               residual of the filter equals it (the model returned then fits to about the same level; see chi2).  Give either noise_std or mu; with neither, 2 per cent of the largest |datum| is used.
    mu         penalty, relative to the largest value of the filter denominator (dimensionless); 0 fits exactly, on the
               padded periodic grid, every wavenumber that the data type can observe (it also fits the noise)
    reference  optional reference model (nx, ny, nz): the norm then measures the departure from it
    detrend    None, 'mean' or 'plane': removed from the data before the inversion (recommended for field data)
    pad        size of the padded grid relative to the data grid (>= 1); pad_mode 'taper' (edge values brought smoothly
               to zero; use for field data) or 'zero'
    check_pad  padding of the forward calculation that gives the data and the misfit of the model returned (default 4;
               it is not smaller than pad).  None or 0 skips this calculation, which takes several times longer than
               the inversion itself for large grids: predicted, residual, rms and chi2 are then those of the filter
               (Result.misfit_of == 'filter').
    field_kw   for kind='magnetic': field (nT), inclination, declination (degrees); optional mag_inclination,
               mag_declination for a magnetisation that is not along the field
    Returns a Result (model, predicted, residual, mu, chi2, rms, trend, z_centres, rms_filter, chi2_filter).
    predicted, residual, rms and chi2 are those of the model returned; rms_filter and chi2_filter those of the filter.
    """
    d = np.array(data, float)
    if d.ndim != 2:
        raise ValueError('data must be a 2-D grid')
    valid = np.isfinite(d)
    if not valid.any():
        raise ValueError('the data grid contains no finite value')
    if noise_std is not None and not (np.isfinite(noise_std) and noise_std > 0):
        raise ValueError('noise_std must be a positive number (or None)')
    if mu is not None and not (np.isfinite(mu) and mu >= 0):
        raise ValueError('mu must be zero or positive (or None)')
    z_edges, zc, dz = _layers(z_edges, height)
    nz = zc.size; shape = d.shape; padded = _padded_shape(shape, pad)
    # --- trend
    trend = np.zeros(shape)
    if detrend == 'mean':
        trend[:] = d[valid].mean()
    elif detrend == 'plane':
        X, Y = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing='ij')
        A = np.c_[np.ones(valid.sum()), X[valid], Y[valid]]
        co = np.linalg.lstsq(A, d[valid], rcond=None)[0]
        trend = co[0] + co[1] * X + co[2] * Y
    elif detrend is not None:
        raise ValueError("detrend must be None, 'mean' or 'plane'")
    r = np.where(valid, d - trend, 0.0)
    # --- reference model
    ref_data = 0.0
    if reference is not None:
        reference = np.asarray(reference, float)
        if reference.shape != shape + (nz,):
            raise ValueError('reference must have shape (nx, ny, nz)')
        ref_data = forward(reference, dx, dy, z_edges, kind, height, max(float(pad), 4.0), **field_kw)
        r = np.where(valid, r - ref_data, 0.0)
    if np.abs(r[valid]).max() == 0.0:
        # nothing to explain (zero data, constant data with the mean removed, or data equal to those of the reference
        # model): the minimiser is the reference model itself, or zero
        model = np.zeros(shape + (nz,), dtype=dtype) if reference is None else reference.astype(dtype)
        pred = ref_data + trend
        if verbose:
            print('fast inversion: the data to be explained are identically zero; the %s model is returned' %
                  ('zero' if reference is None else 'reference'))
        z0 = 0.0 if noise_std else float('nan')
        return Result(model=model, predicted=pred, residual=np.where(valid, d - pred, np.nan),
                      mu=float('inf') if mu is None else float(mu), chi2=z0,
                      rms=0.0, trend=trend, z_centres=zc, rms_filter=0.0, chi2_filter=z0)
    if noise_std is None and mu is None:
        noise_std = 0.02 * np.abs(r[valid]).max()
        if verbose:
            print('noise_std not given: using 2 per cent of the largest datum, %.4g' % noise_std)
    # --- spectra
    k, ks, C = _spectral_setup(shape, padded, dx, dy, kind, **field_kw)
    wz = (zc + height + Z0) ** beta; wz = wz / wz.max()               # inverse squared depth weight of each layer
    lam = np.zeros(k.shape)
    for l in range(nz):
        E = _layer_kernel(k, ks, z_edges[l] + height, z_edges[l + 1] + height)
        lam += wz[l] * E * E / dz[l]
    lam *= np.abs(C) ** 2                                            # the data-space operator G W^-2 G^T, per wavevector
    lam_max = lam.max()
    big, (o1, o2) = _pad(r, padded, pad_mode)
    rh = sfft.rfft2(big, workers=-1)
    crop = (slice(o1, o1 + shape[0]), slice(o2, o2 + shape[1]))

    def ratio(num, m_):                                             # num / (lam + m_), zero where lam + m_ = 0
        den = lam + m_
        return np.divide(num, den, out=np.zeros(num.shape, num.dtype), where=den > 0)

    def predicted_for(m_):
        return sfft.irfft2(rh * ratio(lam, m_), s=padded, workers=-1)[crop]

    if mu is not None:
        mu_abs = float(mu) * lam_max
    else:
        def chi(log_mu):
            return np.mean((r - predicted_for(np.exp(log_mu)))[valid] ** 2) / noise_std ** 2 - 1.0
        lo, hi = np.log(lam_max * 1e-14), np.log(lam_max * 1e4)
        if chi(lo) > 0:
            mu_abs = np.exp(lo)
            if verbose:
                print('warning: the data cannot be fitted to the noise level given; smallest penalty used')
        elif chi(hi) < 0:
            mu_abs = np.exp(hi)
            if verbose:
                print('warning: the data are below the noise level given; the model is close to the reference model')
        else:
            mu_abs = np.exp(brentq(chi, lo, hi, xtol=1e-3))
    # --- model, layer by layer
    core = ratio(rh * np.conj(C), mu_abs)
    model = np.empty(shape + (nz,), dtype=dtype)
    for l in range(nz):
        E = _layer_kernel(k, ks, z_edges[l] + height, z_edges[l + 1] + height)
        model[:, :, l] = sfft.irfft2(core * (wz[l] / dz[l]) * E, s=padded, workers=-1)[crop]
    if reference is not None:
        model += reference.astype(dtype)
    # --- misfit of the filter on the padded, periodic grid (the quantity that mu was tuned on) ...
    rms_f = float(np.sqrt(np.mean((r - predicted_for(mu_abs))[valid] ** 2)))
    # --- ... and of the model that is returned (the part below the data grid), by forward modelling it
    if check_pad:
        pred = forward(model, dx, dy, z_edges, kind, height, max(float(pad), float(check_pad)), **field_kw) + trend
        of = 'model'
    else:
        pred = predicted_for(mu_abs) + ref_data + trend
        of = 'filter'
    res = np.where(valid, d - pred, np.nan)
    rms = float(np.sqrt(np.nanmean(res ** 2)))
    c2 = (lambda x: (x / noise_std) ** 2 if noise_std else float('nan'))
    out = Result(model=model, predicted=pred, residual=res, mu=mu_abs / lam_max, chi2=c2(rms), rms=rms, trend=trend,
                 z_centres=zc, rms_filter=rms_f, chi2_filter=c2(rms_f), misfit_of=of)
    if verbose:
        print('fast inversion: %d x %d data, %d layers, beta = %g, penalty %.3g' % (shape[0], shape[1], nz, beta, out.mu))
        if of == 'model':
            print('  rms residual of the model returned %.4g; of the filter on the padded grid %.4g%s' %
                  (rms, rms_f, '' if not noise_std else '; noise level %.4g' % noise_std))
        else:
            print('  rms residual of the filter on the padded grid %.4g%s (the model returned was not forward modelled)' %
                  (rms_f, '' if not noise_std else '; noise level %.4g' % noise_std))
        if of == 'model' and rms > 1.25 * max(rms_f, 1e-300) and (noise_std is None or rms > 1.25 * noise_std):
            print('  note: the model returned fits the data less well than the filter; anomalies probably reach the edge '
                  'of the grid (see README, Accuracy)')
    return out


# ---------------------------------------------------------------------------------------------------------------------- output
def save_vtk(filename, model, dx, dy, z_edges, x0=0.0, y0=0.0, name='property'):
    """Write the model as a legacy VTK rectilinear grid (cell data) for ParaView.  The vertical coordinate is the
    elevation (negative depth), so the model appears the right way up.  x0, y0: coordinates of the first station."""
    model = np.asarray(model); nx, ny, nz = model.shape
    z_edges = np.asarray(z_edges, float)
    xs = x0 + (np.arange(nx + 1) - 0.5) * dx; ys = y0 + (np.arange(ny + 1) - 0.5) * dy; zs = -z_edges[::-1]
    with open(filename, 'wb') as f:
        f.write(b'# vtk DataFile Version 3.0\nfast inversion model\nBINARY\nDATASET RECTILINEAR_GRID\n')
        f.write(('DIMENSIONS %d %d %d\n' % (nx + 1, ny + 1, nz + 1)).encode())
        for lab, c in (('X', xs), ('Y', ys), ('Z', zs)):
            f.write(('%s_COORDINATES %d double\n' % (lab, c.size)).encode()); f.write(c.astype('>f8').tobytes()); f.write(b'\n')
        f.write(('CELL_DATA %d\nSCALARS %s float 1\nLOOKUP_TABLE default\n' % (nx * ny * nz, name)).encode())
        f.write(np.ascontiguousarray(model[:, :, ::-1].transpose(2, 1, 0)).astype('>f4').tobytes()); f.write(b'\n')


def load_grid(path):
    """Read a data grid.  Returns (data[nx, ny], dx, dy, x0, y0); dx, dy, x0, y0 are None when the file does not give them.
      .npy            2-D array, first axis = x
      .asc            ESRI ASCII grid (rows from north to south): returned with first axis = easting, second = northing
      .csv/.txt/.xyz  three columns x, y, value on a complete regular grid (any order of the points)
      .tif/.tiff      GeoTIFF, if the package 'rasterio' is installed (as for .asc)"""
    ext = path.lower().rsplit('.', 1)[-1]
    if ext == 'npy':
        return np.load(path).astype(float), None, None, None, None
    if ext == 'asc':
        hdr = {}
        with open(path) as f:
            for _ in range(6):
                a, b = f.readline().split(); hdr[a.lower()] = float(b)
            g = np.loadtxt(f)
        g = np.where(g == hdr.get('nodata_value', -9999.0), np.nan, g)
        cs = hdr['cellsize']
        x0 = hdr['xllcorner'] + cs / 2 if 'xllcorner' in hdr else hdr['xllcenter']
        y0 = hdr['yllcorner'] + cs / 2 if 'yllcorner' in hdr else hdr['yllcenter']
        return g[::-1].T.copy(), cs, cs, x0, y0
    if ext in ('tif', 'tiff'):
        import rasterio
        with rasterio.open(path) as src:
            g = src.read(1).astype(float); t = src.transform
            if src.nodata is not None:
                g[g == src.nodata] = np.nan
        return g[::-1].T.copy(), abs(t.a), abs(t.e), t.c + t.a / 2, t.f + t.e * (g.shape[0] - 0.5)
    a = np.loadtxt(path, delimiter=',' if ext == 'csv' else None, comments='#')
    xu, yu = np.unique(a[:, 0]), np.unique(a[:, 1])
    if xu.size * yu.size != a.shape[0]:
        raise ValueError('the x, y, value file is not a complete regular grid (%d points, %d x %d)' % (a.shape[0], xu.size, yu.size))
    g = np.full((xu.size, yu.size), np.nan)
    g[np.searchsorted(xu, a[:, 0]), np.searchsorted(yu, a[:, 1])] = a[:, 2]
    return g, float(xu[1] - xu[0]), float(yu[1] - yu[0]), float(xu[0]), float(yu[0])


def _main():
    import argparse, time
    p = argparse.ArgumentParser(description='Fast depth-weighted inversion of gridded gravity or magnetic data (FFT).')
    p.add_argument('data', help='data grid: .npy, .asc (ESRI ASCII), .csv/.txt/.xyz (x, y, value) or GeoTIFF')
    p.add_argument('--kind', default='gravity', choices=['gravity', 'gradient', 'magnetic'])
    p.add_argument('--dx', type=float, help='station spacing along x (m); needed for .npy'); p.add_argument('--dy', type=float)
    p.add_argument('--nz', type=int, default=32, help='number of layers (default 32)')
    p.add_argument('--dz', type=float, help='layer thickness (m); default: half the station spacing')
    p.add_argument('--beta', type=float, help='exponent of the depth weighting (default 2.5 for gravity, 2.7 for magnetic and gradient data)')
    p.add_argument('--noise', type=float, help='noise standard deviation in data units (default: 2 %% of the largest datum)')
    p.add_argument('--mu', type=float, help='penalty (relative), in place of --noise')
    p.add_argument('--height', type=float, default=1.0, help='height of the stations above the ground (m)')
    p.add_argument('--detrend', default='plane', choices=['none', 'mean', 'plane'])
    p.add_argument('--pad', type=float, default=2.0)
    p.add_argument('--check-pad', type=float, default=4.0, help='padding of the forward calculation of the model returned (0: skip it)')
    p.add_argument('--field', type=float, help='magnetic: field strength (nT)')
    p.add_argument('--inc', type=float, help='magnetic: inclination (degrees, positive down)')
    p.add_argument('--dec', type=float, default=0.0, help='magnetic: declination from the +x axis towards +y (degrees)')
    p.add_argument('--out', default='fast_model', help='prefix of the output files')
    a = p.parse_args()
    d, dx, dy, x0, y0 = load_grid(a.data)
    dx = a.dx or dx; dy = a.dy or dy or dx
    if dx is None:
        p.error('--dx is needed for this file type')
    dz = a.dz or 0.5 * min(dx, dy)
    z_edges = np.arange(a.nz + 1) * dz
    beta = a.beta if a.beta is not None else (2.5 if a.kind == 'gravity' else 2.7)   # gradient data behave as magnetic
    kw = dict(field=a.field, inclination=a.inc, declination=a.dec) if a.kind == 'magnetic' else {}
    t0 = time.perf_counter()
    res = invert(d, dx, dy, z_edges, beta, kind=a.kind, height=a.height, noise_std=a.noise, mu=a.mu,
                 detrend=None if a.detrend == 'none' else a.detrend, pad=a.pad, check_pad=a.check_pad, verbose=True, **kw)
    print('time: %.2f s' % (time.perf_counter() - t0))
    np.save(a.out + '_model.npy', res.model); np.save(a.out + '_predicted.npy', res.predicted); np.save(a.out + '_residual.npy', res.residual)
    save_vtk(a.out + '.vtk', res.model, dx, dy, z_edges, x0 or 0.0, y0 or 0.0, 'density' if a.kind != 'magnetic' else 'susceptibility')
    print('written: %s_model.npy, %s_predicted.npy, %s_residual.npy, %s.vtk' % ((a.out,) * 4))


if __name__ == '__main__':
    _main()
