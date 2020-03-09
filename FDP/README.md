# FDP
This folder contains a port of the original [Fast Debugging Protocol (FDP)](https://winbagility.github.io/) to macOS hosts and VirtualBox 6.1.6. The following sections detail the steps required to 1) build VirtualBox with the FDP patch, 2) build the FDP dylib and 3) install PyFDP for LLDBagility.

## Important notes
- Each time the host reboots, before starting any virtual machine load the VirtualBox drivers by executing the VirtualBox `loadall.sh` script. Note that to load unsigned drivers it is required to [disable System Integrity Protection (SIP)](https://developer.apple.com/library/archive/documentation/Security/Conceptual/System_Integrity_Protection_Guide/ConfiguringSystemIntegrityProtection/ConfiguringSystemIntegrityProtection.html) on the host.
- If needed, it's possible to install the official VirtualBox Extension Pack.
- Take a snapshot of the virtual machine before starting debugging, and be aware that crashes or abrupt terminations of the VM may render it unable to start again.

## 0) Trying the prebuilt binaries

Before building VirtualBox and FDP, try the prebuilt binaries uploaded in the Releases section. Binaries were built on macOS 10.14.5 Mojave and tested (at least) on macOS 10.14.5 Mojave and macOS 10.15.4 Catalina.

### VirtualBox
0. Download `VirtualBox-6.1.6-FDP-macOS.zip` from the Releases section and unzip it anywhere in the file system.
1. Load the VirtualBox drivers (SIP must be disabled):

        VirtualBox-6.1.6-FDP-macOS$ sudo ./loadall.sh

1. Double-click or `open` the VirtualBox application `VirtualBox.app`.
1. Import any virtual machine and check that it starts and runs correctly.

### FDP/PyFDP
0. Download `libFDP.dylib` from the Releases section and move it to `~/LLDBagility/FDP/PyFDP/PyFDP/libFDP.dylib`;
1. Install and test PyFDP as described in section 3) below.

If the prebuilt binaries seem to work, that's it! Otherwise, try building VirtualBox and FDP as described in the next sections.

## 1) Building VirtualBox with the FDP patch for macOS hosts
The easiest way to build VirtualBox is within a virtual machine running macOS Mojave, and the easiest way to test the VirtualBox build is within the same VM thanks to nested virtualisation. VirtualBox requires Xcode 6.2 for building, which fails with SIGABRT on macOS Catalina.

The following instructions are adapted from this thread: https://forums.virtualbox.org/viewtopic.php?t=83521.

0. Download and unzip the VirtualBox [6.1.6](https://download.virtualbox.org/virtualbox/6.1.6/VirtualBox-6.1.6.tar.bz2) sources.
1. Apply the provided FDP patch:

        VirtualBox-6.1.6$ git apply ~/LLDBagility/FDP/VirtualBox/VirtualBox-6.1.6-FDP-macOS.diff

1. Symlink or copy the FDP headers and sources:

        VirtualBox-6.1.6$ ln -fs ~/LLDBagility/FDP/FDP include/
        VirtualBox-6.1.6$ ln -fs ~/LLDBagility/FDP/FDP/include/* include/
        VirtualBox-6.1.6$ ln -fs ~/LLDBagility/FDP/FDP/FDP.c src/VBox/Debugger/

1. Set up the VirtualBox dependencies:
    - Download and install [Homebrew](https://brew.sh/), then execute `/usr/local/bin/brew install libidl glib openssl pkg-config`.
    - Download and install [MacPorts](https://www.macports.org/install.php), then execute `sudo /opt/local/bin/port install qt56`.
    - Download [Xcode_6.2.dmg](https://download.developer.apple.com/Developer_Tools/Xcode_6.2/Xcode_6.2.dmg) (log in with a free Apple ID is required) and mount it (e.g. `open Xcode_6.2.dmg`), then extract the required files:

            VirtualBox-6.1.6$ tools/darwin.amd64/bin/xcode-6.2-extractor.sh

1. Start the build by running the provided Python script:

        VirtualBox-6.1.6$ ~/LLDBagility/FDP/VirtualBox/build.py

Building takes around 15 minutes; once finished, the VirtualBox application will be at `~/LLDBagility-vbox-build/darwin.amd64/release/dist/VirtualBox.app`. To run this application on a different machine, execute the provided Python script that creates a redistributable VirtualBox at `~/LLDBagility-vbox/`:

        VirtualBox-6.1.6$ ~/LLDBagility/FDP/VirtualBox/pack.py

## 2) Building FDP
0. Download and install CMake with e.g. Homebrew:

    ~$ brew install cmake

1. Build the FDP dylib (automatically copied to `~/LLDBagility/FDP/PyFDP/PyFDP/`) with `make`:

    LLDBagility/FDP$ make

1. (Optional, but suggested) Start any virtual machine and check that the FDP tests succeed:

    LLDBagility/FDP$ build/bin/testFDP macos-mojave-18F32

## 3) Installing PyFDP
PyFDP can be installed through pip for any recent Python 3 interpreter, for example:

     /usr/local/bin/python3 -m pip install ~/LLDBagility/FDP/PyFDP/

For LLDBagility, PyFDP must be installed for the Python interpreter used by LLDB, e.g.:

    sudo /Library/Developer/CommandLineTools/usr/bin/python3 -m pip install ~/LLDBagility/FDP/PyFDP/ -t /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/site-packages/

After installing, check that PyFDP can be used by LLDB by starting the debugger, executing `script`, and checking that `import PyFDP` succeeds:

    ~$ lldb
    (lldb) script
    Python Interactive Interpreter. To exit, type 'quit()', 'exit()' or Ctrl-D.
    >>> import PyFDP
    >>>
