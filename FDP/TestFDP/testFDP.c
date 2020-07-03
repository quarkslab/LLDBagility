/*
    MIT License

    Copyright (c) 2015 Nicolas Couffin ncouffin@gmail.com

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
*/
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "FDP.h"

#define MSR_EFER           0xC0000080
#define MSR_STAR           0xC0000081
#define MSR_LSTAR          0xC0000082
#define MSR_CSTAR          0xC0000084
#define MSR_SYSCALL_MASK   0xC0000084
#define MSR_GS_BASE        0xC0000101
#define MSR_KERNEL_GS_BASE 0xC0000102

#define _4K 4 * 1024
#define _1M 1 * 1024 * 1024
#define _2M 2 * 1024 * 1024
#define _1G 1 * 1024 * 1024 * 1024

#define FDP_RESUME(...)                                                                                                \
    {                                                                                                                  \
        if (FDP_Resume(__VA_ARGS__) == false)                                                                          \
        {                                                                                                              \
            printf("Failed to resume ! (#L%d)\n", __LINE__);                                                           \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_SINGLESTEP(...)                                                                                            \
    {                                                                                                                  \
        if (FDP_SingleStep(__VA_ARGS__) == false)                                                                      \
        {                                                                                                              \
            printf("Failed to single step ! (#L%d)\n", __LINE__);                                                      \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_PAUSE(...)                                                                                                 \
    {                                                                                                                  \
        if (FDP_Pause(__VA_ARGS__) == false)                                                                           \
        {                                                                                                              \
            printf("Failed to pause ! (#L%d)\n", __LINE__);                                                            \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_GETSTATE(...)                                                                                              \
    {                                                                                                                  \
        if (FDP_GetState(__VA_ARGS__) == false)                                                                        \
        {                                                                                                              \
            printf("Failed to get state ! (#L%d)\n", __LINE__);                                                        \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_READREGISTER(...)                                                                                          \
    {                                                                                                                  \
        if (FDP_ReadRegister(__VA_ARGS__) == false)                                                                    \
        {                                                                                                              \
            printf("Failed to read register ! (#L%d)\n", __LINE__);                                                    \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_WRITEREGISTER(...)                                                                                         \
    {                                                                                                                  \
        if (FDP_WriteRegister(__VA_ARGS__) == false)                                                                   \
        {                                                                                                              \
            printf("Failed to write register ! (#L%d)\n", __LINE__);                                                   \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_READMSR(...)                                                                                               \
    {                                                                                                                  \
        if (FDP_ReadMsr(__VA_ARGS__) == false)                                                                         \
        {                                                                                                              \
            printf("Failed to read MSR ! (#L%d)\n", __LINE__);                                                         \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_WRITEMSR(...)                                                                                              \
    {                                                                                                                  \
        if (FDP_WriteMsr(__VA_ARGS__) == false)                                                                        \
        {                                                                                                              \
            printf("Failed to write MSR ! (#L%d)\n", __LINE__);                                                        \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_READVIRTUALMEMORY(...)                                                                                     \
    {                                                                                                                  \
        if (FDP_ReadVirtualMemory(__VA_ARGS__) == false)                                                               \
        {                                                                                                              \
            printf("Failed to read virtual memory ! (#L%d)\n", __LINE__);                                              \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_WRITEVIRTUALMEMORY(...)                                                                                    \
    {                                                                                                                  \
        if (FDP_WriteVirtualMemory(__VA_ARGS__) == false)                                                              \
        {                                                                                                              \
            printf("Failed to write virtual memory ! (#L%d)\n", __LINE__);                                             \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_READPHYSICALMEMORY(...)                                                                                    \
    {                                                                                                                  \
        if (FDP_ReadPhysicalMemory(__VA_ARGS__) == false)                                                              \
        {                                                                                                              \
            printf("Failed to read physical memory ! (#L%d)\n", __LINE__);                                             \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_WRITEPHYSICALMEMORY(...)                                                                                   \
    {                                                                                                                  \
        if (FDP_WritePhysicalMemory(__VA_ARGS__) == false)                                                             \
        {                                                                                                              \
            printf("Failed to write physical memory ! (#L%d)\n", __LINE__);                                            \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_VIRTUALTOPHYSICAL(...)                                                                                     \
    {                                                                                                                  \
        if (FDP_VirtualToPhysical(__VA_ARGS__) == false)                                                               \
        {                                                                                                              \
            printf("Failed to virtual to physical ! (#L%d)\n", __LINE__);                                              \
            return false;                                                                                              \
        }                                                                                                              \
    }

#define FDP_UNSETBREAKPOINT(...)                                                                                       \
    {                                                                                                                  \
        if (FDP_UnsetBreakpoint(__VA_ARGS__) == false)                                                                 \
        {                                                                                                              \
            printf("Failed to unset breakpoint ! (#L%d)\n", __LINE__);                                                 \
            return false;                                                                                              \
        }                                                                                                              \
    }

int  iTimerDelay = 2;
bool TimerGo = false;
bool TimerOut = false;

void TimerSetDelay(int iNewTimerDelay)
{
    iTimerDelay = iNewTimerDelay;
}

int TimerGetDelay()
{
    return iTimerDelay;
}

void* TimerRoutine(LPVOID lpParam)
{
    while (true)
    {
        while (TimerGo == false)
            usleep(1000 * 10);
        TimerGo = false;
        usleep(1000 * iTimerDelay * 1000);
        TimerOut = true;
    }
}

bool testReadWriteMSR(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t originalMSRValue;
    uint64_t modMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    uint64_t TEST_MSR_VALUE = 0xFFFFFFFFFFFFFFFF;
    FDP_WRITEMSR(pFDP, 0, MSR_LSTAR, TEST_MSR_VALUE)

    FDP_READMSR(pFDP, 0, MSR_LSTAR, &modMSRValue)
    if (modMSRValue != TEST_MSR_VALUE)
    {
        printf("MSR doesn't match %llx != %llx !\n", modMSRValue, TEST_MSR_VALUE);
        return false;
    }

    FDP_WRITEMSR(pFDP, 0, MSR_LSTAR, originalMSRValue)

    FDP_READMSR(pFDP, 0, MSR_LSTAR, &modMSRValue)
    if (modMSRValue != originalMSRValue)
    {
        printf("MSR doesn't match %llx != %llx !\n", modMSRValue, originalMSRValue);
        return false;
    }

    printf("[OK]\n");
    return true;
}

bool testReadWriteRegister(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    FDP_Register reg = bAArch64 ? FDP_X0_REGISTER : FDP_RAX_REGISTER;

    uint64_t originalRegValue;
    FDP_READREGISTER(pFDP, 0, reg, &originalRegValue)

    uint64_t TEST_REGISTER_VALUE = 0xDEADBEEFDEADBEEF;
    FDP_WRITEREGISTER(pFDP, 0, reg, TEST_REGISTER_VALUE)

    uint64_t modRegValue;
    FDP_READREGISTER(pFDP, 0, reg, &modRegValue)
    if (modRegValue != TEST_REGISTER_VALUE)
    {
        printf("Register doesn't match %llx != %llx !\n", modRegValue, TEST_REGISTER_VALUE);
        return false;
    }

    FDP_WRITEREGISTER(pFDP, 0, reg, originalRegValue)

    printf("[OK]\n");
    return true;
}

bool testReadWritePhysicalMemory(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    uint64_t physicalAddress = bAArch64 ? _1G + 0xc000 : 0xc000;

    uint8_t originalPage[4096];
    FDP_READPHYSICALMEMORY(pFDP, originalPage, 4096, physicalAddress)

    uint8_t garbagePage[4096];
    memset(garbagePage, 0xCA, 4096);
    FDP_WRITEPHYSICALMEMORY(pFDP, garbagePage, 4096, physicalAddress)

    uint8_t modPage[4096];
    FDP_READPHYSICALMEMORY(pFDP, modPage, 4096, physicalAddress)
    if (memcmp(garbagePage, modPage, 4096) != 0)
    {
        printf("Failed to compare garbagePage and modPage !\n");
        return false;
    }

    FDP_WRITEPHYSICALMEMORY(pFDP, originalPage, 4096, physicalAddress)

    printf("[OK]\n");
    return true;
}

bool testReadWriteVirtualMemorySpeed(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t tempVirtualAddress = 0;
    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    tempVirtualAddress = originalMSRValue & 0xFFFFFFFFFFFFF000;
    TimerOut = false;
    TimerGo = true;
    uint64_t ReadCount = 0;
    while (TimerOut == false)
    {
        uint8_t OriginalPage[4096];
        FDP_READVIRTUALMEMORY(pFDP, 0, OriginalPage, 4096, tempVirtualAddress)
        ReadCount++;
    }

    int ReadCountPerSecond = (int)ReadCount / iTimerDelay;
    if (ReadCountPerSecond < 400000)
    {
        printf("Too slow !\n");
        return false;
    }
    printf("[OK] %d/s\n", ReadCountPerSecond);
    return true;
}

bool testReadWritePhysicalMemorySpeed(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    TimerOut = false;
    TimerGo = true;
    uint64_t ReadCount = 0;
    while (TimerOut == false)
    {
        uint8_t OriginalPage[4096];
        FDP_READPHYSICALMEMORY(pFDP, OriginalPage, sizeof(OriginalPage), 0)
        ReadCount++;
    }

    int ReadCountPerSecond = (int)ReadCount / iTimerDelay;
    if (ReadCountPerSecond < 400000)
    {
        printf("Too slow !\n");
        return false;
    }
    printf("[OK] %d/s\n", ReadCountPerSecond);
    return true;
}

bool testReadLargePhysicalMemory(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    // This test may fail if there's not enough contiguous physical memory

    FDP_PAUSE(pFDP)

    uint8_t* pBuffer = (uint8_t*)malloc(50 * _1M);
    if (pBuffer == NULL)
    {
        printf("Failed to malloc !\n");
        return false;
    }

    uint64_t RipValue;
    FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &RipValue)

    uint64_t physicalRipValue;
    FDP_VIRTUALTOPHYSICAL(pFDP, 0, RipValue, &physicalRipValue)

    if (FDP_ReadPhysicalMemory(pFDP, pBuffer, 10 * _1M, physicalRipValue) == false)
    {
        printf("Failed to read physical memory !\n");
        free(pBuffer);
        return false;
    }
    free(pBuffer);

    printf("[OK]\n");
    return true;
}

bool testReadWriteVirtualMemory(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t tempVirtualAddress = 0;

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    tempVirtualAddress = originalMSRValue & 0xFFFFFFFFFFFFF000;

    uint8_t originalPage[4096];
    FDP_READVIRTUALMEMORY(pFDP, 0, originalPage, 4096, tempVirtualAddress)

    uint8_t garbagePage[4096];
    memset(garbagePage, 0xCA, 4096);
    for (int i = 0; i <= 4096; i++)
        FDP_WRITEVIRTUALMEMORY(pFDP, 0, garbagePage, i, tempVirtualAddress)

    uint8_t modPage[4096];
    FDP_READVIRTUALMEMORY(pFDP, 0, modPage, 4096, tempVirtualAddress)
    if (memcmp(garbagePage, modPage, 4096) != 0)
    {
        printf("Failed to compare garbagePage and modPage !\n");
        return false;
    }

    for (int i = 0; i <= 4096; i++)
        FDP_WRITEVIRTUALMEMORY(pFDP, 0, originalPage, i, tempVirtualAddress)

    printf("[OK]\n");
    return true;
}

bool testGetStatePerformance(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    TimerOut = false;
    TimerGo = true;
    uint64_t ReadCount = 0;
    while (TimerOut == false)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
        ReadCount++;
    }

    int ReadPerSecond = (int)(ReadCount / TimerGetDelay());
    printf("[OK] %d/s\n", ReadPerSecond);
    return true;
}

bool testVirtualSyscallBP(FDP_SHM* pFDP, FDP_BreakpointType BreakpointType, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint32_t CPUCount;
    if (FDP_GetCpuCount(pFDP, &CPUCount) == false)
    {
        printf("Failed to get CPU count !\n");
        return false;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                             originalMSRValue, 1, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }

    FDP_RESUME(pFDP)

    int i = 0;
    TimerOut = false;
    TimerGo = true;
    while (TimerOut == false)
    {
        if (FDP_GetStateChanged(pFDP))
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_PAUSED && state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
            {
                i++;

                FDP_GETSTATE(pFDP, &state)

                if (!(state & FDP_STATE_DEBUGGER_ALERTED))
                    printf("!(state & FDP_STATE_DEBUGGER_ALERTED) (state %02x ) !\n", state);

                FDP_UNSETBREAKPOINT(pFDP, breakpointId)

                for (uint32_t c = 0; c < CPUCount; c++)
                    FDP_SINGLESTEP(pFDP, c)

                breakpointId = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                                 originalMSRValue, 1, FDP_NO_CR3);
                if (breakpointId < 0)
                {
                    printf("Failed to insert breakpoint !\n");
                    return false;
                }

                FDP_RESUME(pFDP)
            }
        }
    }

    FDP_PAUSE(pFDP)
    FDP_UNSETBREAKPOINT(pFDP, breakpointId)

    printf("[OK] %d/s\n", (i / TimerGetDelay()));
    return true;
}

bool testPhysicalSyscallBP(FDP_SHM* pFDP, FDP_BreakpointType BreakpointType, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    uint64_t physicalLSTAR;
    FDP_VIRTUALTOPHYSICAL(pFDP, 0, originalMSRValue, &physicalLSTAR)

    int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                             physicalLSTAR, 1, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }

    FDP_RESUME(pFDP)

    int i = 0;
    TimerOut = false;
    TimerGo = true;
    while (TimerOut == false)
    {
        if (FDP_GetStateChanged(pFDP))
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
            {
                i++;
                uint8_t state = 0;
                FDP_UNSETBREAKPOINT(pFDP, breakpointId)

                FDP_SINGLESTEP(pFDP, 0)

                breakpointId = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                                 physicalLSTAR, 1, FDP_NO_CR3);
                if (breakpointId < 0)
                {
                    printf("Failed to insert breakpoint !\n");
                    return false;
                }

                FDP_RESUME(pFDP)
            }
        }
    }

    FDP_PAUSE(pFDP)
    FDP_UNSETBREAKPOINT(pFDP, breakpointId)

    printf("[OK] %d/s\n", (i / TimerGetDelay()));
    return true;
}

bool testMultiplePhysicalSyscallBP(FDP_SHM* pFDP, FDP_BreakpointType BreakpointType, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    uint64_t physicalLSTAR;
    FDP_VIRTUALTOPHYSICAL(pFDP, 0, originalMSRValue, &physicalLSTAR)

    int64_t breakpointId[10];
    for (int j = 0; j < 10; j++)
    {
        breakpointId[j] = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                            physicalLSTAR + j, 1, FDP_NO_CR3);
        if (breakpointId[j] < 0)
        {
            printf("Failed to insert breakpoint !\n");
            return false;
        }
    }

    FDP_RESUME(pFDP)

    int i = 0;
    while (i < 10)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
        if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
        {
            i++;

            for (int j = 0; j < 10; j++)
                FDP_UNSETBREAKPOINT(pFDP, breakpointId[j])

            FDP_SINGLESTEP(pFDP, 0)

            for (int j = 0; j < 10; j++)
            {
                breakpointId[j] = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                                    physicalLSTAR + j, 1, FDP_NO_CR3);
                if (breakpointId[j] < 0)
                {
                    printf("Failed to insert breakpoint !\n");
                    return false;
                }
            }

            FDP_RESUME(pFDP)
        }
    }

    FDP_PAUSE(pFDP)
    for (int j = 0; j < 10; j++)
        FDP_UNSETBREAKPOINT(pFDP, breakpointId[j])

    printf("[OK]\n");
    return true;
}

bool testMultipleVirtualSyscallBP(FDP_SHM* pFDP, FDP_BreakpointType BreakpointType, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint32_t CPUCount;
    if (FDP_GetCpuCount(pFDP, &CPUCount) == false)
    {
        printf("Failed to get CPU count !\n");
        return false;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    int64_t breakpointId[10];
    for (int j = 0; j < 10; j++)
    {
        breakpointId[j] = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                            originalMSRValue + j, 1, FDP_NO_CR3);
        if (breakpointId[j] < 0)
        {
            printf("Failed to insert breakpoint !\n");
            return false;
        }
    }

    FDP_RESUME(pFDP)

    int i = 0;
    while (i < 10)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
        if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
        {
            i++;

            for (int j = 0; j < 10; j++)
                FDP_UNSETBREAKPOINT(pFDP, breakpointId[j])

            for (uint32_t c = 0; c < CPUCount; c++)
                FDP_SINGLESTEP(pFDP, c)

            for (int j = 0; j < 10; j++)
            {
                breakpointId[j] = FDP_SetBreakpoint(pFDP, 0, BreakpointType, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                                    originalMSRValue + j, 1, FDP_NO_CR3);
                if (breakpointId[j] < 0)
                {
                    printf("Failed to insert breakpoint !\n");
                    return false;
                }
            }

            FDP_RESUME(pFDP)
        }
    }

    FDP_PAUSE(pFDP)
    for (int j = 0; j < 10; j++)
        FDP_UNSETBREAKPOINT(pFDP, breakpointId[j])

    printf("[OK]\n");
    return true;
}

bool testLargeVirtualPageSyscallBP(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_PAGEHBP, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                             originalMSRValue, 4096 * 30, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }

    FDP_RESUME(pFDP)

    int i = 0;
    while (i < 10)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
        if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
        {
            i++;
            FDP_UNSETBREAKPOINT(pFDP, breakpointId)

            FDP_SINGLESTEP(pFDP, 0)

            breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_PAGEHBP, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                             originalMSRValue, 4096 * 30, FDP_NO_CR3);
            if (breakpointId < 0)
            {
                printf("Failed to insert breakpoint !\n");
                return false;
            }

            FDP_RESUME(pFDP)

            printf(".");
            fflush(stdout);
        }
    }

    FDP_PAUSE(pFDP)
    FDP_UNSETBREAKPOINT(pFDP, breakpointId)

    printf("[OK]\n");
    return true;
}

bool testLargePhysicalPageSyscallBP(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    uint64_t physicalLSTAR;
    FDP_VIRTUALTOPHYSICAL(pFDP, 0, originalMSRValue, &physicalLSTAR)

    int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_PAGEHBP, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                             physicalLSTAR, 4096 * 30, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }

    FDP_RESUME(pFDP)

    int i = 0;
    while (i < 10)
    {
        if (FDP_GetStateChanged(pFDP))
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
            {
                i++;
                FDP_UNSETBREAKPOINT(pFDP, breakpointId)

                FDP_SINGLESTEP(pFDP, 0)

                breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_PAGEHBP, -1, FDP_EXECUTE_BP, FDP_PHYSICAL_ADDRESS,
                                                 physicalLSTAR, 4096 * 30, FDP_NO_CR3);
                if (breakpointId < 0)
                {
                    printf("Failed to insert breakpoint !\n");
                    return false;
                }

                FDP_RESUME(pFDP)
            }
        }
    }

    FDP_PAUSE(pFDP)
    FDP_UNSETBREAKPOINT(pFDP, breakpointId)

    printf("[OK]\n");
    return true;
}

bool testState(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    if (FDP_Resume(pFDP) == false)
    {
        printf("Failed to resume !\n");
        system("pause");
        return false;
    }

    if (FDP_Pause(pFDP) == false)
    {
        printf("Failed to pause !\n");
        system("pause");
        return false;
    }

    FDP_State state;
    if (FDP_GetState(pFDP, &state) == false)
    {
        printf("Failed to get state !\n");
        system("pause");
        return false;
    }

    if (!(state & FDP_STATE_PAUSED))
    {
        printf("1. state != STATE_PAUSED (state %02x) !\n", state);
        system("pause");
        return false;
    }

    if (FDP_Pause(pFDP) == false)
    {
        printf("Failed to pause !\n");
        system("pause");
        return false;
    }

    if (FDP_Resume(pFDP) == false)
    {
        printf("Failed to resume !\n");
        system("pause");
        return false;
    }

    if (FDP_Resume(pFDP) == false)
    {
        printf("Failed to resume !\n");
        system("pause");
        return false;
    }

    if (FDP_Pause(pFDP) == false)
    {
        printf("Failed to pause !\n");
        system("pause");
        return false;
    }

    if (FDP_GetState(pFDP, &state) == false)
    {
        printf("Failed to get state !\n");
        system("pause");
        return false;
    }

    if (!(state & FDP_STATE_PAUSED))
    {
        printf("2. state != STATE_PAUSED (state %02x) !\n", state);
        system("pause");
        return false;
    }

    if (!bAArch64)
    {
        uint64_t originalMSRValue;
        FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

        int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_SOFTHBP, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                                 originalMSRValue, 1, FDP_NO_CR3);
        if (breakpointId < 0)
        {
            printf("Failed to insert breakpoint !\n");
            return false;
        }

        FDP_RESUME(pFDP)

        while (true)
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
                break;
            usleep(1000 * 100);
        }

        FDP_UNSETBREAKPOINT(pFDP, breakpointId)
    }

    printf("[OK]\n");
    return true;
}

bool testDebugRegisters(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t oldDR0Value;
    uint64_t oldDR7Value;
    FDP_READREGISTER(pFDP, 0, FDP_DR0_REGISTER, &oldDR0Value)
    FDP_READREGISTER(pFDP, 0, FDP_DR7_REGISTER, &oldDR7Value)

    uint64_t LSTARValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &LSTARValue)

    FDP_WRITEREGISTER(pFDP, 0, FDP_DR0_REGISTER, LSTARValue)
    FDP_WRITEREGISTER(pFDP, 0, FDP_DR7_REGISTER, 0x0000000000000403)

    FDP_RESUME(pFDP)

    TimerOut = false;
    TimerGo = true;
    TimerSetDelay(5);
    uint64_t i = 0;
    while (TimerOut == false)
    {
        if (FDP_GetStateChanged(pFDP))
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_BREAKPOINT_HIT)
            {
                i++;
                FDP_SINGLESTEP(pFDP, 0)
                FDP_RESUME(pFDP)
            }
        }
    }

    FDP_WRITEREGISTER(pFDP, 0, FDP_DR0_REGISTER, oldDR0Value)
    FDP_WRITEREGISTER(pFDP, 0, FDP_DR7_REGISTER, oldDR7Value)

    int BreakpointPerSecond = (int)i / TimerGetDelay();
    printf("[OK] %d/s\n", BreakpointPerSecond);
    return true;
}

bool threadRunning;

void* testStateThread(LPVOID lpParam)
{
    FDP_SHM* pFDP = (FDP_SHM*)lpParam;
    while (threadRunning)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
    }
    return 0;
}

void* testReadRegisterThread(LPVOID lpParam)
{
    FDP_SHM* pFDP = (FDP_SHM*)lpParam;

    uint64_t   v;
    const bool bAArch64 = FDP_ReadRegister(pFDP, 0, FDP_X0_REGISTER, &v);

    while (threadRunning)
    {
        uint64_t RegisterValue;
        FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_X0_REGISTER : FDP_RAX_REGISTER, &RegisterValue)
    }
    return 0;
}

