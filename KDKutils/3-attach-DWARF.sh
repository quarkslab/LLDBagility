#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

: ${1?"Usage: $0 VARSFILE"}
VARSFILE="$1"
echo "VARSFILE=\"$VARSFILE\""

source "$VARSFILE"

echo "KDKUTILS_TARGET_KERNEL=\"$KDKUTILS_TARGET_KERNEL\""
echo "KDKUTILS_TARGET_KERNEL_DWARF=\"$KDKUTILS_TARGET_KERNEL_DWARF\""
echo "KDKUTILS_LLDBMACROS=\"$KDKUTILS_LLDBMACROS\""
echo "LLDBAGILITY_VMNAME=\"$LLDBAGILITY_VMNAME\""

# attach and debug the VM
env PATH="/usr/bin:/bin:/usr/sbin:/sbin" LOGLEVEL="DEBUG" lldb \
    -o "target create \"$KDKUTILS_TARGET_KERNEL\"" \
    -o "target symbols add \"$KDKUTILS_TARGET_KERNEL_DWARF\"" \
    -o "fdp-attach $LLDBAGILITY_VMNAME" \
    -o "command script import \"$KDKUTILS_LLDBMACROS\"" \
    -o "showversion"
