#!/usr/bin/env python3
import datetime
import os
import pathlib
import shutil
import subprocess
import sys

DIRPATH_VBOX_BUILD = pathlib.Path.home() / "Desktop/FDP-VirtualBox-build"


if __name__ == "__main__":
    assert "FDPINC" in os.environ and "FDPLIB" in os.environ

    shutil.rmtree(DIRPATH_VBOX_BUILD, ignore_errors=True)
    DIRPATH_VBOX_BUILD.mkdir(parents=True)

    starttime = datetime.datetime.now()
    SCRIPT_VBOX_BUILD = DIRPATH_VBOX_BUILD / "build.sh"
    with open(SCRIPT_VBOX_BUILD, "w") as f:
        f.write(
            f"""\
cat > "{DIRPATH_VBOX_BUILD}/LocalConfig.kmk" <<EOF
VBOX_WITH_R0_LOGGING = 1  # Requires building with kmk BUILD_TYPE=debug
VBOX_WITH_TESTSUITE =
VBOX_WITH_TESTCASES =
kBuildGlobalDefaults_LD_DEBUG =
EOF

./configure\
    --disable-hardening\
    `# Using --disable-java, --disable-python and --disable-docs just to speed up the build`\
    --disable-java\
    --disable-python\
    --disable-docs\
    --with-qt-dir="/opt/local/libexec/qt5"\
    --with-openssl-dir="/usr/local/opt/openssl"\
    --with-xcode-dir="tools/darwin.amd64/xcode/v6.2/x.app"\
    --out-path="{DIRPATH_VBOX_BUILD}"

source "{DIRPATH_VBOX_BUILD}/env.sh"
kmk
"""
        )
    subprocess.run(["/usr/bin/env", "bash", SCRIPT_VBOX_BUILD], check=True, stdout=sys.stdout, stderr=sys.stderr)

    print("Done in {}".format(datetime.datetime.now() - starttime))
