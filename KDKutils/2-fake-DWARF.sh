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
echo "KDKUTILS_RELOCATESYMBOLS=\"$KDKUTILS_RELOCATESYMBOLS\""

# update the UUID of the generated DWARF so that it matches the UUID of the kernel to debug
DEBUGGEEKERNEL_UUID=$(dwarfdump -u "$KDKUTILS_TARGET_KERNEL" | python -c 'import re, sys; print(re.match(r"UUID: (.+?) ", sys.stdin.read()).group(1))')
./set-macho-uuid.py "$KDKUTILS_TARGET_KERNEL_DWARF" "$DEBUGGEEKERNEL_UUID"

# relocate the "__TEXT", "__DATA" and "__LINKEDIT" segments of the generated DWARF so that
# their location matches the location of the same segments of the kernel to debug
vmaddr () {
    SEGNAME="$1"
    otool -l "$KDKUTILS_TARGET_KERNEL" | grep -A2 "segname $SEGNAME" | head -n 3 | python -c 'import re, sys; print(re.search(r"vmaddr (0x[0-9a-f]+)", sys.stdin.read()).group(1))'
}
vmsize () {
    SEGNAME="$1"
    otool -l "$KDKUTILS_TARGET_KERNEL" | grep -A2 "segname $SEGNAME" | head -n 3 | python -c 'import re, sys; print(re.search(r"vmsize (0x[0-9a-f]+)", sys.stdin.read()).group(1))'
}
./set-segments-vmaddr-and-vmsize.py "$KDKUTILS_TARGET_KERNEL_DWARF" \
    --text      "$(vmaddr __TEXT),$(vmsize __TEXT)" \
    --data      "$(vmaddr __DATA),$(vmsize __DATA)" \
    --linkedit  "$(vmaddr __LINKEDIT),$(vmsize __LINKEDIT)"

# relocate the symbols in the generated DWARF so that their location matches the location
# of the same symbols in the symbol table of the kernel to debug
relocate () {
    SYMBOL="$1"
    ADDRESS=$(nm "$KDKUTILS_TARGET_KERNEL" \
        | grep -E " _$SYMBOL\$" \
        | echo "0x$(awk '{print $1;}')")
    ../DWARFutils/relocate-dwarf-variable.py "$KDKUTILS_TARGET_KERNEL_DWARF" "$SYMBOL" "$ADDRESS"
}
for SYMBOL in "${KDKUTILS_RELOCATESYMBOLS[@]}"
do
    relocate "$SYMBOL"
done
