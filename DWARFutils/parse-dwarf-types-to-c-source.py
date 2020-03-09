#!/usr/bin/env python
import argparse
import collections
import dataclasses
import os
import re
import sys
import tempfile

import dwarfutils


@dataclasses.dataclass
class DIE:
    pass


@dataclasses.dataclass
class DIEArray(DIE):
    ttype: tuple
    size: int


def _extract_array_count(off):
    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, off, children=True)
    assert dwarfutils.extract_tag(txts[0]) == "TAG_array_type"
    assert dwarfutils.extract_tag(txts[1]) == "TAG_subrange_type"
    try:
        count = dwarfutils.extract_count(txts[1])
    except AttributeError:
        count = -1
    return count


def parse_array_type(txt):
    off = dwarfutils.extract_offset(txt)
    type_off, type_name = dwarfutils.extract_type(txt)
    extract_and_parse_die(type_off)
    DIEs[off] = DIEArray(ttype=(type_off, type_name), size=_extract_array_count(off))


@dataclasses.dataclass
class DIEBase(DIE):
    name: str
    byte_size: int


def parse_base_type(txt):
    off = dwarfutils.extract_offset(txt)
    DIEs[off] = DIEBase(name=dwarfutils.extract_name(txt), byte_size=dwarfutils.extract_byte_size(txt))


@dataclasses.dataclass
class DIECompileUnit(DIE):
    name: str


def parse_compile_unit_type(txt):
    off = dwarfutils.extract_offset(txt)
    DIEs[off] = DIECompileUnit(name=dwarfutils.extract_name(txt))


@dataclasses.dataclass
class DIEConst(DIE):
    ttype: tuple


def parse_const_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        type_off, type_name = dwarfutils.extract_type(txt)
    except AttributeError:
        type_off, type_name = None, None
    else:
        extract_and_parse_die(type_off)
    DIEs[off] = DIEConst(ttype=(type_off, type_name))


@dataclasses.dataclass
class DIEEnumeration(DIE):
    name: str
    members: list


@dataclasses.dataclass
class DIEEnumerator(DIE):
    name: str
    const_value: int


def parse_enumeration_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        name = dwarfutils.extract_name(txt)
    except AttributeError:
        name = None
    DIEs[off] = DIEEnumeration(name=name, members=list())
    parse_enumeration(off)


def parse_enumeration(parent_off):
    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, parent_off, children=True)
    assert dwarfutils.extract_tag(txts[0]) == "TAG_enumeration_type"
    for txt in txts[1:]:
        if "TAG_enumerator" in txt:
            off = dwarfutils.extract_offset(txt)
            DIEs[off] = DIEEnumerator(
                name=dwarfutils.extract_name(txt), const_value=dwarfutils.extract_const_value(txt)
            )
            DIEs[parent_off].members.append(off)
        elif "NULL" in txt:
            return
        else:
            raise NotImplementedError
    else:
        assert "AT_declaration" in txts[0]


@dataclasses.dataclass
class DIEFormalParameter(DIE):
    ttype: tuple


@dataclasses.dataclass
class DIEMember(DIE):
    name: str
    ttype: tuple
    location: int
    bit_size: int


def parse_member_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        name = dwarfutils.extract_name(txt)
    except AttributeError:
        name = None
    type_off, type_name = dwarfutils.extract_type(txt)
    extract_and_parse_die(type_off)
    try:
        location = dwarfutils.extract_location(txt)
    except AttributeError:
        try:
            location = dwarfutils.extract_bit_location(txt)
        except AttributeError:
            location = -1
    try:
        bit_size = dwarfutils.extract_bit_size(txt)
    except AttributeError:
        bit_size = -1
    DIEs[off] = DIEMember(name=name, ttype=(type_off, type_name), location=location, bit_size=bit_size)


@dataclasses.dataclass
class DIEPointer(DIE):
    ttype: tuple


def parse_pointer_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        type_off, type_name = dwarfutils.extract_type(txt)
    except AttributeError:
        type_off, type_name = None, None
    else:
        extract_and_parse_die(type_off)
    DIEs[off] = DIEPointer(ttype=(type_off, type_name))


@dataclasses.dataclass
class DIEStructure(DIE):
    name: str
    byte_size: int
    members: list


def parse_structure_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        name = dwarfutils.extract_name(txt)
    except AttributeError:
        name = None
    try:
        byte_size = dwarfutils.extract_byte_size(txt)
    except AttributeError:
        assert "AT_declaration" in txt
        byte_size = -1
    DIEs[off] = DIEStructure(name=name, byte_size=byte_size, members=list())
    parse_struct(off)


