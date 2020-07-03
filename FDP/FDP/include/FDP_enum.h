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
#ifndef __FDP_ENUM_H__
#define __FDP_ENUM_H__

enum FDP_BreakpointType_
{
    FDP_INVHBP = 0x0,
    FDP_SOFTHBP,
    FDP_HARDHBP,
    FDP_PAGEHBP,
    FDP_MSRHBP,
    FDP_CRHBP
};
typedef uint16_t FDP_BreakpointType;

enum FDP_AddressType_
{
    FDP_WRONG_ADDRESS = 0x0,
    FDP_VIRTUAL_ADDRESS = 0x1,
    FDP_PHYSICAL_ADDRESS = 0x2
};
typedef uint16_t FDP_AddressType;

enum FDP_Access_
{
    FDP_WRONG_BP = 0x0,
    FDP_EXECUTE_BP = 0x1,
    FDP_WRITE_BP = 0x2,
    FDP_READ_BP = 0x4,
    FDP_INSTRUCTION_FETCH_BP = 0x8
};
typedef uint16_t FDP_Access;

enum FDP_State_
{
    FDP_STATE_NULL = 0x0,
    FDP_STATE_PAUSED = 0x1,
    FDP_STATE_BREAKPOINT_HIT = 0x2,
    FDP_STATE_DEBUGGER_ALERTED = 0x4,
    FDP_STATE_HARD_BREAKPOINT_HIT = 0x8
};
typedef uint16_t FDP_State;

enum FDP_Register_
{
    // x86-64
    FDP_RAX_REGISTER = 0x0,
    FDP_RBX_REGISTER = 0x1,
    FDP_RCX_REGISTER = 0x2,
    FDP_RDX_REGISTER = 0x3,
    FDP_R8_REGISTER = 0x4,
    FDP_R9_REGISTER = 0x5,
    FDP_R10_REGISTER = 0x6,
    FDP_R11_REGISTER = 0x7,
    FDP_R12_REGISTER = 0x8,
    FDP_R13_REGISTER = 0x9,
    FDP_R14_REGISTER = 0xA,
    FDP_R15_REGISTER = 0xB,
    FDP_RSP_REGISTER = 0xC,
    FDP_RBP_REGISTER = 0xD,
    FDP_RSI_REGISTER = 0xE,
    FDP_RDI_REGISTER = 0xF,
    FDP_RIP_REGISTER = 0x10,
    FDP_DR0_REGISTER = 0x11,
    FDP_DR1_REGISTER = 0x12,
    FDP_DR2_REGISTER = 0x13,
    FDP_DR3_REGISTER = 0x14,
    FDP_DR6_REGISTER = 0x15,
    FDP_DR7_REGISTER = 0x16,
    FDP_VDR0_REGISTER = 0x17,
    FDP_VDR1_REGISTER = 0x18,
    FDP_VDR2_REGISTER = 0x19,
    FDP_VDR3_REGISTER = 0x1A,
    FDP_VDR6_REGISTER = 0x1B,
    FDP_VDR7_REGISTER = 0x1C,
    FDP_CS_REGISTER = 0x1D,
    FDP_DS_REGISTER = 0x1E,
    FDP_ES_REGISTER = 0x1F,
    FDP_FS_REGISTER = 0x20,
    FDP_GS_REGISTER = 0x21,
    FDP_SS_REGISTER = 0x22,
    FDP_RFLAGS_REGISTER = 0x23,
    FDP_MXCSR_REGISTER = 0x24,
    FDP_GDTRB_REGISTER = 0x25,
    FDP_GDTRL_REGISTER = 0x26,
    FDP_IDTRB_REGISTER = 0x27,
    FDP_IDTRL_REGISTER = 0x28,
    FDP_CR0_REGISTER = 0x29,
    FDP_CR2_REGISTER = 0x2A,
    FDP_CR3_REGISTER = 0x2B,
    FDP_CR4_REGISTER = 0x2C,
    FDP_CR8_REGISTER = 0x2D,
    FDP_LDTR_REGISTER = 0x2E,
    FDP_LDTRB_REGISTER = 0x2F,
    FDP_LDTRL_REGISTER = 0x30,
    FDP_TR_REGISTER = 0x31,

    // AArch64
    FDP_X0_REGISTER = 0x100,
    FDP_X1_REGISTER = 0x101,
    FDP_X2_REGISTER = 0x102,
    FDP_X3_REGISTER = 0x103,
    FDP_X4_REGISTER = 0x104,
    FDP_X5_REGISTER = 0x105,
    FDP_X6_REGISTER = 0x106,
    FDP_X7_REGISTER = 0x107,
    FDP_X8_REGISTER = 0x108,
    FDP_X9_REGISTER = 0x109,
    FDP_X10_REGISTER = 0x10A,
    FDP_X11_REGISTER = 0x10B,
    FDP_X12_REGISTER = 0x10C,
    FDP_X13_REGISTER = 0x10D,
    FDP_X14_REGISTER = 0x10E,
    FDP_X15_REGISTER = 0x10F,
    FDP_X16_REGISTER = 0x110,
    FDP_X17_REGISTER = 0x111,
    FDP_X18_REGISTER = 0x112,
    FDP_X19_REGISTER = 0x113,
    FDP_X20_REGISTER = 0x114,
    FDP_X21_REGISTER = 0x115,
    FDP_X22_REGISTER = 0x116,
    FDP_X23_REGISTER = 0x117,
    FDP_X24_REGISTER = 0x118,
    FDP_X25_REGISTER = 0x119,
    FDP_X26_REGISTER = 0x11A,
    FDP_X27_REGISTER = 0x11B,
    FDP_X28_REGISTER = 0x11C,
    FDP_X29_REGISTER = 0x11D,
    FDP_LR_REGISTER = 0x11E,
    FDP_SP_REGISTER = 0x11F,
    FDP_PC_REGISTER = 0x120,
};
typedef uint16_t FDP_Register;

#endif  // __FDP_ENUM_H__
