#!/usr/bin/env python
from PyFDP.FDP import FDP


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
