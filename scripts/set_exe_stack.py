"""Raise the main-thread stack size of a native Windows Tomofast-x executable.

MinGW/gfortran builds are linked with a 2 MB stack. Larger problems (e.g. MVI,
where solver vectors are 3x longer) overflow it and the exe dies with exit code
3221225725 (0xC00000FD) right after "Entered subroutine lsqr_solve_sensit".
OMP_STACKSIZE does not help because it only affects worker threads.

This patches the PE header (SizeOfStackReserve) in place. A backup copy
<name>.bak is written first. The proper long-term fix is to link with a bigger
stack, e.g. gfortran -Wl,--stack,536870912.

Usage:
    python set_exe_stack.py path/to/tomofastx.exe [stack_MB]   (default 512)
"""
import os
import shutil
import struct
import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    megabytes = int(sys.argv[2]) if len(sys.argv) > 2 else 512

    with open(path, "rb") as f:
        data = bytearray(f.read())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        print("Not a PE executable:", path)
        return 1
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x20B:  # PE32+ (64-bit)
        offset, fmt = opt + 72, "<Q"
    elif magic == 0x10B:  # PE32 (32-bit)
        offset, fmt = opt + 68, "<I"
    else:
        print("Unknown PE format")
        return 1

    current = struct.unpack_from(fmt, data, offset)[0]
    wanted = megabytes * 1024 * 1024
    print(f"Current stack reserve: {current / 2**20:.1f} MB")
    if current >= wanted:
        print("Already large enough, nothing to do.")
        return 0

    backup = path + ".bak"
    if not os.path.exists(backup):
        shutil.copyfile(path, backup)
        print("Backup written:", backup)
    struct.pack_into(fmt, data, offset, wanted)
    with open(path, "wb") as f:
        f.write(data)
    print(f"Stack reserve set to {megabytes} MB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