def parse_struct(parent_off):
    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, parent_off, children=True)
    level = 0
    for txt in txts[1:]:
        if "TAG_member" in txt:
            if level > 0:
                # ignore
                continue
            parse_member_type(txt)
            DIEs[parent_off].members.append(dwarfutils.extract_offset(txt))
        elif "NULL" in txt:
            level -= 1
            if level < 0:
                return
        elif "TAG_union_type" in txt:
            if not "AT_declaration" in txt:
                level += 1
            if level == 0:
                parse_union_type(txt)
        elif "TAG_structure_type" in txt:
            if not "AT_declaration" in txt:
                level += 1
            if level == 0:
                parse_structure_type(txt)
        else:
            raise NotImplementedError
    else:
        assert len(txts) == 1 or "AT_declaration" in txts[0]


@dataclasses.dataclass
class DIESubroutine(DIE):
    ttype: tuple
    members: list


def parse_subroutine_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        type_off, type_name = dwarfutils.extract_type(txt)
    except AttributeError:
        type_off, type_name = None, "void"
    else:
        extract_and_parse_die(type_off)
    DIEs[off] = DIESubroutine(ttype=(type_off, type_name), members=list())
    parse_subroutine(off)


def parse_subroutine(parent_off):
    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, parent_off, children=True)
    assert dwarfutils.extract_tag(txts[0]) == "TAG_subroutine_type"
    for txt in txts[1:]:
        if "TAG_formal_parameter" in txt:
            off = dwarfutils.extract_offset(txt)
            type_off, type_name = dwarfutils.extract_type(txt)
            extract_and_parse_die(type_off)
            DIEs[off] = DIEFormalParameter(ttype=(type_off, type_name))
            DIEs[parent_off].members.append(off)
        elif "TAG_unspecified_parameters" in txt:
            pass
        elif "NULL" in txt:
            return
        else:
            raise NotImplementedError


@dataclasses.dataclass
class DIETypedef(DIE):
    name: str
    ttype: tuple


def parse_typedef(txt):
    off = dwarfutils.extract_offset(txt)
    name = dwarfutils.extract_name(txt)
    if "__builtin_va_list" in name:
        name = name.upper()
    type_off, type_name = dwarfutils.extract_type(txt)
    extract_and_parse_die(type_off)
    DIEs[off] = DIETypedef(name=name, ttype=(type_off, type_name))


@dataclasses.dataclass
class DIEUnion(DIE):
    name: str
    byte_size: int
    members: list


def parse_union_type(txt):
    off = dwarfutils.extract_offset(txt)
    try:
        name = dwarfutils.extract_name(txt)
    except AttributeError:
        name = None
    byte_size = dwarfutils.extract_byte_size(txt)
    DIEs[off] = DIEUnion(name=name, byte_size=byte_size, members=list())
    parse_union(off)


def parse_union(parent_off):
    parse_struct(parent_off)


@dataclasses.dataclass
class DIEVariable(DIE):
    name: str
    ttype: tuple


def parse_variable_type(txt):
    off = dwarfutils.extract_offset(txt)
    name = dwarfutils.extract_name(txt)
    type_off, type_name = dwarfutils.extract_type(txt)
    extract_and_parse_die(type_off)
    DIEs[off] = DIEVariable(name=name, ttype=(type_off, type_name))


@dataclasses.dataclass
class DIEVolatile(DIE):
    ttype: tuple


def parse_volatile_type(txt):
    off = dwarfutils.extract_offset(txt)
    type_off, type_name = dwarfutils.extract_type(txt)
    extract_and_parse_die(type_off)
    DIEs[off] = DIEVolatile(ttype=(type_off, type_name))


def find_compile_unit(off):
    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, off, parents=True)
    assert "TAG_compile_unit" in txts[0]
    cu_off = dwarfutils.extract_offset(txts[0])
    return cu_off


def extract_and_parse_die(off):
    if off in DIEs:
        print("Using cached {}".format(DIEs[off]), file=sys.stderr)
        return

    txts = dwarfutils.extract_dies_by_offset(args.dwarffile.name, off)
    txt = txts[0]
    print(txt, file=sys.stderr)
    assert dwarfutils.extract_offset(txt) == off

    handlers = {
        "TAG_array_type": parse_array_type,
        "TAG_base_type": parse_base_type,
        "TAG_compile_unit": parse_compile_unit_type,
        "TAG_const_type": parse_const_type,
        "TAG_enumeration_type": parse_enumeration_type,
        "TAG_member": parse_member_type,
        "TAG_pointer_type": parse_pointer_type,
        "TAG_structure_type": parse_structure_type,
        "TAG_subroutine_type": parse_subroutine_type,
        "TAG_typedef": parse_typedef,
        "TAG_union_type": parse_union_type,
        "TAG_variable": parse_variable_type,
        "TAG_volatile_type": parse_volatile_type,
    }
    tag = dwarfutils.extract_tag(txt)
    try:
        return handlers[tag](txt)
    except KeyError:
        raise NotImplementedError