void* testReadMemoryThread(LPVOID lpParam)
{
    FDP_SHM* pFDP = (FDP_SHM*)lpParam;

    while (threadRunning)
    {
        uint8_t TempBuffer[1024];
        FDP_READPHYSICALMEMORY(pFDP, TempBuffer, 1024, 0)
    }
    return 0;
}

bool testMultiThread(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    threadRunning = true;

    pthread_t t1;
    pthread_create(&t1, NULL, testStateThread, pFDP);

    pthread_t t2;
    pthread_create(&t2, NULL, testReadRegisterThread, pFDP);

    pthread_t t3;
    pthread_create(&t3, NULL, testReadMemoryThread, pFDP);

    usleep(1000 * 2000);

    threadRunning = false;

    usleep(1000 * 100);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);

    printf("[OK]\n");
    return true;
}

bool testUnsetBreakpoint(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    for (int64_t breakpointId = 0; breakpointId <= FDP_MAX_BREAKPOINT_ID; breakpointId++)
        FDP_UnsetBreakpoint(pFDP, breakpointId);

    printf("[OK]\n");
    return true;
}

bool testManyBreakpoints(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    uint64_t RipValue;
    FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &RipValue)

    for (uint64_t i = 0; i < 1024; ++i)
        FDP_SetBreakpoint(pFDP, 0, FDP_SOFTHBP, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS, RipValue + i * 4096, 1,
                          FDP_NO_CR3);
    for (int64_t breakpointId = 0; breakpointId <= FDP_MAX_BREAKPOINT_ID; breakpointId++)
        FDP_UnsetBreakpoint(pFDP, breakpointId);

    printf("[OK]\n");
    return true;
}

