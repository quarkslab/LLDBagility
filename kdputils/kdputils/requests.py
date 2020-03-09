#!/usr/bin/env python
from . import protocol

# https://github.com/llvm/llvm-project/blob/llvmorg-8.0.0/lldb/source/Plugins/Process/MacOSX-Kernel/CommunicationKDP.cpp
# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/kdp/ml/x86_64/kdp_machdep.c#L72


def kdp_connect(req_reply_port, exc_note_port, greeting):
    return dict(
        is_reply=0x0,
        request=protocol.KDPRequest.KDP_CONNECT,
        seq=-1,
        len=-1,
        key=-1,
        req_reply_port=req_reply_port,
        exc_note_port=exc_note_port,
        greeting=greeting,
    )


def kdp_reattach(req_reply_port):
    return dict(
        is_reply=0x0,
        request=protocol.KDPRequest.KDP_REATTACH,
        seq=-1,
        len=-1,
        key=-1,
        req_reply_port=req_reply_port,
    )


def kdp_kernelversion():
    return dict(
        is_reply=0x0,
        request=protocol.KDPRequest.KDP_KERNELVERSION,
        seq=-1,
        len=-1,
        key=-1,
    )


def kdp_exception(n_exc_info, cpu, exception, code, subcode):
    return dict(
        is_reply=0x0,
        request=protocol.KDPRequest.KDP_EXCEPTION,
        seq=-1,
        len=-1,
        key=-1,
        n_exc_info=n_exc_info,
        cpu=cpu,
        exception=exception,
        code=code,
        subcode=subcode,
    )
