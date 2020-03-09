#!/usr/bin/env python
from . import protocol

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/kdp/kdp.c


def kdp_connect(error):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_CONNECT, seq=-1, len=-1, key=-1, error=error)


def kdp_disconnect():
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_DISCONNECT, seq=-1, len=-1, key=-1)


def kdp_hostinfo(cpus_mask, cpu_type, cpu_subtype):
    return dict(
        is_reply=0x1,
        request=protocol.KDPRequest.KDP_HOSTINFO,
        seq=-1,
        len=-1,
        key=-1,
        cpus_mask=cpus_mask,
        cpu_type=cpu_type,
        cpu_subtype=cpu_subtype,
    )


def kdp_version(version, feature):
    return dict(
        is_reply=0x1,
        request=protocol.KDPRequest.KDP_VERSION,
        seq=-1,
        len=-1,
        key=-1,
        version=version,
        feature=feature,
        pad0=0,
        pad1=0,
    )


def kdp_readregs(error, regs):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_READREGS, seq=-1, len=-1, key=-1, error=error, **regs)


def kdp_writeregs(error):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_WRITEREGS, seq=-1, len=-1, key=-1, error=error)


def kdp_resumecpus():
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_RESUMECPUS, seq=-1, len=-1, key=-1)


def kdp_reattach():
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_REATTACH, seq=-1, len=-1, key=-1)


def kdp_readmem64(error, data):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_READMEM64, seq=-1, len=-1, key=-1, error=error, data=data)


def kdp_writemem64(error):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_WRITEMEM64, seq=-1, len=-1, key=-1, error=error)


def kdp_breakpoint64_set(error):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_BREAKPOINT64_SET, seq=-1, len=-1, key=-1, error=error)


def kdp_breakpoint64_remove(error):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_BREAKPOINT64_REMOVE, seq=-1, len=-1, key=-1, error=error)


def kdp_kernelversion(version):
    return dict(is_reply=0x1, request=protocol.KDPRequest.KDP_KERNELVERSION, seq=-1, len=-1, key=-1, version=version)
