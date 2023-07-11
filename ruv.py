#!/bin/python

import os
import struct
import argparse
from time import sleep

FS_PATH = '/sys/kernel/ryzen_smu_drv/'

VER_PATH = FS_PATH + 'version'
SMU_ARGS = FS_PATH + 'smu_args'
MP1_CMD  = FS_PATH + 'mp1_smu_cmd'

def is_root():
    return os.getenv("SUDO_USER") is not None or os.geteuid() == 0

def driver_loaded():
    return os.path.isfile(VER_PATH)


def read_file32(file):
    with open(file, "rb") as fp:
        result = fp.read(4)
        result = struct.unpack("<I", result)[0]
        fp.close()

    return result

def write_file32(file, value):
    with open(file, "wb") as fp:
        result = fp.write(struct.pack("<I", value))
        fp.close()

    return result == 4


def read_file192(file):
    with open(file, "rb") as fp:
        result = fp.read(24)
        result = struct.unpack("<IIIIII", result)
        fp.close()

    return result


def write_file192(file, v1, v2, v3, v4, v5, v6):
    with open(file, "wb") as fp:
        result = fp.write(struct.pack("<IIIIII", v1, v2, v3, v4, v5, v6))
        fp.close()

    return result == 24

def smu_command(op, arg1, arg2 = 0, arg3 = 0, arg4 = 0, arg5 = 0, arg6 = 0):
    check = True

    # Check if SMU is currently executing a command
    value = read_file32(MP1_CMD)
    if value != False:
        while int(value) == 0:
            print("Wating for existing SMU command to complete ...")
            sleep(1)
            value = read_file32(MP1_CMD)
    else:
        print("Failed to get SMU status response")
        return False

    # Write all arguments to the appropriate files
    if write_file192(SMU_ARGS, arg1, arg2, arg3, arg4, arg5, arg6) == False:
        print("Failed to write SMU arguments")
        return False

    # Write the command
    if write_file32(MP1_CMD, op) == False:
        print("Failed to execute the SMU command: {:08X}".format(op))

    # Check for the result:
    value = read_file32(MP1_CMD)
    if value != False:
        while value == 0:
            print("Wating for existing SMU command to complete ...")
            sleep(1)
            value = read_file32(MP1_CMD)
    else:
        print("SMU OP readback returned false")
        return False

    if value != 1:
        print("SMU Command Result Failed: " + value)
        return False

    args = read_file192(SMU_ARGS)

    if args == False:
        print("Failed to read SMU response arguments")
        return False

    return args

def getCoreOffset(core_id):
    value=smu_command(0x48,((core_id & 8) << 5 | core_id & 7) << 20)[0]
    if value > 2**31:
       value=value-2**32
    return value

def setCoreOffset(core_id,value):
    smu_command(0x35,((core_id & 8) << 5 | core_id & 7) << 20 | value & 0xffff)




if is_root() == False:
        print("Script must be run with root privileges.")
        quit()

if driver_loaded() == False:
        print("The driver doesn't seem to be loaded.")
        quit()



parser = argparse.ArgumentParser(description='PBO undervolt for Ryzen processors')
parser.add_argument('-l', '--list', action='store_true', help='List curve offsets')
parser.add_argument('-o', '--offset', type=int, help='Set curve offset')
parser.add_argument('-c', '--corecount', default=1, type=int, help='Set offset to cores [0..corecount]')
parser.add_argument('-r','--reset', action='store_true', help='Reset offsets to 0')


args = parser.parse_args()
cc=1
if args.corecount:
   cc=args.corecount

if args.list:
        for c in range(0,cc):
                print('Core {}: {}'.format(c, getCoreOffset))
        quit()
if args.reset:
        smu_command(0x36,0)
        print("Offsets set to 0 on all cores!")
        quit()
if args.offset:
        for c in range(0,cc):
                if args.offset < 0:
                   setCoreOffset(c,args.offset)
                   print('Core {} set to: {} readback: {}'.format(c, args.offset, getCoreOffset(c)))
                else:
                   print("Offset needs to be negative!")
                   quit()
else:
    parser.print_help()
