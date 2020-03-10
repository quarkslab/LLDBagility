#!/usr/bin/env python
import argparse
import functools
import re
import shlex
import threading
import time
import traceback

import kdpserver
import lldb
import lldbagilityutils
import stubs.FDPSTUB
import stubs.VMSNSTUB
import stubvm

vm = None


def _exec_cmd(debugger, command, capture_output=False):
    if capture_output:
        cmdretobj = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand(command, cmdretobj)
        return cmdretobj
    else:
        debugger.HandleCommand(command)
        return None


def _evaluate_expression(exe_ctx, expression):
    res = exe_ctx.frame.EvaluateExpression(expression)
    try:
        vaddr = int(res.GetValue(), 0)
    except (TypeError, ValueError):
        return None
    else:
        return vaddr


def fdp_attach(debugger, command, exe_ctx, result, internal_dict):
    """
    Connect to a macOS VM via FDP.
    The VM must have already been started.
    Existing breakpoints are deleted on attaching.
    Re-execute this command every time the VM is rebooted.
    """
    parser = argparse.ArgumentParser(prog="fdp-attach")
    parser.add_argument("vm_name")
    args = parser.parse_args(shlex.split(command))

    _attach(debugger, exe_ctx, stubs.FDPSTUB.FDPSTUB, args.vm_name)


def vmsn_attach(debugger, command, exe_ctx, result, internal_dict):
    """
    Connect to a macOS VM via VMSN. Currently not maintained!
    Existing breakpoints are deleted on attaching.
    """
    parser = argparse.ArgumentParser(prog="vmsn-attach")
    parser.add_argument("vm_name")
    args = parser.parse_args(shlex.split(command))

    _attach(debugger, exe_ctx, stubs.VMSNSTUB.VMSNSTUB, args.vm_name)


def _attach(debugger, exe_ctx, vm_stub, vm_name):
    global vm
    print(lldbagilityutils.LLDBAGILITY)

    print("* Attaching to the VM")
    try:
        vm = stubvm.STUBVM(vm_stub, vm_name)
    except Exception as exc:
        print("* Could not attach! {}".format(str(exc)))
        return

    print("* Resuming the VM execution until reaching kernel code")
    vm.complete_attach()
    print("* Kernel load address: 0x{:016x}".format(vm.kernel_load_vaddr))
    print("* Kernel slide:        0x{:x}".format(vm.kernel_slide))
    print("* Kernel cr3:          0x{:x}".format(vm.kernel_cr3))
    print("* Kernel version:      {}".format(vm.kernel_version))
    print("* VM breakpoints deleted")

    # detach the previous process (if any)
    exe_ctx.process.Detach()

    # remove all LLDB breakpoints
    exe_ctx.target.DeleteAllBreakpoints()
    print("* LLDB breakpoints deleted")

    # start the fake KDP server
    kdpsv = kdpserver.KDPServer()
    th = threading.Thread(target=kdpsv.debug, args=(vm,))
    th.daemon = True
    th.start()

    # connect LLDB to the fake KDP server
    kdpsv_addr, kdpsv_port = kdpsv.sv_sock.getsockname()
    _exec_cmd(debugger, "kdp-remote '{}:{}'".format(kdpsv_addr, kdpsv_port))

    # trigger a memory write to find out the address of the kdp struct
    vm.store_kdp_at_next_write_virtual_memory()
    if _exec_cmd(debugger, "memory write &kdp 41", capture_output=True).GetError():
        print("* Unable to find the 'kdp' symbol. Did you specify the target to debug?")
        vm.abort_store_kdp_at_next_write_virtual_memory()


