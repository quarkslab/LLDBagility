#!/usr/bin/env python
import re
import threading

import lldbagilityutils
from PyFDP.FDP import FDP
from VMSN import VMSN

logger = lldbagilityutils.create_indented_logger(__name__, "/tmp/stubvm.log")


NULL = 0x0

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/eflags.h
EFL_TF = 0x00000100

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/i386/vm_param.h
I386_PGBYTES = 4096
VM_MIN_KERNEL_ADDRESS = 0xFFFFFF8000000000
VM_MAX_KERNEL_ADDRESS = 0xFFFFFFFFFFFFEFFF

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/EXTERNAL_HEADERS/mach-o/loader.h
MH_MAGIC_64 = 0xFEEDFACF

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/exception_types.h
EXC_SOFTWARE = 0x5
EXC_BREAKPOINT = 0x6
EXC_SOFT_SIGNAL = 0x10003
# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/i386/exception.h
EXC_I386_BPTFLT = 0x3
# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/bsd/sys/signal.h
SIGINT = 0x2

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/proc_reg.h
MSR_IA32_GS_BASE = 0xC0000101
MSR_IA32_KERNEL_GS_BASE = 0xC0000102

# https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/mach/machine.h
CPU_TYPE_X86 = 0x7
CPU_ARCH_ABI64 = 0x01000000
CPU_TYPE_X86_64 = CPU_TYPE_X86 | CPU_ARCH_ABI64
CPU_SUBTYPE_X86_ARCH1 = 0x4


