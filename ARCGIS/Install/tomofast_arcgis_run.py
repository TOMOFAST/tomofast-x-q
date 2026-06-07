# -*- coding: utf-8 -*-
import os
import sys
import re
import shutil
import platform
import subprocess
import tkinter as tk


class RunMixin:

    # ------------------------------------------------------------------
    def _poll_debug_log(self):
        if not self._debug_polling_active:
            return
        if self._debug_log_path and os.path.exists(self._debug_log_path):
            try:
                with open(self._debug_log_path, "r", errors="replace") as fh:
                    fh.seek(self._debug_log_pos)
                    new_text = fh.read()
                    if new_text:
                        self._debug_log_pos = fh.tell()
                        self.ui.textEdit_inversion_log.insertPlainText(new_text)
                        self.ui.textEdit_inversion_log.moveCursor(None)
                        if "THE END." in new_text:
                            self._debug_polling_active = False
                            self._check_inversion_results()
                            return
            except Exception:
                pass
        self.ui.root.after(500, self._poll_debug_log)

    # ------------------------------------------------------------------
    def _log_colored(self, text, color, bold=False):
        widget = self.ui.textEdit_inversion_log._widget
        tag_name = f"col_{color}{'_bold' if bold else ''}"
        try:
            widget.tag_configure(
                tag_name,
                foreground=color,
                font=("Courier", 9, "bold" if bold else "normal"),
            )
            widget.insert(tk.END, text + "\n", tag_name)
            widget.see(tk.END)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _get_output_dir_from_parfile(self):
        try:
            with open(self.paramfile_Path, "r", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if (
                        stripped.startswith("global.outputFolderPath")
                        and "=" in stripped
                    ):
                        return stripped.split("=", 1)[1].strip()
        except Exception:
            pass
        return ""

    # ------------------------------------------------------------------
    def _check_inversion_results(self):
        def warn(msg):
            self._log_colored(f"FAIL  {msg}", "red", bold=True)

        def ok(msg):
            self._log_colored(f"PASS  {msg}", "green", bold=True)

        debug_text = ""
        try:
            with open(self._debug_log_path, "r", errors="replace") as fh:
                debug_text = fh.read()
        except Exception:
            return

        output_dir = self._get_output_dir_from_parfile()
        self._log_colored("─" * 60, "gray")

        # --- 1. costs.txt ---
        if output_dir:
            costs_path = os.path.join(output_dir, "costs.txt")
            if os.path.exists(costs_path):
                try:
                    with open(costs_path, "r") as fh:
                        data_lines = [
                            ln for ln in fh
                            if ln.strip() and not ln.strip().startswith("#")
                        ]
                    if data_lines:
                        cols = data_lines[-1].split()
                        data_cost_ok = True
                        for idx in (1, 2):
                            if len(cols) > idx:
                                val = float(cols[idx])
                                if val > 0.1:
                                    warn(
                                        f"Data cost exceeds 0.1 ({val:.4g}) "
                                        f"[costs.txt col {idx + 1}]\n"
                                        f"Try to relax constraints, e.g. reduce ADMM weighting"
                                    )
                                    data_cost_ok = False
                        if data_cost_ok:
                            ok("Data cost within acceptable range")
                        admm_cost_ok = True
                        for idx in (5, 6):
                            if len(cols) > idx:
                                val = float(cols[idx])
                                if val > 0.05:
                                    warn(
                                        f"ADMM cost exceeds 0.05 ({val:.4g}) "
                                        f"[costs.txt col {idx + 1}]\n"
                                        f"Try to increase the admm weight, or adjust intervals"
                                    )
                                    admm_cost_ok = False
                        if admm_cost_ok:
                            ok("ADMM cost within acceptable range")
                except Exception:
                    pass

        # --- 2. Compression error ---
        compr_val = None
        for line in debug_text.splitlines():
            if "COMPRESSION ERROR (read)" in line and "=" in line:
                try:
                    compr_val = float(line.split("=")[-1].strip())
                except ValueError:
                    pass
        if compr_val is None:
            ok("Compression error check skipped (not found in log)")
        elif compr_val > 0.01:
            warn(f"Compression error > 0.01 ({compr_val:.4g})\nTry reducing the compression ratio")
        else:
            ok(f"Compression error acceptable ({compr_val:.4g})")

        # --- 3. Data RMSE ---
        last_rmse = None
        for line in debug_text.splitlines():
            if re.search(r"\bdata RMSE\b", line) and "=" in line:
                try:
                    last_rmse = float(line.split("=")[-1].strip())
                except ValueError:
                    pass
        if last_rmse is None:
            ok("Data RMSE check skipped (not found in log)")
        elif last_rmse < 4e-7 and self.global_experimentType in (1, 3):
            warn(
                f"Possible overfitting of data (data RMSE = {last_rmse:.4g})\n"
                f"Try increasing inversion.targetMisfit to this value"
            )
        elif last_rmse < 1 and self.global_experimentType in (2, 3):
            warn(
                f"Possible overfitting of data (data RMSE = {last_rmse:.4g})\n"
                f"Try increasing inversion.targetMisfit to this value"
            )
        else:
            ok(f"Data RMSE acceptable ({last_rmse:.4g})")

        # --- 4. Major iterations ---
        n_iter = None
        admm_grav = 0.0
        admm_magn = 0.0
        for line in debug_text.splitlines():
            if "inversion.nMajorIterations" in line and "=" in line:
                try:
                    n_iter = int(line.split("=")[-1].strip())
                except ValueError:
                    pass
            if "inversion.admm.grav.weight" in line and "=" in line:
                try:
                    admm_grav = float(line.split("=")[-1].strip())
                except ValueError:
                    pass
            if "inversion.admm.magn.weight" in line and "=" in line:
                try:
                    admm_magn = float(line.split("=")[-1].strip())
                except ValueError:
                    pass
        if n_iter is None:
            ok("Iteration count check skipped (not found in log)")
        elif n_iter > 3 and admm_grav == 0.0 and admm_magn == 0.0:
            warn(f"More than 3 major iterations for unconstrained inversion ({n_iter})")
        else:
            ok(f"Major iteration count acceptable ({n_iter})")

        # --- 5. Model range ---
        if self.global_experimentType in (1, 3):
            last_min = last_max = None
            pattern = re.compile(
                r"Model\s+1\s+min/max values\s*=\s*([\S]+)\s+([\S]+)", re.IGNORECASE
            )
            for line in debug_text.splitlines():
                m = pattern.search(line)
                if m:
                    try:
                        last_min = float(m.group(1))
                        last_max = float(m.group(2))
                    except ValueError:
                        pass
            if last_min is None:
                ok("Density range check skipped (min/max not found in log)")
            elif abs(last_min) > 1000 or abs(last_max) > 1000:
                warn(
                    f"Check density unit scaling "
                    f"(model min={last_min:.4g}, max={last_max:.4g})"
                )
            else:
                ok(f"Density range acceptable (min={last_min:.4g}, max={last_max:.4g})")
        elif self.global_experimentType in (2, 3):
            last_min = last_max = None
            pattern = re.compile(
                r"Model\s+2\s+min/max values\s*=\s*([\S]+)\s+([\S]+)", re.IGNORECASE
            )
            for line in debug_text.splitlines():
                m = pattern.search(line)
                if m:
                    try:
                        last_min = float(m.group(1))
                        last_max = float(m.group(2))
                    except ValueError:
                        pass
            if last_min is None:
                ok("Mag sus range check skipped (min/max not found in log)")
            elif abs(last_min) > 1 or abs(last_max) > 1:
                warn(
                    f"Check magnetic susceptibility unit scaling "
                    f"(model min={last_min:.4g}, max={last_max:.4g})"
                )
            else:
                ok(
                    f"Magnetic susceptibility range acceptable "
                    f"(min={last_min:.4g}, max={last_max:.4g})"
                )

    # ------------------------------------------------------------------
    def run_inversion(self):
        if (
            os.path.exists(self.paramfile_Path)
            and self.paramfile_Path != ""
            and os.path.exists(self.tomo_Path)
            and self.tomo_Path != ""
        ):
            use_native_windows = (
                platform.system() == "Windows"
                and self.ui.radioButton_windowsNative.isChecked()
            )
            noProc = self.ui.mQgsSpinBox_noProc.value()

            try:
                if use_native_windows:
                    process, distro, mpi_path = self._run_windows_native(noProc)
                    self._debug_log_path = self.paramfile_Path + "_debug.txt"
                elif platform.system() == "Windows":
                    process, distro, mpi_path = self._run_windows_wsl(noProc)
                    self._debug_log_path = self.paramfile_Path_run + "_debug.txt"
                elif platform.system() == "Darwin":
                    process, distro, mpi_path = self._run_macos(noProc)
                    self._debug_log_path = self.paramfile_Path + "_debug.txt"
                else:
                    process, distro, mpi_path = self._run_linux(noProc)
                    self._debug_log_path = self.paramfile_Path + "_debug.txt"

                try:
                    if os.path.exists(self._debug_log_path):
                        os.remove(self._debug_log_path)
                except Exception:
                    pass

                self._debug_log_pos = 0
                self.ui.textEdit_inversion_log.clear()
                self._debug_polling_active = True
                self.ui.root.after(500, self._poll_debug_log)

                self.ui.lineEdit_tomoPath.setText(self.tomo_Path)
                with open(
                    os.path.join(self.plugin_dir, "tomoconfig.txt"), "w"
                ) as tpfile:
                    tpfile.write(self.tomo_Path + "\n")
                    tpfile.write(distro + "\n")
                    tpfile.write("\n")
                    tpfile.write(mpi_path + "\n")
                    tpfile.write(
                        self.ui.lineEdit_setvarsPath.text().strip() + "\n"
                    )
                    tpfile.write(("1" if use_native_windows else "0") + "\n")
                    tpfile.write(str(noProc) + "\n")

                self.show_message(
                    f"Process started with PID: {process.pid}",
                    "Command is running in the background",
                )
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            self.show_message(
                "Paths to tomofastx and paramfile must be defined", level="warning"
            )

    # ------------------------------------------------------------------
    def _run_windows_native(self, noProc):
        tomo_path = self._validate_path(self.tomo_Path)
        param_path = self._validate_path(self.paramfile_Path)
        mpiexec_path = (
            self._validate_path(
                self.ui.lineEdit_2_mpirunPath_2.text().strip()
            )
            if hasattr(self.ui, "lineEdit_2_mpirunPath_2")
            else r"C:\Program Files (x86)\Intel\oneAPI\mpi\2021.17\bin\mpiexec.exe"
        )
        oneapi_path = self._validate_path(
            self.ui.lineEdit_setvarsPath.text().strip()
        )
        distro = " "

        debug_path = param_path.replace('"', "") + "_debug.txt"
        oneapi_path_bat = oneapi_path.replace("/", "\\")
        tomo_path_bat = tomo_path.replace("/", "\\")
        param_path_bat = param_path.replace("/", "\\")
        debug_path_bat = debug_path.replace("/", "\\")

        if noProc == 1:
            run_command = f'"{tomo_path_bat}" -p "{param_path_bat}"'
        else:
            run_command = (
                f'"{mpiexec_path}" -n {noProc} "{tomo_path_bat}" -p "{param_path_bat}"'
            )

        batch_content = (
            f'@echo off\nsetlocal\n\ncall "{oneapi_path_bat}"\n'
            f'if errorlevel 1 (\n    exit /b 1\n)\n\n'
            f'{run_command} > "{debug_path_bat}" 2>&1\n\nendlocal\n'
        )
        batch_file_path = os.path.join(
            os.path.dirname(self.paramfile_Path), "run_tomofastx.bat"
        )
        with open(batch_file_path, "w") as batch_file:
            batch_file.write(batch_content)

        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        process = subprocess.Popen(
            [batch_file_path],
            shell=False,
            creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
        )
        return process, distro, mpiexec_path

    # ------------------------------------------------------------------
    def _run_windows_wsl(self, noProc):
        distro = self.ui.lineEdit_pre_command_2_WSL_Distro.text()
        self.paramfile_Path_run = self._validate_path(self.paramfile_Path + "_run")
        shutil.copyfile(self.paramfile_Path, self.paramfile_Path_run)
        drive = self.paramfile_Path_run[0:2]
        self.replace_text_in_file(
            self.paramfile_Path_run,
            "= {}:/".format(drive[0]),
            "= /mnt/{}/".format(drive[0].lower()),
        )

        wsl_path = "//wsl.localhost/" + distro
        wsl_param_path = self.add_quotes_to_path(
            self.paramfile_Path_run.replace(
                "{}:/".format(drive[0]), "/mnt/{}/".format(drive[0].lower())
            )
        )
        if wsl_path in wsl_param_path:
            wsl_param_path = wsl_param_path.replace(wsl_path, "")
            self.replace_text_in_file(self.paramfile_Path_run, wsl_path, "")

        wsl_tomo_path = self.tomo_Path.replace(wsl_path, "")
        mpirun_path = " mpirun "
        wsl_param_path = wsl_param_path.replace('"', "")
        wsl_debug_path = wsl_param_path + "_debug.txt"

        if noProc == 1:
            base_command = (
                f"'{wsl_tomo_path}' -p '{wsl_param_path}' 2>&1 | tee '{wsl_debug_path}'"
            )
        else:
            base_command = (
                f"{mpirun_path} -np {noProc} '{wsl_tomo_path}' -j "
                f"'{wsl_param_path}' 2>&1 | tee '{wsl_debug_path}'"
            )

        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        process = subprocess.Popen(
            ["wsl", "-d", distro, "bash", "-l", "-c", base_command],
            shell=False,
            creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
        )
        return process, distro, mpirun_path

    # ------------------------------------------------------------------
    def _run_macos(self, noProc):
        tomo_path = self._validate_path(self.tomo_Path)
        param_path = self._validate_path(self.paramfile_Path)
        mpirun_path = self._validate_path(
            self.ui.lineEdit_2_mpirunPath_2.text().strip()
        )
        distro = " "
        debug_path = param_path.replace('"', "") + "_debug.txt"

        print("noProc - ", noProc)
        print("tomo_path - ", tomo_path)
        print("param_path - ", param_path)
        print("debug_path - ", debug_path)
        print("mpirun_path - ", mpirun_path)

        if noProc == 1:
            command = (
                f"'{tomo_path}' -p '{param_path}' 2>&1 | tee '{debug_path}'"
            )
        else:
            command = (
                f"{mpirun_path} -np {noProc} '{tomo_path}' -j '{param_path}' "
                f"2>&1 | tee '{debug_path}'"
            )

        print("command: ", command)
        kwargs = (
            {"preexec_fn": os.setsid}
            if sys.version_info < (3, 2)
            else {"start_new_session": True}
        )
        process = subprocess.Popen(
            command,
            shell=True,  # nosec B602
            env=os.environ.copy(),
            **kwargs,
        )
        return process, distro, mpirun_path

    # ------------------------------------------------------------------
    def _run_linux(self, noProc):
        tomo_path = self._validate_path(self.tomo_Path)
        param_path = self._validate_path(self.paramfile_Path)
        mpirun_path = self._validate_path(
            self.ui.lineEdit_2_mpirunPath_2.text().strip()
        )
        distro = " "
        debug_path = param_path.replace('"', "") + "_debug.txt"

        print("noProc - ", noProc)
        print("tomo_path - ", tomo_path)
        print("param_path - ", param_path)
        print("debug_path - ", debug_path)
        print("mpirun_path - ", mpirun_path)

        if noProc == 1:
            command = (
                f"'{tomo_path}' -p '{param_path}' 2>&1 | tee '{debug_path}'"
            )
        else:
            command = (
                f"{mpirun_path} -np {noProc} '{tomo_path}' -j '{param_path}' "
                f"2>&1 | tee '{debug_path}'"
            )

        print("command: ", command)
        kwargs = (
            {"preexec_fn": os.setsid}
            if sys.version_info < (3, 2)
            else {"start_new_session": True}
        )
        process = subprocess.Popen(
            command,
            shell=True,  # nosec B602
            env=os.environ.copy(),
            **kwargs,
        )
        return process, distro, mpirun_path

    # ------------------------------------------------------------------
    def _update_run_controls(self):
        is_windows = platform.system() == "Windows"
        native = is_windows and self.ui.radioButton_windowsNative.isChecked()
        wsl = is_windows and self.ui.radioButton_windowsWSL.isChecked()

        for w in (self.ui.radioButton_windowsNative, self.ui.radioButton_windowsWSL):
            w.setEnabled(is_windows)

        for w in (
            self.ui.label_wsl_distro,
            self.ui.lineEdit_pre_command_2_WSL_Distro,
        ):
            w.setEnabled(wsl)
        for w in (
            self.ui.label_setvars_path,
            self.ui.lineEdit_setvarsPath,
            self.ui.pushButton_select_setvars,
        ):
            w.setEnabled(native)

    # ------------------------------------------------------------------
    def select_tomo_Path(self):
        from tkinter import filedialog
        self.tomo_Path = filedialog.askopenfilename(
            title="Select tomofast executable", filetypes=[("All", "*.*")]
        )
        if os.path.exists(self.tomo_Path) and self.tomo_Path != "":
            self.ui.lineEdit_tomoPath.setText(self.tomo_Path)

    def select_paramfile_path(self):
        from tkinter import filedialog
        self.paramfile_Path = filedialog.askopenfilename(
            title="Select tomofast paramfile", filetypes=[("All", "*.*")]
        )
        if os.path.exists(self.paramfile_Path) and self.paramfile_Path != "":
            self.ui.lineEdit_2_parfilePath.setText(self.paramfile_Path)

    def select_mpirunexec_path(self):
        from tkinter import filedialog
        self.mpi_runexec_path = filedialog.askopenfilename(
            title="Select mpirun or mpiexec.exe path", filetypes=[("All", "*.*")]
        )
        if os.path.exists(self.mpi_runexec_path) and self.mpi_runexec_path != "":
            self.ui.lineEdit_2_mpirunPath_2.setText(self.mpi_runexec_path)

    def select_setvars_path(self):
        from tkinter import filedialog
        self.setvars_Path = filedialog.askopenfilename(
            title="Select setvars.bat",
            filetypes=[("BAT", "*.bat *.BAT")],
        )
        if os.path.exists(self.setvars_Path) and self.setvars_Path != "":
            self.ui.lineEdit_setvarsPath.setText(self.setvars_Path)

    def select_kernel_path(self):
        from tkinter import filedialog
        self.kernelfiledirectory = filedialog.askdirectory(
            title="Select kernel directory"
        )
        if self.kernelfiledirectory != "":
            self.ui.lineEdit_kernel_path.setText(self.kernelfiledirectory)