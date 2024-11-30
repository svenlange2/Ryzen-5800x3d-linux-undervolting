#!/bin/python

import os
import struct
import argparse
from time import sleep

FS_PATH = "/sys/kernel/ryzen_smu_drv/"

VER_PATH = FS_PATH + "version"
SMU_ARGS = FS_PATH + "smu_args"
MP1_CMD = FS_PATH + "mp1_smu_cmd"


def is_root():
    return os.getenv("SUDO_USER") is not None or os.geteuid() == 0


def driver_loaded():
    return os.path.isfile(VER_PATH)


def read_file(file, size):
    with open(file, "rb") as fp:
        result = fp.read(size)
    return result


def write_file(file, data):
    with open(file, "wb") as fp:
        return fp.write(data)


def read_file32(file):
    result = read_file(file, 4)
    return struct.unpack("<I", result)[0]


def write_file32(file, value):
    data = struct.pack("<I", value)
    result = write_file(file, data)

    return result == 4


def read_file192(file):
    result = read_file(file, 24)
    return struct.unpack("<IIIIII", result)


def write_file192(file, *values):
    data = struct.pack("<IIIIII", *values)
    result = write_file(file, data)

    return result == 24


def smu_command(op, arg1, arg2=0, arg3=0, arg4=0, arg5=0, arg6=0):
    # Check if SMU is currently executing a command
    value = read_file32(MP1_CMD)
    if not value:
        print("Failed to get SMU status response")
        return False

    while int(value) == 0:
        print("Waiting for existing SMU command to complete...")
        sleep(1)
        value = read_file32(MP1_CMD)

    # Write all arguments to the appropriate files
    if not write_file192(SMU_ARGS, arg1, arg2, arg3, arg4, arg5, arg6):
        print("Failed to write SMU arguments")
        return False

    # Write the command
    if not write_file32(MP1_CMD, op):
        print("Failed to execute the SMU command: {:08X}".format(op))

    # Check for the result:
    value = read_file32(MP1_CMD)
    if not value:
        print("SMU OP readback returned false")
        return False

    while value == 0:
        print("Waiting for existing SMU command to complete...")
        sleep(1)
        value = read_file32(MP1_CMD)

    if value != 1:
        print("SMU Command Result Failed: " + value)
        return False

    args = read_file192(SMU_ARGS)

    if not args:
        print("Failed to read SMU response arguments")
        return False

    return args


def get_core_offset(core_id):
    result = smu_command(0x48, ((core_id & 8) << 5 | core_id & 7) << 20)
    # Result could be a boolean False
    if result:
        value = result[0]
        if value > 2**31:
            value = value - 2**32
        return value


def set_core_offset(core_id, value):
    smu_command(0x35, ((core_id & 8) << 5 | core_id & 7) << 20 | value & 0xFFFF)


if not is_root():
    print("Script must be run with root privileges.")
    quit(1)

if not driver_loaded():
    print("The driver doesn't seem to be loaded.")
    quit(1)


parser = argparse.ArgumentParser(
    description="PBO undervolt for Ryzen 5800X3D processor"
)
parser.add_argument("-l", "--list", action="store_true", help="List curve offsets")
parser.add_argument("-o", "--offset", type=int, help="Set curve offset")
parser.add_argument(
    "-c", "--corecount", default=1, type=int, help="Set offset to cores [0..corecount]"
)
parser.add_argument("-r", "--reset", action="store_true", help="Reset offsets to 0")


args = parser.parse_args()
cc = 1
if args.corecount:
    cc = args.corecount

if args.list:
    for c in range(0, cc):
        print("Core {}: {}".format(c, get_core_offset(c)))
    quit()
if args.reset:
    smu_command(0x36, 0)
    print("Offsets set to 0 on all cores!")
    quit()
if args.offset:
    for c in range(0, cc):
        if args.offset >= 0:
            print("Offset needs to be negative!")
            quit(1)

        set_core_offset(c, args.offset)
        print(
            "Core {} set to: {} readback: {}".format(c, args.offset, get_core_offset(c))
        )
else:
    parser.print_help()
