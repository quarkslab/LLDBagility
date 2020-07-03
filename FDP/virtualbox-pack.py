#!/usr/bin/env python3
import argparse
import collections
import datetime
import pathlib
import shutil
import subprocess
import sys


def _install_name_change(libpath, newlibpath, fpath):
    return subprocess.check_output(
        ["install_name_tool", "-change", libpath, newlibpath, fpath]
    )


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
        "../" * (len(fpath.relative_to(DIRPATH_VBOX).parts) - 1),
        newlibpath.relative_to(DIRPATH_VBOX),
    )
    _install_name_change(libpath, newlibpath, fpath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("builddir")
    parser.add_argument("outdir")
    parser.add_argument("fdplib", type=argparse.FileType())
    args = parser.parse_args()

    args = parser.parse_args()

    DIRPATH_VBOX_BUILD = pathlib.Path(args.builddir)
    assert DIRPATH_VBOX_BUILD.is_dir()
    DIRPATH_VBOX = pathlib.Path(args.outdir)
    assert not DIRPATH_VBOX.is_dir()

    DIRPATH_VBOX_LIBS = DIRPATH_VBOX / "libs"

    DIRPATH_MACPORTS_LIBS = pathlib.Path("/opt/local")

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
        pathlib.Path(args.fdplib.name),
        DIRPATH_VBOX / "VirtualBox.app/Contents/MacOS/libFDP.dylib",
    )

    print("Done in {}".format(datetime.datetime.now() - starttime))
