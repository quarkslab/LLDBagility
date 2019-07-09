# LLDBagility
LLDBagility is a tool for **debugging macOS virtual machines** with the aid of the Fast Debugging Protocol (FDP).

For all information, read the accompanying blog posts:

- [An overview of macOS kernel debugging](https://blog.quarkslab.com/an-overview-of-macos-kernel-debugging.html)
- [LLDBagility: practical macOS kernel debugging](https://blog.quarkslab.com/lldbagility-practical-macos-kernel-debugging.html)

## Features
LLDBagility implements a set of new LLDB commands that allows the debugger to:
- attach to running macOS VirtualBox virtual machines and debug their kernel, stealthily, without the need of changing the guest OS (e.g. no necessity of DEVELOPMENT or DEBUG kernels, boot-args modification or SIP disabling) and with minimal changes to the configuration of the VM;
- interrupt (and later resume) the execution of the guest kernel at any moment;
- set hardware breakpoints anywhere in kernel code, even at the start of the boot process;
- set hardware watchpoints that trigger on read and/or write accesses of the specified memory locations;
- save and restore the state of the VM in a few seconds.

## Files
- [DWARFutils/](DWARFutils/): scripts for working with DWARF files
- [FDPutils/](FDPutils/): Fast Debugging Protocol for macOS hosts and VirtualBox 5.2.14 and 6.0.8
- [KDKutils/](KDKutils/): scripts for working with Kernel Debug Kits (KDKs) and lldbmacros
- [KDPutils/](KDPutils/): Python reimplementation of the KDP protocol
- [LLDBagility/](LLDBagility/): the tool
- [misc/](misc/): helper scripts for creating macOS Mojave VMs

In the Releases section:
- `data.zip`: kernels and lldbmacros used in some of the examples
- `VirtualBox-5.2.14_FDP.app.zip`: prebuilt VirtualBox 5.2.14 app with the FDP patch for macOS hosts
- `VirtualBox-6.0.8_FDP.app.zip`: prebuilt VirtualBox 6.0.8 app with the FDP patch for macOS hosts

## Requisites
- A **recent version of macOS as host OS**, with the LLDB debugger (can be installed with e.g. `xcode-select --install`)
- A working build of VirtualBox with the FDP patch for macOS hosts along with the PyFDP bindings (instructions in the dedicated [README](FDPutils/))
- A VirtualBox VM with any version of macOS as guest OS
- A copy of the macOS kernel binary of the guest (not needed if the guest has the same kernel of the host, or if the Kernel Debug Kit of the guest kernel is installed in the host)
- The KDPutils Python package (instructions in the dedicated [README](KDPutils/))

Note that both packages PyFDP and KDPutils must be installed for the Python version used by LLDB (likely Python 2). LLDBagility has been tested with LLDB from the Command Line Tools and the Python 2 interpreter shipped with macOS, but other versions of these software should work as well; for example, to use Python 2 from Homebrew run LLDB with `env DYLD_FRAMEWORK_PATH="$(brew --prefix python@2)/Frameworks/" lldb`.

## Installation
Assuming all requisites are satisfied, simply add `command script import <path-to-LLDBagility>/LLDBagility/lldbagility.py` to `~/.lldbinit`.

## Usage
1. Start the macOS virtual machine to debug and LLDB;
2. (required only if the kernel binary of the guest is different from the kernel of the host and no KDK for the guest kernel is installed in the host) in LLDB, execute the command `target create <path-to-guest-kernel-binary>`;
3. in LLDB, execute the command `fdp-attach <name-of-macos-vm>` to start debugging the VM.

The new LLDB commands implemented by LLDBagility are:
- `fdp-attach` or `fa`, to connect the debugger to a running macOS VirtualBox virtual machine;
- `fdp-hbreakpoint` or `fh`, to set and unset read/write/execute hardware breakpoints;
- `fdp-interrupt` or `fi`, to pause the execution of the VM and return the control to the debugger (equivalent to the known sudo dtrace -w -n "BEGIN { breakpoint(); }");
- `fdp-save` or `fs`, to save the current state of the VM;
- `fdp-restore` or `fr`, to restore the VM to the last saved state.

In the debugger, use `help <command>` and `<command> -h` to see the command usage, like:
```
(lldb) help fdp-attach
     For more information run 'help fdp-attach'  Expects 'raw' input (see 'help raw-input'.)

Syntax: fdp-attach

    Connect to a macOS VM via FDP.
    The VM must have already been started.
    Existing breakpoints are deleted on attaching.
    Re-execute this command every time the VM is rebooted.

(lldb) fdp-attach -h
usage: fdp-attach [-h] vm_name

positional arguments:
  vm_name

optional arguments:
  -h, --help  show this help message and exit
```

## Important notes
- As per current FDP limitations, set the macOS VM to use one CPU only and less or equal than 2 GB of RAM (in VirtualBox' settings)
- Do not connect multiple instances of LLDBagility to the same macOS VM at the same time
- If the macOS VM reboots (for any reason), redo `fdp-attach` (the kernel slide changes and LLDB is not aware of this)
- If debugging seems slow or intermittent, disable App Nap in the macOS host
- Pause the kernel execution before setting software breakpoints or LLDB will complain
- Pause the kernel execution before setting hardware breakpoints with `fdp-hbreakpoint` or LLDB will return `Invalid expression`
- Preferably load lldbmacros after attaching, otherwise the error `FATAL FAILURE: Unable to find kdp_thread state for this connection.` is raised (and some macros breaks)
- LLBDagility should work out of the box from XNU 4903.251.3 (the latest at the time of writing) to XNU 1486.2.11; before that, minor adjustments are required in `STUBVM.read_virtual_memory()` so that the fake `kdp` struct matches the one used by the kernel

## Example session
```
$ env PATH="/usr/bin:/bin:/usr/sbin:/sbin" lldb
(lldb) fdp-attach macos-mojave-18E226
LLDBagility
  Kernel load address: 0xffffff800d200000
  Kernel slide:        0xd000000
  Kernel version:      Darwin Kernel Version 18.5.0: Mon Mar 11 20:40:32 PDT 2019; root:xnu-4903.251.3~3/RELEASE_X86_64
Version: Darwin Kernel Version 18.5.0: Mon Mar 11 20:40:32 PDT 2019; root:xnu-4903.251.3~3/RELEASE_X86_64; stext=0xffffff800d200000
Kernel UUID: 4170BF94-38B6-364F-A1B0-2F7C2C30F9A9
Load Address: 0xffffff800d200000
warning: 'kernel' contains a debug script. To run this script in this debug session:

    command script import "/Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/DWARF/../Python/kernel.py"

To run all discovered debug scripts in this session:

    settings set target.load-script-from-symbol-file true

Kernel slid 0xd000000 in memory.
Loaded kernel file /Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel
Loading 62 kext modules .............................................................. done.
kernel was compiled with optimization - stepping may behave oddly; variables may not be available.
Process 1 stopped
* thread #1, stop reason = signal SIGSTOP
    frame #0: 0xffffff800d4c2fb6 kernel`pmap_pcid_activate(tpmap=0xffffff800dcc17e0, ccpu=<unavailable>, nopagezero=<unavailable>, copyio=<unavailable>) at pmap_pcid.c:343 [opt]
Target 0: (kernel) stopped.
(lldb) command script import "/Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/DWARF/../Python/kernel.py"
Loading kernel debugging from /Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/DWARF/../Python/kernel.py
. . .
xnu debug macros loaded successfully. Run showlldbtypesummaries to enable type summaries.
settings set target.process.optimization-warnings false
(lldb) showversion
Darwin Kernel Version 18.5.0: Mon Mar 11 20:40:32 PDT 2019; root:xnu-4903.251.3~3/RELEASE_X86_64
(lldb) showbootargs
"fs4:\System\Library\CoreServices\boot.efi" usb=0x800 keepsyms=1 -v -serial=0x1
(lldb) showproctree
PID    PROCESS        POINTER
===    =======        =======
0      kernel_task    [  0xffffff800de15968 ]
|--1      launchd          [  0xffffff801456df10 ]
|  |--11     kextcache        [  0xffffff801456daa0 ]
(lldb) c
Process 1 resuming
(lldb) fdp-interrupt
Process 1 stopped
* thread #3, name = '0xffffff8013da71d0', queue = '0x0', stop reason = signal SIGINT
    frame #0: 0xffffff800d4def80 kernel`machine_idle at pmCPU.c:181 [opt]
Target 0: (kernel) stopped.
(lldb) showproctree
PID    PROCESS        POINTER
===    =======        =======
0      kernel_task    [  0xffffff800de15968 ]
|--1      launchd          [  0xffffff801456df10 ]
|  |--220    com.apple.Ambien [  0xffffff80179d1d50 ]
|  |--219    sharedfilelistd  [  0xffffff80179d21c0 ]
|  |--218    CVMCompiler      [  0xffffff80179d2630 ]
|  |--217    CVMServer        [  0xffffff80179d2aa0 ]
. . .
|  |--40     uninstalld       [  0xffffff801456d1c0 ]
|  |--39     wifiFirmwareLoad [  0xffffff801456d630 ]
|  |--37     UserEventAgent   [  0xffffff801456daa0 ]
|  |--36     syslogd          [  0xffffff801456e380 ]
(lldb) showipcsummary
task                 pid    #acts  tablesize  command
0xffffff8013d89cc0   0      94     21         kernel_task
0xffffff8013d8a840   1      4      1194       launchd
0xffffff8014e42b80   86     6      341        loginwindow
0xffffff8014e45980   37     5      512        UserEventAgent
0xffffff8014e425c0   39     2      42         wifiFirmwareLoad
. . .
0xffffff80179d6000   218    2      42         CVMCompiler
0xffffff80179d8e00   219    4      85         sharedfilelistd
0xffffff80179d93c0   220    4      85         com.apple.Ambien
Total Table size: 13619
```