class STUBVM(object):
    def __init__(self, stub, name):
        self.stub = stub(name)
        self.name = name
        self.lock = threading.RLock()

        self._exception = None
        self._soft_breakpoints = {}
        self._interrupt_at_next_resume = False
        self._singlestep_at_next_resume = False
        self._kdp_vaddr = None
        self._store_kdp_at_next_write_virtual_memory = False
        self._return_incremented_at_next_read_register_rip = False

    @lldbagilityutils.indented(logger)
    def _continue_until_kernel_code(self):
        logger.debug("_continue_until_kernel_code()")
        if _in_kernel_space(self.read_register("rip")):
            return
        # set a breakpoint on writes to the CR3 register (with high probability
        # only the kernel is doing it)
        cr3bp_id = self.stub.SetBreakpoint(
            self.stub.CR_HBP,
            0x0,
            self.stub.WRITE_BP,
            self.stub.VIRTUAL_ADDRESS,
            0x3,
            0x1,
            self.stub.NO_CR3,
        )
        assert 0 <= cr3bp_id <= 254
        # resume the VM execution until reaching kernel code
        while True:
            self.stub.Resume()
            self.stub.WaitForStateChanged()
            if _in_kernel_space(self.read_register("rip")):
                logger.debug(">  stopping: 0x{:016x}".format(self.read_register("rip")))
                break
            self.stub.SingleStep()
        self.stub.UnsetBreakpoint(cr3bp_id)

    @lldbagilityutils.indented(logger)
    def _get_active_thread_vaddr(self):
        logger.debug("_get_active_thread_vaddr()")
        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/cpu_data.h#L392

        def _get_gs_base(self):
            logger.debug("_get_gs_base()")

            gs_base = self.read_msr64(MSR_IA32_GS_BASE)
            logger.debug(">  MSR_IA32_GS_BASE: 0x{:016x}".format(gs_base))
            if not _in_kernel_space(gs_base):
                gs_base = self.read_msr64(MSR_IA32_KERNEL_GS_BASE)
                logger.debug(">  MSR_IA32_KERNEL_GS_BASE: 0x{:016x}".format(gs_base))
            return gs_base

        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/mp_desc.c#L476
        cpu_data_vaddr = _get_gs_base(self)
        logger.debug(">  cpu_data_vaddr: 0x{:016x}".format(cpu_data_vaddr))

        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/cpu_data.h#L149
        cpu_this = lldbagilityutils.u64(self.read_virtual_memory(cpu_data_vaddr, 0x8))
        logger.debug(">  cpu_this: 0x{:016x}".format(cpu_this))
        assert cpu_data_vaddr == cpu_this

        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/i386/cpu_data.h#L150
        cpu_active_thread = lldbagilityutils.u64(
            self.read_virtual_memory(cpu_data_vaddr + 0x8, 0x8)
        )
        logger.debug(">  cpu_active_thread: 0x{:016x}".format(cpu_active_thread))
        return cpu_active_thread

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def complete_attach(self):
        logger.debug("complete_attach()")
        self.halt()
        self.unset_all_breakpoints()
        self._continue_until_kernel_code()

        assert _in_kernel_space(self.read_register("rip"))
        self.kernel_cr3 = self.read_register("cr3")
        logger.debug(">  kernel_cr3: 0x{:x}".format(self.kernel_cr3))

        self.kernel_load_vaddr = _find_kernel_load_vaddr(self)
        logger.debug(">  kernel_load_vaddr: 0x{:016x}".format(self.kernel_load_vaddr))
        self.kernel_slide = _compute_kernel_slide(self.kernel_load_vaddr)
        logger.debug(">  kernel_slide: 0x{:x}".format(self.kernel_slide))
        self.kernel_version = _find_kernel_version(self)
        logger.debug(">  kernel_version: {}".format(self.kernel_version))

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def get_num_cpus(self):
        logger.debug("get_num_cpus()")
        return self.stub.GetCpuCount()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def get_host_info(self):
        logger.debug("get_host_info()")
        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/kdp/ml/x86_64/kdp_machdep.c#L256
        cpus_mask = 0x0
        for i in range(self.get_num_cpus()):
            cpus_mask |= 1 << i
        cpu_type = CPU_TYPE_X86_64
        cpu_subtype = CPU_SUBTYPE_X86_ARCH1
        return cpus_mask, cpu_type, cpu_subtype

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def get_kernel_version(self):
        logger.debug("get_kernel_version()")
        kernel_version = self.kernel_version
        if "stext" not in kernel_version:
            logger.debug(">  stext")
            # return the known kernel load address to make LLDB do less requests
            kernel_version += "; stext=0x{:016x}".format(self.kernel_load_vaddr)
        return kernel_version

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def read_msr64(self, msr):
        logger.debug("read_msr64(msr=0x{:x})".format(msr))
        return self.stub.ReadMsr(msr, CpuId=self.stub.CPU0)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def write_msr64(self, msr, val):
        logger.debug("write_msr64(msr=0x{:x}, val=0x{:x})".format(msr, val))
        self.stub.WriteMsr(self, msr, val, CpuId=self.stub.CPU0)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def read_register(self, reg):
        logger.debug("read_register(reg='{}')".format(reg))
        val = getattr(self.stub, reg)
        if reg == "rip" and self._return_incremented_at_next_read_register_rip:
            logger.debug(">  _return_incremented_at_next_read_register_rip")
            self._return_incremented_at_next_read_register_rip = False
            # https://github.com/llvm/llvm-project/tree/llvmorg-8.0.0/lldb/source/Plugins/Process/MacOSX-Kernel/ThreadKDP.cpp#L157
            # https://github.com/llvm/llvm-project/tree/llvmorg-8.0.0/lldb/source/Plugins/Process/Utility/StopInfoMachException.cpp#L571
            return val + 1
        return val

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def read_registers(self, regs):
        logger.debug("read_registers()")
        return {reg: self.read_register(reg) for reg in regs}

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def write_register(self, reg, val):
        logger.debug("write_register(reg='{}', val=0x{:x})".format(reg, val))
        if reg == "rflags":
            if val & EFL_TF:
                logger.debug(">  _singlestep_at_next_resume")
                self._singlestep_at_next_resume = True
            # disallow changes to RFLAGS
            return
        setattr(self.stub, reg, val)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def write_registers(self, regs):
        logger.debug("write_registers()")
        for reg, val in regs.items():
            self.write_register(reg, val)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def read_virtual_memory(self, vaddr, nbytes):
        logger.debug(
            "read_virtual_memory(vaddr=0x{:016x}, nbytes=0x{:x})".format(vaddr, nbytes)
        )
        data = self.stub.ReadVirtualMemory(vaddr, nbytes)

        if not data and not _in_kernel_space(self.read_register("rip")):
            # if reading fails, it could be the case that we are trying to read kernel
            # virtual addresses from user space (e.g. when LLDB stops in user land and
            # the user loads or uses lldbmacros)
            # in this case, we try the read again but using the kernel pmap
            logger.debug(">  using kernel pmap")
            process_cr3 = self.read_register("cr3")
            # switch to kernel pmap
            self.write_register("cr3", self.kernel_cr3)
            # try the read again
            data = self.stub.ReadVirtualMemory(vaddr, nbytes)
            # switch back to the process pmap
            self.write_register("cr3", process_cr3)

        if self._kdp_vaddr and vaddr <= self._kdp_vaddr <= vaddr + nbytes:
            # this request has very likely been generated by LLDBmacros
            logger.debug(">  fake kdp struct")
            assert data is not None
            # fill some fields of the empty (since the boot-arg "debug" is probably not set) kdp struct
            saved_state = lldbagilityutils.p64(NULL)
            kdp_thread = lldbagilityutils.p64(self._get_active_thread_vaddr())
            fake_partial_kdp_struct = b"".join((saved_state, kdp_thread))
            kdp_struct_offset = self._kdp_vaddr - vaddr
            data = (
                data[:kdp_struct_offset]
                + fake_partial_kdp_struct
                + data[kdp_struct_offset + len(fake_partial_kdp_struct) :]
            )

        data = data if data else b""
        logger.debug(">  len(data): 0x{:x}".format(len(data)))
        return data

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def write_virtual_memory(self, vaddr, data):
        logger.debug("write_virtual_memory(vaddr=0x{:016x}, data=...)".format(vaddr))
        assert self.is_state_halted()
        if self._store_kdp_at_next_write_virtual_memory:
            logger.debug(">  _store_kdp_at_next_write_virtual_memory")
            self._store_kdp_at_next_write_virtual_memory = False
            self._kdp_vaddr = vaddr
            return
        return self.stub.WriteVirtualMemory(vaddr, data)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def set_soft_exec_breakpoint(self, vaddr):
        logger.debug("set_soft_exec_breakpoint(vaddr=0x{:016x})".format(vaddr))
        assert self.is_state_halted()
        id = 0x0
        length = 0x1
        self._soft_breakpoints[vaddr] = self.stub.SetBreakpoint(
            self.stub.SOFT_HBP,
            id,
            self.stub.EXECUTE_BP,
            self.stub.VIRTUAL_ADDRESS,
            vaddr,
            length,
            self.stub.NO_CR3,
        )
        logger.debug(">  bp id: {}".format(self._soft_breakpoints[vaddr]))
        return self._soft_breakpoints[vaddr]

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def unset_soft_breakpoint(self, vaddr):
        logger.debug("unset_soft_breakpoint(vaddr=0x{:016x})")
        assert self.is_state_halted()
        try:
            id = self._soft_breakpoints[vaddr]
        except KeyError:
            logger.debug(">  no such breakpoint")
        else:
            del self._soft_breakpoints[vaddr]
            return self.stub.UnsetBreakpoint(id)
        return False

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def set_hard_breakpoint(self, trigger, nreg, vaddr):
        logger.debug(
            "set_hard_exec_breakpoint(trigger='{}', nreg=0x{:016x}, vaddr=0x{:016x})".format(
                trigger, nreg, vaddr
            )
        )
        assert self.is_state_halted()
        assert trigger in ("e", "w", "rw")
        assert 0 <= nreg <= 3
        trigger_bitshifts = {nreg: 16 + nreg * 4 for nreg in range(4)}
        status_bitshifts = {nreg: nreg * 2 for nreg in range(4)}

        ctrl_mask = self.read_register("dr7")
        # reset trigger entry for the chosen register to 0b00
        ctrl_mask &= ~(0b11 << trigger_bitshifts[nreg])
        # set new entry
        if trigger == "e":
            trigger_entry = 0b00
        elif trigger == "w":
            trigger_entry = 0b01
        elif trigger == "rw":
            trigger_entry = 0b11
        else:
            raise NotImplementedError
        ctrl_mask |= trigger_entry << trigger_bitshifts[nreg]
        # enable breakpoint globally
        ctrl_mask |= 0b10 << status_bitshifts[nreg]
        logger.debug(">  ctrl_mask: 0b{:032b}".format(ctrl_mask))

        self.write_register("dr{}".format(nreg), vaddr)
        self.write_register("dr7", ctrl_mask)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def unset_hard_breakpoint(self, nreg):
        logger.debug("unset_hard_breakpoint(nreg=0x{:016x})".format(nreg))
        assert self.is_state_halted()
        assert 0 <= nreg <= 3
        status_bitshifts = {nreg: nreg * 2 for nreg in range(4)}

        ctrl_mask = self.read_register("dr7")
        # disable breakpoint globally and locally
        ctrl_mask &= ~(0b11 << status_bitshifts[nreg])
        logger.debug(">  ctrl_mask: 0b{:032b}".format(ctrl_mask))

        self.write_register("dr{}".format(nreg), 0x0)
        self.write_register("dr7", ctrl_mask)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def unset_all_breakpoints(self):
        logger.debug("unset_all_breakpoints()")
        assert self.is_state_halted()
        # remove soft breakpoints
        self._soft_breakpoints.clear()
        self.stub.UnsetAllBreakpoint()
        # remove hard breakpoints
        self.write_register("dr0", 0x0)
        self.write_register("dr1", 0x0)
        self.write_register("dr2", 0x0)
        self.write_register("dr3", 0x0)
        self.write_register("dr6", 0x0)
        self.write_register("dr7", 0x0)

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def halt(self):
        logger.debug("halt()")
        self.stub.Pause()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def interrupt(self):
        logger.debug("interrupt()")
        self._exception = (EXC_SOFTWARE, EXC_SOFT_SIGNAL, SIGINT)
        self.halt()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def single_step(self):
        logger.debug("single_step()")
        self._exception = (EXC_BREAKPOINT, EXC_I386_BPTFLT, 0x0)
        self.stub.SingleStep()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def resume(self):
        logger.debug("resume()")

        if self._interrupt_at_next_resume:
            logger.debug(">  _interrupt_at_next_resume")
            self._interrupt_at_next_resume = False
            self.interrupt()
            return

        if self._singlestep_at_next_resume:
            logger.debug(">  _singlestep_at_next_resume")
            self._singlestep_at_next_resume = False
            self.single_step()
            return

        if self.is_breakpoint_hit():
            logger.debug(
                ">  state breakpoint hit: 0x{:016x}".format(self.read_register("rip"))
            )
            self.stub.SingleStep()

        self.stub.Resume()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def interrupt_and_take_snapshot(self):
        logger.debug("interrupt_and_take_snapshot()")
        self.interrupt()
        self.stub.Save()

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def interrupt_and_restore_last_snapshot(self):
        logger.debug("interrupt_and_restore_last_snapshot()")
        self.interrupt()
        if self.stub.Restore():
            # breakpoints are not restored
            self._soft_breakpoints.clear()
            return True
        else:
            logger.debug(">  could not restore")
            return False

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def state(self):
        logger.debug("state()")
        if self.is_breakpoint_hit():
            logger.debug(">  state breakpoint hit")
            self._exception = (EXC_BREAKPOINT, EXC_I386_BPTFLT, 0x0)
            # the following assumes that the next call to STUBVM.read_register("rip")
            # will be made by LLDB in response to this EXC_BREAKPOINT exception
            self._return_incremented_at_next_read_register_rip = True
        state = (self.stub.GetState(), self._exception)
        self._exception = None
        return state

    @lldbagilityutils.synchronized
    def is_state_changed(self):
        return self.stub.GetStateChanged() or self._exception

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def is_state_halted(self):
        logger.debug("is_state_halted()")
        return self.stub.GetState() & self.stub.STATE_PAUSED

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def is_breakpoint_hit(self):
        logger.debug("is_breakpoint_hit()")
        return self.stub.GetState() & (
            self.stub.STATE_BREAKPOINT_HIT | self.stub.STATE_HARD_BREAKPOINT_HIT
        )

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def interrupt_at_next_resume(self):
        logger.debug("interrupt_at_next_resume()")
        self._interrupt_at_next_resume = True

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def store_kdp_at_next_write_virtual_memory(self):
        logger.debug("store_kdp_at_next_write_virtual_memory()")
        self._store_kdp_at_next_write_virtual_memory = True

    @lldbagilityutils.indented(logger)
    @lldbagilityutils.synchronized
    def abort_store_kdp_at_next_write_virtual_memory(self):
        logger.debug("abort_store_kdp_at_next_write_virtual_memory()")
        assert not self._kdp_vaddr
        self._store_kdp_at_next_write_virtual_memory = False


