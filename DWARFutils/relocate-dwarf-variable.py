#!/usr/bin/env python
import argparse
import re
import subprocess

import dwarfutils


def extract_var_info(dwarffilepath, varname):
    textdies = dwarfutils.extract_dies_by_name(dwarffilepath, varname)
    for textdie in textdies:
        try:
            location, b, addr = re.search(
                r"AT_location\( \<(0x[0-9a-f]+)> ([0-9a-f]+) .+? \( addr (0x[0-9a-f]+)", textdie
            ).groups()
            location = int(location, 16)
            b = int(b, 16)
            addr = int(addr, 16)
        except AttributeError:
            continue
        else:
            # first valid occurrence seems to be always the correct one
            return location, b, addr
    else:
        raise AssertionError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dwarffile", type=argparse.FileType())
    parser.add_argument("varname")
    parser.add_argument("newaddr", type=lambda i: int(i, 0))
    args = parser.parse_args()

    location, b, curr_addr = extract_var_info(args.dwarffile.name, args.varname)
    curr_addr_len_in_bytes = 8
    bytes_to_find_in_dwarffile = b"%b%b%b" % (
        location.to_bytes(1, byteorder="little"),
        b.to_bytes(1, byteorder="little"),
        curr_addr.to_bytes(curr_addr_len_in_bytes, byteorder="little"),
    )

    with open(args.dwarffile.name, "rb") as f:
        dwarffile = f.read()

    dwarffile_addr_offset = (
        dwarffile.find(bytes_to_find_in_dwarffile) + len(bytes_to_find_in_dwarffile) - curr_addr_len_in_bytes
    )

    dwarffile_addr_value = int.from_bytes(
        dwarffile[dwarffile_addr_offset : dwarffile_addr_offset + curr_addr_len_in_bytes], byteorder="little"
    )
    assert dwarffile_addr_value == curr_addr

    new_addr = args.newaddr.to_bytes(8, byteorder="little")

    new_dwarffile = bytearray(dwarffile)
    new_dwarffile[dwarffile_addr_offset : dwarffile_addr_offset + len(new_addr)] = new_addr
    with open(args.dwarffile.name, "wb") as f:
        f.write(new_dwarffile)