bool testSingleStep(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    uint64_t SingleStepCount = 0;
    TimerSetDelay(30);
    TimerOut = false;
    TimerGo = true;
    while (TimerOut == false)
    {
        FDP_SINGLESTEP(pFDP, 0)
        SingleStepCount++;
    }

    printf("[OK]\n");
    return true;
}

bool testSingleStepSpeed(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    uint64_t SingleStepCount = 0;
    TimerSetDelay(3);
    TimerOut = false;
    TimerGo = true;
    while (TimerOut == false)
    {
        FDP_SingleStep(pFDP, 0);
        SingleStepCount++;
    }

    int SingleStepCountPerSecond = (int)SingleStepCount / TimerGetDelay();
    if (SingleStepCountPerSecond < 50000)
    {
        printf("Too slow !\n");
        return false;
    }
    printf("[OK] %d/s\n", SingleStepCountPerSecond);
    return true;
}

bool testSaveRestore(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    if (FDP_Save(pFDP) == false)
    {
        printf("Failed to save !\n");
        return false;
    }

    uint64_t OriginalRipValue;
    FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &OriginalRipValue)

    FDP_RESUME(pFDP)

    for (int i = 0; i < 5; i++)
    {
        usleep(1000 * 3000);

        if (FDP_Restore(pFDP) == false)
        {
            printf("Failed to restore !\n");
            return false;
        }

        uint64_t NewRipValue;
        FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &NewRipValue)

        if (OriginalRipValue != NewRipValue)
        {
            printf("OriginalRipValue != NewRipValue !\n");
            return false;
        }

        FDP_RESUME(pFDP)

        //Wait for Rip change
        uint64_t OldRipValue;
        uint64_t RipValue;
        FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &OldRipValue)
        while (true)
        {
            FDP_READREGISTER(pFDP, 0, bAArch64 ? FDP_PC_REGISTER : FDP_RIP_REGISTER, &RipValue)
            if (RipValue != OldRipValue)
                break;
        }

        printf(".");
        fflush(stdout);
    }

    printf("[OK]\n");
    return true;
}

