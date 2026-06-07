# -*- coding: utf-8 -*-
"""
Tkinter UI for Tomofast-x ArcGIS port.
Provides widget proxies with Qt-compatible API so tomofast_arcgis.py
can call .value(), .setValue(), .text(), .setText(), .isChecked(), etc.
"""
import tkinter as tk
from tkinter import ttk
import platform

# ---------------------------------------------------------------------------
# Widget proxy classes — expose Qt-style API on top of tkinter variables
# ---------------------------------------------------------------------------

class _WidgetProxy:
    """General-purpose wrapper around a tk variable + optional widget."""

    def __init__(self, var, widget=None):
        self._var = var
        self._widget = widget

    # ---- value accessors ----
    def get(self):          return self._var.get()
    def set(self, x):       self._var.set(x)
    def value(self):        return self._var.get()
    def setValue(self, x):  self._var.set(x)

    # ---- text accessors ----
    def text(self):         return str(self._var.get())
    def setText(self, x):   self._var.set(x)
    def clear(self):        self._var.set("" if isinstance(self._var, tk.StringVar) else 0)

    # ---- checked accessors ----
    def isChecked(self):        return bool(self._var.get())
    def setChecked(self, x):    self._var.set(1 if x else 0)
    def toggled(self):          pass

    # ---- combo accessors ----
    def currentText(self):  return str(self._var.get())
    def addItems(self, items):
        if self._widget and hasattr(self._widget, "configure"):
            self._widget.configure(values=list(items))
        if items and not self._var.get():
            self._var.set(items[0])
    def setCurrentIndex(self, i):
        if self._widget and hasattr(self._widget, "cget"):
            vals = self._widget.cget("values")
            if vals and i < len(vals):
                self._var.set(vals[i])

    # ---- text widget accessors ----
    def toPlainText(self):
        if self._widget and hasattr(self._widget, "get"):
            try:
                return self._widget.get("1.0", tk.END).strip()
            except Exception:
                pass
        return str(self._var.get())

    def insertPlainText(self, x):
        if self._widget and hasattr(self._widget, "insert"):
            self._widget.insert(tk.END, x)
        else:
            self._var.set(str(self._var.get()) + str(x))

    def moveCursor(self, pos):
        if self._widget and hasattr(self._widget, "see"):
            self._widget.see(tk.END)

    # ---- state ----
    def setEnabled(self, state):
        if self._widget:
            try:
                self._widget.configure(state="normal" if state else "disabled")
            except Exception:
                pass

    def setToolTip(self, txt):
        pass   # tooltips not implemented in this version

    def configure(self, **kw):
        if self._widget:
            try:
                self._widget.configure(**kw)
            except Exception:
                pass

    # ---- CRS widget interface ----
    def setCrs(self, crs):
        """Accept a string EPSG ('EPSG:4326') or object with .authid()."""
        if hasattr(crs, "authid"):
            self._var.set(crs.authid())
        else:
            self._var.set(str(crs))

    def crs(self):
        class _CRS:
            def __init__(self, epsg):
                self._epsg = epsg
            def authid(self):
                return self._epsg
        return _CRS(self._var.get())

    # ---- Date widget interface ----
    def date(self):
        """Return object with .toPyDate() that parses yyyy-mm-dd string."""
        import datetime
        val = str(self._var.get())
        class _Date:
            def __init__(self, s):
                try:
                    parts = s.split("-")
                    self._d = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                except Exception:
                    self._d = datetime.date.today()
            def toPyDate(self):
                return self._d
        return _Date(val)

    def setDisplayFormat(self, fmt):    pass


class _RadioProxy(_WidgetProxy):
    """Proxy for one radio button in a shared IntVar group."""

    def __init__(self, group_var, value, widget=None):
        self._group = group_var
        self._value = value
        self._widget = widget
        self._var = group_var   # needed for base _WidgetProxy methods

    def isChecked(self):        return self._group.get() == self._value
    def setChecked(self, x):
        if x:
            self._group.set(self._value)


class _GroupBoxProxy:
    """Proxy for a ttk.LabelFrame; setEnabled() cascades to children."""

    def __init__(self, frame):
        self._frame = frame

    def setEnabled(self, state):
        s = "normal" if state else "disabled"
        try:
            for child in self._frame.winfo_children():
                try:
                    child.configure(state=s)
                except Exception:
                    pass
        except Exception:
            pass

    def setToolTip(self, txt):  pass


class _LabelProxy:
    """Proxy for a ttk.Label backed by a StringVar."""
    def __init__(self, var, widget=None):
        self._var = var
        self._widget = widget
    def text(self):         return self._var.get()
    def setText(self, x):   self._var.set(str(x))
    def setToolTip(self, x): pass
    def setEnabled(self, x): pass


# ---------------------------------------------------------------------------
# Main UI class
# ---------------------------------------------------------------------------

