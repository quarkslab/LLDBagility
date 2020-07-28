# KDPutils

KDPutils is a Python package that reimplements many of the functionalities of XNU's Kernel Debugging Protocol (KDP).

## Requisites

- A recent Python 3 interpreter

## Installation

1. Install the package for any Python 3 interpreter using pip:

        kdputils$ python -m pip install .

    To use kdputils with LLDBagility, install the package for the Python interpreter used by LLDB. For example, if using LLDB from the Command Line Tools:

        kdputils$ sudo /Library/Developer/CommandLineTools/usr/bin/python3 -m pip install . -t /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/site-packages/

## Usage

To run the included example:

1. set up a macOS machine for remote kernel debugging;
2. then, boot the machine, drop in the debugger (by e.g. injecting an NMI) and wait until the string "`Waiting for remote debugger connection.`" is printed on screen;
3. finally, execute `python <path-to-LLDBagility>/KDPutils/examples/kdpclient.py <host>` to connect to the debuggee (via Ethernet only) and retrieve the kernel version.
