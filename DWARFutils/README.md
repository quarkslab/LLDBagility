# DWARFutils
This folder contains some utility scripts for working with the DWARF debugging data format. Currently, the scripts parse the output of the `dwarfdump` macOS utility (included here in the repository to preserve compatibility among macOS versions), but they can be easily modified to work with other similar utilities for dumping Mach-O DWARF information like `objdump`.

## Files

### `./dump-dwarf-dies.py`
```
usage: dump-dwarf-dies.py [-h] [--children] [--filter FILTER] dwarffile symbol
```
This convenient script dumps DIEs at a specific offset or with a specific name, optionally filtering the output only to DIEs (as printed by `dwarfdump`) which contain specific strings (e.g. `structure`, `declaration`, or any other).

### `./parse-dwarf-types-to-c-source.py`
```
usage: parse-dwarf-types-to-c-source.py [-h] dwarffile offset [offset ...]
```
This script extracts (as compilable C sources) the definitions of the types (typedefs, structs, unions, enums) and the variables defined in a DWARF file at the specified offsets. The generated C files can be formatted more nicely with any C code beautifier.

### `./relocate-dwarf-variable.py`
```
usage: relocate-dwarf-variable.py [-h] dwarffile varname newaddr
```
This script can be used to change the address of any variable in a DWARF file to a new address. This can be useful, for example, when a binary with DWARF information is debugged with LLDB, since to locate variables in memory the debugger uses the addresses specified in the DWARF sections.

### `./misc/debug.sh` and `./misc/test.sh`
Scripts for testing `./parse-dwarf-types-to-c.py`.
