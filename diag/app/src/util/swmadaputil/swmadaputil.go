package main

import (
    "fmt"
    //"os"

    "common/cli"
    "common/errType"
    "common/misc"

    "flag"
    "strings"
    "hardware/i2cinfo"

    "device/cpld/cpldSmb"

    "device/cpld/naples25swmAdapCpld"
)

func init() {
}

func myUsage() {
    flag.PrintDefaults()
}


const SMI_CMD_REG	uint8 =     0x18
const SMI_DATA_REG	uint8 =	    0x19
const SMI_PHY_ADDR	uint8 =	    0x1C
const SMI_BUSY		uint16 =	(1 << 15)
const SMI_MODE		uint16 =	(1 << 12)
const SMI_READ		uint16 =	(1 << 11)
const SMI_WRITE		uint16 =	(1 << 10)
const SMI_DEV_SHIFT	uint16 =	5

const MVSW_PORT0    uint8 = 0x10
const MVSW_PORT1    uint8 = 0x11
const MVSW_PORT2    uint8 = 0x12
const MVSW_PORT3    uint8 = 0x13
const MVSW_PORT4    uint8 = 0x14
const MVSW_PORT5    uint8 = 0x15
const MVSW_PORT6    uint8 = 0x16

const MVSW_SMI_PORT0    uint8 = 0x0C
const MVSW_SMI_PORT1    uint8 = 0x0D
const MVSW_SMI_PORT3    uint8 = 0x03
const MVSW_SMI_PORT4    uint8 = 0x04

const GLOBAL1_PHY_ADDR  uint8 =	0x1B
const GLOBAL2_PHY_ADDR  uint8 =	0x1C

const MVSW_STAT_BUSY    			uint16 = (1<<15) 

const MVSW_STAT_STATS_OP_SHIFT      uint16 = 12
const MVSW_STAT_FLUSH_ALL_PORTS     uint16 = 0x1
const MVSW_STAT_FLUSH_PER_PORT      uint16 = 0x2
const MVSW_STAT_RD_CAPTURED_PORT    uint16 = 0x4
const MVSW_STAT_TYPE_OFFSET			uint16 = 0
const MVSW_STAT_PORT_SHIFT			uint16 = 5
const MVSW_GLB1_STAT_OPER_REG       uint8 = 0x1D
const MVSW_GLB1_STAT_CNT_HI_REG		uint8 =	0x1E
const MVSW_GLB1_STAT_CNT_LO_REG		uint8 =	0x1F



// Ingress Counters
const RMON_IN_GOOD_OCTETS_LO   uint8 = 0x00
const RMON_IN_GOOD_OCTETS_HI   uint8 = 0x01
const RMON_IN_BAD_OCTETS       uint8 = 0x02
const RMON_IN_UNICAST          uint8 = 0x04
const RMON_IN_BROADCAST        uint8 = 0x06
const RMON_IN_MULTICAST        uint8 = 0x07
const RMON_IN_PAUSE            uint8 = 0x16
const RMON_IN_UNDERSIZE        uint8 = 0x18
const RMON_IN_FRAGMENTS        uint8 = 0x19
const RMON_IN_OVERSIZE         uint8 = 0x1A
const RMON_IN_JABBER           uint8 = 0x1B
const RMON_IN_RX_ERR           uint8 = 0x1C
const RMON_IN_FCS_ERR          uint8 = 0x1D
const RMON_64_OCTETS           uint8 = 0x08
const RMON_65_127_OCTETS       uint8 = 0x09
const RMON_128_255_OCTETS      uint8 = 0x0A
const RMON_256_511_OCTETS      uint8 = 0x0B
const RMON_512_1023_OCTETS     uint8 = 0x0C
const RMON_1024_MAX_OCTETS     uint8 = 0x0D

// Egress Counters
const RMON_OUT_OCTETS_LO       uint8 = 0x0E
const RMON_OUT_OCTETS_HI       uint8 = 0x0F
const RMON_OUT_UNICAST         uint8 = 0x10
const RMON_OUT_BROADCAST       uint8 = 0x13
const RMON_OUT_MULTICAST       uint8 = 0x12
const RMON_OUT_PAUSE           uint8 = 0x15
const RMON_COLLISIONS          uint8 = 0x1E
const RMON_DEFERRED            uint8 = 0x5
const RMON_SINGLE              uint8 = 0x14
const RMON_MULTIPLE            uint8 = 0x17
const RMON_OUT_FCS_ERR         uint8 = 0x03
const RMON_EXCESSIVE           uint8 = 0x11
const RMON_LATE                uint8 = 0x1F




type RmonInfo struct {
    statname string
    reg uint8
}