class TomofastUI:
    """
    Builds the full tkinter window and exposes all widget attributes with
    the same names used in Tomofast_x.py (QGIS version), but backed by
    tkinter variables and proxy objects.
    """

    def __init__(self, root):
        self.root = root
        root.title("Tomofast-x")
        root.geometry("860x900")

        # ---- notebook (tabs) ----
        nb = ttk.Notebook(root)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        tab_data   = ttk.Frame(nb); nb.add(tab_data,   text="Data")
        tab_mesh   = ttk.Frame(nb); nb.add(tab_mesh,   text="Mesh")
        tab_inv    = ttk.Frame(nb); nb.add(tab_inv,    text="Inversion")
        tab_run    = ttk.Frame(nb); nb.add(tab_run,    text="Run")
        tab_export = ttk.Frame(nb); nb.add(tab_export, text="Export")

        # scrollable frames for each tab
        tab_data   = self._scrollable(tab_data)
        tab_mesh   = self._scrollable(tab_mesh)
        tab_inv    = self._scrollable(tab_inv)
        tab_run    = self._scrollable(tab_run)
        tab_export = self._scrollable(tab_export)

        self._build_data_tab(tab_data)
        self._build_mesh_tab(tab_mesh)
        self._build_inversion_tab(tab_inv)
        self._build_run_tab(tab_run)
        self._build_export_tab(tab_export)

        # Patch setEnabled / setToolTip onto every raw ttk.Button attribute so
        # that the mixin code can call .setEnabled(True/False) on any button.
        def _make_set_enabled(w):
            def _se(enabled, _btn=w):
                try:
                    _btn.configure(state="normal" if enabled else "disabled")
                except Exception:
                    pass
            return _se

        for _attr_val in vars(self).values():
            if isinstance(_attr_val, ttk.Button):
                _attr_val.setEnabled = _make_set_enabled(_attr_val)
                _attr_val.setToolTip = lambda _: None

    # ---- helpers ----

    def _scrollable(self, parent):
        """Return a scrollable inner frame for a tab."""
        canvas = tk.Canvas(parent, borderwidth=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        inner.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        return inner

    def _row(self, parent, row, label, widget, colspan=1):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=2)
        widget.grid(row=row, column=1, columnspan=colspan, sticky="we", padx=4, pady=2)
        parent.columnconfigure(1, weight=1)

    def _section(self, parent, row, title):
        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="we", pady=4)
        ttk.Label(parent, text=title, font=("", 9, "bold")).grid(
            row=row+1, column=0, columnspan=3, sticky="w", padx=4)
        return row + 2

    def _entry(self, parent, var, width=40):
        e = ttk.Entry(parent, textvariable=var, width=width)
        return e, _WidgetProxy(var, e)

    def _spinbox_int(self, parent, var, frm=-9999999, to=9999999, wid=12):
        sb = ttk.Spinbox(parent, textvariable=var, from_=frm, to=to, width=wid)
        return sb, _WidgetProxy(var, sb)

    def _spinbox_dbl(self, parent, var, frm=-1e15, to=1e15, inc=0.01, wid=12):
        sb = ttk.Spinbox(parent, textvariable=var, from_=frm, to=to,
                         increment=inc, width=wid, format="%.6f")
        return sb, _WidgetProxy(var, sb)

    def _combobox(self, parent, var, width=20):
        cb = ttk.Combobox(parent, textvariable=var, width=width, state="readonly")
        return cb, _WidgetProxy(var, cb)

    def _check(self, parent, var, text=""):
        cb = ttk.Checkbutton(parent, variable=var, text=text)
        return cb, _WidgetProxy(var, cb)

    def _text(self, parent, height=3, width=40):
        sv = tk.StringVar()
        t = tk.Text(parent, height=height, width=width)
        proxy = _WidgetProxy(sv, t)
        # Override toPlainText/setText to use tk.Text directly
        def _toPlain():
            return t.get("1.0", tk.END).strip()
        def _setTxt(x):
            t.delete("1.0", tk.END)
            t.insert("1.0", str(x))
        def _insertPlain(x):
            t.insert(tk.END, x)
        proxy.toPlainText = _toPlain
        proxy.setText = _setTxt
        proxy.insertPlainText = _insertPlain
        proxy.clear = lambda: t.delete("1.0", tk.END)
        proxy.moveCursor = lambda pos: t.see(tk.END)
        return t, proxy

    def _label_var(self, parent, text="0", width=10):
        sv = tk.StringVar(value=text)
        lbl = ttk.Label(parent, textvariable=sv, width=width, relief="sunken",
                        anchor="center")
        return lbl, _LabelProxy(sv, lbl)

    def _crs_entry(self, parent, default="EPSG:4326"):
        sv = tk.StringVar(value=default)
        e = ttk.Entry(parent, textvariable=sv, width=14)
        return e, _WidgetProxy(sv, e)

    def _browse_btn(self, parent, text="...", cmd=None):
        b = ttk.Button(parent, text=text, command=cmd, width=4)
        return b

    # ====================================================================
    # DATA tab
    # ====================================================================

    def _build_data_tab(self, p):
        r = 0

        # ---- Inversion type ----
        r = self._section(p, r, "Experiment Type")
        inv_var = tk.IntVar(value=1)
        self._inv_type_var = inv_var

        f_inv = ttk.Frame(p)
        f_inv.grid(row=r, column=0, columnspan=3, sticky="w", padx=4)
        rb_g = ttk.Radiobutton(f_inv, text="Gravity", variable=inv_var, value=1)
        rb_m = ttk.Radiobutton(f_inv, text="Magnetic", variable=inv_var, value=2)
        rb_j = ttk.Radiobutton(f_inv, text="Joint Grav+Mag", variable=inv_var, value=3)
        rb_g.pack(side=tk.LEFT, padx=4)
        rb_m.pack(side=tk.LEFT, padx=4)
        rb_j.pack(side=tk.LEFT, padx=4)
        self.radioButton_grav_inv  = _RadioProxy(inv_var, 1, rb_g)
        self.radioButton_magn_inv  = _RadioProxy(inv_var, 2, rb_m)
        self.radioButton_joint_inv = _RadioProxy(inv_var, 3, rb_j)
        r += 1

        # ---- Gravity data ----
        r = self._section(p, r, "Gravity Data")
        sv = tk.StringVar()
        e, self.lineEdit_grav_data_path = self._entry(p, sv)
        e.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="Gravity file:").grid(row=r, column=0, sticky="w", padx=4)
        self.pushButton_grav_data_path = self._browse_btn(p, "...")
        self.pushButton_grav_data_path.grid(row=r, column=2, padx=2)
        r += 1

        # Grav CRS
        ttk.Label(p, text="Input CRS:").grid(row=r, column=0, sticky="w", padx=4)
        e_in, self.mQgsProjectionSelectionWidget_grav_in = self._crs_entry(p)
        e_in.grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(p, text="Output CRS:").grid(row=r, column=0, sticky="w", padx=4)
        e_out, self.mQgsProjectionSelectionWidget_grav_out = self._crs_entry(p)
        e_out.grid(row=r, column=1, sticky="w", padx=4)
        r += 1

        # Grav field columns
        f_gf = ttk.LabelFrame(p, text="Gravity Field Columns")
        f_gf.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_grav_fields = _GroupBoxProxy(f_gf)
        ttk.Label(f_gf, text="X/Lon:").grid(row=0, column=0, sticky="w", padx=2)
        sv_gx = tk.StringVar()
        cb_gx, self.comboBox_grav_field_x = self._combobox(f_gf, sv_gx, 18)
        cb_gx.grid(row=0, column=1, padx=2)
        ttk.Label(f_gf, text="Y/Lat:").grid(row=0, column=2, sticky="w", padx=2)
        sv_gy = tk.StringVar()
        cb_gy, self.comboBox_grav_field_y = self._combobox(f_gf, sv_gy, 18)
        cb_gy.grid(row=0, column=3, padx=2)
        ttk.Label(f_gf, text="Data:").grid(row=0, column=4, sticky="w", padx=2)
        sv_gd = tk.StringVar()
        cb_gd, self.comboBox_grav_field_data = self._combobox(f_gf, sv_gd, 18)
        cb_gd.grid(row=0, column=5, padx=2)
        self.pushButton_assign_grav_fields = ttk.Button(f_gf, text="Assign")
        self.pushButton_assign_grav_fields.grid(row=0, column=6, padx=4)
        self.pushButton_load_grav_data = ttk.Button(f_gf, text="Load Grav")
        self.pushButton_load_grav_data.grid(row=1, column=0, columnspan=3, sticky="w", padx=2, pady=2)
        r += 1

        # Grav unit multipliers
        f_gum = ttk.LabelFrame(p, text="Gravity Multipliers")
        f_gum.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_grav_unit_multipliers = _GroupBoxProxy(f_gum)
        ttk.Label(f_gum, text="Data units mult:").grid(row=0, column=0, sticky="w", padx=2)
        sv_gdm = tk.StringVar(value="1e-05")
        e_gdm, self.lineEdit_grav_data_multiplier = self._entry(f_gum, sv_gdm, 14)
        e_gdm.grid(row=0, column=1, padx=2)
        ttk.Label(f_gum, text="Model mult:").grid(row=0, column=2, sticky="w", padx=2)
        sv_gmm = tk.DoubleVar(value=1.0)
        sb_gmm, self.mQgsDoubleSpinBox_grav_model_multiplier = self._spinbox_dbl(f_gum, sv_gmm)
        sb_gmm.grid(row=0, column=3, padx=2)
        r += 1

        # Sensor heights (grav + magn together)
        f_sh = ttk.LabelFrame(p, text="Sensor Heights")
        f_sh.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_sensor_height = _GroupBoxProxy(f_sh)
        ttk.Label(f_sh, text="Grav:").grid(row=0, column=0, sticky="w", padx=2)
        sv_gsh = tk.DoubleVar(value=0.0)
        sb_gsh, self.doubleSpinBox_grav_sensor_height = self._spinbox_dbl(f_sh, sv_gsh, inc=1.0)
        sb_gsh.grid(row=0, column=1, padx=2)
        ttk.Label(f_sh, text="Mag:").grid(row=0, column=2, sticky="w", padx=8)
        sv_msh = tk.DoubleVar(value=0.0)
        sb_msh, self.doubleSpinBox_magn_sensor_height = self._spinbox_dbl(f_sh, sv_msh, inc=1.0)
        sb_msh.grid(row=0, column=3, padx=2)
        r += 1

        # Grav model damping
        f_gmd = ttk.LabelFrame(p, text="Gravity Model Damping")
        f_gmd.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_grav_model_damping = _GroupBoxProxy(f_gmd)
        ttk.Label(f_gmd, text="Weight:").grid(row=0, column=0, sticky="w", padx=2)
        sv_gdw = tk.DoubleVar(value=0.0)
        sb_gdw, self.mQgsDoubleSpinBox_grav_mmodel_damping_weight = self._spinbox_dbl(f_gmd, sv_gdw)
        sb_gdw.grid(row=0, column=1, padx=2)
        ttk.Label(f_gmd, text="Norm power:").grid(row=0, column=2, sticky="w", padx=2)
        sv_gnp = tk.DoubleVar(value=2.0)
        sb_gnp, self.mQgsDoubleSpinBox_grav_mmodel_norm_power = self._spinbox_dbl(f_gmd, sv_gnp)
        sb_gnp.grid(row=0, column=3, padx=2)
        r += 1

        # Grav ADMM
        f_gadmm = ttk.LabelFrame(p, text="Gravity ADMM")
        f_gadmm.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_grav_admm = _GroupBoxProxy(f_gadmm)
        ttk.Label(f_gadmm, text="# Lithologies:").grid(row=0, column=0, sticky="w", padx=2)
        sv_galn = tk.IntVar(value=0)
        sb_galn, self.spinBox_grav_number_ADMM_litho = self._spinbox_int(f_gadmm, sv_galn, 0, 20)
        sb_galn.grid(row=0, column=1, padx=2)
        ttk.Label(f_gadmm, text="Weight:").grid(row=0, column=2, sticky="w", padx=2)
        sv_gaw = tk.StringVar(value="0")
        e_gaw, self.lineEdit_grav_ADMM_weight = self._entry(f_gadmm, sv_gaw, 10)
        e_gaw.grid(row=0, column=3, padx=2)
        ttk.Label(f_gadmm, text="Bounds:").grid(row=1, column=0, sticky="w", padx=2)
        t_gab, self.textEdit_grav_ADMM_bounds = self._text(f_gadmm, 2, 30)
        t_gab.grid(row=1, column=1, columnspan=4, padx=2, sticky="we")
        r += 1

        # ---- Magnetic data ----
        r = self._section(p, r, "Magnetic Data")
        sv_mf = tk.StringVar()
        e_mf, self.lineEdit_magn_data_path = self._entry(p, sv_mf)
        e_mf.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="Magn file:").grid(row=r, column=0, sticky="w", padx=4)
        self.pushButton_magn_data_path = self._browse_btn(p, "...")
        self.pushButton_magn_data_path.grid(row=r, column=2, padx=2)
        r += 1

        ttk.Label(p, text="Input CRS:").grid(row=r, column=0, sticky="w", padx=4)
        e_mi, self.mQgsProjectionSelectionWidget_magn_in = self._crs_entry(p)
        e_mi.grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(p, text="Output CRS:").grid(row=r, column=0, sticky="w", padx=4)
        e_mo, self.mQgsProjectionSelectionWidget_magn_out = self._crs_entry(p)
        e_mo.grid(row=r, column=1, sticky="w", padx=4)
        r += 1

        f_mf = ttk.LabelFrame(p, text="Magnetic Field Columns")
        f_mf.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_magn_fields = _GroupBoxProxy(f_mf)
        self.groupBox_magn_data_file = _GroupBoxProxy(f_mf)
        ttk.Label(f_mf, text="X/Lon:").grid(row=0, column=0, sticky="w", padx=2)
        sv_mx = tk.StringVar()
        cb_mx, self.comboBox_magn_field_x = self._combobox(f_mf, sv_mx, 18)
        cb_mx.grid(row=0, column=1, padx=2)
        ttk.Label(f_mf, text="Y/Lat:").grid(row=0, column=2, sticky="w", padx=2)
        sv_my = tk.StringVar()
        cb_my, self.comboBox_magn_field_y = self._combobox(f_mf, sv_my, 18)
        cb_my.grid(row=0, column=3, padx=2)
        ttk.Label(f_mf, text="Data:").grid(row=0, column=4, sticky="w", padx=2)
        sv_md = tk.StringVar()
        cb_md, self.comboBox_magn_field_data = self._combobox(f_mf, sv_md, 18)
        cb_md.grid(row=0, column=5, padx=2)
        self.pushButton_assign_magn_fields = ttk.Button(f_mf, text="Assign")
        self.pushButton_assign_magn_fields.grid(row=0, column=6, padx=4)
        self.pushButton_load_magn_data = ttk.Button(f_mf, text="Load Magn")
        self.pushButton_load_magn_data.grid(row=1, column=0, columnspan=3, sticky="w", padx=2, pady=2)
        r += 1

        f_mum = ttk.LabelFrame(p, text="Magnetic Multipliers")
        f_mum.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_magn_unit_multipliers = _GroupBoxProxy(f_mum)
        ttk.Label(f_mum, text="Data units mult:").grid(row=0, column=0, sticky="w", padx=2)
        sv_mdm = tk.StringVar(value="1")
        e_mdm, self.lineEdit_magn_data_multiplier = self._entry(f_mum, sv_mdm, 14)
        e_mdm.grid(row=0, column=1, padx=2)
        ttk.Label(f_mum, text="Model mult:").grid(row=0, column=2, sticky="w", padx=2)
        sv_mmm = tk.DoubleVar(value=1.0)
        sb_mmm, self.mQgsDoubleSpinBox_magn_model_multiplier = self._spinbox_dbl(f_mum, sv_mmm)
        sb_mmm.grid(row=0, column=3, padx=2)
        r += 1

        f_mmd = ttk.LabelFrame(p, text="Magnetic Model Damping")
        f_mmd.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_magn_model_damping = _GroupBoxProxy(f_mmd)
        ttk.Label(f_mmd, text="Weight:").grid(row=0, column=0, sticky="w", padx=2)
        sv_mdw = tk.DoubleVar(value=0.0)
        sb_mdw, self.mQgsDoubleSpinBox_magn_model_weight = self._spinbox_dbl(f_mmd, sv_mdw)
        sb_mdw.grid(row=0, column=1, padx=2)
        ttk.Label(f_mmd, text="Norm power:").grid(row=0, column=2, sticky="w", padx=2)
        sv_mnp = tk.DoubleVar(value=2.0)
        sb_mnp, self.mQgsDoubleSpinBox_magn_model_norm_power = self._spinbox_dbl(f_mmd, sv_mnp)
        sb_mnp.grid(row=0, column=3, padx=2)
        r += 1

        f_madmm = ttk.LabelFrame(p, text="Magnetic ADMM")
        f_madmm.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_magn_admm = _GroupBoxProxy(f_madmm)
        ttk.Label(f_madmm, text="# Lithologies:").grid(row=0, column=0, sticky="w", padx=2)
        sv_maln = tk.IntVar(value=0)
        sb_maln, self.spinBox_magn_ADMM_number_litho = self._spinbox_int(f_madmm, sv_maln, 0, 20)
        sb_maln.grid(row=0, column=1, padx=2)
        ttk.Label(f_madmm, text="Weight:").grid(row=0, column=2, sticky="w", padx=2)
        sv_maw = tk.StringVar(value="0")
        e_maw, self.lineEdit_magn_ADMM_weight = self._entry(f_madmm, sv_maw, 10)
        e_maw.grid(row=0, column=3, padx=2)
        ttk.Label(f_madmm, text="Bounds:").grid(row=1, column=0, sticky="w", padx=2)
        t_mab, self.textEdit_5_magn_ADMM_bounds = self._text(f_madmm, 2, 30)
        t_mab.grid(row=1, column=1, columnspan=4, padx=2, sticky="we")
        r += 1

        # Joint problem weights
        f_jp = ttk.LabelFrame(p, text="Joint Inversion Weights")
        f_jp.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        ttk.Label(f_jp, text="Grav weight:").grid(row=0, column=0, sticky="w", padx=2)
        sv_gw = tk.DoubleVar(value=1.0)
        sb_gw, self.mQgsDoubleSpinBox_grav_weight = self._spinbox_dbl(f_jp, sv_gw)
        sb_gw.grid(row=0, column=1, padx=2)
        ttk.Label(f_jp, text="Magn weight:").grid(row=0, column=2, sticky="w", padx=2)
        sv_mw = tk.DoubleVar(value=2.5e-6)
        sb_mw, self.mQgsDoubleSpinBox_magn_weight = self._spinbox_dbl(f_jp, sv_mw)
        sb_mw.grid(row=0, column=3, padx=2)
        r += 1

        # DTM
        r = self._section(p, r, "Digital Terrain Model (DTM)")
        f_dtm = ttk.LabelFrame(p, text="DTM")
        f_dtm.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_dtm = _GroupBoxProxy(f_dtm)
        sv_dtm = tk.StringVar()
        e_dtm, self.lineEdit_dtm_path = self._entry(f_dtm, sv_dtm)
        e_dtm.grid(row=0, column=0, sticky="we", padx=2)
        f_dtm.columnconfigure(0, weight=1)
        self.pushButton_select_dtm_path = ttk.Button(f_dtm, text="Browse...")
        self.pushButton_select_dtm_path.grid(row=0, column=1, padx=2)
        r += 1

        # ROI
        r = self._section(p, r, "ROI / 2D Profile Line")
        sv_roi = tk.StringVar()
        e_roi, self.lineEdit_ROI_path = self._entry(p, sv_roi)
        e_roi.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="ROI file:").grid(row=r, column=0, sticky="w", padx=4)
        self.lineEdit_ROI_path_select = self._browse_btn(p, "Browse...")
        self.lineEdit_ROI_path_select.grid(row=r, column=2, padx=2)
        r += 1

        # Output directory
        r = self._section(p, r, "Output Directory")
        sv_out = tk.StringVar()
        e_out2, self.lineEdit_output_directory_path = self._entry(p, sv_out)
        e_out2.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="Output dir:").grid(row=r, column=0, sticky="w", padx=4)
        self.lineEdit_output_directory_path_select = ttk.Button(p, text="Browse/Process")
        self.lineEdit_output_directory_path_select.grid(row=r, column=2, padx=2)
        r += 1

        # Description
        ttk.Label(p, text="Description:").grid(row=r, column=0, sticky="nw", padx=4)
        t_desc, self.textEdit_experiment_description = self._text(p, 3, 50)
        t_desc.grid(row=r, column=1, columnspan=2, sticky="we", padx=4)
        r += 1

        # Parfile
        r = self._section(p, r, "Load Existing Parfile")
        sv_pf = tk.StringVar()
        e_pf, self.lineEdit_param_load_path = self._entry(p, sv_pf)
        e_pf.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="Parfile:").grid(row=r, column=0, sticky="w", padx=4)
        self.pushButton_param_load_path = ttk.Button(p, text="Load Parfile")
        self.pushButton_param_load_path.grid(row=r, column=2, padx=2)
        r += 1

        # Reset + labels
        self.label_grav_params_header = _LabelProxy(tk.StringVar(value="Gravity Params"))
        self.label_magn_params_header = _LabelProxy(tk.StringVar(value="Magn Params"))
        self.label_grav_input_crs  = _LabelProxy(tk.StringVar())
        self.label_grav_output_crs = _LabelProxy(tk.StringVar())
        self.label_magn_input_crs  = _LabelProxy(tk.StringVar())
        self.label_magn_output_crs = _LabelProxy(tk.StringVar())
        self.label_grav_field_long_x  = _LabelProxy(tk.StringVar())
        self.label_grav_field_lat_y   = _LabelProxy(tk.StringVar())
        self.label_grav_field_data_col = _LabelProxy(tk.StringVar())
        self.label_wsl_distro = _LabelProxy(tk.StringVar())
        self.label_setvars_path = _LabelProxy(tk.StringVar())
        self.groupBox_grav_data_file  = _GroupBoxProxy(ttk.Frame(p))
        self.pushButton_reset = ttk.Button(p, text="Reset Params")
        self.pushButton_reset.grid(row=r, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        r += 1

    # ====================================================================
    # MESH tab
    # ====================================================================

    def _build_mesh_tab(self, p):
        r = 0
        r = self._section(p, r, "Mesh Bounding Box (projected metres)")
        f_bb = ttk.LabelFrame(p, text="Mesh Extents")
        f_bb.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_mesh_params = _GroupBoxProxy(f_bb)

        for label, attr, val in [
            ("South (min N):", "mQgsSpinBox_mesh_south", 6730000),
            ("North (max N):", "mQgsSpinBox_mesh_north", 6790000),
            ("West  (min E):", "mQgsSpinBox_mesh_west",  430000),
            ("East  (max E):", "mQgsSpinBox_mesh_east",  482000),
        ]:
            ttk.Label(f_bb, text=label).grid(row=r, column=0, sticky="w", padx=4)
            sv = tk.IntVar(value=val)
            sb, proxy = self._spinbox_int(f_bb, sv, -9999999, 9999999, 14)
            sb.grid(row=r, column=1, sticky="w", padx=4)
            setattr(self, attr, proxy)
            r += 1

        r = self._section(p, r, "Cell Sizes")
        for label, attr, val, is_dbl in [
            ("Cell X (m):", "mQgsSpinBox_mesh_size_x", 2000, False),
            ("Cell Y (m):", "mQgsSpinBox_mesh_size_y", 2000, False),
            ("Cell Z (m):", "mQgsSpinBox_mesh_size_z", 100,  True),
            ("Padding (m):", "mQgsSpinBox_mesh_padding", 10000, False),
        ]:
            ttk.Label(p, text=label).grid(row=r, column=0, sticky="w", padx=4)
            if is_dbl:
                sv = tk.DoubleVar(value=val)
                sb, proxy = self._spinbox_dbl(p, sv, 0, 1e6, 10)
            else:
                sv = tk.IntVar(value=val)
                sb, proxy = self._spinbox_int(p, sv, 0, 9999999)
            sb.grid(row=r, column=1, sticky="w", padx=4)
            setattr(self, attr, proxy)
            r += 1

        r = self._section(p, r, "Depth Layers")
        ttk.Label(p, text="Core depth (m):").grid(row=r, column=0, sticky="w", padx=4)
        sv_cd = tk.DoubleVar(value=10000)
        sb_cd, self.doubleSpinBox_coreDepth = self._spinbox_dbl(p, sv_cd, 0, 1e7, 500)
        sb_cd.grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(p, text="Full depth (m):").grid(row=r, column=0, sticky="w", padx=4)
        sv_fd = tk.DoubleVar(value=20000)
        sb_fd, self.doubleSpinBox_fullDepth = self._spinbox_dbl(p, sv_fd, 0, 1e7, 500)
        sb_fd.grid(row=r, column=1, sticky="w", padx=4)
        r += 1

        ttk.Label(p, text="Z cell size list:").grid(row=r, column=0, sticky="nw", padx=4)
        t_zcsl, self.textEdit_z_cell_size_list = self._text(p, 2, 30)
        t_zcsl.grid(row=r, column=1, columnspan=2, sticky="we", padx=4)
        r += 1
        ttk.Label(p, text="Z layer thick list:").grid(row=r, column=0, sticky="nw", padx=4)
        t_zltl, self.textEdit_z_layer_thickness_list = self._text(p, 2, 30)
        t_zltl.grid(row=r, column=1, columnspan=2, sticky="we", padx=4)
        r += 1

        r = self._section(p, r, "Grid Size (auto-calculated)")
        f_gs = ttk.Frame(p)
        f_gs.grid(row=r, column=0, columnspan=3, sticky="we", padx=4)
        for i, (lbl, attr) in enumerate([("NX:", "nx_label"), ("NY:", "ny_label"), ("NZ:", "nz_label")]):
            ttk.Label(f_gs, text=lbl).grid(row=0, column=i*2, padx=4)
            lb, proxy = self._label_var(f_gs, "0", 8)
            lb.grid(row=0, column=i*2+1, padx=2)
            setattr(self, attr, proxy)
        ttk.Label(f_gs, text="Memory (GB):").grid(row=1, column=0, padx=4)
        lb_mem, self.memory_label = self._label_var(f_gs, "0", 10)
        lb_mem.grid(row=1, column=1, padx=2)
        r += 1

        r = self._section(p, r, "Compression")
        ttk.Label(p, text="Use compression:").grid(row=r, column=0, sticky="w", padx=4)
        sv_uc = tk.IntVar(value=1)
        cb_uc, self.checkBox_use_compression = self._check(p, sv_uc)
        cb_uc.grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(p, text="Compression ratio:").grid(row=r, column=0, sticky="w", padx=4)
        sv_cr = tk.DoubleVar(value=0.1)
        sb_cr, self.mQgsDoubleSpinBox_compression_ratio = self._spinbox_dbl(p, sv_cr, 0, 1, 0.01)
        sb_cr.grid(row=r, column=1, sticky="w", padx=4)
        r += 1

        r = self._section(p, r, "Sensitivity Kernel")
        ttk.Label(p, text="Read from files:").grid(row=r, column=0, sticky="w", padx=4)
        sv_rsm = tk.IntVar(value=0)
        cb_rsm, self.checkBox_read_sens_matrix = self._check(p, sv_rsm)
        cb_rsm.grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(p, text="Kernel dir:").grid(row=r, column=0, sticky="w", padx=4)
        sv_kp = tk.StringVar()
        e_kp, self.lineEdit_kernel_path = self._entry(p, sv_kp)
        e_kp.grid(row=r, column=1, sticky="we", padx=4)
        self.pushButton_kernel_path_select = ttk.Button(p, text="Browse...")
        self.pushButton_kernel_path_select.grid(row=r, column=2, padx=2)
        r += 1

    # ====================================================================
    # INVERSION tab
    # ====================================================================

    def _build_inversion_tab(self, p):
        r = 0
        r = self._section(p, r, "Inversion Iterations")
        for label, attr, val, mn, mx in [
            ("Major iterations:", "mQgsSpinBox_major_iters", 3, 0, 1000),
            ("Minor iterations:", "mQgsSpinBox_minor_iters", 100, 0, 10000),
            ("Save every N iters:", "mQgsSpinBox_model_save_iters", 0, 0, 1000),
        ]:
            ttk.Label(p, text=label).grid(row=r, column=0, sticky="w", padx=4)
            sv = tk.IntVar(value=val)
            sb, proxy = self._spinbox_int(p, sv, mn, mx)
            sb.grid(row=r, column=1, sticky="w", padx=4)
            setattr(self, attr, proxy)
            r += 1

        ttk.Label(p, text="Min residual:").grid(row=r, column=0, sticky="nw", padx=4)
        t_mr, self.textEdit_min_residual = self._text(p, 2, 30)
        t_mr.grid(row=r, column=1, sticky="we", padx=4)
        r += 1
        ttk.Label(p, text="Target misfit:").grid(row=r, column=0, sticky="w", padx=4)
        sv_tm = tk.StringVar(value="1e-7")
        e_tm, self.lineEdit_targetMisfit = self._entry(p, sv_tm)
        e_tm.grid(row=r, column=1, sticky="we", padx=4)
        r += 1

        r = self._section(p, r, "Magnetic Field")
        f_mag = ttk.LabelFrame(p, text="Magnetic Field Parameters")
        f_mag.grid(row=r, column=0, columnspan=3, sticky="we", padx=4, pady=2)
        self.groupBox_magnetic_field = _GroupBoxProxy(f_mag)
        ttk.Label(f_mag, text="Survey date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", padx=2)
        import datetime
        sv_date = tk.StringVar(value=str(datetime.date.today()))
        e_date, self.dateEdit = self._entry(f_mag, sv_date, 14)
        e_date.grid(row=0, column=1, padx=2)
        self.pushButton_calc_IGRF = ttk.Button(f_mag, text="Calc IGRF")
        self.pushButton_calc_IGRF.grid(row=0, column=2, padx=4)
        for label, attr, val, inc in [
            ("Declination:", "doubleSpinBox_mag_dec", 0.0, 0.01),
            ("Inclination:", "doubleSpinBox_mag_inc", -45.0, 0.01),
            ("Intensity (nT):", "doubleSpinBox_mag_int", 65000.0, 1.0),
        ]:
            row_i = f_mag.grid_size()[1]
            ttk.Label(f_mag, text=label).grid(row=row_i, column=0, sticky="w", padx=2)
            sv = tk.DoubleVar(value=val)
            sb, proxy = self._spinbox_dbl(f_mag, sv, -9e6, 9e6, inc)
            sb.grid(row=row_i, column=1, padx=2)
            setattr(self, attr, proxy)
        r += 1

    # ====================================================================
    # RUN tab
    # ====================================================================

    def _build_run_tab(self, p):
        r = 0
        r = self._section(p, r, "Tomofast-x Executable")
        sv_tp = tk.StringVar()
        e_tp, self.lineEdit_tomoPath = self._entry(p, sv_tp)
        e_tp.grid(row=r, column=1, sticky="we", padx=4)
        ttk.Label(p, text="Tomofast path:").grid(row=r, column=0, sticky="w", padx=4)
        self.pushButton_select_tomoPath = ttk.Button(p, text="Browse...")
        self.pushButton_select_tomoPath.grid(row=r, column=2, padx=2)
        r += 1

        ttk.Label(p, text="Parfile:").grid(row=r, column=0, sticky="w", padx=4)
        sv_pf = tk.StringVar()
        e_pf2, self.lineEdit_2_parfilePath = self._entry(p, sv_pf)
        e_pf2.grid(row=r, column=1, sticky="we", padx=4)
        self.pushButton_2_select_parfilePath = ttk.Button(p, text="Browse...")
        self.pushButton_2_select_parfilePath.grid(row=r, column=2, padx=2)
        r += 1

        ttk.Label(p, text="# Processors:").grid(row=r, column=0, sticky="w", padx=4)
        sv_np = tk.IntVar(value=1)
        sb_np, self.mQgsSpinBox_noProc = self._spinbox_int(p, sv_np, 1, 256)
        sb_np.grid(row=r, column=1, sticky="w", padx=4)
        r += 1

        ttk.Label(p, text="mpirun path:").grid(row=r, column=0, sticky="w", padx=4)
        sv_mpi = tk.StringVar()
        e_mpi, self.lineEdit_2_mpirunPath_2 = self._entry(p, sv_mpi)
        e_mpi.grid(row=r, column=1, sticky="we", padx=4)
        self.pushButton_select_mpirun_mipexec = ttk.Button(p, text="Browse...")
        self.pushButton_select_mpirun_mipexec.grid(row=r, column=2, padx=2)
        r += 1

        r = self._section(p, r, "Platform")
        inv_os = tk.IntVar(value=1)
        self._os_var = inv_os
        f_os = ttk.Frame(p)
        f_os.grid(row=r, column=0, columnspan=3, sticky="w", padx=4)
        rb_win = ttk.Radiobutton(f_os, text="Windows (native)", variable=inv_os, value=1)
        rb_wsl = ttk.Radiobutton(f_os, text="Windows WSL", variable=inv_os, value=2)
        rb_win.pack(side=tk.LEFT, padx=4)
        rb_wsl.pack(side=tk.LEFT, padx=4)
        self.radioButton_windowsNative = _RadioProxy(inv_os, 1, rb_win)
        self.radioButton_windowsWSL    = _RadioProxy(inv_os, 2, rb_wsl)
        r += 1

        ttk.Label(p, text="WSL Distro:").grid(row=r, column=0, sticky="w", padx=4)
        sv_wsl = tk.StringVar()
        e_wsl, self.lineEdit_pre_command_2_WSL_Distro = self._entry(p, sv_wsl)
        e_wsl.grid(row=r, column=1, sticky="we", padx=4)
        r += 1

        ttk.Label(p, text="setvars.bat:").grid(row=r, column=0, sticky="w", padx=4)
        sv_sv = tk.StringVar()
        e_sv, self.lineEdit_setvarsPath = self._entry(p, sv_sv)
        e_sv.grid(row=r, column=1, sticky="we", padx=4)
        self.pushButton_select_setvars = ttk.Button(p, text="Browse...")
        self.pushButton_select_setvars.grid(row=r, column=2, padx=2)
        r += 1

        r = self._section(p, r, "Run Inversion")
        self.pushButton_3_runInversion = ttk.Button(p, text="Run Inversion",
                                                     style="Accent.TButton" if "Accent.TButton" in ttk.Style().theme_names() else "TButton")
        self.pushButton_3_runInversion.grid(row=r, column=0, columnspan=3, pady=6, padx=4)
        r += 1

        r = self._section(p, r, "Inversion Log")
        t_log, self.textEdit_inversion_log = self._text(p, 20, 60)
        t_log.configure(bg="black", fg="white", font=("Courier", 9))
        t_log.grid(row=r, column=0, columnspan=3, padx=4, pady=2, sticky="we")
        r += 1

        r = self._section(p, r, "Version")
        sv_ver = tk.StringVar(value="v ?")
        lbl_ver, self.version_label = self._label_var(p, "v ?", 14)
        lbl_ver.grid(row=r, column=0, columnspan=2, sticky="w", padx=4)
        # help buttons (no-ops in ArcGIS version)
        self.pushButton_plugin_manual    = ttk.Button(p, text="Plugin Manual")
        self.pushButton_plugin_cheat_sheat = ttk.Button(p, text="Cheat Sheet")
        self.pushButton_tomofast_manual  = ttk.Button(p, text="Tomofast Manual")
        self.pushButton_plugin_manual.grid(row=r, column=1, padx=4)
        self.pushButton_plugin_cheat_sheat.grid(row=r, column=2, padx=4)
        r += 1

    # ====================================================================
    # EXPORT tab
    # ====================================================================

    def _build_export_tab(self, p):
        r = 0
        r = self._section(p, r, "Export / Visualise")
        self.pushButton_3_Export   = ttk.Button(p, text="Export Model CSV")
        self.pushButton_3_visualise = ttk.Button(p, text="Visualise Output")
        self.pushButton_3_Export.grid(row=r, column=0, padx=4, pady=4, sticky="w")
        self.pushButton_3_visualise.grid(row=r, column=1, padx=4, pady=4, sticky="w")
        r += 1
