#!/usr/bin/env python
import mmap
import os
import struct

# WARNING !!! TODO !!! This is a crappy PoC !


class PMEM(str):
    def __init__(self, name):
        self.f_info = open("/dev/pmem_info", "r")
        self.f = open("/dev/pmem", "rb")
        self.rax = 0xDEADDEADDEADDEAD
        self.rbx = 0xDEADDEADDEADDEAD
        self.rcx = 0xDEADDEADDEADDEAD
        self.rdx = 0xDEADDEADDEADDEAD
        self.rdi = 0xDEADDEADDEADDEAD
        self.rsi = 0xDEADDEADDEADDEAD
        self.rsp = 0xDEADDEADDEADDEAD
        self.rbp = 0xDEADDEADDEADDEAD
        self.r8 = 0xDEADDEADDEADDEAD
        self.r9 = 0xDEADDEADDEADDEAD
        self.r10 = 0xDEADDEADDEADDEAD
        self.r11 = 0xDEADDEADDEADDEAD
        self.r12 = 0xDEADDEADDEADDEAD
        self.r13 = 0xDEADDEADDEADDEAD
        self.r14 = 0xDEADDEADDEADDEAD
        self.r15 = 0xDEADDEADDEADDEAD
        self.rip = 0xDEADDEADDEADDEAD
        self.cs = 0x0
        self.fs = 0x0
        self.gs = 0x0
        self.cr3 = 0xDEADDEADDEADDEAD
        data = self.f_info.readlines()
        for l in data:
            if "cr3:" in l:
                self.cr3 = int(l.split(": ")[1])
            if "kaslr_slide:" in l:
                self.rip = 0xFFFFFF8000200000 + int(l.split(": ")[1])
            if "phys_mem_size:" in l:
                self.mem_size = int(l.split(": ")[1])
        self.rflags = 0x0000000000010246

    def GetCpuCount(self):
        return 1

    def Pause(self):
        return True

    def UnsetAllBreakpoint(self):
        return True

    def SetBreakpoint(self, a0, a1, a2, a3, a4, a5, a6):
        return 0

    def ReadyPhysicalMemory(self, address, size):
        self.f.seek(address, 0)
        return self.f.read(size)

    def ReadPhysical64(self, address):
        return struct.unpack("Q", self.ReadyPhysicalMemory(address, 8))[0]

    def V2P(self, address):
        _4K = 4 * 1024
        _2M = 2 * 1024 * 1024
        PML4E_index = (address & 0x0000FF8000000000) >> (9 + 9 + 9 + 12)
        PDPE_index = (address & 0x0000007FC0000000) >> (9 + 9 + 12)
        PDE_index = (address & 0x000000003FE00000) >> (9 + 12)
        PTE_index = (address & 0x00000000001FF000) >> (12)
        P_offset = address & 0x0000000000000FFF
        CR3 = self.cr3 & 0xFFFFFFFFFFFFF000

        PDPE_base = self.ReadPhysical64(CR3 + (PML4E_index * 8)) & 0x0000FFFFFFFFF000
        if (PDPE_base == 0) or (PDPE_base > (self.mem_size - _4K)):
            return None
        tmp = self.ReadPhysical64(PDPE_base + (PDPE_index * 8))
        if tmp & 0x80:  # This page is a huge one (1G) !
            print("TODO !!  HUGE !!!")
            return None
        PDE_base = tmp & 0x0000FFFFFFFFF000
        if (PDE_base == 0) or (PDE_base > (self.mem_size - _4K)):
            return None
        tmp = self.ReadPhysical64(PDE_base + (PDE_index * 8))
        if (tmp & 0x1) == 0:
            return None
        if tmp & 0x80:  # This page is a large one (2M) !
            tmpPhysical = (tmp & 0xFFFFFFFE00000) | (address & 0x00000000001FFFFF)
            if (tmpPhysical == 0) or (tmpPhysical > (self.mem_size - _2M)):
                return None
            return (_2M, tmpPhysical)
        PTE_base = tmp & 0x0000FFFFFFFFF000
        if (PTE_base == 0) or (PTE_base > (self.mem_size - _4K)):
            return None
        tmp = self.ReadPhysical64(PTE_base + (PTE_index * 8))
        if (tmp & 0x1) == 0:
            return None
        P_base = tmp & 0x0000FFFFFFFFF000
        if (P_base == 0) or (P_base > (self.mem_size - _4K)):
            return None
        return (_4K, (P_base | P_offset))

    def ReadVirtualMemory(self, address, size):
        data = ""
        left_to_read = size
        while left_to_read > 0:
            ret = self.V2P(address)
            if ret == None:
                return None
            (page_size, physical_address) = ret
            page_base = physical_address & ~(page_size - 1)
            page_end = page_base + page_size
            left_on_page = page_end - physical_address
            byte_to_read = min(left_on_page, left_to_read)
            tmp_data = self.ReadyPhysicalMemory(physical_address, byte_to_read)
            if tmp_data == None:
                return None
            data += tmp_data
            left_to_read = left_to_read - byte_to_read
        return data

    def GetStateChanged(self):
        return False

    def GetState(self):
        return self.STATE_PAUSED

    def SingleStep(self):
        return True

    def Resume(self):
        return True

    def UnsetBreakpoint(self, a0):
        return True
