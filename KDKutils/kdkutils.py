#!/usr/bin/env python
import ctypes
import struct

p64 = lambda i: struct.pack("<Q", i)


# https://bitbucket.org/ronaldoussoren/macholib/src/e287095a0b4a02dccb7537c9d1de904dc0f45cc2/macholib/mach_o.py

integer_t = ctypes.c_int32
cpu_type_t = integer_t
cpu_subtype_t = ctypes.c_uint32
vm_prot_t = ctypes.c_int32

LC_SEGMENT_64 = 0x19
LC_UUID = 0x1B


class mach_header_64(ctypes.Structure):
    _fields_ = (
        ("magic", ctypes.c_uint32),
        ("cputype", cpu_type_t),
        ("cpusubtype", cpu_subtype_t),
        ("filetype", ctypes.c_uint32),
        ("ncmds", ctypes.c_uint32),
        ("sizeofcmds", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
    )


class load_command(ctypes.Structure):
    _fields_ = (("cmd", ctypes.c_uint32), ("cmdsize", ctypes.c_uint32))


class segment_command_64(ctypes.Structure):
    _fields_ = (
        ("segname", ctypes.c_char * 16),
        ("vmaddr", ctypes.c_uint64),
        ("vmsize", ctypes.c_uint64),
        ("fileoff", ctypes.c_uint64),
        ("filesize", ctypes.c_uint64),
        ("maxprot", vm_prot_t),
        ("initprot", vm_prot_t),
        ("nsects", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    )


class section_64(ctypes.Structure):
    _fields_ = (
        ("sectname", ctypes.c_char * 16),
        ("segname", ctypes.c_char * 16),
        ("addr", ctypes.c_uint64),
        ("size", ctypes.c_uint64),
        ("offset", ctypes.c_uint32),
        ("align", ctypes.c_uint32),
        ("reloff", ctypes.c_uint32),
        ("nreloc", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("reserved1", ctypes.c_uint32),
        ("reserved2", ctypes.c_uint32),
        ("reserved3", ctypes.c_uint32),
    )