def _in_kernel_space(addr):
    return VM_MIN_KERNEL_ADDRESS <= addr <= VM_MAX_KERNEL_ADDRESS


@lldbagilityutils.indented(logger)
def _find_kernel_load_vaddr(vm):
    logger.debug("_find_kernel_load_vaddr()")
    assert _in_kernel_space(vm.read_register("rip"))

    @lldbagilityutils.indented(logger)
    def _is_kernel_load_vaddr(vaddr):
        logger.debug("_is_kernel_load_vaddr()")
        if not _in_kernel_space(vaddr):
            return False
        data = vm.read_virtual_memory(vaddr, 0x4)
        return data and lldbagilityutils.u32(data) == MH_MAGIC_64

    @lldbagilityutils.indented(logger)
    def _get_debug_kernel_load_vaddr():
        logger.debug("_get_debug_kernel_load_vaddr()")
        # from the LLDB documentation: "If the debug flag is included in the
        #   boot-args nvram setting, the kernel's load address will be noted
        #   in the lowglo page at a fixed address"
        # https://github.com/llvm/llvm-project/blob/llvmorg-8.0.0/lldb/source/Plugins/DynamicLoader/Darwin-Kernel/DynamicLoaderDarwinKernel.cpp#L226
        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/x86_64/lowglobals.h#L54
        # https://github.com/apple/darwin-xnu/blob/xnu-4903.221.2/osfmk/x86_64/pmap.c#L1175
        lgStext_vaddr = 0xFFFFFF8000002010
        data = vm.read_virtual_memory(lgStext_vaddr, 0x8)
        if data:
            vaddr = lldbagilityutils.u64(data)
            if _is_kernel_load_vaddr(vaddr):
                return vaddr
            else:
                # probably trying to attach to the target before lgStext is initialised
                return None
        else:
            return None

    @lldbagilityutils.indented(logger)
    def _search_kernel_load_vaddr(start_vaddr):
        logger.debug(
            "_search_kernel_load_vaddr(start_vaddr=0x{:016x})".format(start_vaddr)
        )
        # try to find the load address manually
        assert _in_kernel_space(start_vaddr)
        vaddr = start_vaddr & ~(I386_PGBYTES - 1)
        while vaddr >= VM_MIN_KERNEL_ADDRESS:
            if _is_kernel_load_vaddr(vaddr):
                return vaddr
            vaddr -= I386_PGBYTES
        else:
            raise AssertionError

    kernel_load_vaddr = _get_debug_kernel_load_vaddr() or _search_kernel_load_vaddr(
        vm.read_register("rip")
    )
    return kernel_load_vaddr


