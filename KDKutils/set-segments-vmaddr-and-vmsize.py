#!/usr/bin/env python
import argparse
import ctypes

import kdkutils


def _find_segments_offsets(macho, segname):
    offset = 0

    header = kdkutils.mach_header_64.from_buffer(macho[offset:])
    offset += ctypes.sizeof(kdkutils.mach_header_64)

    for _ in range(header.ncmds):
        cmd = kdkutils.load_command.from_buffer(macho[offset:])
        offset += ctypes.sizeof(kdkutils.load_command)

        if cmd.cmd == kdkutils.LC_SEGMENT_64:
            segment = kdkutils.segment_command_64.from_buffer(macho[offset:])
            offset += ctypes.sizeof(kdkutils.segment_command_64)

            assert cmd.cmdsize == (
                ctypes.sizeof(kdkutils.load_command)
                + ctypes.sizeof(kdkutils.segment_command_64)
                + ctypes.sizeof(kdkutils.section_64) * segment.nsects
            )

            if segment.segname.decode("ascii") == segname:
                o = offset - ctypes.sizeof(kdkutils.segment_command_64) + 16
                return o

            for _ in range(segment.nsects):
                section = kdkutils.section_64.from_buffer(macho[offset:])
                offset += ctypes.sizeof(kdkutils.section_64)
                # print(section.sectname)

        else:
            offset += cmd.cmdsize - ctypes.sizeof(kdkutils.load_command)
    else:
        raise AssertionError


def set_segments_vmaddr_and_vmsize(machofilepath, vals):
    with open(machofilepath, "rb") as f:
        macho = bytearray(f.read())

    for segname in ("__TEXT", "__DATA", "__LINKEDIT"):
        segoffset = _find_segments_offsets(macho, segname)
        vmaddr, vmsize = vals[segname]
        macho = macho[:segoffset] + kdkutils.p64(vmaddr) + kdkutils.p64(vmsize) + macho[segoffset + 16 :]

    with open(machofilepath, "wb") as f:
        f.write(macho)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("machofile", type=argparse.FileType())
    parser.add_argument("--text")
    parser.add_argument("--data")
    parser.add_argument("--linkedit")
    args = parser.parse_args()

    vals = {
        "__TEXT": [int(n, 0) for n in args.text.split(",")],
        "__DATA": [int(n, 0) for n in args.data.split(",")],
        "__LINKEDIT": [int(n, 0) for n in args.linkedit.split(",")],
    }
    set_segments_vmaddr_and_vmsize(args.machofile.name, vals)
