# Fast Debugging Protocol (FDP)

- API for virtual machine introspection and debugging
- Supports x86-64 and AArch64
- Provides patches for VirtualBox
- Provides Python bindings
- Originally from [Winbagility](https://github.com/Winbagility/Winbagility), now used by [LLDBagility](https://github.com/quarkslab/LLDBagility) on macOS hosts

## Notes to users

- Backup your virtual machine before debugging with FDP, since crashes and abrupt terminations may cause the VM to not boot anymore.
- The FDP server code for VirtualBox supports virtual machines configured to use one virtual CPU and at most 2 GB of RAM.
- Before starting any virtual machine load the VirtualBox drivers by executing the VirtualBox `loadall.sh` script. Note that to load unsigned drivers it is required to [disable System Integrity Protection (SIP)](https://developer.apple.com/library/archive/documentation/Security/Conceptual/System_Integrity_Protection_Guide/ConfiguringSystemIntegrityProtection/ConfiguringSystemIntegrityProtection.html) on the host. Drivers have to be reloaded every time the host reboots.
- If needed, it should be possible to install the official VirtualBox Extension Pack.

## Quick start

The Releases section contains prebuilt binaries whose installation is explained in this section. Building instructions are provided in the next sections.

### Prebuilt FDP client code

1. Download the PyFDP wheel from the latest release in Releases section.
1. Install the wheel for any Python 3 interpreter. To use FDP with LLDBagility, install the wheel for the Python interpreter used by LLDB. For example, if using LLDB from the Command Line Tools:

        Downloads$ sudo /Library/Developer/CommandLineTools/usr/bin/python3 -m pip install ./PyFDP-20.0-py3-none-any.whl -t /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/site-packages/

   Then, check that PyFDP can be used by LLDB:

        $ lldb
        (lldb) script
        Python Interactive Interpreter. To exit, type 'quit()', 'exit()' or Ctrl-D.
        >>> import PyFDP
        >>>

### Prebuilt VirtualBox for macOS hosts with the FDP server code

1. Download the zipped VirtualBox from the latest release in Releases section and unzip it anywhere in the file system.
1. Load the VirtualBox drivers (SIP must be disabled):

        VirtualBox$ sudo ./loadall.sh

1. Double-click or `open` the VirtualBox application:

        VirtualBox$ open VirtualBox.app

1. Import any virtual machine. Then, in the VM settings in VirtualBox, set the number of virtual CPUs to 1 and the RAM to 2 GB maximum. Then, starts the VM and check that it runs correctly. Lastly, download `testFDP` from the latest release in Releases section, execute the FDP tests (which change the state of the machine) and check they succeed:

        Downloads$ ./testFDP macos-mojave-18F32

## Building the FDP client code

FDP has been built only on macOS (but with little effort it should also compile on Linux).

1. Download and install [Homebrew](https://brew.sh).
1. Install the FDP dependencies:

        $ brew install cmake

1. Build FDP:

        FDP$ make fdp

## Building VirtualBox for macOS hosts with the FDP server code

The easiest and supported way to build VirtualBox is within a virtual machine running macOS Mojave, and the simplest way to test the VirtualBox build is within the same VM thanks to nested virtualisation. VirtualBox requires Xcode 6.2 for building (which fails with `SIGABRT` on macOS Catalina).

In addition to the steps for building the FDP client code:

1. Install some VirtualBox dependencies with Homebrew:

        $ brew install libidl glib openssl pkg-config

1. Install Qt with [MacPorts](https://www.macports.org/install.php):

        $ sudo /opt/local/bin/port install qt56

1. Download [Xcode_6.2.dmg](https://download.developer.apple.com/Developer_Tools/Xcode_6.2/Xcode_6.2.dmg) (log in with a free Apple ID is required) and mount it:

        Downloads$ open Xcode_6.2.dmg

1. Run the VirtualBox extractor script:

        FDP$ virtualbox/tools/darwin.amd64/bin/xcode-6.2-extractor.sh

1. Build FDP and VirtualBox:

        FDP$ make virtualbox

    Building takes around 15 minutes; once finished, the VirtualBox application will be at `out-latest/VirtualBox/VirtualBox.app`.
