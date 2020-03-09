#!/usr/bin/env python
import argparse
import binascii
import ctypes

import kdkutils


def _find_uuid_offset(macho):
    offset = 0

    header = kdkutils.mach_header_64.from_buffer(macho[offset:])
    offset += ctypes.sizeof(kdkutils.mach_header_64)

    for _ in range(header.ncmds):
        loadcmd = kdkutils.load_command.from_buffer(macho[offset:])
        if loadcmd.cmd == kdkutils.LC_UUID:
            offset += ctypes.sizeof(kdkutils.load_command)
            return offset
        offset += loadcmd.cmdsize
    else:
        raise AssertionError


def set_macho_uuid(machofilepath, uuid):
    uuid_bytesize = 16
    assert len(uuid) == uuid_bytesize

    with open(machofilepath, "rb") as f:
        macho = bytearray(f.read())

    uuid_offset = _find_uuid_offset(macho)

    with open(machofilepath, "wb") as f:
        f.write(macho[:uuid_offset])
        f.write(uuid)
        f.write(macho[uuid_offset + uuid_bytesize :])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("machofile", type=argparse.FileType())
    parser.add_argument("uuid")
    args = parser.parse_args()

    assert len(args.uuid) == 36
    uuid = binascii.unhexlify(args.uuid.replace("-", ""))
    set_macho_uuid(args.machofile.name, uuid)
