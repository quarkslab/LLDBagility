#!/usr/bin/env python
from . import kdputils

logger = kdputils.create_logger(__name__, "/tmp/kdputils.log")

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/kdp/kdp_protocol.h

KDP_REMOTE_PORT = 41139

KDP_VERSION = 12
KDP_FEATURE_BP = 1

MAX_KDP_PKT_SIZE = 1200
MAX_KDP_DATA_SIZE = 1024


class KDPRequest:
    KDP_CONNECT = 0
    KDP_DISCONNECT = 1
    KDP_HOSTINFO = 2
    KDP_VERSION = 3
    KDP_MAXBYTES = 4
    KDP_READMEM = 5
    KDP_WRITEMEM = 6
    KDP_READREGS = 7
    KDP_WRITEREGS = 8
    KDP_LOAD = 9
    KDP_IMAGEPATH = 10
    KDP_SUSPEND = 11
    KDP_RESUMECPUS = 12
    KDP_EXCEPTION = 13
    KDP_TERMINATION = 14
    KDP_BREAKPOINT_SET = 15
    KDP_BREAKPOINT_REMOVE = 16
    KDP_REGIONS = 17
    KDP_REATTACH = 18
    KDP_HOSTREBOOT = 19
    KDP_READMEM64 = 20
    KDP_WRITEMEM64 = 21
    KDP_BREAKPOINT64_SET = 22
    KDP_BREAKPOINT64_REMOVE = 23
    KDP_KERNELVERSION = 24
    KDP_READPHYSMEM64 = 25
    KDP_WRITEPHYSMEM64 = 26
    KDP_READIOPORT = 27
    KDP_WRITEIOPORT = 28
    KDP_READMSR64 = 29
    KDP_WRITEMSR64 = 30
    KDP_DUMPINFO = 31
    KDP_INVALID_REQUEST = 32


class KDPError:
    KDPERR_NO_ERROR = 0
    KDPERR_ALREADY_CONNECTED = 1
    KDPERR_BAD_NBYTES = 2
    KDPERR_BADFLAVOR = 3
    KDPERR_BAD_ACCESS = 4
    KDPERR_MAX_BREAKPOINTS = 100
    KDPERR_BREAKPOINT_NOT_FOUND = 101
    KDPERR_BREAKPOINT_ALREADY_SET = 102


HEADER_FIELDS = (
    ("type", kdputils.UInt8),
    ("seq", kdputils.UInt8),
    ("len", kdputils.LEUInt16),
    ("key", kdputils.BEUInt32),
)

_request = 0
_reply = 1
BODY_FIELDS = {
    (_request, KDPRequest.KDP_CONNECT): [
        ("req_reply_port", kdputils.BEUInt16),
        ("exc_note_port", kdputils.BEUInt16),
        ("greeting", kdputils.CStr),
    ],
    (_reply, KDPRequest.KDP_CONNECT): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_DISCONNECT): [],
    (_reply, KDPRequest.KDP_DISCONNECT): [],
    (_request, KDPRequest.KDP_REATTACH): [("req_reply_port", kdputils.BEUInt16)],
    (_reply, KDPRequest.KDP_REATTACH): [],
    (_request, KDPRequest.KDP_HOSTINFO): [],
    (_reply, KDPRequest.KDP_HOSTINFO): [
        ("cpus_mask", kdputils.LEUInt32),
        ("cpu_type", kdputils.LEUInt32),
        ("cpu_subtype", kdputils.LEUInt32),
    ],
    (_request, KDPRequest.KDP_VERSION): [],
    (_reply, KDPRequest.KDP_VERSION): [
        ("version", kdputils.LEUInt32),
        ("feature", kdputils.LEUInt32),
        ("pad0", kdputils.LEUInt32),
        ("pad1", kdputils.LEUInt32),
    ],
    (_request, KDPRequest.KDP_READMEM64): [("address", kdputils.LEUInt64), ("nbytes", kdputils.LEUInt32)],
    (_reply, KDPRequest.KDP_READMEM64): [("error", kdputils.LEUInt32), ("data", kdputils.Str)],
    (_request, KDPRequest.KDP_WRITEMEM64): [
        ("address", kdputils.LEUInt64),
        ("nbytes", kdputils.LEUInt32),
        ("data", kdputils.Str),
    ],
    (_reply, KDPRequest.KDP_WRITEMEM64): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_READMSR64): [("address", kdputils.LEUInt32), ("lcpu", kdputils.LEUInt16)],
    (_reply, KDPRequest.KDP_READMSR64): [("error", kdputils.LEUInt32), ("data", kdputils.CStr)],
    (_request, KDPRequest.KDP_WRITEMSR64): [
        ("address", kdputils.LEUInt32),
        ("lcpu", kdputils.LEUInt16),
        ("data", kdputils.CStr),
    ],
    (_reply, KDPRequest.KDP_WRITEMSR64): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_READREGS): [("cpu", kdputils.LEUInt32), ("flavor", kdputils.LEUInt32)],
    (_reply, KDPRequest.KDP_READREGS): [
        ("error", kdputils.LEUInt32),
        ("rax", kdputils.LEUInt64),
        ("rbx", kdputils.LEUInt64),
        ("rcx", kdputils.LEUInt64),
        ("rdx", kdputils.LEUInt64),
        ("rdi", kdputils.LEUInt64),
        ("rsi", kdputils.LEUInt64),
        ("rbp", kdputils.LEUInt64),
        ("rsp", kdputils.LEUInt64),
        ("r8", kdputils.LEUInt64),
        ("r9", kdputils.LEUInt64),
        ("r10", kdputils.LEUInt64),
        ("r11", kdputils.LEUInt64),
        ("r12", kdputils.LEUInt64),
        ("r13", kdputils.LEUInt64),
        ("r14", kdputils.LEUInt64),
        ("r15", kdputils.LEUInt64),
        ("rip", kdputils.LEUInt64),
        ("rflags", kdputils.LEUInt64),
        ("cs", kdputils.LEUInt64),
        ("fs", kdputils.LEUInt64),
        ("gs", kdputils.LEUInt64),
    ],
    (_request, KDPRequest.KDP_WRITEREGS): [
        ("cpu", kdputils.LEUInt32),
        ("flavor", kdputils.LEUInt32),
        ("rax", kdputils.LEUInt64),
        ("rbx", kdputils.LEUInt64),
        ("rcx", kdputils.LEUInt64),
        ("rdx", kdputils.LEUInt64),
        ("rdi", kdputils.LEUInt64),
        ("rsi", kdputils.LEUInt64),
        ("rbp", kdputils.LEUInt64),
        ("rsp", kdputils.LEUInt64),
        ("r8", kdputils.LEUInt64),
        ("r9", kdputils.LEUInt64),
        ("r10", kdputils.LEUInt64),
        ("r11", kdputils.LEUInt64),
        ("r12", kdputils.LEUInt64),
        ("r13", kdputils.LEUInt64),
        ("r14", kdputils.LEUInt64),
        ("r15", kdputils.LEUInt64),
        ("rip", kdputils.LEUInt64),
        ("rflags", kdputils.LEUInt64),
        ("cs", kdputils.LEUInt64),
        ("fs", kdputils.LEUInt64),
        ("gs", kdputils.LEUInt64),
    ],
    (_reply, KDPRequest.KDP_WRITEREGS): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_RESUMECPUS): [("cpu_mask", kdputils.LEUInt32)],
    (_reply, KDPRequest.KDP_RESUMECPUS): [],
    (_request, KDPRequest.KDP_BREAKPOINT64_SET): [("address", kdputils.LEUInt64)],
    (_reply, KDPRequest.KDP_BREAKPOINT64_SET): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_BREAKPOINT64_REMOVE): [("address", kdputils.LEUInt64)],
    (_reply, KDPRequest.KDP_BREAKPOINT64_REMOVE): [("error", kdputils.LEUInt32)],
    (_request, KDPRequest.KDP_EXCEPTION): [
        ("n_exc_info", kdputils.LEUInt32),
        ("cpu", kdputils.LEUInt32),
        ("exception", kdputils.LEUInt32),
        ("code", kdputils.LEUInt32),
        ("subcode", kdputils.LEUInt32),
    ],
    (_reply, KDPRequest.KDP_EXCEPTION): [],
    (_request, KDPRequest.KDP_KERNELVERSION): [],
    (_reply, KDPRequest.KDP_KERNELVERSION): [("version", kdputils.CStr)],
}


