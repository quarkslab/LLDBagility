#!/usr/bin/env python
import argparse
import struct

from PyFDP.FDP import FDP

p32 = lambda i: struct.pack("<I", i)
p64 = lambda i: struct.pack("<Q", i)
u32 = lambda s: struct.unpack("<I", s)[0]
u64 = lambda s: struct.unpack("<Q", s)[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vmname")
    args = parser.parse_args()

    fdp = FDP(args.vmname)

    g = fdp.GetState
    p = fdp.Pause
    pc = lambda: hex(fdp.rip)
    r = fdp.Resume
    s = fdp.SingleStep
    u = fdp.UnsetAllBreakpoint

    p()
    assert g() == FDP.FDP_STATE_PAUSED
