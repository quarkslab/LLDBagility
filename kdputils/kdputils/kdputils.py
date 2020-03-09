#!/usr/bin/env python
import logging
import os
import struct


class Int:
    fmt = None

    @classmethod
    def pack(cls, value):
        return struct.pack(cls.fmt, value)

    @classmethod
    def unpack(cls, data):
        (value,) = struct.unpack_from(cls.fmt, data)
        return value, struct.calcsize(cls.fmt)

    @classmethod
    def calcsize(cls, value):
        return struct.calcsize(cls.fmt)


class UInt8(Int):
    fmt = "B"


class UInt8(Int):
    fmt = "B"


class LEUInt16(Int):
    fmt = "<H"


class BEUInt16(Int):
    fmt = ">H"


class LEUInt32(Int):
    fmt = "<I"


class BEUInt32(Int):
    fmt = ">I"


class LEUInt64(Int):
    fmt = "<Q"


class Str:
    fmt = None

    @staticmethod
    def pack(value):
        return value

    @staticmethod
    def unpack(data):
        return data, len(data)

    @staticmethod
    def calcsize(value):
        return len(value)


class CStr:
    fmt = None

    @staticmethod
    def pack(value):
        return b"".join((value, b"\0"))

    @staticmethod
    def unpack(data):
        value = data[: data.index(b"\0") + 1]
        return value, len(value)

    @staticmethod
    def calcsize(value):
        return len(value) + 1


def create_logger(name, filename):
    filehandler = logging.FileHandler(filename, mode="w")
    filehandler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.addHandler(filehandler)
    logger.setLevel(os.getenv("LOGLEVEL", default="WARNING").upper())
    return logger