var RmonIngressStruct = []RmonInfo {
    RmonInfo{"IN_GOOD_OCTETS_LO",       RMON_IN_GOOD_OCTETS_LO   },
    RmonInfo{"IN_GOOD_OCTETS_HI",       RMON_IN_GOOD_OCTETS_HI   },
    RmonInfo{"IN_BAD_OCTETS",           RMON_IN_BAD_OCTETS       },
    RmonInfo{"IN_UNICAST",              RMON_IN_UNICAST          },
    RmonInfo{"IN_BROADCAST",            RMON_IN_BROADCAST        },
    RmonInfo{"IN_MULTICAST",            RMON_IN_MULTICAST        },
    RmonInfo{"IN_PAUSE",                RMON_IN_PAUSE            },
    RmonInfo{"IN_UNDERSIZE",            RMON_IN_UNDERSIZE        },
    RmonInfo{"IN_FRAGMENTS",            RMON_IN_FRAGMENTS        },
    RmonInfo{"IN_OVERSIZE",             RMON_IN_OVERSIZE         },
    RmonInfo{"IN_JABBER",               RMON_IN_JABBER           },
    RmonInfo{"IN_RX_ERR",               RMON_IN_RX_ERR           },
    RmonInfo{"IN_FCS_ERR",              RMON_IN_FCS_ERR          },
    RmonInfo{"64_OCTETS",               RMON_64_OCTETS           },
    RmonInfo{"65_127_OCTETS",           RMON_65_127_OCTETS       },
    RmonInfo{"128_255_OCTETS",          RMON_128_255_OCTETS      },
    RmonInfo{"256_511_OCTETS",          RMON_256_511_OCTETS      },
    RmonInfo{"512_1023_OCTETS",         RMON_512_1023_OCTETS     },
    RmonInfo{"1024_MAX_OCTETS",         RMON_1024_MAX_OCTETS     },
}

var RmonEgressStruct = []RmonInfo {
    RmonInfo{"OUT_OCTETS_LO",       RMON_OUT_OCTETS_LO       },
    RmonInfo{"OUT_OCTETS_HI",       RMON_OUT_OCTETS_HI       },
    RmonInfo{"OUT_UNICAST",         RMON_OUT_UNICAST         },
    RmonInfo{"OUT_BROADCAST",       RMON_OUT_BROADCAST       },
    RmonInfo{"OUT_MULTICAST",       RMON_OUT_MULTICAST       },
    RmonInfo{"OUT_PAUSE",           RMON_OUT_PAUSE           },
    RmonInfo{"DEFERRED",            RMON_DEFERRED            },
    RmonInfo{"COLLISIONS",          RMON_COLLISIONS          },
    RmonInfo{"SINGLE",              RMON_SINGLE              },
    RmonInfo{"MULTIPLE",            RMON_MULTIPLE            },
    RmonInfo{"EXCESSIVE",           RMON_EXCESSIVE           },
    RmonInfo{"LATE",                RMON_LATE                },
    RmonInfo{"OUT_FCS_ERR",         RMON_OUT_FCS_ERR         },
}





func MdioRead(phyAddr uint8, regAddr uint8) (value uint16, err int) {
    err = errType.SUCCESS
    var data8 byte = 0;

    //REGISTER ADDR
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_HIGH), regAddr) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    data8 = 0x01 | 0x02 | ((phyAddr & 0x1f) << 3)
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_LOW), data8)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    data8 = 0x00
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_LOW), data8)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    data8, err = cpldSmb.ReadSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_DATA_LOW))
    value = uint16(data8) & 0xFF
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    data8, err = cpldSmb.ReadSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_DATA_HIGH))
    value |= ((uint16(data8)) << 8)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    return;
}



func MdioWrite(phyAddr uint8, regAddr uint8, wrData uint16) (err int) {
    err = errType.SUCCESS
    var data8 byte = 0;

    //REGISTER ADDR
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_HIGH), regAddr) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    //DATA
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_DATA_LOW), uint8(wrData & 0xFF)) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    //DATA
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_DATA_HIGH), uint8(wrData >> 8)) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    //CMD
    data8 =  0x01 | 0x04 | ((phyAddr & 0x1f) << 3)   //EN ACC / WRITE BIT / PHY ADD
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_LOW), data8) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    data8 =  0x00
    err = cpldSmb.WriteSmb("CPLD_ADAP", uint64(naples25swmAdapCpld.REG_ESW_MDIO_CTRL_LOW), data8) 
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to write device CPLD_ADAP", "at", regAddr)
    }

    return;
}


func MdioSMIRead(phyAddr uint8, regAddr uint8) (value uint16, err int) {
	var data16 uint16 = 0
    err = errType.SUCCESS

	data16 = SMI_BUSY | SMI_MODE | SMI_READ | (uint16(phyAddr & 0x1F) << SMI_DEV_SHIFT) | uint16(regAddr & 0x1F)

    err = MdioWrite(SMI_PHY_ADDR, SMI_CMD_REG, data16)

    misc.SleepInUSec(1000)

    value, err = MdioRead(uint8(SMI_PHY_ADDR), uint8(SMI_DATA_REG))

	return
}