def _compute_deps(off, deps_cache, ptroffs):
    if off in deps_cache:
        return deps_cache[off]
    die = DIEs[off]

    deps = [off]

    if any((isinstance(die, DIEBase), isinstance(die, DIEEnumeration))):
        deps_cache[off] = deps
        return deps

    elif any(
        (
            isinstance(die, DIEArray),
            isinstance(die, DIEConst),
            isinstance(die, DIEFormalParameter),
            isinstance(die, DIEMember),
            isinstance(die, DIETypedef),
            isinstance(die, DIEVariable),
            isinstance(die, DIEVolatile),
        )
    ):
        type_off, type_name = die.ttype
        if type_off and type_name:
            deps.extend(_compute_deps(type_off, deps_cache, ptroffs))

        deps_cache[off] = deps
        return deps

    elif any((isinstance(die, DIEStructure), isinstance(die, DIESubroutine), isinstance(die, DIEUnion))):
        if isinstance(die, DIESubroutine):
            type_off, type_name = die.ttype
            if type_off and type_name:
                deps.extend(_compute_deps(type_off, deps_cache, ptroffs))

        for mem_off in die.members:
            deps.extend(_compute_deps(mem_off, deps_cache, ptroffs))

        deps_cache[off] = deps
        return deps

    elif isinstance(die, DIEPointer):
        if off in ptroffs:
            # cycling
            return deps

        type_off, type_name = die.ttype
        if type_off and type_name:
            ptroffs = ptroffs | {off}
            deps.extend(_compute_deps(type_off, deps_cache, ptroffs))

        deps_cache[off] = deps
        return deps

    else:
        raise NotImplementedError


def _resolve_type(die):
    try:
        type_off, type_name = die.ttype
    except AttributeError:
        child_off = None
    else:
        if type_off:
            # TODO this is for void*
            child_off = DIEs[type_off]
        else:
            child_off = None

    if isinstance(die, DIEArray):
        return "{}[{}]".format(_resolve_type(child_off), die.size if die.size >= 0 else "")

    elif isinstance(die, DIEBase):
        return die.name

    elif isinstance(die, DIEConst):
        return "const {}".format(_resolve_type(child_off) if child_off else "void")

    elif isinstance(die, DIEEnumeration):
        if die.name:
            return "enum {}".format(die.name)
        else:
            members = "\n".join(
                "{} = {},".format(DIEs[mem_off].name, DIEs[mem_off].const_value) for mem_off in die.members
            )
            return "enum {{\n{}\n}}".format(members)

    elif isinstance(die, DIEFormalParameter):
        return _resolve_type(child_off)

    elif isinstance(die, DIEMember):
        return _resolve_type(child_off)

    elif isinstance(die, DIEPointer):
        if not child_off:
            return "void*"
        return "{}*".format(_resolve_type(child_off))

    elif any((isinstance(die, DIEStructure), isinstance(die, DIEUnion))):
        dtype = "struct" if isinstance(die, DIEStructure) else "union"
        if die.name:
            return "{} {}".format(dtype, die.name)
        else:
            members = "\n".join(_generate_declaration(mem_off) for mem_off in die.members)
            return "{} {{\n{}\n}}".format(dtype, members)

    elif isinstance(die, DIESubroutine):
        members = ",".join(_generate_declaration(mem_off).replace(";", "") for mem_off in die.members)
        return "{} ()({})".format(_resolve_type(child_off) if child_off else "void", members)

    elif isinstance(die, DIETypedef):
        return die.name

    elif isinstance(die, DIEVariable):
        return _resolve_type(child_off)

    elif isinstance(die, DIEVolatile):
        return "volatile {}".format(_resolve_type(child_off))

    raise NotImplementedError


def _member_off(die):
    try:
        return "/* off=0x{:04x} */".format(die.location)
    except AttributeError:
        return ""
    except TypeError:
        return "/* off=0x{:04x} bit={} */".format(die.location[0], die.location[1])


def _dwarf_off(off):
    return "/* die=0x{:x} */".format(off)


def _struct_info(off):
    return "/* size=0x{:x} die=0x{:x} */".format(DIEs[off].byte_size, off)


