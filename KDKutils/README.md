# KDKutils
This folder contains some utility scripts for creating a fake kernel DWARF file to use available XNU's lldbmacros with a macOS kernel without its specific Kernel Debug Kit (KDK). Some of the examples included here uses the `data.zip` archive uploaded in the Releases section.

## Files

### `./set-macho-uuid.py`
```
usage: set-macho-uuid.py [-h] machofile uuid
```
This script allows to replace the UUID in a Mach-O file with another arbitrary UUID.

### `./set-segments-vmaddr-and-vmsize.py`
```
usage: set-segments-vmaddr-and-vmsize.py [-h] [--text TEXT] [--data DATA]
                                         [--linkedit LINKEDIT]
                                         machofile
```
This script allows to modify the virtual address and size of the `__TEXT`, `__DATA` and `__LINKEDIT` segments in a Mach-O file.

### `./1-create-DWARF.sh`
```
Usage: ./1-create-DWARF.sh VARSFILE
```
This script extracts from a source DWARF file the structures/variables at the specified offsets and recompiles the generated C sources to create a new DWARF. The file `VARSFILE` should define the shell variables:
- `KDKUTILS_SOURCE_KERNEL_DWARF`: path to the source kernel DWARF file
- `KDKUTILS_SOURCE_KERNEL_DIEOFFSETS`: array of DIE offsets to extract (e.g. offsets of all symbols used by lldbmacros)
- `KDKUTILS_GENERATED_KERNEL`: path of the output DWARF file

### `./2-fake-DWARF.sh`
```
Usage: ./2-fake-DWARF.sh VARSFILE
```
This script modifies the created DWARF file so that it can be used as a fake symbol file for the specified macOS kernel. The file `VARSFILE` should define the shell variables:
- `KDKUTILS_TARGET_KERNEL`: path to the macOS kernel binary (e.g. the one used by the debuggee)
- `KDKUTILS_TARGET_KERNEL_DWARF`: path to the DWARF file created with `./1-create-DWARF.sh` (e.g. same as `KDKUTILS_GENERATED_KERNEL`)
- `KDKUTILS_RELOCATESYMBOLS`: array of DIE names to be relocated (e.g. names of all symbols used by lldbmacros)

### `./3-attach-DWARF.sh`
```
Usage: ./3-attach-DWARF.sh VARSFILE
```
Assuming LLDBagility has been set up, this script simply starts LLDB with the specified target and symbol file, then attaches to the specified macOS VM and finally imports the specified LLDBmacros. The file `VARSFILE` should define the shell variables:
- `KDKUTILS_TARGET_KERNEL`: as above
- `KDKUTILS_TARGET_KERNEL_DWARF`: as above
- `KDKUTILS_LLDBMACROS`: path to `kernel.py` from the lldbmacros to use
- `LLDBAGILITY_VMNAME`: name of the VM to attach to with LLDBagility

## Requisites
- A recent Python 2 or Python 3 interpreter
- A [macOS KDK](https://developer.apple.com/download/more/?q=Kernel%20Debug%20Kit) (preferably for a similar build of the kernel used by the debuggee), containing the source kernel DWARF file (e.g. `/Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/DWARF/kernel`) and the accompanying lldbmacros (e.g. `/Library/Developer/KDKs/KDK_10.14.4_18E226.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/Python/`)

## Usage
In the `examples/` directory, two complete input files are provided with the necessary definitions for using lldbmacros from macOS 10.14.2 build 18C54 with macOS 10.14.3 build 18D109 or macOS 10.14.4 build 18E226; use them as a starting point for creating input files for other builds. The examples uses the `data.zip` archive uploaded in the Releases section.

Once the input file is filled with appropriate values for all the required variables (as in the two provided examples):
1. Execute `./1-create-DWARF.sh <input-file>` to create a new DWARF;
2. then, execute `./2-fake-DWARF.sh <input-file>` to update the created DWARF;
3. finally, if LLDBagility is set up, execute `./3-attach-DWARF.sh <input-file>` to start LLDB and attach to the VM with the symbols provided by the created DWARF.

#### Which are correct values for `KDKUTILS_SOURCE_KERNEL_DIEOFFSETS`?
To work correctly, lldbmacros rely on a few structures/variables from the kernel binary, like `version`, `kernel_stack_size`, `kdp` and so on; because of this, the created DWARF file must naturally contain at minimum all of them. For each structure/variable used by lldbmacros (see the provided examples for a list), it is possible to find its offset in the source DWARF file with a command similar to:
```
$ dwarfdump -n kdp /Library/Developer/KDKs/KDK_10.12_16A323.kdk/System/Library/Kernels/kernel.dSYM/Contents/Resources/DWARF/kernel | grep -C6 ffffff
0x0002c6d8: TAG_variable [54]
             AT_name( "kdp" )
             AT_type( {0x0002c6ee} ( kdp_glob_t ) )
             AT_external( 0x01 )
             AT_decl_file( "/Library/Caches/com.apple.xbs/Sources/xnu/xnu-3789.1.32/osfmk/kdp/kdp.c" )
             AT_decl_line( 99 )
             AT_location( [0xffffff8000a63008] )
```
In this example, the DIE offset of the `kdp` variable in the source DWARF file is 0x0002c6d8.

#### Which are correct values for `KDKUTILS_RELOCATESYMBOLS`?
This is simply the list of the names of all symbols dumped from the source DWARF file, i.e. `KDKUTILS_SOURCE_KERNEL_DIEOFFSETS`.