def _pack(pkt):
    pkt["type"] = pkt["is_reply"] << 7 | pkt["request"] & 0b01111111
    data = bytes(
        b"".join(
            ttype.pack(pkt[name])
            for fields in (HEADER_FIELDS, BODY_FIELDS[(pkt["is_reply"], pkt["request"])])
            for name, ttype in fields
        )
    )
    del pkt["type"]
    return data


def _unpack(data):
    pkt = dict()
    offset = 0
    for name, ttype in HEADER_FIELDS:
        pkt[name], size = ttype.unpack(data[offset:])
        offset += size
    pkt["is_reply"] = pkt["type"] >> 7
    pkt["request"] = pkt["type"] & 0b01111111
    del pkt["type"]
    for name, ttype in BODY_FIELDS[(pkt["is_reply"], pkt["request"])]:
        pkt[name], size = ttype.unpack(data[offset:])
        offset += size
    return pkt


def _calcsize(pkt):
    pkt["type"] = pkt["is_reply"] << 7 | pkt["request"] & 0b01111111
    size = sum(
        ttype.calcsize(pkt[name])
        for fields in (HEADER_FIELDS, BODY_FIELDS[(pkt["is_reply"], pkt["request"])])
        for name, ttype in fields
    )
    del pkt["type"]
    return size


def send(from_sock, to_addr, sendpkt, seq, key):
    sendpkt["seq"] = seq
    sendpkt["len"] = _calcsize(sendpkt)
    sendpkt["key"] = key
    logger.debug("--> {}".format(_summary(sendpkt)))
    return from_sock.sendto(_pack(sendpkt), to_addr)


def recv(from_sock):
    data, addr = from_sock.recvfrom(MAX_KDP_PKT_SIZE)
    recvpkt = _unpack(data)
    logger.debug("<-- {}".format(_summary(recvpkt)))
    return recvpkt, addr


KDPRequest.names = {getattr(KDPRequest, name): name for name in dir(KDPRequest) if name.startswith("KDP_")}

KDPError.names = {getattr(KDPError, name): name for name in dir(KDPError) if name.startswith("KDPERR")}


def _repr(k, v):
    if k == "request":
        return KDPRequest.names[v]
    elif k == "error":
        return KDPError.names[v]
    elif isinstance(v, int):
        return "0x{:x}".format(v)
    return repr(v)


def _summary(pkt):
    return "{} {{{}}}".format(
        KDPRequest.names[pkt["request"]],
        ", ".join("'{}': {}".format(k, _repr(k, v)) for k, v in pkt.items() if k != "request"),
    )


if __name__ == "__main__":
    import unittest
    from . import replies

    class PackageTestCase(unittest.TestCase):
        def test_pack_unpack(self):
            pkt1 = replies.kdp_connect(error=123)
            pkt1["seq"] = 1
            pkt1["len"] = 2
            pkt1["key"] = 3
            pkt2 = _unpack(_pack(pkt1))
            self.assertTrue(all(pkt1[k] == pkt2[k] for k in pkt1))

    unittest.main()