bool testReadAllPhysicalMemory(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    uint64_t PhysicalMaxAddress = 0;
    if (FDP_GetPhysicalMemorySize(pFDP, &PhysicalMaxAddress) == false)
    {
        printf("Failed to get physical memory size !\n");
        return false;
    }

    uint64_t PhysicalAddress = 0;
    char     Buffer[4096];
    while (PhysicalAddress < PhysicalMaxAddress)
    {
        if (FDP_ReadPhysicalMemory(pFDP, (uint8_t*)Buffer, sizeof(Buffer), PhysicalAddress) == false)
        {
            // Some physical addresses aren't readable
        }
        PhysicalAddress += sizeof(Buffer);
    }

    printf("[OK]\n");
    return true;
}

bool testReadWriteAllPhysicalMemory(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    uint64_t PhysicalMaxAddress = 0;
    if (FDP_GetPhysicalMemorySize(pFDP, &PhysicalMaxAddress) == false)
    {
        printf("Failed to get physical memory size !\n");
        return false;
    }

    uint64_t PhysicalAddress = 0;
    char     Buffer[4096];
    while (PhysicalAddress < PhysicalMaxAddress)
    {
        if (FDP_ReadPhysicalMemory(pFDP, (uint8_t*)Buffer, sizeof(Buffer), PhysicalAddress))
            FDP_WRITEPHYSICALMEMORY(pFDP, (uint8_t*)Buffer, sizeof(Buffer), PhysicalAddress)
        PhysicalAddress += sizeof(Buffer);
    }

    printf("[OK]\n");
    return true;
}

