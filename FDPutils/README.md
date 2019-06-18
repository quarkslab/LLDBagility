# FDPutils
This folder contains a port of the original [Fast Debugging Protocol](https://winbagility.github.io/) (FDP) to macOS hosts and VirtualBox 5.2.14 and 6.0.8. The following sections detail the steps required to build VirtualBox with the FDP patch, build the FDP dylib and install PyFDP.

The Releases section contains zipped VirtualBox 5.2.14 and 6.0.8 apps already built with the FDP patch; these still require for now to install MacPorts and `qt56` (see step 1.4 below). Launch the apps from the terminal with `open <path-to-Virtualbox-app>` to catch possible errors. The 6.0.8 version may also require setting the shell variable `DYLD_LIBRARY_PATH="<path-to-Virtualbox-app/Contents/MacOS"`.

Before starting virtual machines, remember to load the VirtualBox drivers by executing the `loadall.sh` script (located at `VirtualBox.app/Utils/` in the released app); note that to load unsigned drivers it is required to disable SIP. If needed, it is also possible to install the official [Extension Pack](https://www.virtualbox.org/wiki/Download_Old_Builds_5_2).

## 1. Building VirtualBox with the FDP patch for macOS hosts
The following instructions are adapted from this thread: https://forums.virtualbox.org/viewtopic.php?t=83521.

0. Download and unzip the VirtualBox [5.2.14](https://download.virtualbox.org/virtualbox/5.2.14/VirtualBox-5.2.14.tar.bz2) (or [6.0.8](https://download.virtualbox.org/virtualbox/6.0.8/VirtualBox-6.0.8.tar.bz2)) sources;
1. `cd` to `VirtualBox-5.2.14/` (or `VirtualBox-6.0.8/`) (assumed to be the working directory for all the next steps);
2. apply the provided patch with e.g. `git apply <path-to-LLDBagility>/FDPutils/VirtualBox-5.2.14_FDP_macOS.patch` (or `VirtualBox-6.0.8_FDP_macOS.patch`);
3. symlink or copy the FDP headers and sources with e.g. `ln -fs <path-to-LLDBagility>/FDPutils/FDP include/`, `ln -fs <path-to-LLDBagility>/FDPutils/FDP/include/* include/` and `ln -fs <path-to-LLDBagility>/FDPutils/FDP/FDP.c src/VBox/Debugger/`;
4. set up the VirtualBox dependencies:
- download and install [javaforosx.dmg](https://support.apple.com/kb/dl1572);
- download and install [Homebrew](https://brew.sh/), then `/usr/local/bin/brew install libidl glib openssl pkg-config`;
- download and install [MacPorts](https://www.macports.org/install.php), then `sudo /opt/local/bin/port install qt56`;
- download [Xcode_6.2.dmg](https://download.developer.apple.com/Developer_Tools/Xcode_6.2/Xcode_6.2.dmg) and mount it (e.g. `open Xcode_6.2.dmg`), then execute `tools/darwin.amd64/bin/xcode-6.2-extractor.sh`;
5. create a folder for the build (e.g. `mkdir /tmp/build`), then execute:
```
$ ./configure --disable-hardening --disable-docs --with-openssl-dir=/usr/local/opt/openssl --with-xcode-dir=tools/darwin.amd64/xcode/v6.2/x.app --out-path=/tmp/build
```
6. lastly, start the build process:
```
$ source /tmp/build/env.sh
$ kmk
```

Building takes around 10/15 minutes; once finished, VirtualBox will be at `/tmp/build/darwin.amd64/release/dist/VirtualBox.app` and the script for loading drivers at `/tmp/build/darwin.amd64/release/dist/loadall.sh` To run this app on a different machine it should be enough to install the `qt56` MacPorts package as above.

## 2. Building FDP
0. Download and install CMake (e.g. `brew install cmake`);
1. `cd` to `<path-to-LLDBagility>/FDPutils/build/` (assumed to be the working directory for all the next steps);
2. execute `cmake .`;
3. execute `make`;
4. `cp lib/libFDP.dylib ../PyFDP/PyFDP/`;
5. (optional, but suggested) execute `make testFDP`, start up a macOS virtual machine, execute `bin/testFDP <name-of-macos-vm>` and check that the tests succeed.

## 3. Installing the Python bindings (PyFDP)
PyFDP should be compatible with both Python 2 and 3; if you are installing it for LLDBagility, pick the Python version used by your LLDB installation (likely Python 2).
1. `cd` to `<path-to-LLDBagility>/FDPutils/PyFDP/`;
2. then, execute either `sudo /usr/bin/python setup.py install` to install PyFDP for system Python or `/usr/local/bin/python2 -m pip install .` for Homebrew Python 2;
3. (optional, but suggested) start a Python shell, execute `import PyFDP` and check that it succeeds.