func MdioSMIWrite(phyAddr uint8, regAddr uint8, WRdata uint16) (err int) {
	var data16 uint16 = 0

    err = MdioWrite(SMI_PHY_ADDR, SMI_DATA_REG, WRdata)

    misc.SleepInUSec(1000)
	
    data16 = SMI_BUSY | SMI_MODE | SMI_WRITE | (uint16(phyAddr & 0x1F) << SMI_DEV_SHIFT) | uint16(regAddr & 0x1F)
    err = MdioWrite(SMI_PHY_ADDR, SMI_CMD_REG, data16)

	return
}


func MvSwRmonStatBusy() (err int) {
    err = errType.SUCCESS
    var data16 uint16 = 0
    var i uint32 = 0

    for i=0; i<10; i++ {
        data16, err =  MdioRead(GLOBAL1_PHY_ADDR, MVSW_GLB1_STAT_OPER_REG)
        if err != errType.SUCCESS {
            cli.Printf("e", " Marvell Switch Read Phy Addr 0x%x Failed\n", GLOBAL1_PHY_ADDR)
            return
        }
        if (data16 & MVSW_STAT_BUSY) == 0 {
            break
        }
        misc.SleepInUSec(1000)
    }
    if i == 10 {
        cli.Printf("e", " Marvell Switch Read Rmon Stats Failed.  Reg 0x%x Busy Bit No Clearing.  Data=0x%x\n", MVSW_GLB1_STAT_OPER_REG, data16)
        err = errType.FAIL
    }
    return
}

func MvSwReadRmonStat(portNum uint8, StatRegAddr uint8) (value uint32, err int) {
    err = errType.SUCCESS
    var data16 uint16 = 0
    value = 0
    
    portNum+=1  //port starts at 1 for Marvell

    err = MvSwRmonStatBusy()
    if err != errType.SUCCESS {
        return
    }

    data16 = MVSW_STAT_BUSY | (MVSW_STAT_RD_CAPTURED_PORT << MVSW_STAT_STATS_OP_SHIFT) | (uint16(portNum) << MVSW_STAT_PORT_SHIFT) | uint16(StatRegAddr)
    err = MdioWrite(GLOBAL1_PHY_ADDR, MVSW_GLB1_STAT_OPER_REG, data16)
    if err != errType.SUCCESS {
        return
    }

    err = MvSwRmonStatBusy()
    if err != errType.SUCCESS {
        return
    }

    data16, err =  MdioRead(GLOBAL1_PHY_ADDR, MVSW_GLB1_STAT_CNT_HI_REG)
    if err != errType.SUCCESS {
        return
    }
    value |= (uint32(data16)<<16)

    data16, err =  MdioRead(GLOBAL1_PHY_ADDR, MVSW_GLB1_STAT_CNT_LO_REG)
    if err != errType.SUCCESS {
        return
    }
    value |= uint32(data16)
    

    return
}



func main() {
    flag.Usage = myUsage

    //fmt.Println(os.Args)
    //fmt.Println(os.Args[1])

    readPtr     := flag.Bool(  "mvrd",   false, "Read Marvell Switch register value")
    writePtr    := flag.Bool(  "mvwr",   false, "Write Marvell Switch register value")
    phyPtr      := flag.Uint64("phy", 0,    "Port/Phy addr")
    smiPtr      := flag.Bool(  "smi", false, "Marvell Switch SMI Phy/Serdes access (otherwise switch port access)")
    addrPtr     := flag.Uint64("addr", 0,    "Register addr")
    dataPtr     := flag.Uint64("data", 0,    "Register data")
    uutPtr      := flag.String("uut",  "UUT_NONE", "Target UUT")
    flag.Parse()

    addr := uint8(*addrPtr)
    data := uint16(*dataPtr)
    phyAddr := uint8(*phyPtr)
    uut := strings.ToUpper(*uutPtr)


    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }


    fmt.Printf(" smiPtr=%t\n", *smiPtr)
    fmt.Printf(" phyPtr=%v\n", phyAddr)


    if *readPtr == true {
        if *smiPtr == true {
            dataL, err := MdioSMIRead(phyAddr, addr)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read Marvell Switch (SMI)", "at", addr)
            } else {
                cli.Printf("i", " [RD] PhyAddr=0x%x Reg=0x%x data=0x%x\n", phyAddr, addr, dataL)
            }
        } else {
            dataL, err := MdioRead(phyAddr, addr)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read Marvell Switch", "at", addr)
            } else {
                cli.Printf("i", " [RD] PhyAddr=0x%x Reg=0x%x data=0x%x\n", phyAddr, addr, dataL)
            }
        }
        return
    } else if *writePtr == true {
        if *smiPtr == true {
            err := MdioSMIWrite(phyAddr, addr, data)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read Marvell Switch", "at", addr)
            } else {
                cli.Printf("i", " [WR] PhyAddr=0x%x Reg=0x%x data=0x%x - Done\n", phyAddr, addr, data)
            }
        } else {
            err := MdioWrite(phyAddr, addr, data)
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read Marvell Switch", "at", addr)
            } else {
                cli.Printf("i", " [WR] PhyAddr=0x%x Reg=0x%x data=0x%x - Done\n", phyAddr, addr, data)
            }
        }
        return
    } else {
        myUsage()
    }
}

