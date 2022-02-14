#!/usr/bin/env python

import re
import sys

# constant and data structure definition in go
title_str = """package pmbusCmd

// Access mode
const (
    NA          = 0
    WRITE_BYTE  = 1
    WRITE_WORD  = 2
    READ_BYTE   = 3
    READ_WORD   = 4
    READ_32     = 5
    BLOCK_WRITE = 6
    BLOCK_READ  = 7
    BLOCK_WRP   = 8
    SEND_BYTE   = 9
    RCV_BYTE    = 10
    EXT_CMD     = 11
    MFR_DEF     = 12
)

// Number of bytes
const (
    NB_NA      = 0xFD
    NB_VAR     = 0xFE
    NB_MFR_DEF = 0xFF
)

// Register info structure
type regInfo_t struct {
    write    int
    read     int
    numBytes int
}

var Reg = map[int]regInfo_t{}

"""

# Matching pattern for registers in use
re_pattern = (
    "^([0-9A-Z][0-9A-Z])h "
    "(.*) "
    "(N/A|Write Byte|Write Word|Extended Command|Mfr Defined|Block Write|Send Byte) "
    "(N/A|Block Write-Block Read Process Call|Block Read|Read Byte|Read Word|Extended Command|Mfr Defined|Block Read|Read 32) "
    "([0-9]|Variable|Mfr Defined)|[0-9][0-9]$"
)

# Matching pattern for reserved registers
re_pattern_rev = "^([0-9A-Z][0-9A-Z])h Reserved.*$"

# Register constant
const_start = "const (\n"
const_fmt = "    {:<25} = 0x{}\n"
const_end = ")\n\n"

# Register access property mapping
fmt_reg_pre = "func init() {\n"
fmt_reg = "    Reg[{}] = regInfo_t{{{}, {}, {}}}\n"
fmt_reg_post = "}\n"

mode_dict = {"N/A": "NA",
        "Write Byte": "WRITE_BYTE",
        "Write Word": "WRITE_WORD",
        "Read Byte": "READ_BYTE",
        "Read Word": "READ_WORD",
        "Read 32": "READ_32",
        "Block Write": "BLOCK_WRITE",
        "Block Read": "BLOCK_READ",
        "Block Write-Block Read Process Call": "BLOCK_WRP",
        "Send Byte": "SEND_BYTE",
        "Extended Command": "EXT_CMD",
        "Mfr Defined": "MFR_DEF",
        }

nb_dict = {"Variable": "NB_VARIABLE",
           "Mfr Defined": "NB_MFR_DEFINED",
        }

with open("./temp1") as f:
        content = f.readlines()

f = open('pmbusReg.go', 'w')
f.write(title_str)

re_p = re.compile(re_pattern)
re_p_rev = re.compile(re_pattern_rev)

# Output pmbus command constant defintion 
f.write(const_start)
count = 0
rsvd_idx = 0
for line in content:
    m = re_p.match(line)
    if m:
        code = m.group(1)
        name = m.group(2)

        f.write(const_fmt.format(name, code))
        count = count + 1
        continue

    m = re_p_rev.match(line)
    if m:
        code = m.group(1)
        name = "RESERVED_"+code

        f.write(const_fmt.format(name, code))
        #print m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        count = count + 1
        rsvd_idx = rsvd_idx + 1
        continue

    raise NameError("ERROR! unhandle line: "+line)
f.write(const_end)
print "count = ", count
#sys.exit()

count = 0
rsvd_idx = 0
f.write(fmt_reg_pre)
for line in content:
    m = re_p.match(line)
    if m:
        code = m.group(1)
        name = m.group(2)
        write = mode_dict[m.group(3)]
        read = mode_dict[m.group(4)]

        if m.group(5) == "Variable":
            num_bytes = "NB_VAR"
        elif m.group(5) == "Mfr Defined":
            num_bytes = "NB_MFR_DEF"
        else:
            num_bytes = m.group(5)

        # Output register details
        f.write(fmt_reg.format(name, write, read, num_bytes))

        count = count + 1
        continue

    m = re_p_rev.match(line)
    if m:
        code = m.group(1)
        name = "RESERVED_"+code

        f.write(fmt_reg.format(name, "NA", "NA", "NB_NA"))
        count = count + 1
        rsvd_idx = rsvd_idx + 1
        continue

    raise NameError("ERROR! unhandle line: "+line)
f.write(fmt_reg_post)

f.close()
print "count = ", count
