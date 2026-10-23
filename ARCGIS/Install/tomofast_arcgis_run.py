# -*- coding: utf-8 -*-
import os
import sys
import re
import shutil
import signal
import platform
import subprocess  # nosec B404 - needed to launch Tomofast-x
import tkinter as tk


class RunMixin:

    # ------------------------------------------------------------------
    def _poll_debug_log(self):
        if not self._debug_polling_active:
            return
        ended = self._process is not None and self._process.poll() is not None
        if ended:
            self.ui.pushButton_cancel_inversion.setEnabled(False)
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
                            self.ui.pushButton_cancel_inversion.setEnabled(False)
                            self._check_inversion_results()
                            return
            except OSError:
                pass
        if ended:
            # The job has finished without printing THE END. (usually a crash):
            # say so, since the exit code is the only clue
            self._debug_polling_active = False
            self._report_process_exit()
            return
        self.ui.root.after(500, self._poll_debug_log)

    # ------------------------------------------------------------------
    def _report_process_exit(self):
        if self._exit_reported or self._process is None:
            return
        self._exit_reported = True
        code = self._process.returncode
        log = self.ui.textEdit_inversion_log
        log.insertPlainText(f"\n*** Process ended (exit code {code}) ***\n")
        if code in (0xC00000FD, -1073741571):
            log.insertPlainText(
                "Stack overflow in tomofastx.exe (its default stack is only 2 MB, "
                "too small for large problems such as MVI).\n"
                "Fix: python scripts/set_exe_stack.py <path to tomofastx.exe> "
                "(in the plugin folder), or relink with gfortran -Wl,--stack,536870912\n"
            )
        log.moveCursor(None)

    # ------------------------------------------------------------------
    def cancel_inversion(self):
        """Kill the running tomofast job (and any child processes)."""
        process = self._process
        if process is None or process.poll() is not None:
            self.ui.pushButton_cancel_inversion.setEnabled(False)
            return
        try:
            if platform.system() == "Windows":
                # /T kills the whole process tree, /F forces it
                subprocess.run(  # nosec B603 B607 - fixed command / user-selected Tomofast-x executable, shell not used
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    creationflags=0x08000000,  # CREATE_NO_WINDOW
                    check=False,
                )
                if self._wsl_distro.strip() and self._wsl_param_path:
                    # Killing wsl.exe does not stop the Linux-side job. Match only
                    # processes whose command line contains this job's (unique)
                    # parfile path, so other tomofast runs are left alone.
                    subprocess.run(  # nosec B603 B607 - fixed command / user-selected Tomofast-x executable, shell not used
                        ["wsl", "-d", self._wsl_distro.strip(), "--exec",
                         "pkill", "-f", "--", re.escape(self._wsl_param_path)],
                        creationflags=0x08000000,
                        check=False,
                    )
            else:
                # Job was started in its own session/process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            print(f"Could not cancel the inversion: {e}")
            return
        self._debug_polling_active = False
        self._exit_reported = True
        self.ui.textEdit_inversion_log.insertPlainText("\n*** Inversion cancelled by user ***\n")
        self.ui.textEdit_inversion_log.moveCursor(None)
        self.ui.pushButton_cancel_inversion.setEnabled(False)
        self.show_message("Inversion cancelled")

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
        except tk.TclError:
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
                        return self._resolve_param_path(
                            stripped.split("=", 1)[1].strip(),
                            os.path.dirname(os.path.abspath(self.paramfile_Path)),
                        )
        except OSError:
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
                except (OSError, ValueError, IndexError):
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
        elif self.forward_data_grav_type != 1 and self.global_experimentType in (1, 3):
            ok("Data RMSE check skipped (gradiometry data has different units)")
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
            elif self.modelGrid_magn_nModelComponents != 1:
                # MVI solves for magnetisation, not susceptibility, so the limit doesn't apply
                ok(f"MVI magnetisation range (min={last_min:.4g}, max={last_max:.4g}); susceptibility scaling check not applied")
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
                except OSError:
                    pass

                self._debug_log_pos = 0
                self._exit_reported = False
                self._process = process
                self._wsl_distro = (
                    distro if platform.system() == "Windows" and not use_native_windows else ""
                )
                self.ui.pushButton_cancel_inversion.setEnabled(True)
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
                    tpfile.write("\n")  # legacy setvars line, kept for file layout
                    tpfile.write(("1" if use_native_windows else "0") + "\n")
                    tpfile.write(str(noProc) + "\n")

                self.show_message(
                    f"Process started with PID: {process.pid}",
                    "Command is running in the background",
                )
            except Exception as e:
                print(f"An error occurred: {e}")
                self.show_message(
                    "Could not start the inversion", str(e), level="warning"
                )
        else:
            self.show_message(
                "Paths to tomofastx and paramfile must be defined", level="warning"
            )

    # ------------------------------------------------------------------
    def _run_windows_native(self, noProc):
        """Launch the MPI-free native Windows executable directly (no console window)."""
        tomo_path = os.path.normpath(self.tomo_Path)
        param_path = os.path.normpath(self.paramfile_Path)
        distro = " "

        debug_path = param_path + "_debug.txt"

        # The exe shells out to Unix `cp` to archive the parfile in the output
        # folder, which fails on Windows, so do the copy here instead.
        out_dir = self._get_output_dir_from_parfile()
        if out_dir and os.path.isdir(out_dir):
            try:
                shutil.copyfile(
                    param_path, os.path.join(out_dir, os.path.basename(param_path))
                )
            except Exception as e:
                print(f"Could not copy parfile to output folder: {e}")

        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        # Redirect stdout/stderr to the debug log, which the GUI tails.
        # OpenMP build: thread count is set through OMP_NUM_THREADS
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(noProc)
        # Worker threads default to a small stack (a few MB), which the larger
        # MVI / gradiometry problems overflow (exit code 0xC00000FD). Honoured by
        # both gfortran (libgomp) and Intel (libiomp) OpenMP runtimes.
        env.setdefault("OMP_STACKSIZE", "512M")
        # stdout is a file, so Fortran runtimes buffer it by default; force
        # unbuffered output so the GUI can tail the log live.
        env["GFORTRAN_UNBUFFERED_ALL"] = "y"  # gfortran
        env["FORT_BUFFERED"] = "false"        # Intel ifort/ifx

        debug_file = open(debug_path, "w")
        try:
            process = subprocess.Popen(
                [tomo_path, "-p", param_path],
                shell=False,  # nosec B603 - fixed command / user-selected Tomofast-x executable, shell not used
                env=env,
                stdout=debug_file,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(param_path),
                creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
            )
        finally:
            debug_file.close()
        return process, distro, ""

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
        self._wsl_param_path = wsl_param_path
        wsl_debug_path = wsl_param_path + "_debug.txt"
        # Relative paths in the parameter file are relative to its folder
        wsl_param_dir = wsl_param_path.rsplit("/", 1)[0] or "/"

        if noProc == 1:
            base_command = (
                f"cd '{wsl_param_dir}' && '{wsl_tomo_path}' -p '{wsl_param_path}' "
                f"2>&1 | tee '{wsl_debug_path}'"
            )
        else:
            base_command = (
                f"cd '{wsl_param_dir}' && {mpirun_path} -np {noProc} '{wsl_tomo_path}' -j "
                f"'{wsl_param_path}' 2>&1 | tee '{wsl_debug_path}'"
            )

        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        # bash -l so the login profile is sourced, giving the same PATH as an
        # interactive WSL terminal (mpirun etc.)
        process = subprocess.Popen(  # nosec B603 B607 - fixed command / user-selected Tomofast-x executable, shell not used
            ["wsl", "-d", distro, "bash", "-l", "-c", base_command],
            shell=False,  # nosec B603 B607 - fixed command / user-selected Tomofast-x executable, shell not used
            creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
        )
        return process, distro, mpirun_path

    # ------------------------------------------------------------------
    def _run_unix(self, noProc):
        """Launch the inversion on macOS or Linux."""
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
            # relative paths in the parameter file are relative to its folder
            cwd=os.path.dirname(os.path.abspath(self.paramfile_Path)),
            **kwargs,
        )
        return process, distro, mpirun_path

    def _run_macos(self, noProc):
        return self._run_unix(noProc)

    def _run_linux(self, noProc):
        return self._run_unix(noProc)

    # ------------------------------------------------------------------
    def _update_run_controls(self):
        is_windows = platform.system() == "Windows"
        wsl = is_windows and self.ui.radioButton_windowsWSL.isChecked()

        for w in (self.ui.radioButton_windowsNative, self.ui.radioButton_windowsWSL):
            w.setEnabled(is_windows)

        for w in (
            self.ui.label_wsl_distro,
            self.ui.lineEdit_pre_command_2_WSL_Distro,
        ):
            w.setEnabled(wsl)

        # mpirun path is only needed on macOS/Linux; the native Windows exe needs no MPI
        for w in getattr(self.ui, "_mpirun_widgets", ()):
            if is_windows:
                w.grid_remove()
            else:
                w.grid()

    # ------------------------------------------------------------------
    def select_tomo_Path(self):
        from tkinter import filedialog
        self.tomo_Path = filedialog.askopenfilename(
            title="Select tomofast executable", filetypes=[("All", "*")]
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
            title="Select mpirun path", filetypes=[("All", "*")]
        )
        if os.path.exists(self.mpi_runexec_path) and self.mpi_runexec_path != "":
            self.ui.lineEdit_2_mpirunPath_2.setText(self.mpi_runexec_path)

    def select_kernel_path(self):
        from tkinter import filedialog
        self.kernelfiledirectory = filedialog.askdirectory(
            title="Select kernel directory"
        )
        if self.kernelfiledirectory != "":
            self.ui.lineEdit_kernel_path.setText(self.kernelfiledirectory)