#!/usr/bin/env python
import os
import pickle
import re
import subprocess
import sys

dwarfdump = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "dwarfdump")


def extract_dies_by_name(dwarffilepath, name, children=False, parents=False):
    return extract_dies(["--name={}".format(name), dwarffilepath], children, parents)


def extract_dies_by_offset(dwarffilepath, offset, children=False, parents=False):
    return extract_dies(["--debug-info={}".format(offset), dwarffilepath], children, parents)


def extract_dies(dwarfdumpargs, children, parents):
    popenargs = [dwarfdump, "--verbose"] + dwarfdumpargs
    if children:
        popenargs.append("--show-children")
    if parents:
        popenargs.append("--show-parents")
    stdout = subprocess.run(popenargs, stdout=subprocess.PIPE).stdout.decode("ascii")
    dies = stdout.strip().split("\n\n")[1:]
    return dies


def extract_uuid(dwarffilepath):
    stdout = subprocess.run([dwarfdump, "--uuid", dwarffilepath], stdout=subprocess.PIPE).stdout.decode("ascii")
    uuid = stdout.strip().split()[1]
    return uuid


def _compute_cache_filepath(dwarffilepath):
    return "/tmp/cache-{}.pickle".format(extract_uuid(dwarffilepath))


def load_cache(dwarffilepath):
    try:
        with open(_compute_cache_filepath(dwarffilepath), "rb") as f:
            DIEs = pickle.load(f)
            return DIEs
    except FileNotFoundError:
        return {}


def save_cache(dwarffilepath, DIEs):
    with open(_compute_cache_filepath(dwarffilepath), "wb") as f:
        pickle.dump(DIEs, f)


re_bit_offset = re.compile(r"AT_data_bit_offset\( (0x[0-9a-f]+) \)")
re_bit_size = re.compile(r"AT_bit_size\( (0x[0-9a-f]+) \)")
re_byte_size = re.compile(r"AT_byte_size\( (0x[0-9a-f]+) \)")
re_const_value = re.compile(r"AT_const_value\( (0x[0-9a-f]+) \)")
re_count = re.compile(r"AT_count\( (0x[0-9a-f]+) \)")
re_decl_file = re.compile(r'AT_decl_file\( .*?"(.+?)" \)')
re_decl_line = re.compile(r"AT_decl_line\( .*?\( ([0-9]+) \) \)")
re_location = re.compile(r"AT_data_member_location\( (?:.+?plus-uconst )?.+(0x[0-9a-f]+?) \)")
re_name = re.compile(r'AT_name\( .*?"(.+?)" \)')
re_offset = re.compile(r"^(0x[0-9a-f]+)\:")
re_tag = re.compile(r"(TAG\_.+?) ")
re_ttype = re.compile(r"AT_type\( .*?\{(0x[0-9a-f]+)\} \( +(.+?) +\) \)")


def extract_bit_size(textdie):
    (bit_size,) = re_bit_size.search(textdie).groups()
    bit_size = int(bit_size, 16)
    return bit_size


def extract_byte_size(textdie):
    (byte_size,) = re_byte_size.search(textdie).groups()
    byte_size = int(byte_size, 16)
    return byte_size


def extract_const_value(textdie):
    (const_value,) = re_const_value.search(textdie).groups()
    const_value = int(const_value, 16)
    return const_value


def extract_count(textdie):
    (count,) = re_count.search(textdie).groups()
    count = int(count, 16)
    return count


def extract_decl_file(textdie):
    (decl_file,) = re_decl_file.search(textdie).groups()
    return decl_file


def extract_decl_line(textdie):
    (decl_line,) = re_decl_line.search(textdie).groups()
    decl_line = int(decl_line)
    return decl_line


def extract_location(textdie):
    (location,) = re_location.search(textdie).groups()
    location = int(location, 16)
    return location


def extract_bit_location(textdie):
    (bit_offset,) = re_bit_offset.search(textdie).groups()
    bit_offset = int(bit_offset, 16)
    location = (bit_offset // 0x8, bit_offset % 0x8)
    return location


def extract_name(textdie):
    (name,) = re_name.search(textdie).groups()
    return name


def extract_offset(textdie):
    (offset,) = re_offset.search(textdie).groups()
    offset = int(offset, 16)
    return offset


def extract_tag(textdie):
    (tag,) = re_tag.search(textdie).groups()
    return tag


def extract_type(textdie):
    ttype_offset, ttype_name = re_ttype.search(textdie).groups()
    ttype_offset = int(ttype_offset, 16)
    return (ttype_offset, ttype_name)
