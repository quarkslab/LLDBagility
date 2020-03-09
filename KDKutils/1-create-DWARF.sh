#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

: ${1?"Usage: $0 VARSFILE"}
VARSFILE="$1"
echo "VARSFILE=\"$VARSFILE\""

source "$VARSFILE"

echo "KDKUTILS_SOURCE_KERNEL_DWARF=\"$KDKUTILS_SOURCE_KERNEL_DWARF\""
echo "KDKUTILS_SOURCE_KERNEL_DIEOFFSETS=\"${KDKUTILS_SOURCE_KERNEL_DIEOFFSETS[@]}\""
echo "KDKUTILS_GENERATED_KERNEL=\"$KDKUTILS_GENERATED_KERNEL\""

# from the input DWARF file, extract the structures/variables at the specified offsets
DWARFUTILS_SRCDIRECTORY=$(../DWARFutils/parse-dwarf-types-to-c-source.py "$KDKUTILS_SOURCE_KERNEL_DWARF" ${KDKUTILS_SOURCE_KERNEL_DIEOFFSETS[@]} \
    | python -c 'import re, sys; print(re.search("Output directory: .(.+?).$", sys.stdin.read()).group(1))' )
# compile the extracted structures/variables into a new DWARF file
cd "$DWARFUTILS_SRCDIRECTORY" >/dev/null
    command -v clang-format >/dev/null && clang-format -i -style="{AlignConsecutiveDeclarations: true}" *.c
    clang -g -x c -shared -Wno-visibility *.c
    mkdir -p "$(dirname "$KDKUTILS_GENERATED_KERNEL")"
    cp "a.out.dSYM/Contents/Resources/DWARF/a.out" "$KDKUTILS_GENERATED_KERNEL"
    rm -r "a.out" "a.out.dSYM"
    file "$KDKUTILS_GENERATED_KERNEL"
cd - >/dev/null
echo "DWARFUTILS_SRCDIRECTORY=\"$DWARFUTILS_SRCDIRECTORY\""
