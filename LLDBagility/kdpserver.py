#!/usr/bin/env python
import itertools
import socket
import time

import kdputils.replies
import kdputils.requests
import lldbagilityutils
from kdputils.protocol import KDP_FEATURE_BP, KDP_VERSION, MAX_KDP_DATA_SIZE, KDPError, KDPRequest

logger = lldbagilityutils.create_logger(__name__, "/tmp/kdpserver.log")

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/i386/thread_status.h
x86_THREAD_STATE64 = 0x4
x86_FLOAT_STATE64 = 0x5

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/i386/_structs.h#L658
_STRUCT_X86_THREAD_STATE64 = (
    "rax",
    "rbx",
    "rcx",
    "rdx",
    "rdi",
    "rsi",
    "rbp",
    "rsp",
    "r8",
    "r9",
    "r10",
    "r11",
    "r12",
    "r13",
    "r14",
    "r15",
    "rip",
    "rflags",
    "cs",
    "fs",
    "gs",
)


class KDPServer:
    def __init__(self):
        self.sv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sv_sock.setblocking(False)
        self.sv_sock.bind(("127.0.0.1", 0))

        self._cl_host = None
        self._cl_reply_port = None
        self._cl_exception_port = None
        self._cl_exception_seq = None
        self._cl_session_key = 0x1337
        self._cl_connected = False

        self._continue_debug_loop = True

    def _process(self, vm, reqpkt, cl_addr):
        if reqpkt["request"] == KDPRequest.KDP_CONNECT:
            assert self._cl_host and self._cl_reply_port
            self._cl_exception_port = reqpkt["exc_note_port"]
            self._cl_exception_seq = itertools.cycle(range(256))
            self._cl_connected = True
            vm.halt()
            vm.unset_all_breakpoints()
            replypkt = kdputils.replies.kdp_connect(KDPError.KDPERR_NO_ERROR)

        elif reqpkt["request"] == KDPRequest.KDP_DISCONNECT:
            assert self._cl_connected
            self._cl_connected = False
            self._continue_debug_loop = False
            vm.unset_all_breakpoints()
            replypkt = kdputils.replies.kdp_disconnect()

        elif reqpkt["request"] == KDPRequest.KDP_HOSTINFO:
            assert self._cl_connected
            cpus_mask, cpu_type, cpu_subtype = vm.get_host_info()
            replypkt = kdputils.replies.kdp_hostinfo(cpus_mask, cpu_type, cpu_subtype)

        elif reqpkt["request"] == KDPRequest.KDP_VERSION:
            assert self._cl_connected
            version, feature = KDP_VERSION, KDP_FEATURE_BP
            replypkt = kdputils.replies.kdp_version(version, feature)

        elif reqpkt["request"] == KDPRequest.KDP_READREGS:
            assert self._cl_connected
            if reqpkt["flavor"] == x86_THREAD_STATE64:
                regs = vm.read_registers(_STRUCT_X86_THREAD_STATE64)
                replypkt = kdputils.replies.kdp_readregs(KDPError.KDPERR_NO_ERROR, regs)
            elif reqpkt["flavor"] == x86_FLOAT_STATE64:
                raise NotImplementedError
            else:
                regs = {}
                replypkt = kdputils.replies.kdp_readregs(KDPError.KDPERR_BADFLAVOR, regs)

        elif reqpkt["request"] == KDPRequest.KDP_WRITEREGS:
            assert self._cl_connected
            if reqpkt["flavor"] == x86_THREAD_STATE64:
                regs = {k: v for k, v in reqpkt.items() if k in _STRUCT_X86_THREAD_STATE64}
                vm.write_registers(regs)
                replypkt = kdputils.replies.kdp_writeregs(KDPError.KDPERR_NO_ERROR)
            elif reqpkt["flavor"] == x86_FLOAT_STATE64:
                raise NotImplementedError
            else:
                replypkt = kdputils.replies.kdp_writeregs(KDPError.KDPERR_BADFLAVOR)

        elif reqpkt["request"] == KDPRequest.KDP_RESUMECPUS:
            assert self._cl_connected
            vm.resume()
            replypkt = kdputils.replies.kdp_resumecpus()

        elif reqpkt["request"] == KDPRequest.KDP_REATTACH:
            assert not self._cl_connected
            self._cl_host, self._cl_reply_port = cl_addr
            replypkt = kdputils.replies.kdp_reattach()

        elif reqpkt["request"] == KDPRequest.KDP_READMEM64:
            assert self._cl_connected
            if reqpkt["nbytes"] > MAX_KDP_DATA_SIZE:
                data = b""
                replypkt = kdputils.replies.kdp_readmem64(KDPError.KDPERR_BAD_NBYTES, data)
            else:
                data = vm.read_virtual_memory(reqpkt["address"], reqpkt["nbytes"])
                if len(data) != reqpkt["nbytes"]:
                    replypkt = kdputils.replies.kdp_readmem64(KDPError.KDPERR_BAD_ACCESS, data)
                else:
                    replypkt = kdputils.replies.kdp_readmem64(KDPError.KDPERR_NO_ERROR, data)

        elif reqpkt["request"] == KDPRequest.KDP_WRITEMEM64:
            assert self._cl_connected
            if reqpkt["nbytes"] > MAX_KDP_DATA_SIZE:
                replypkt = kdputils.replies.kdp_writemem64(KDPError.KDPERR_BAD_NBYTES)
            else:
                assert reqpkt["nbytes"] == len(reqpkt["data"])
                vm.write_virtual_memory(reqpkt["address"], reqpkt["data"])
                replypkt = kdputils.replies.kdp_writemem64(KDPError.KDPERR_NO_ERROR)

        elif reqpkt["request"] == KDPRequest.KDP_BREAKPOINT64_SET:
            assert self._cl_connected
            vm.set_soft_exec_breakpoint(reqpkt["address"])
            replypkt = kdputils.replies.kdp_breakpoint64_set(KDPError.KDPERR_NO_ERROR)

        elif reqpkt["request"] == KDPRequest.KDP_BREAKPOINT64_REMOVE:
            assert self._cl_connected
            vm.unset_soft_breakpoint(reqpkt["address"])
            replypkt = kdputils.replies.kdp_breakpoint64_remove(KDPError.KDPERR_NO_ERROR)

        elif reqpkt["request"] == KDPRequest.KDP_KERNELVERSION:
            assert self._cl_connected
            kernel_version = vm.get_kernel_version()
            replypkt = kdputils.replies.kdp_kernelversion(kernel_version)

        elif reqpkt["request"] == KDPRequest.KDP_EXCEPTION:
            assert self._cl_connected
            assert reqpkt["is_reply"]
            replypkt = None

        else:
            raise NotImplementedError

        return replypkt

    def debug(self, vm):
        # it is implicitly assumed the first two KDP requests received are
        # KDP_REATTACH and KDP_CONNECT (this is always true when LLDB connects)
        while self._continue_debug_loop:
            time.sleep(0.003)

            try:
                # receive a request
                reqpkt, cl_addr = kdputils.protocol.recv(self.sv_sock)
            except socket.error:
                pass
            else:
                # process the request
                replypkt = self._process(vm, reqpkt, cl_addr)
                if replypkt:
                    # send the response
                    cl_addr = (self._cl_host, self._cl_reply_port)
                    kdputils.protocol.send(self.sv_sock, cl_addr, replypkt, reqpkt["seq"], reqpkt["key"])

            if self._cl_connected and vm.state_changed():
                _, exception = vm.state()
                if exception:
                    (exception, code, subcode) = exception
                    reqpkt = kdputils.requests.kdp_exception(
                        n_exc_info=0x1, cpu=0x0, exception=exception, code=code, subcode=subcode
                    )
                    cl_addr = (self._cl_host, self._cl_exception_port)
                    kdputils.protocol.send(
                        self.sv_sock, cl_addr, reqpkt, next(self._cl_exception_seq), self._cl_session_key
                    )