bool testSetCr3(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    // Get a valid CR3 and RIP
    uint64_t firstCr3;
    FDP_READREGISTER(pFDP, 0, FDP_CR3_REGISTER, &firstCr3)

    uint64_t firstRip;
    FDP_READREGISTER(pFDP, 0, FDP_RIP_REGISTER, &firstRip)

    uint64_t firstValue;
    FDP_READVIRTUALMEMORY(pFDP, 0, (uint8_t*)&firstValue, sizeof(firstValue), firstRip)

    // Get a second valid CR3 and RIP
    uint64_t secondCr3;
    uint64_t secondRip;
    uint64_t secondValue;

    int64_t breakpointId =
        FDP_SetBreakpoint(pFDP, 0, FDP_CRHBP, -1, FDP_WRITE_BP, FDP_VIRTUAL_ADDRESS, 3, 1, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }
    while (true)
    {
        FDP_State state;
        FDP_GETSTATE(pFDP, &state)
        if (state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
        {
            FDP_READREGISTER(pFDP, 0, FDP_CR3_REGISTER, &secondCr3)
            if (secondCr3 != firstCr3)
            {
                FDP_READREGISTER(pFDP, 0, FDP_RIP_REGISTER, &secondRip)
                FDP_READVIRTUALMEMORY(pFDP, 0, (uint8_t*)&secondValue, sizeof(secondValue), secondRip)
                if (secondValue != firstValue)
                    break;
            }
        }

        FDP_SingleStep(pFDP, 0);
        FDP_RESUME(pFDP)
        usleep(1000 * 100);
    }
    FDP_UnsetBreakpoint(pFDP, breakpointId);

    // Switch to the first CR3 and re-read memory at first RIP
    FDP_WRITEREGISTER(pFDP, 0, FDP_CR3_REGISTER, firstCr3)
    uint64_t firstValueNew;
    FDP_READVIRTUALMEMORY(pFDP, 0, (uint8_t*)&firstValueNew, sizeof(firstValueNew), firstRip)
    if (firstValueNew != firstValue)
    {
        printf("Failed to change Cr3 !\n");
        return false;
    }

    // Restore the second CR3 and re-read memory at second RIP
    FDP_WRITEREGISTER(pFDP, 0, FDP_CR3_REGISTER, secondCr3)
    uint64_t secondValueNew;
    FDP_READVIRTUALMEMORY(pFDP, 0, (uint8_t*)&secondValueNew, sizeof(secondValueNew), secondRip)
    if (secondValueNew != secondValue)
    {
        printf("Failed to restore Cr3 !\n");
        return false;
    }

    printf("[OK]\n");
    return true;
}

bool testSingleStepPageBreakpoint(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    if (bAArch64)
    {
        printf("[OK] NOT IMPLEMENTED YET\n");
        return true;
    }

    bool bReturnValue = false;

    uint64_t originalMSRValue;
    FDP_READMSR(pFDP, 0, MSR_LSTAR, &originalMSRValue)

    int64_t breakpointId = FDP_SetBreakpoint(pFDP, 0, FDP_PAGEHBP, -1, FDP_EXECUTE_BP, FDP_VIRTUAL_ADDRESS,
                                             originalMSRValue, 1, FDP_NO_CR3);
    if (breakpointId < 0)
    {
        printf("Failed to insert breakpoint !\n");
        return false;
    }

    FDP_RESUME(pFDP)

    bool bRunning = true;
    while (bRunning)
    {
        if (FDP_GetStateChanged(pFDP))
        {
            FDP_State state;
            FDP_GETSTATE(pFDP, &state)
            if (state & FDP_STATE_PAUSED && state & FDP_STATE_BREAKPOINT_HIT && !(state & FDP_STATE_DEBUGGER_ALERTED))
                break;
        }
    }

    uint64_t OldRip;
    FDP_READREGISTER(pFDP, 0, FDP_RIP_REGISTER, &OldRip)

    FDP_SINGLESTEP(pFDP, 0)

    uint64_t NewRip;
    FDP_READREGISTER(pFDP, 0, FDP_RIP_REGISTER, &NewRip)
    if (OldRip == NewRip)
        bReturnValue = false;
    else
        bReturnValue = true;

    FDP_PAUSE(pFDP)
    FDP_UNSETBREAKPOINT(pFDP, breakpointId)

    if (bReturnValue)
        printf("[OK]\n");
    else
        printf("[FAIL]\n");
    return bReturnValue;
}

bool testPauseSingleStep(FDP_SHM* pFDP, bool bAArch64)
{
    printf("%s ...", __FUNCTION__);
    fflush(stdout);

    FDP_PAUSE(pFDP)

    FDP_SINGLESTEP(pFDP, 0)

    printf("[OK]\n");
    return true;
}

int testFDP(const char* pVMName, bool bTestSpeed)
{
    int returnCode = 1;

    FDP_SHM* pFDP = FDP_OpenSHM(pVMName);
    if (pFDP == NULL)
        printf("Failed to open shared memory !\n");
    else
    {
        if (FDP_Init(pFDP) == false)
            printf("Failed to init !\n");
        else
        {
            pthread_t t1;
            pthread_create(&t1, NULL, TimerRoutine, NULL);

            uint64_t   v;
            const bool bAArch64 = FDP_IsAArch64(pFDP);

            if (FDP_Pause(pFDP) == false)
                goto Fail;
            if (testUnsetBreakpoint(pFDP, bAArch64) == false)
                goto Fail;
            if (testReadWriteRegister(pFDP, bAArch64) == false)
                goto Fail;
            if (testPauseSingleStep(pFDP, bAArch64) == false)
                goto Fail;
            if (testManyBreakpoints(pFDP, bAArch64) == false)
                goto Fail;
            if (testSingleStepPageBreakpoint(pFDP, bAArch64) == false)
                goto Fail;
            if (bTestSpeed && testSingleStepSpeed(pFDP, bAArch64) == false)
                goto Fail;
            if (testReadWriteMSR(pFDP, bAArch64) == false)
                goto Fail;
            if (testSetCr3(pFDP, bAArch64) == false)
                goto Fail;
            if (testMultiThread(pFDP, bAArch64) == false)
                goto Fail;
            if (testState(pFDP, bAArch64) == false)
                goto Fail;
            if (testVirtualSyscallBP(pFDP, FDP_SOFTHBP, bAArch64) == false)
                goto Fail;
            if (testReadWritePhysicalMemory(pFDP, bAArch64) == false)
                goto Fail;
            if (testReadWriteVirtualMemory(pFDP, bAArch64) == false)
                goto Fail;
            if (testGetStatePerformance(pFDP, bAArch64) == false)
                goto Fail;
            if (testDebugRegisters(pFDP, bAArch64) == false)
                goto Fail;
            if (testVirtualSyscallBP(pFDP, FDP_PAGEHBP, bAArch64) == false)
                goto Fail;
            if (testVirtualSyscallBP(pFDP, FDP_SOFTHBP, bAArch64) == false)
                goto Fail;
            if (testPhysicalSyscallBP(pFDP, FDP_PAGEHBP, bAArch64) == false)
                goto Fail;
            if (testPhysicalSyscallBP(pFDP, FDP_SOFTHBP, bAArch64) == false)
                goto Fail;
            if (testMultipleVirtualSyscallBP(pFDP, FDP_PAGEHBP, bAArch64) == false)
                goto Fail;
            if (testMultipleVirtualSyscallBP(pFDP, FDP_SOFTHBP, bAArch64) == false)
                goto Fail;
            if (testMultiplePhysicalSyscallBP(pFDP, FDP_PAGEHBP, bAArch64) == false)
                goto Fail;
            if (testMultiplePhysicalSyscallBP(pFDP, FDP_SOFTHBP, bAArch64) == false)
                goto Fail;
            if (testReadAllPhysicalMemory(pFDP, bAArch64) == false)
                goto Fail;
            // if (testReadWriteAllPhysicalMemory(pFDP) == false)
            //     goto Fail;
            if (testLargeVirtualPageSyscallBP(pFDP, bAArch64) == false)
                goto Fail;
            if (testLargePhysicalPageSyscallBP(pFDP, bAArch64) == false)
                goto Fail;
            if (bTestSpeed && testReadWriteVirtualMemorySpeed(pFDP, bAArch64) == false)
                goto Fail;
            if (bTestSpeed && testReadWritePhysicalMemorySpeed(pFDP, bAArch64) == false)
                goto Fail;
            if (testReadLargePhysicalMemory(pFDP, bAArch64) == false)
                goto Fail;
            if (testSaveRestore(pFDP, bAArch64) == false)
                goto Fail;

            returnCode = 0;
        Fail:
            testUnsetBreakpoint(pFDP, bAArch64);
            FDP_RESUME(pFDP)
        }
    }

    printf("**********************\n");
    printf("**********************\n");
    if (returnCode == 0)
        printf("**  TESTS PASSED !  **\n");
    else
        printf("**  TESTS FAILED !  **\n");
    printf("**********************\n");
    printf("**********************\n");

    return returnCode;
}

int main(int argc, char* argv[])
{
    if (argc != 2 && argc != 3)
    {
        printf("Usage: %s <VM Name> [--testSpeed]\n", argv[0]);
        return 2;
    }

    bool bTestSpeed = false;
    if (argc == 3)
        bTestSpeed = strcmp(argv[2], "--testSpeed") == 0;

    return testFDP(argv[1], bTestSpeed);
}
