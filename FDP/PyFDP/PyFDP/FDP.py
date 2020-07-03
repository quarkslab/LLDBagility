import re
from ctypes import *

import PyFDP


class FDP(object):
    """ Fast Debug Protocol client object.

    Send requests to a FDP server located in an instrumented VirtualBox implementation.
    """

    FDP_MAX_BREAKPOINT_ID = 254

    FDP_NO_CR3 = 0x0

    FDP_CPU0 = 0x0

    # FDP_BreakpointType
    FDP_SOFTHBP = 0x1
    FDP_HARDHBP = 0x2
    FDP_PAGEHBP = 0x3
    FDP_MSRHBP = 0x4
    FDP_CRHBP = 0x5

    # FDP_AddressType
    FDP_VIRTUAL_ADDRESS = 0x1
    FDP_PHYSICAL_ADDRESS = 0x2

    # FDP_Access
    FDP_EXECUTE_BP = 0x1
    FDP_WRITE_BP = 0x2
    FDP_READ_BP = 0x4
    FDP_INSTRUCTION_FETCH_BP = 0x8

    # FDP_State
    FDP_STATE_PAUSED = 0x1
    FDP_STATE_BREAKPOINT_HIT = 0x2
    FDP_STATE_DEBUGGER_ALERTED = 0x4
    FDP_STATE_HARD_BREAKPOINT_HIT = 0x8

    # FDP_Register
    # x86-64
    FDP_RAX_REGISTER = 0x0
    FDP_RBX_REGISTER = 0x1
    FDP_RCX_REGISTER = 0x2
    FDP_RDX_REGISTER = 0x3
    FDP_R8_REGISTER = 0x4
    FDP_R9_REGISTER = 0x5
    FDP_R10_REGISTER = 0x6
    FDP_R11_REGISTER = 0x7
    FDP_R12_REGISTER = 0x8
    FDP_R13_REGISTER = 0x9
    FDP_R14_REGISTER = 0xA
    FDP_R15_REGISTER = 0xB
    FDP_RSP_REGISTER = 0xC
    FDP_RBP_REGISTER = 0xD
    FDP_RSI_REGISTER = 0xE
    FDP_RDI_REGISTER = 0xF
    FDP_RIP_REGISTER = 0x10
    FDP_DR0_REGISTER = 0x11
    FDP_DR1_REGISTER = 0x12
    FDP_DR2_REGISTER = 0x13
    FDP_DR3_REGISTER = 0x14
    FDP_DR6_REGISTER = 0x15
    FDP_DR7_REGISTER = 0x16
    FDP_VDR0_REGISTER = 0x17
    FDP_VDR1_REGISTER = 0x18
    FDP_VDR2_REGISTER = 0x19
    FDP_VDR3_REGISTER = 0x1A
    FDP_VDR6_REGISTER = 0x1B
    FDP_VDR7_REGISTER = 0x1C
    FDP_CS_REGISTER = 0x1D
    FDP_DS_REGISTER = 0x1E
    FDP_ES_REGISTER = 0x1F
    FDP_FS_REGISTER = 0x20
    FDP_GS_REGISTER = 0x21
    FDP_SS_REGISTER = 0x22
    FDP_RFLAGS_REGISTER = 0x23
    FDP_MXCSR_REGISTER = 0x24
    FDP_GDTRB_REGISTER = 0x25
    FDP_GDTRL_REGISTER = 0x26
    FDP_IDTRB_REGISTER = 0x27
    FDP_IDTRL_REGISTER = 0x28
    FDP_CR0_REGISTER = 0x29
    FDP_CR2_REGISTER = 0x2A
    FDP_CR3_REGISTER = 0x2B
    FDP_CR4_REGISTER = 0x2C
    FDP_CR8_REGISTER = 0x2D
    FDP_LDTR_REGISTER = 0x2E
    FDP_LDTRB_REGISTER = 0x2F
    FDP_LDTRL_REGISTER = 0x30
    FDP_TR_REGISTER = 0x31
    # AArch64
    FDP_X0_REGISTER = 0x100
    FDP_X1_REGISTER = 0x101
    FDP_X2_REGISTER = 0x102
    FDP_X3_REGISTER = 0x103
    FDP_X4_REGISTER = 0x104
    FDP_X5_REGISTER = 0x105
    FDP_X6_REGISTER = 0x106
    FDP_X7_REGISTER = 0x107
    FDP_X8_REGISTER = 0x108
    FDP_X9_REGISTER = 0x109
    FDP_X10_REGISTER = 0x10A
    FDP_X11_REGISTER = 0x10B
    FDP_X12_REGISTER = 0x10C
    FDP_X13_REGISTER = 0x10D
    FDP_X14_REGISTER = 0x10E
    FDP_X15_REGISTER = 0x10F
    FDP_X16_REGISTER = 0x110
    FDP_X17_REGISTER = 0x111
    FDP_X18_REGISTER = 0x112
    FDP_X19_REGISTER = 0x113
    FDP_X20_REGISTER = 0x114
    FDP_X21_REGISTER = 0x115
    FDP_X22_REGISTER = 0x116
    FDP_X23_REGISTER = 0x117
    FDP_X24_REGISTER = 0x118
    FDP_X25_REGISTER = 0x119
    FDP_X26_REGISTER = 0x11A
    FDP_X27_REGISTER = 0x11B
    FDP_X28_REGISTER = 0x11C
    FDP_X29_REGISTER = 0x11D
    FDP_LR_REGISTER = 0x11E
    FDP_SP_REGISTER = 0x11F
    FDP_PC_REGISTER = 0x120

    def __init__(self, name):
        FDP_Register = c_uint32
        FDP_BreakpointType = c_uint16
        FDP_Access = c_uint16
        FDP_AddressType = c_uint16
        FDP_State = c_uint8

        self._fdpdll = PyFDP.FDP_DLL_HANDLE
        self._fdpdll.FDP_CreateSHM.restype = c_void_p
        self._fdpdll.FDP_CreateSHM.argtypes = [c_char_p]
        self._fdpdll.FDP_OpenSHM.restype = c_void_p
        self._fdpdll.FDP_OpenSHM.argtypes = [c_char_p]
        self._fdpdll.FDP_Init.restype = c_bool
        self._fdpdll.FDP_Init.argtypes = [c_void_p]
        self._fdpdll.FDP_Pause.restype = c_bool
        self._fdpdll.FDP_Pause.argtypes = [c_void_p]
        self._fdpdll.FDP_Resume.restype = c_bool
        self._fdpdll.FDP_Resume.argtypes = [c_void_p]
        self._fdpdll.FDP_ReadPhysicalMemory.restype = c_bool
        self._fdpdll.FDP_ReadPhysicalMemory.argtypes = [c_void_p, POINTER(c_uint8), c_uint32, c_uint64]
        self._fdpdll.FDP_WritePhysicalMemory.restype = c_bool
        self._fdpdll.FDP_WritePhysicalMemory.argtypes = [c_void_p, POINTER(c_uint8), c_uint32, c_uint64]
        self._fdpdll.FDP_ReadVirtualMemory.restype = c_bool
        self._fdpdll.FDP_ReadVirtualMemory.argtypes = [c_void_p, c_uint32, POINTER(c_uint8), c_uint32, c_uint64]
        self._fdpdll.FDP_WriteVirtualMemory.restype = c_bool
        self._fdpdll.FDP_WriteVirtualMemory.argtypes = [c_void_p, c_uint32, POINTER(c_uint8), c_uint32, c_uint64]
        self._fdpdll.FDP_SearchPhysicalMemory.restype = c_uint64
        self._fdpdll.FDP_SearchPhysicalMemory.argtypes = [c_void_p, c_void_p, c_uint32, c_uint64]
        self._fdpdll.FDP_SearchVirtualMemory.restype = c_bool
        self._fdpdll.FDP_SearchVirtualMemory.argtypes = [c_void_p, c_uint32, c_void_p, c_uint32, c_uint64]
        self._fdpdll.FDP_ReadRegister.restype = c_bool
        self._fdpdll.FDP_ReadRegister.argtypes = [c_void_p, c_uint32, FDP_Register, POINTER(c_uint64)]
        self._fdpdll.FDP_WriteRegister.restype = c_bool
        self._fdpdll.FDP_WriteRegister.argtypes = [c_void_p, c_uint32, FDP_Register, c_uint64]
        self._fdpdll.FDP_ReadMsr.restype = c_bool
        self._fdpdll.FDP_ReadMsr.argtypes = [c_void_p, c_uint32, c_uint64, POINTER(c_uint64)]
        self._fdpdll.FDP_WriteMsr.restype = c_bool
        self._fdpdll.FDP_WriteMsr.argtypes = [c_void_p, c_uint32, c_uint64, c_uint64]
        self._fdpdll.FDP_SetBreakpoint.restype = c_int
        self._fdpdll.FDP_SetBreakpoint.argtypes = [
            c_void_p,
            c_uint32,
            FDP_BreakpointType,
            c_uint8,
            FDP_Access,
            FDP_AddressType,
            c_uint64,
            c_uint64,
            c_uint64,
        ]
        self._fdpdll.FDP_UnsetBreakpoint.restype = c_bool
        self._fdpdll.FDP_UnsetBreakpoint.argtypes = [c_void_p, c_uint8]
        self._fdpdll.FDP_VirtualToPhysical.restype = c_bool
        self._fdpdll.FDP_VirtualToPhysical.argtypes = [c_void_p, c_uint32, c_uint64, POINTER(c_uint64)]
        self._fdpdll.FDP_GetState.restype = c_bool
        self._fdpdll.FDP_GetState.argtypes = [c_void_p, POINTER(FDP_State)]
        self._fdpdll.FDP_GetFxState64.restype = c_bool
        self._fdpdll.FDP_GetFxState64.argtypes = [c_void_p, c_uint32, c_void_p]
        self._fdpdll.FDP_SetFxState64.restype = c_bool
        self._fdpdll.FDP_SetFxState64.argtypes = [c_void_p, c_uint32, c_void_p]
        self._fdpdll.FDP_SingleStep.restype = c_bool
        self._fdpdll.FDP_SingleStep.argtypes = [c_void_p, c_uint32]
        self._fdpdll.FDP_GetPhysicalMemorySize.restype = c_bool
        self._fdpdll.FDP_GetPhysicalMemorySize.argtypes = [c_void_p, POINTER(c_uint64)]
        self._fdpdll.FDP_GetCpuCount.restype = c_bool
        self._fdpdll.FDP_GetCpuCount.argtypes = [c_void_p, POINTER(c_uint32)]
        self._fdpdll.FDP_GetCpuState.restype = c_bool
        self._fdpdll.FDP_GetCpuState.argtypes = [c_void_p, c_uint32, POINTER(FDP_State)]
        self._fdpdll.FDP_Reboot.restype = c_bool
        self._fdpdll.FDP_Reboot.argtypes = [c_void_p]
        self._fdpdll.FDP_Save.restype = c_bool
        self._fdpdll.FDP_Save.argtypes = [c_void_p]
        self._fdpdll.FDP_Restore.restype = c_bool
        self._fdpdll.FDP_Restore.argtypes = [c_void_p]
        self._fdpdll.FDP_GetStateChanged.restype = c_bool
        self._fdpdll.FDP_GetStateChanged.argtypes = [c_void_p]
        self._fdpdll.FDP_SetStateChanged.restype = c_void_p
        self._fdpdll.FDP_SetStateChanged.argtypes = [c_void_p]
        self._fdpdll.FDP_InjectInterrupt.restype = c_bool
        self._fdpdll.FDP_InjectInterrupt.argtypes = [c_void_p, c_uint32, c_uint32, c_uint32, c_uint64]

        pName = cast(pointer(create_string_buffer(name.encode("ascii"))), c_char_p)
        self._pFDP = self._fdpdll.FDP_OpenSHM(pName)
        if self._pFDP == 0 or self._pFDP is None:
            raise Exception("PyFDP: Cannot open shared memory '{}'".format(name))

        self._fdpdll.FDP_Init(self._pFDP)

        # Create registers attributes
        for varname in dir(self):
            match = re.match(r"FDP_(.+?)_REGISTER", varname)
            if match:
                regname = match.group(1).lower()
                regid = getattr(self, varname)

                def pproperty(regid):
                    def read(self):
                        return self.ReadRegister(regid)

                    def write(self, value):
                        self.WriteRegister(regid, value)

                    return property(read, write)

                setattr(FDP, regname, pproperty(regid))

    def __fix_names__(self, name):
        regx = re.compile(r"FDP_(.*)_REGISTER")
        return re.findall(regx, name)[0].lower()

    def ReadRegister(self, RegisterId, CpuId=FDP_CPU0):
        """ Return the value stored in the specified register
        RegisterId must be a member of FDP.FDP_REGISTER
        """
        pRegisterValue = pointer(c_uint64(0))
        if self._fdpdll.FDP_ReadRegister(self._pFDP, CpuId, RegisterId, pRegisterValue) == True:
            return pRegisterValue[0]
        return None

    def WriteRegister(self, RegisterId, RegisterValue, CpuId=FDP_CPU0):
        """ Store the given value into the specified register
        RegisterId must be a member of FDP.FDP_REGISTER
        """
        return self._fdpdll.FDP_WriteRegister(self._pFDP, CpuId, RegisterId, c_uint64(RegisterValue))

    def ReadMsr(self, MsrId, CpuId=FDP_CPU0):
        """ Return the value stored in the Model-specific register (MSR) indexed by MsrId
        MSR typically don't have an enum Id since there are vendor specific.
        """
        pMsrValue = pointer(c_uint64(0))
        if self._fdpdll.FDP_ReadMsr(self._pFDP, CpuId, c_uint64(MsrId), pMsrValue) == True:
            return pMsrValue[0]
        return None

    def WriteMsr(self, MsrId, MsrValue, CpuId=FDP_CPU0):
        """ Store the value into the Model-specific register (MSR) indexed by MsrId
        MSR typically don't have an enum Id since there are vendor specific.
        """
        return self._fdpdll.FDP_WriteMsr(self._pFDP, CpuId, c_uint64(MsrId), c_uint64(MsrValue))

    def Pause(self):
        """ Suspend the target virtual machine """
        return self._fdpdll.FDP_Pause(self._pFDP)

    def Resume(self):
        """ Resume the target virtual machine execution """
        return self._fdpdll.FDP_Resume(self._pFDP)

    def Save(self):
        """Save the virtual machine state (CPU+memory).
        Only one save state allowed.
        """
        return self._fdpdll.FDP_Save(self._pFDP)

    def Restore(self):
        """ Restore the previously stored virtual machine state (CPU+memory). """
        return self._fdpdll.FDP_Restore(self._pFDP)

    def Reboot(self):
        """ Reboot the target virtual machine """
        return self._fdpdll.FDP_Reboot(self._pFDP)

    def SingleStep(self, CpuId=FDP_CPU0):
        """ Single step a paused execution """
        return self._fdpdll.FDP_SingleStep(self._pFDP, CpuId)

    def VirtualToPhysical(self, VirtualAddress, CpuId=FDP_CPU0):
        """ Convert a virtual address to the corresponding physical address """
        pPhysicalAddress = pointer(c_uint64(0))
        if self._fdpdll.FDP_VirtualToPhysical(self._pFDP, CpuId, c_uint64(VirtualAddress), pPhysicalAddress) == True:
            return pPhysicalAddress[0]
        return None

    def ReadVirtualMemory(self, VirtualAddress, ReadSize, CpuId=FDP_CPU0):
        """ Attempt to read a VM virtual memory buffer.
        Check CR3 to know which process's memory your're reading
        """
        try:
            Buffer = create_string_buffer(int(ReadSize))
        except (OverflowError):
            return None

        pBuffer = cast(pointer(Buffer), POINTER(c_uint8))
        if self._fdpdll.FDP_ReadVirtualMemory(self._pFDP, CpuId, pBuffer, ReadSize, c_uint64(VirtualAddress)) == True:
            return Buffer.raw
        return None

    def ReadPhysicalMemory(self, PhysicalAddress, ReadSize):
        """ Attempt to read a VM physical memory buffer. """
        Buffer = create_string_buffer(int(ReadSize))
        pBuffer = cast(pointer(Buffer), POINTER(c_uint8))
        if self._fdpdll.FDP_ReadPhysicalMemory(self._pFDP, pBuffer, ReadSize, c_uint64(PhysicalAddress)) == True:
            return Buffer.raw
        return None

    def WritePhysicalMemory(self, PhysicalAddress, WriteBuffer):
        """ Attempt to write a buffer at a VM physical memory address. """
        Buffer = create_string_buffer(WriteBuffer)
        pBuffer = cast(pointer(Buffer), POINTER(c_uint8))
        return self._fdpdll.FDP_WritePhysicalMemory(
            self._pFDP, pBuffer, len(WriteBuffer), c_uint64(PhysicalAddress)
        )

    def WriteVirtualMemory(self, VirtualAddress, WriteBuffer, CpuId=FDP_CPU0):
        """ Attempt to write a buffer at a VM virtual memory address.
        Check CR3 to know which process's memory your're writing into.
        """
        Buffer = create_string_buffer(WriteBuffer)
        pBuffer = cast(pointer(Buffer), POINTER(c_uint8))
        return self._fdpdll.FDP_WriteVirtualMemory(
            self._pFDP, CpuId, pBuffer, len(WriteBuffer), c_uint64(VirtualAddress)
        )

    def SetBreakpoint(
        self,
        BreakpointType,
        BreakpointId,
        BreakpointAccessType,
        BreakpointAddressType,
        BreakpointAddress,
        BreakpointLength,
        BreakpointCr3,
        CpuId=FDP_CPU0,
    ):
        """ Place a breakpoint.

        * BreakpointType :
            - FDP.FDP_SOFTHBP : "soft" hyperbreakpoint, backed by a shadow "0xcc" isntruction in the VM physical memory page.
            - FDP.FDP_HARDHBP : "hard" hyperbreakpoint, backed by a shadow debug register (only 4)
            - FDP.FDP_PAGEHBP : "page" hyperbreakpoint relying on Extended Page Table (EPT) page guard faults.
            - FDP.FDP_MSRHBP  : "msr" hyperbreakpoint, specifically to read a VM's MSR
            - FDP.FDP_CRHBP  : "cr" hyperbreakpoint, specifically to read a VM's Context Register

        * BreakpointId: Currently unused

        * BreakpointAccessType:
            - FDP.FDP_EXECUTE_BP : break on execution
            - FDP.FDP_WRITE_BP : break on write
            - FDP.FDP_READ_BP : break on read
            - FDP.FDP_INSTRUCTION_FETCH_BP : break when fetching instructions before executing

        * BreakpointAddressType:
            - FDP.FDP_VIRTUAL_ADDRESS : VM's virtual addressing
            - FDP.FDP_PHYSICAL_ADDRESS  : VM's physical addressing

        * BreakpointAddress: address (virtual or physical) to break execution

        * BreakpointLength: Length of the data pointed by BreakpointAddress which trigger the breakpoint (think "ba e 8" style of breakpoint)

        * BreakpointCr3: Filter breakpoint on a specific CR3 value. Mandatory if you want to break on a particular process.
        """

        BreakpointId = self._fdpdll.FDP_SetBreakpoint(
            self._pFDP,
            c_uint32(CpuId),
            c_uint16(BreakpointType),
            c_uint8(BreakpointId),
            c_uint16(BreakpointAccessType),
            c_uint16(BreakpointAddressType),
            c_uint64(BreakpointAddress),
            c_uint64(BreakpointLength),
            c_uint64(BreakpointCr3),
        )
        if BreakpointId >= 0:
            return BreakpointId
        return None

    def UnsetBreakpoint(self, BreakpointId):
        """ Remove the selected breakoint. Return True on success """
        return self._fdpdll.FDP_UnsetBreakpoint(self._pFDP, c_uint8(BreakpointId))

    def GetState(self):
        """ Return the bitfield state of an system execution break (all CPUs considered):

        - FDP.FDP_STATE_PAUSED : the VM is paused.
        - FDP.FDP_STATE_BREAKPOINT_HIT : the execution has hit a soft or page breakpoint
        - FDP.FDP_STATE_DEBUGGER_ALERTED : the VM is in a debuggable state
        - FDP.FDP_STATE_HARD_BREAKPOINT_HIT : the execution has hit a hard breakpoint
        """
        pState = pointer(c_uint8(0))
        if self._fdpdll.FDP_GetState(self._pFDP, pState) == True:
            return pState[0]
        return None

    def GetCpuState(self, CpuId=FDP_CPU0):
        """ Return the bitfield state of an execution break for the sprecified CpuId:

        - FDP.FDP_STATE_PAUSED : the VM is paused.
        - FDP.FDP_STATE_BREAKPOINT_HIT : the execution has hit a soft or page breakpoint
        - FDP.FDP_STATE_DEBUGGER_ALERTED : the VM is in a debuggable state
        - FDP.FDP_STATE_HARD_BREAKPOINT_HIT : the execution has hit a hard breakpoint
        """
        pState = pointer(c_uint8(0))
        if self._fdpdll.FDP_GetCpuState(self._pFDP, CpuId, pState) == True:
            return pState[0]
        return None

    def GetPhysicalMemorySize(self):
        """ return the target VM physical memory size, or None on failure """
        pPhysicalMemorySize = pointer(c_uint64(0))
        if self._fdpdll.FDP_GetPhysicalMemorySize(self._pFDP, pPhysicalMemorySize) == True:
            return pPhysicalMemorySize[0]
        return None

    def GetCpuCount(self):
        """ return the target VM CPU count, or None on failure """
        pCpuCount = pointer(c_uint32(0))
        if self._fdpdll.FDP_GetCpuCount(self._pFDP, pCpuCount) == True:
            return pCpuCount[0]
        return None

    def GetStateChanged(self):
        """ check if the VM execution state has changed. Useful on resume."""
        return self._fdpdll.FDP_GetStateChanged(self._pFDP)

    def WaitForStateChanged(self):
        """ wait for the VM execution state has change. Useful on when waiting for a breakpoint to hit."""
        pState = pointer(c_uint8(0))
        if self._fdpdll.FDP_WaitForStateChanged(self._pFDP, pState) == True:
            return pState[0]
        return None

    def InjectInterrupt(self, InterruptionCode, ErrorCode, Cr2Value, CpuId=FDP_CPU0):
        """ Inject an interruption in the VM execution state.

        * InterruptionCode (int) : interrupt code (e.g. 0x0E for a #PF)
        * ErrorCode : the error code for the interruption (e.g. 0x02 for a Write error on a #PF)
        * Cr2Value : typically the address associated with the interruption
        """
        return self._fdpdll.FDP_InjectInterrupt(self._pFDP, CpuId, InterruptionCode, ErrorCode, c_uint64(Cr2Value))

    def UnsetAllBreakpoint(self):
        """ Remove every set breakpionts """
        for i in range(FDP.FDP_MAX_BREAKPOINT_ID + 1):
            self.UnsetBreakpoint(i)
        return True

    def WaitForStateChanged(self):
        """ wait for the VM state to change """
        while True:
            if self.GetStateChanged() == True:
                return self.GetState()
        return 0

    def DumpPhysicalMemory(self, FilePath):
        """ Write the whole VM physicai memory to the host disk. Useful for Volatility-like tools."""
        _4K = 4096
        PhysicalMemorySize = self.GetPhysicalMemorySize()

        with open(FilePath, "wb") as dumped_memory_file:
            for physical_page in range(0, PhysicalMemorySize, _4K):
                PageContent = self.ReadPhysicalMemory(physical_page, _4K)
                if PageContent == None:
                    PageContent = b"?" * _4K

                dumped_memory_file.write(PageContent)