def _attached(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        global vm
        if not vm:
            print("* Not attached to a VM!")
            return
        return f(*args, **kwargs)

    return _wrapper


@_attached
def fdp_save(debugger, command, exe_ctx, result, internal_dict):
    """
    Save the current state of the attached macOS VM.
    Breakpoints are not saved (but retained for the current session).
    """
    # saving the state causes all breakpoints (soft and hard) to be unset, but
    # we can preserve them at least for the current session

    # we disable soft breakpoints before saving and then re-enable them once the state
    # has been saved, so that LLDB sends again the KDP requests for setting them
    exe_ctx.target.DisableAllBreakpoints()
    # similarly, for hard breakpoints we save the state of the debug registers before saving,
    # and restore it afterwards
    dbgregs = vm.read_registers(("dr0", "dr1", "dr2", "dr3", "dr6", "dr7"))

    # interrupt and save the VM state
    process_was_stopped = exe_ctx.process.is_stopped
    print("* Saving the VM state")
    vm.interrupt_and_take_snapshot()
    print("* State saved")

    # restore soft breakpoints
    exe_ctx.target.EnableAllBreakpoints()
    # restore hard breakpoints
    vm.write_registers(dbgregs)

    if not process_was_stopped:
        # display stop info
        _exec_cmd(debugger, "process status")


@_attached
def fdp_restore(debugger, command, exe_ctx, result, internal_dict):
    """
    Restore the attached macOS VM to the last saved state.
    Breakpoints are deleted on restoring.
    """
    # interrupt and restore the VM state
    print("* Restoring the last saved VM state")
    if vm.interrupt_and_restore_last_snapshot():
        print("* State restored")
        # do a full reattach (the kernel load address may differ)
        fdp_attach(debugger, vm.name, exe_ctx, result, internal_dict)
    else:
        print("* No saved state found")


@_attached
def fdp_interrupt(debugger, command, exe_ctx, result, internal_dict):
    """
    Interrupt (pause) the execution of the attached macOS VM.
    """
    vm.interrupt()


@_attached
def fdp_hbreakpoint(debugger, command, exe_ctx, result, internal_dict):
    """
    Set or unset hardware breakpoints.
    Hardware breakpoints are implemented using the debug registers DR0, DR1, DR2 and DR3.
    Consequently, a maximum of four hardware breakpoints can be active simultaneously.
    """
    parser = argparse.ArgumentParser(prog="fdp-hbreakpoint")
    subparsers = parser.add_subparsers(dest="action")

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument(
        "trigger",
        choices={"e", "rw", "w"},
        help="Type of memory access to trap on: execute, read/write, or write only.",
    )
    set_parser.add_argument(
        "nreg",
        type=lambda i: int(i, 0),
        choices={0, 1, 2, 3},
        help="Breakpoint slot to use (corresponding to registers ).",
    )
    set_parser.add_argument("expression", help="Breakpoint address or expression to be evaluated as such.")

    unset_parser = subparsers.add_parser("unset")
    unset_parser.add_argument(
        "nreg",
        type=lambda i: int(i, 0),
        choices={0, 1, 2, 3},
        help="Breakpoint slot to free (corresponding to registers DR0, DR1, DR2 and DR3).",
    )

    args = parser.parse_args(shlex.split(command))
    if args.action == "set":
        vaddr = _evaluate_expression(exe_ctx, args.expression)
        if vaddr:
            vm.set_hard_breakpoint(args.trigger, args.nreg, vaddr)
            print("* Hardware breakpoint set: address = 0x{:016x}".format(vaddr))
        else:
            print("* Invalid expression")
    elif args.action == "unset":
        vm.unset_hard_breakpoint(args.nreg)
        print("* Hardware breakpoint unset")
    else:
        raise AssertionError


@_attached
def fdp_test(debugger, command, exe_ctx, result, internal_dict):
    """
    Run some tests.
    Warning: tests change the state of the machine and modify the last saved state!
    """
    regs = {
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
    }

    def _t1():
        print("* Halt/resume/single step")
        vm.halt()
        assert vm.is_state_halted()

        vm.resume()
        assert not vm.is_state_halted()

        vm.halt()
        for _ in range(100):
            vm.single_step()
            assert vm.is_state_halted()

    def _t2():
        print("* Read/write registers")
        vm.halt()

        orig_values = vm.read_registers(regs)

        new_values = {reg: 0x1337 for reg in regs}
        for reg in regs:
            vm.write_register(reg, new_values[reg])
        # modifications to RFLAGS should be disabled
        assert vm.read_register("rflags") == orig_values["rflags"]
        del new_values["rflags"]
        assert vm.read_registers(regs - {"rflags"}) == new_values

        vm.write_registers(orig_values)
        for reg in regs:
            assert vm.read_register(reg) == orig_values[reg]

    def _t3():
        print("* Read/write virtual memory")
        vm.halt()

        data = vm.read_virtual_memory(vm.read_register("rsp"), 0x8)

        new_data = b"ABCDEFGH"
        vm.write_virtual_memory(vm.read_register("rsp"), new_data)
        assert vm.read_virtual_memory(vm.read_register("rsp"), 0x8) == new_data

        vm.write_virtual_memory(vm.read_register("rsp"), data)
        assert vm.read_virtual_memory(vm.read_register("rsp"), 0x8) == data

    def _t4():
        print("* Save/restore")
        vm.halt()

        orig_values = vm.read_registers(regs)
        orig_data = vm.read_virtual_memory(vm.read_register("rsp"), 0x100)
        vm.interrupt_and_take_snapshot()
        assert vm.is_state_halted()

        vm.write_virtual_memory(vm.read_register("rsp"), b"A" * 0x100)
        vm.single_step()
        vm.resume()
        time.sleep(0.100)

        vm.interrupt_and_restore_last_snapshot()
        assert vm.is_state_halted()
        assert not vm.is_breakpoint_hit()
        assert vm.read_registers(regs) == orig_values
        assert vm.read_virtual_memory(vm.read_register("rsp"), 0x100) == orig_data

    def _t5():
        print("* Debug registers")
        vm.halt()
        vm.write_register("dr7", 0x0)

        vm.set_hard_breakpoint("rw", 0x0, 0x1234)
        assert vm.read_register("dr0") == 0x1234
        assert vm.read_register("dr7") == 0b00000000000000110000000000000010
        vm.set_hard_breakpoint("e", 0x0, 0x1234)
        assert vm.read_register("dr7") == 0b00000000000000000000000000000010
        vm.set_hard_breakpoint("w", 0x0, 0x1234)
        assert vm.read_register("dr7") == 0b00000000000000010000000000000010

        vm.set_hard_breakpoint("rw", 0x1, 0x1234)
        assert vm.read_register("dr1") == 0x1234
        assert vm.read_register("dr7") == 0b00000000001100010000000000001010
        vm.set_hard_breakpoint("rw", 0x2, 0x1234)
        assert vm.read_register("dr2") == 0x1234
        assert vm.read_register("dr7") == 0b00000011001100010000000000101010
        vm.set_hard_breakpoint("rw", 0x3, 0x1234)
        assert vm.read_register("dr3") == 0x1234
        assert vm.read_register("dr7") == 0b00110011001100010000000010101010

        vm.unset_hard_breakpoint(0x0)
        assert vm.read_register("dr7") == 0b00110011001100010000000010101000
        vm.unset_hard_breakpoint(0x1)
        assert vm.read_register("dr7") == 0b00110011001100010000000010100000
        vm.unset_hard_breakpoint(0x2)
        assert vm.read_register("dr7") == 0b00110011001100010000000010000000
        vm.unset_hard_breakpoint(0x3)
        assert vm.read_register("dr7") == 0b00110011001100010000000000000000

    def _t6():
        print("* Soft/hard exec breakpoint")
        vm.halt()

        # keep in mind that FDP soft and page breakpoints do not work just after a restore
        # (see VMR3AddSoftBreakpoint())

        vm.unset_all_breakpoints()
        vm.single_step()
        assert not vm.is_breakpoint_hit()

        vm.interrupt_and_take_snapshot()
        vm.single_step()
        vm.single_step()
        rip = vm.read_register("rip")

        vm.interrupt_and_restore_last_snapshot()
        vm.single_step()
        bpid = vm.set_soft_exec_breakpoint(rip)
        assert 0 <= bpid <= 254
        assert not vm.is_breakpoint_hit()
        vm.resume()
        time.sleep(0.100)
        vm.halt()
        assert vm.is_breakpoint_hit()

        vm.interrupt_and_restore_last_snapshot()
        vm.single_step()
        vm.set_hard_breakpoint("e", 0x0, rip)
        assert not vm.is_breakpoint_hit()
        vm.resume()
        time.sleep(0.100)
        vm.halt()
        assert vm.is_breakpoint_hit()

    if exe_ctx.process.is_running:
        vm.interrupt()
    vm.unset_all_breakpoints()

    for _t in (_t1, _t2, _t3, _t4, _t5, _t6):
        _t()
    print("* All tests passed!")


def __lldb_init_module(debugger, internal_dict):
    # FDP
    debugger.HandleCommand("command script add -f lldbagility.fdp_attach fdp-attach")
    debugger.HandleCommand("command script add -f lldbagility.fdp_save fdp-save")
    debugger.HandleCommand("command script add -f lldbagility.fdp_restore fdp-restore")
    debugger.HandleCommand("command script add -f lldbagility.fdp_interrupt fdp-interrupt")
    debugger.HandleCommand("command script add -f lldbagility.fdp_hbreakpoint fdp-hbreakpoint")
    debugger.HandleCommand("command script add -f lldbagility.fdp_test fdp-test")

    debugger.HandleCommand("command alias fa fdp-attach")
    debugger.HandleCommand("command alias fs fdp-save")
    debugger.HandleCommand("command alias fr fdp-restore")
    debugger.HandleCommand("command alias fi fdp-interrupt")
    debugger.HandleCommand("command alias fh fdp-hbreakpoint")

    # VMSN
    debugger.HandleCommand("command script add -f lldbagility.vmsn_attach vmsn-attach")

    debugger.HandleCommand("command alias va vmsn-attach")