def _compute_kernel_slide(kernel_load_vaddr):
    return kernel_load_vaddr - 0xFFFFFF8000200000


@lldbagilityutils.indented(logger)
def _find_kernel_version(vm):
    logger.debug("_find_kernel_version()")

    kernel_macho = b""
    while len(kernel_macho) < 42 * 1024 * 1024:  # a reasonable upper bound?
        buf = b""
        while len(buf) < 2 * 1024 * 1024:
            vaddr = vm.kernel_load_vaddr + len(kernel_macho) + len(buf)
            buf += vm.read_virtual_memory(vaddr, I386_PGBYTES)
        kernel_macho += buf
        try:
            kernel_version = re.search(b"(?P<version>Darwin Kernel Version .+?X86_64)\0", kernel_macho).group("version").decode("ascii")
        except AttributeError:
            continue
        else:
            return kernel_version
    else:
        raise AssertionError


class FDPSTUB(FDP):
    NO_CR3 = FDP.FDP_NO_CR3

    SOFT_HBP = FDP.FDP_SOFTHBP
    CR_HBP = FDP.FDP_CRHBP

    VIRTUAL_ADDRESS = FDP.FDP_VIRTUAL_ADDRESS

    EXECUTE_BP = FDP.FDP_EXECUTE_BP
    WRITE_BP = FDP.FDP_WRITE_BP

    STATE_PAUSED = FDP.FDP_STATE_PAUSED
    STATE_BREAKPOINT_HIT = FDP.FDP_STATE_BREAKPOINT_HIT
    STATE_HARD_BREAKPOINT_HIT = FDP.FDP_STATE_HARD_BREAKPOINT_HIT

    CPU0 = FDP.FDP_CPU0

    def __init__(self, name):
        super(FDPSTUB, self).__init__(name)
        assert self.GetCpuCount() == 1, (
            "VMs with more than one CPU are not fully supported by FDP! "
            "Decrease the number of processors in the VM settings"
        )


class VMSNSTUB(VMSN):
    NO_CR3 = 0

    SOFT_HBP = 2
    CR_HBP = 0

    VIRTUAL_ADDRESS = 0

    EXECUTE_BP = 0
    WRITE_BP = 0

    STATE_PAUSED = 1
    STATE_BREAKPOINT_HIT = 1
    STATE_HARD_BREAKPOINT_HIT = 0

    CPU0 = FDP.FDP_CPU0

    def __init__(self, name):
        super(VMSNSTUB, self).__init__(name)
