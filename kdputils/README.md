# KDPutils
KDPutils is a Python package that reimplements many of the functionalities of XNU's Kernel Debugging Protocol (KDP).

## Requisites
- A recent Python 2 or Python 3 interpreter

## Installation
- `cd` to `<path-to-LLDBagility>/KDPutils`;
- then execute `python -m pip install .` (on macOS, execute either `sudo /usr/bin/python setup.py install` to install KDPutils for system Python or `/usr/local/bin/python -m pip install .` for Homebrew Python).

## Usage
To run the included example:
1. set up a macOS machine for remote kernel debugging;
2. then, boot the machine, drop in the debugger (by e.g. injecting an NMI) and wait until the string "`Waiting for remote debugger connection.`" is printed on screen;
3. finally, execute `python <path-to-LLDBagility>/KDPutils/examples/kdpclient.py <host>` to connect to the debuggee (via Ethernet only) and retrieve the kernel version.
