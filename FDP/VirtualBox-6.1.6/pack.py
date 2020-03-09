#!/usr/bin/env python3
import collections
import datetime
import os
import pathlib
import shutil
import subprocess
import sys

DIRPATH_VBOX_BUILD = pathlib.Path.home() / "Desktop/FDP-VirtualBox-build"

DIRPATH_VBOX = pathlib.Path.home() / "Desktop/FDP-VirtualBox"
DIRPATH_VBOX_LIBS = DIRPATH_VBOX / "libs"

DIRPATH_MACPORTS_LIBS = pathlib.Path("/opt/local")


def _install_name_change(libpath, newlibpath, fpath):
    return subprocess.check_output(["install_name_tool", "-change", libpath, newlibpath, fpath])


def _get_libs(fpath):
    output = subprocess.check_output(["otool", "-L", fpath])
    for line in output.splitlines()[1:]:
        libpath = pathlib.Path(line[: line.index(b" ")].strip().decode("ascii"))
        if libpath.is_file():
            yield libpath


def _is_macports_lib(fpath):
    return DIRPATH_MACPORTS_LIBS in fpath.parents


def _copy_in_libs(libpath, newlibpath):
    assert libpath.is_file()
    assert not newlibpath.is_file()
    newlibpath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(libpath, newlibpath)
    newlibpath.chmod(0o644)


def _patch_reference(fpath, libpath, newlibpath):
    assert newlibpath.is_file()
    newlibpath = "@loader_path/{}{}".format(
        "../" * (len(fpath.relative_to(DIRPATH_VBOX).parts) - 1), newlibpath.relative_to(DIRPATH_VBOX)
    )
    _install_name_change(libpath, newlibpath, fpath)


if __name__ == "__main__":
    assert "FDPINC" in os.environ and "FDPLIB" in os.environ

    assert DIRPATH_VBOX in DIRPATH_VBOX_LIBS.parents
    shutil.rmtree(DIRPATH_VBOX, ignore_errors=True)
    shutil.copytree(DIRPATH_VBOX_BUILD / "darwin.amd64/release/dist", DIRPATH_VBOX)

    DIRPATH_VBOX_LIBS.mkdir(parents=True)

    starttime = datetime.datetime.now()
    fpaths_to_process = collections.deque(DIRPATH_VBOX.rglob("*"))
    fpaths_already_processed = set()
    fpaths_already_saved = set()
    while fpaths_to_process:
        fpath = fpaths_to_process.pop()
        assert DIRPATH_VBOX in fpath.parents
        if not fpath.is_file() or fpath in fpaths_already_processed:
            continue
        fpaths_already_processed.add(fpath)

        for libpath in _get_libs(fpath):
            if _is_macports_lib(libpath):
                newlibpath = DIRPATH_VBOX_LIBS / libpath.relative_to(libpath.anchor)
                if libpath not in fpaths_already_saved:
                    _copy_in_libs(libpath, newlibpath)
                    fpaths_already_saved.add(libpath)
                    fpaths_to_process.append(newlibpath)
                _patch_reference(fpath, libpath, newlibpath)

    _copy_in_libs(
        pathlib.Path(os.environ["FDPLIB"]) / "libFDP.dylib", DIRPATH_VBOX / "VirtualBox.app/Contents/MacOS/libFDP.dylib"
    )

    print("Done in {}".format(datetime.datetime.now() - starttime))