def _generate_declaration(off):
    die = DIEs[off]
    type_str = _resolve_type(die)

    try:
        name = die.name
    except AttributeError:
        assert isinstance(die, DIEFormalParameter)
        name = ""
    else:
        if name is None:
            assert isinstance(die, DIEMember)
            # unnamed struct, union, enum
            name = ""

    try:
        bit_size = die.bit_size
    except AttributeError:
        pass
    else:
        if bit_size >= 0:
            assert isinstance(die, DIEMember)
            return "{} {}:{};  {}".format(type_str, name, bit_size, _member_off(die))

    try:
        (array_size_with_brackets,) = re.search(r"(\[\d*\])$", type_str).groups()
    except AttributeError:
        pass
    else:
        return "{} {}{};  {}".format(
            type_str.replace(array_size_with_brackets, ""), name, array_size_with_brackets, _member_off(die)
        )

    try:
        ret_type_str, params, ptrs = re.search(r"(.*?) *\(\)\((.*?)\)(\**)$", type_str).groups()
    except AttributeError:
        pass
    else:
        return "{} ({}{})({});  {}".format(ret_type_str, ptrs, name, params, _member_off(die))

    return "{} {};  {}".format(type_str, name, _member_off(die))


def _generate_definition(off):
    die = DIEs[off]

    if isinstance(die, DIEEnumeration):
        assert die.name
        members = "\n".join("{} = {},".format(DIEs[mem_off].name, DIEs[mem_off].const_value) for mem_off in die.members)
        return "enum {} {{\n{}\n}}; {}".format(die.name, members, _dwarf_off(off))

    elif any((isinstance(die, DIEStructure), isinstance(die, DIEUnion))):
        assert die.name
        dtype = "struct" if isinstance(die, DIEStructure) else "union"
        if die.byte_size == -1:
            return "{} {}; {}".format(dtype, die.name, _dwarf_off(off))
        members = "\n".join(_generate_declaration(mem_off) for mem_off in die.members)
        return "{} {} {{\n{}\n}}; {}".format(dtype, die.name, members, _struct_info(off))

    elif isinstance(die, DIETypedef):
        type_off, _ = die.ttype
        child_off = DIEs[type_off]

        child_type_str = _resolve_type(child_off)
        try:
            (array_size_with_brackets,) = re.search(r"(\[\d*\])$", child_type_str).groups()
        except AttributeError:
            pass
        else:
            return "typedef {} {}{}; {}".format(
                child_type_str.replace(array_size_with_brackets, ""),
                die.name,
                array_size_with_brackets,
                _dwarf_off(off),
            )

        try:
            ret_type_str, params, ptrs = re.search(r"(.+?) \(\)\((.*?)\)(\*?)$", child_type_str).groups()
        except AttributeError:
            pass
        else:
            return "typedef {} ({}{})({}); {}".format(ret_type_str, ptrs, die.name, params, _dwarf_off(off))

        return "typedef {} {}; {}".format(child_type_str, die.name, _dwarf_off(off))

    elif isinstance(die, DIEVariable):
        return _generate_declaration(off)

    raise NotImplementedError


def generate_c_source(offs):
    deps_cache = {}
    deps = list()
    for off in offs:
        curr_deps = _compute_deps(off, deps_cache, set())
        curr_deps = list(reversed(curr_deps))
        deps = curr_deps + deps
    # remove duplicates maintaining the order
    deps = list(collections.OrderedDict.fromkeys(deps))

    csource = ""
    for off in deps:
        die = DIEs[off]
        if (
            not any(
                (
                    isinstance(die, DIEEnumeration),
                    isinstance(die, DIEStructure),
                    isinstance(die, DIETypedef),
                    isinstance(die, DIEUnion),
                    isinstance(die, DIEVariable),
                )
            )
            or die.name is None
        ):
            continue
        csource += "{}\n\n".format(_generate_definition(off))
    return csource


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dwarffile", type=argparse.FileType())
    parser.add_argument("offset", type=lambda n: int(n, 0), nargs="+")
    args = parser.parse_args()

    DIEs = dwarfutils.load_cache(args.dwarffile.name)

    # extract and parse DIEs at the specified offsets
    print("Extracting DIEs...")
    CUs = collections.defaultdict(set)
    for off in args.offset:
        cu_off = find_compile_unit(off)
        extract_and_parse_die(cu_off)
        CUs[cu_off].add(off)

        extract_and_parse_die(off)

    dwarfutils.save_cache(args.dwarffile.name, DIEs)

    # generate C source files, one per CU
    print("Generating C sources...")
    outdirpath = tempfile.mkdtemp()
    for cu_off, offs in CUs.items():
        cu = DIEs[cu_off]
        # assume no multiple CUs with the same basename...
        cfilename = os.path.basename(cu.name)
        with open(os.path.join(outdirpath, cfilename), "w") as f:
            csource = generate_c_source(offs)
            f.write(csource)

    # print the output directory so that other scripts know where to look
    print("Output directory: '{}'".format(outdirpath))
