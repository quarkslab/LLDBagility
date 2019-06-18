#!/usr/bin/env bash
set -e
dirname () { python -c "import os; print(os.path.dirname(os.path.realpath('$0')))"; }
cd "$(dirname "$0")"

OFFSETS=( 0x00028090 0x00026D0E 0x000F0124 0x0002E494 0x0002E00B 0x00027DF6 0x0000E7E4 0x001EB43F 0x00DC1EA5 0x000272F1)
for OFFSET in "${OFFSETS[@]}"
do
    echo "Testing $OFFSET"
    ./debug.sh "$OFFSET"
    echo
done
