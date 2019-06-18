#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

DWARFUTILS_DWARFFILE="../../data/10-14-2-18C54/DWARF/kernel"

: ${1?"Usage: $0 OFFSETS"}
OFFSETS="$*"

echo "DWARFUTILS_DWARFFILE=\"$DWARFUTILS_DWARFFILE\""
echo "OFFSETS=\"$OFFSETS\""

DWARFUTILS_SRCDIRECTORY=$(../parse-dwarf-types-to-c-source.py "$DWARFUTILS_DWARFFILE" $OFFSETS \
    | python -c 'import re, sys; print(re.search("Output directory: .(.+?).$", sys.stdin.read()).group(1))' )
echo $DWARFUTILS_SRCDIRECTORY
cd "$DWARFUTILS_SRCDIRECTORY" >/dev/null
    clang -g -x c -shared *.c
    command -v clang-format >/dev/null && clang-format -i -style="{AlignConsecutiveDeclarations: true}" *.c
cd - 1>/dev/null
