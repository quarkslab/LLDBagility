#!/usr/bin/env python
import argparse

import dwarfutils

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dwarffile", type=argparse.FileType())
    parser.add_argument("symbol")
    parser.add_argument("--children", action="store_true")
    parser.add_argument("--filter")
    args = parser.parse_args()

    try:
        offset = int(args.symbol, 0)
        textdies = dwarfutils.extract_dies_by_offset(args.dwarffile.name, offset, children=args.children)
    except ValueError:
        name = args.symbol
        textdies = dwarfutils.extract_dies_by_name(args.dwarffile.name, name, children=args.children)

    for textdie in textdies:
        if not args.filter or args.filter in dwarfutils.extract_tag(textdie):
            print(textdie)
            print()
